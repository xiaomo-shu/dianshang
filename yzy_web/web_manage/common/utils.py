import uuid
import time
import hashlib
import logging
import base64
import netaddr
import socket
import struct
import random

from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from rest_framework.renderers import JSONRenderer
from django.http import HttpResponse, JsonResponse
from django.db import models
from django.db.utils import OperationalError
from django.db.models.query import QuerySet
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework.response import Response
from collections import OrderedDict
from rest_framework.authentication import BaseAuthentication,TokenAuthentication
from .errcode import get_error_result
from rest_framework import exceptions
from rest_framework import HTTP_HEADER_ENCODING
from django.core.cache import cache
from rest_framework.permissions import BasePermission
from .constants import *


logger = logging.getLogger(__name__)


# 自定义软删除查询基类
class SoftDeletableQuerySetMixin(object):
    """
    QuerySet for SoftDeletableModel. Instead of removing instance sets
    its ``is_deleted`` field to True.
    """

    def delete(self):
        """
        Soft delete objects from queryset (set their ``is_deleted``
        field to True)
        """
        now_time = timezone.now()
        self.update(deleted=self.id, deleted_at=now_time)


class SoftDeletableQuerySet(SoftDeletableQuerySetMixin, QuerySet):
    pass


class SoftDeletableManagerMixin(object):
    """
    Manager that limits the queryset by default to show only not deleted
    instances of model.
    """
    _queryset_class = SoftDeletableQuerySet

    def get_queryset(self):
        """
        Return queryset limited to not deleted entries.
        """
        kwargs = {'model': self.model, 'using': self._db}
        if hasattr(self, '_hints'):
            kwargs['hints'] = self._hints

        return self._queryset_class(**kwargs).filter(deleted=False)


class SoftDeletableManager(SoftDeletableManagerMixin, models.Manager):
    pass


# 自定义软删除抽象基类
class SoftDeletableModel(models.Model):
    """
    An abstract base class model with a ``is_deleted`` field that
    marks entries that are not going to be used anymore, but are
    kept in db for any reason.
    Default manager returns only not-deleted entries.
    """
    deleted = models.IntegerField(default=0)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True

    objects = SoftDeletableManager()

    def delete(self, using=None, soft=True, *args, **kwargs):
        """
        Soft delete object (set its ``is_deleted`` field to True).
        Actually delete object if setting ``soft`` to False.
        """
        if soft:
            self.deleted = self.id
            self.deleted_at = timezone.now()
            self.save(using=using)
        else:
            return super(SoftDeletableModel, self).delete(using=using, *args, **kwargs)


class YzyWebPagination(PageNumberPagination):
    page_size = 2000 # 表示每页的默认显示数量
    page_size_query_param = 'page_size' # 表示url中每页数量参数
    page_query_param = 'page' # 表示url中的页码参数
    max_page_size = 2000  # 表示每页最大显示数量，做限制使用，避免突然大量的查询数据，数据库崩溃

    def get_paginated_response(self, data, ext_dict=None):
        _resp = {"code": 0, "msg": "成功"}
        _dict = OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ])
        if ext_dict:
            _dict.update(ext_dict)
        _resp["data"] = _dict
        # if ext_dict:
        #     _resp.update(ext_dict)
        # return JSONResponse(_resp)
        return Response(_resp)


class JSONResponse(HttpResponse):

    def __init__(self, data, **kwargs):
        _status = kwargs.get("status", status.HTTP_200_OK)
        if status.is_success(_status):
            if "code" in data:
                if data["code"] == 0:
                    _d = data.get("data", {})
                    data = {"code": 0, "msg": data.get("msg", "成功"), "data": _d}
                # else:
                #     kwargs.update({"status": status.HTTP_404_NOT_FOUND})
            else:
                data = {"code": 0, "msg": "成功", "data": data}
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)
        super(JSONResponse, self).__setitem__("Access-Control-Allow-Origin", "*")


def create_uuid():
    return str(uuid.uuid4())


def create_md5(s, salt=''):
    new_s = str(s) + salt
    m = hashlib.md5(new_s.encode())
    return m.hexdigest()


class ServerHttpClient():
    """
    服务端接口
    """


def get_authorization_header(request):
    auth = request.META.get('HTTP_AUTHORIZATION', b'')
    if isinstance(auth, type('')):
        auth = auth.encode(HTTP_HEADER_ENCODING)
    return auth


def param_error(error, **kwargs):
    return JsonResponse(get_error_result(error, **kwargs), status=200,
                        json_dumps_params={'ensure_ascii': False})


def datetime_to_timestamp(times):
    time_strp = time.strptime(times, "%Y-%m-%d %H:%M:%S")
    timestamp = int(time.mktime(time_strp))
    return timestamp


class CustomDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        utc = timezone.utc
        # 先将时间值设置为UTC时区
        tz = timezone.get_default_timezone()
        # 转换时区
        local = value.replace(tzinfo=utc).astimezone(tz)
        output_format = '%Y-%m-%d %H:%M:%S'
        return local.strftime(output_format)


class DateTimeFieldMix(serializers.ModelSerializer):

    deleted_at = CustomDateTimeField(read_only=True)
    updated_at = CustomDateTimeField(read_only=True)
    created_at = CustomDateTimeField(read_only=True)


class YzyAuthentication(BaseAuthentication):
    '''认证类'''

    # def authenticate(self, request):
    #     token = request._request.GET.get("token")
    #     token_obj = models.member_token.objects.filter(token=token).first()
    #     if not token_obj:
    #         raise exceptions.AuthenticationFailed('用户认证失败')
    #     return (token_obj.user, token_obj)  # 这里返回值一次给request.user,request.auth

    # def authenticate_header(self, request):
    #     pass

    def authenticate(self, request):
        auth = get_authorization_header(request)
        if not auth:
            raise exceptions.AuthenticationFailed("用户认证失败")
        try:
            token = auth.decode()
        except UnicodeError as e:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)
        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        # 解决循环导入问题
        from web_manage.yzy_admin.models import YzyAdminUser, YzyRole
        try:
            # token string:1 <==> base64 string
            _s = base64.b64decode(key[6:]).decode("utf-8")
            token, uid = _s.split(":")
            if not token or not cache.get(token):
                logger.error("token not exist")
                raise Exception("token not exist")

            cache_user = cache.get(token)
            if uid != str(cache_user.id):
                logger.error("user id is not correct")
                raise Exception("token error")
        except Exception as e:
            raise exceptions.AuthenticationFailed('auth fail.')
        try:
            _id = cache_user.id
            try:
                user = YzyAdminUser.objects.filter(deleted=False).get(id=_id)
                if not user.is_active:
                    logger.error("the account has been disabled:%s" % _id)
                    raise Exception("account has disabled")
            except OperationalError as e:
                return cache_user, token
            role = YzyRole.objects.filter(deleted=False).get(id=user.role_id)
            if not role.enable:
                logger.error("the account permission is disabled: %s" % role.role)
                raise Exception("account permission is disabled")
        except Exception as e:
            raise exceptions.PermissionDenied('No authority')
        return cache_user, token

    def authenticate_header(self, request):
        return 'Token'


class YzyPermission(BasePermission):

    def has_permission(self, request, view):
        # print("permission .....")
        if request._request.path.endswith("/menus/"):
            return True

        if not request.user:
            return False

        return True


def errors_to_str(errors):
    s = []
    for k, v in errors.items():
        s.append("(%s:%s)"% (k, "|".join(v)))

    return " " + ",".join(s)


def is_ip_addr(ip):
    try:
        netaddr.IPAddress(ip)
        return True
    except:
        return False


def is_netmask(ip):
    ip_addr = netaddr.IPAddress(ip)
    return ip_addr.is_netmask(), ip_addr.netmask_bits()


def find_ips(start, end):
    ipstruct = struct.Struct('>I')
    start, = ipstruct.unpack(socket.inet_aton(start))
    end, = ipstruct.unpack(socket.inet_aton(end))
    return [socket.inet_ntoa(ipstruct.pack(i)) for i in range(start, end+1)]


def size_to_G(size, bit=2):
    return round(size / Gi, bit)


def size_to_M(size, bit=2):
    return round(size / Mi, bit)


def gi_to_section(size):
    return int(size * 1024 * 1024 * 2)


def bytes_to_section(_bytes):
    return int(_bytes / 512)


class NumberToChinese:
    """
       阿拉伯数字转中文
    """

    def __init__(self):
        self.result = ""
        self.num_dict = {0: "零", 1: "一", 2: "二", 3: "三", 4: "四",
                    5: "五", 6: "六", 7: "七", 8: "八", 9: "九"}
        self.unit_map = [
            ["", "十", "百", "千"],
            ["万", "十万", "百万", "千万"],
            ["亿", "十亿", "百亿", "千亿"],
            ["兆", "十兆", "百兆", "千兆"]
        ]
        self.unit_step = ["万", "亿", "兆"]

    def number_to_str_10000(self, data_str):
        """一万以内的数转成大写"""
        res = []
        count = 0
        # 倒转
        str_rev = reversed(data_str)  # seq -- 要转换的序列，可以是 tuple, string, list 或 range。返回一个反转的迭代器。
        for i in str_rev:
            if i is not "0":
                count_cos = count // 4  # 行
                count_col = count % 4  # 列
                res.append(self.unit_map[count_cos][count_col])
                res.append(self.num_dict[int(i)])
                count += 1
            else:
                count += 1
                if not res:
                    res.append("零")
                elif res[-1] is not "零":
                    res.append("零")
        # 再次倒序，这次变为正序了
        res.reverse()
        # 去掉"一十零"这样整数的“零”
        if res[-1] is "零" and len(res) is not 1:
            res.pop()

        return "".join(res)

    def number_to_str(self, data):
        """分段转化"""
        assert isinstance(data, (float, int))
        data_str = str(data)
        len_data = len(str(data_str))
        count_cos = len_data // 4  # 行
        count_col = len_data - count_cos * 4  # 列
        if count_col > 0: count_cos += 1

        res = ""
        for i in range(count_cos):
            if i == 0:
                data_in = data_str[-4:]
            elif i == count_cos - 1 and count_col > 0:
                data_in = data_str[:count_col]
            else:
                data_in = data_str[-(i + 1) * 4:-(i * 4)]
            res_ = self.number_to_str_10000(data_in)
            res = res_ + self.unit_map[i][0] + res
        return res

    def decimal_chinese(self, data):
        assert isinstance(data, (float, int))
        data_str = str(data)
        if "." not in data_str:
            res = self.number_to_str(data_str)
        else:
            data_str_split = data_str.split(".")
            if len(data_str_split) is 2:
                res_start = self.number_to_str(data_str_split[0])
                res_end = "".join([self.num_dict[int(number)] for number in data_str_split[1]])
                res = res_start + random.sample(["点", "."], 1)[0] + res_end
            else:
                res = str(data)
        return res


if __name__ == "__main__":
    a = "1234"
    mds = create_md5(a)
    print(mds)