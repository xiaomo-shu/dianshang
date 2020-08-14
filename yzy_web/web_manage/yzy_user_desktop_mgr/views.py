import json
import os
import logging
from urllib.parse import quote
from django.http import JsonResponse, FileResponse
from rest_framework.views import APIView
from django.utils.encoding import escape_uri_path

from web_manage.common.errcode import get_error_result
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.http import server_post
from web_manage.common.schemas import check_input
from web_manage.common.general_query import GeneralQuery
from web_manage.yzy_edu_desktop_mgr.serializers import InstanceSerializer
from .serializers import *
from .personal_manager.user_manager import UserManager
from .personal_manager.desktop_manager import DesktopManager
from .personal_manager.instance_manager import InstanceManager

logger = logging.getLogger(__name__)


def param_error(error):
    return JsonResponse(get_error_result(error), status=200,
                        json_dumps_params={'ensure_ascii': False})


class PersonalGroupView(APIView):
    """
    用户分组接口
    """

    def get(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        group_type = query_dict.get('group_type__icontains', None)
        if group_type:
            query_dict.pop('group_type__icontains')
            query_dict['group_type'] = group_type
        return query.model_query(request, education_model.YzyGroup,
                                          UserGroupSerializer, query_dict)

    @operation_record("创建用户分组{data[name]}", module="user_group")
    def create_group(self, data, log_user=None):
        """
        :param data:
            {
                "name": "group2",
                "group_type": 2,
                "desc": "this is group2",
                "start_ip": "172.16.1.60",
                "end_ip": "172.16.1.80"
            }
        :return:
        """

        # if education_model.YzyGroup.objects.filter(deleted=False, group_type=data.get("group_type")).count() > 49:
        #     logger.info("create personal group error, the quantity must not exceed 50")
        #     return get_error_result("GroupCreationOverflow")
        if education_model.YzyGroup.objects.filter(name=data['name'], group_type=2, deleted=False):
            logger.info("create personal group error, it's already exists")
            return get_error_result("GroupAlreadyExists", name=data['name'])

        ret = server_post("/api/v1/group/create", data)
        return ret

    @check_input("person_group", action="create")
    def post(self, request):
        try:
            logger.info("create personal group")
            data = json.loads(request.body)
        except Exception as e:
            logger.error("get request data error:%s", e)
            return JsonResponse(get_error_result("MessageError"), status=200,
                                json_dumps_params={'ensure_ascii': False})
        try:
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = self.create_group(data, log_user)
        except Exception as e:
            logger.error("create personal group error:%s", e, exc_info=True)
            ret = get_error_result("GroupCreateError", name=data.get('name', ''))
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    def delete_groups(self, groups):
        for group in groups:
            logger.info("delete personal group, name:%s, uuid:%s", group['name'], group['uuid'])
            if not education_model.YzyGroup.objects.filter(uuid=group['uuid'], deleted=False):
                logger.info("delete education group error, it is not exists")
                return get_error_result("GroupNotExists", name=group['name'])
            ret = server_post("/api/v1/group/delete", {"uuid": group['uuid']})
            if ret.get('code') != 0:
                logger.info("delete personal group failed:%s", ret['msg'])
                return ret
            else:
                logger.info("delete personal group success, name:%s, uuid:%s", group['name'], group['uuid'])
        return get_error_result("Success")

    @check_input("person_group", action="delete")
    def delete(self, request):
        """
        {
            "groups": [
                    {
                        "uuid": "f38c048e-59fc-11ea-84fd-000c295dd728",
                        "name": "group1"
                    }
                ]
        }
        """
        try:
            data = json.loads(request.body)
            groups = data.get('groups', [])
            names = list()
            for group in groups:
                names.append(group['name'])
            ret = self.delete_groups(groups)
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            msg = "删除用户分组'%s'" % ('/'.join(names))
            insert_operation_log(msg, ret['msg'], log_user, module="user_group")
        except Exception as e:
            logger.error("delete education group error:%s", e, exc_info=True)
            ret = get_error_result("GroupDeleteError")
            msg = "删除用户分组'%s'" % ('/'.join(names))
            insert_operation_log(msg, ret['msg'], log_user, module="user_group")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    def update_group(self, data):
        if not education_model.YzyGroup.objects.filter(uuid=data['uuid'], deleted=False):
            logger.info("update education group error, it is not exists")
            return get_error_result("GroupNotExists", name=data['name'])
        if data['name'] != data['value']['name']:
            if education_model.YzyGroup.objects.filter(name=data['value']['name'], deleted=False):
                return get_error_result("GroupAlreadyExists", name=data['value']['name'])
        ret = server_post("/api/v1/group/update", data)
        if ret.get('code') != 0:
            logger.info("update group failed:%s", ret['msg'])
            return ret
        else:
            logger.info("update group success, uuid:%s", data['uuid'])
        return get_error_result("Success")

    @check_input("person_group", action="update")
    def put(self, request):
        """
        {
            "uuid": "00d4e728-59f8-11ea-972d-000c295dd728",
            "name": "group1",
            "value": {
                "name": "group1",
                "desc": "this is group",
                "start_ip": "172.16.1.20",
                "end_ip": "172.16.1.60"
            }
        }
        """
        try:
            logger.info("update education group")
            data = json.loads(request.body)
        except Exception as e:
            logger.error("get request data error:%s", e)
            return JsonResponse(get_error_result("MessageError"), status=200,
                                json_dumps_params={'ensure_ascii': False})
        try:
            msg = "更新用户分组 %s" % data['name']
            ret = self.update_group(data)
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            insert_operation_log(msg, ret['msg'], log_user, module="user_group")
        except Exception as e:
            logger.error("update personal group error:%s", e, exc_info=True)
            ret = get_error_result("GroupUpdateError", name=data.get('name', ''))
            insert_operation_log(msg, ret['msg'], log_user, module="user_group")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class GroupUserView(APIView):
    """
    个人桌面中的用户管理接口
    """
    def get(self, request, *args, **kwargs):
        from django.db.models import Q
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        group = query_dict.get('group__icontains', None)
        if group:
            query_dict.pop('group__icontains')
            query_dict['group'] = group
        user_name = query_dict.get('user_name__icontains', None)
        phone = query_dict.get('phone__icontains', None)
        fil = None
        if user_name and phone:
            query_dict.pop('user_name__icontains')
            query_dict.pop('phone__icontains')
            fil = (Q(user_name__icontains=user_name) | Q(phone__icontains=phone) | Q(name__icontains=user_name))
        return query.model_query(request, models.YzyGroupUser, GroupUserSerializer, query_dict, fil)

    @check_input("group_user", need_action=True)
    def post(self, request):
        """
        :param request.body:
            {
                "action": "single_create",  # or multi_create
                "param": {}     # 创建需要的参数
            }
        :return:
        """
        try:
            logger.info("group user request")
            data = json.loads(request.body)
            action = data['action']
            param = data['param']
            try:
                func = getattr(UserManager, action + '_check')
            except:
                ret = get_error_result("ParamError")
                return JsonResponse(ret, status=200,
                                    json_dumps_params={'ensure_ascii': False})
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = func(UserManager(), param, log_user)
        except Exception as e:
            logger.error("%s group user error:%s", action, e, exc_info=True)
            ret = get_error_result("OtherError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    @check_input("group_user", action="delete")
    def delete(self, request):
        """
        {
            "users": [
                    {
                        "uuid": "",
                        "user_name": ""
                    }
                ]
        }
        """
        try:
            logger.info("delete group user")
            data = json.loads(request.body)
        except Exception as e:
            logger.error("get request data error:%s", e)
            return JsonResponse(get_error_result("MessageError"), status=200,
                                json_dumps_params={'ensure_ascii': False})
        try:
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = UserManager().delete_check(data, log_user)
        except Exception as e:
            logger.error("delete group user error:%s", e, exc_info=True)
            ret = get_error_result("GroupUserDeleteError", user_name='')
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    @check_input("group_user", action="update")
    def put(self, request):
        """
        {
            "uuid": "ba63d8d0-579f-11ea-b1ca-000c295dd728",
            "user_name": "user1",
            "value": {
                "group_uuid": "d02cd368-5396-11ea-ad80-000c295dd728",
                "user_name": "test"
            }
        }
        """
        try:
            logger.info("update group user")
            data = json.loads(request.body)
        except Exception as e:
            logger.error("get request data error:%s", e)
            return JsonResponse(get_error_result("MessageError"), status=200,
                                json_dumps_params={'ensure_ascii': False})
        try:
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = UserManager().update_user(data, log_user)
        except Exception as e:
            logger.error("delete group user error:%s", e, exc_info=True)
            ret = get_error_result("GroupUserDeleteError", name='')
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class GroupUserUploadView(APIView):
    """
    个人桌面中的用户导入
    """
    authentication_classes = []

    def get(self, request):
        filepath = "/opt/导入模板.xlsx"
        file = open(filepath, 'rb')
        response = FileResponse(file)
        response['Content-Type'] = "application/octet-stream; charset=UTF-8"
        filename = filepath.split('/')[-1]
        response["Content-disposition"] = "attachment; filename*=UTF-8''{}".format(escape_uri_path(filename))
        return response

    def post(self, request):
        file_obj = request.FILES.get("file", None)
        enable = request.data.get("enabled", True)
        path = "/root/users.xlsx"
        with open(path, "wb+") as f:
            while True:
                chunk = file_obj.read(constants.Mi)
                if chunk:
                    f.write(chunk)
                else:
                    break
        try:
            logger.info("import user")
            action = "import"
            try:
                func = getattr(UserManager, action + '_check')
            except:
                ret = get_error_result("ParamError")
                return JsonResponse(ret, status=200,
                                    json_dumps_params={'ensure_ascii': False})
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = func(UserManager(), {"filepath": path, "enabled": enable}, log_user=log_user)
            try:
                os.remove(path)
            except:
                pass
        except Exception as e:
            logger.error("import group user error:%s", e, exc_info=True)
            ret = get_error_result("OtherError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class PersonalDesktopGroupView(APIView):
    """
    个人桌面组接口
    """

    def get(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        return query.model_query(request, models.YzyPersonalDesktop, PersonalDesktopSerializer, query_dict)

    @check_input("personal_desktop", need_action=True)
    def post(self, request):
        """
        :param request.body:
            {
                "action": "create",
                "param": {}
            }
        :return:
        """
        try:
            logger.info("personal desktop group post request")
            data = json.loads(request.body)
            action = data['action']
            param = data['param']
            try:
                func = getattr(DesktopManager, action + '_check')
            except:
                ret = get_error_result("ParamError")
                return JsonResponse(ret, status=200,
                                    json_dumps_params={'ensure_ascii': False})
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = func(DesktopManager(), param, log_user)
        except Exception as e:
            logger.error("%s personal desktop group error:%s", action, e, exc_info=True)
            ret = get_error_result("OtherError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    @check_input("personal_desktop", action="delete")
    def delete(self, request):
        """
        {
            "desktops": [
                "",
                ...
            ]
        }
        """
        try:
            data = json.loads(request.body)
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = DesktopManager().delete_check(data, log_user)
        except Exception as e:
            logger.error("delete desktop group error:%s", e, exc_info=True)
            ret = get_error_result("DesktopDeleteFail")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    @check_input("personal_desktop", action="update")
    def put(self, request):
        try:
            logger.info("update personal desktop group")
            data = json.loads(request.body)
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = DesktopManager().update_desktop(data, log_user)
        except Exception as e:
            logger.error("update personal desktop group error:%s", e, exc_info=True)
            ret = get_error_result("DesktopUpdateFail", name='')
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class PersonalInstanceView(APIView):
    """
    个人桌面接口
    """

    def get(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        return query.model_query(request, education_model.YzyInstances, InstanceSerializer, query_dict)

    @check_input("personal_instance", need_action=True)
    def post(self, request):
        """
        :param request.body:
            {
                "action": "create",
                "param": {}
            }
        :return:
        """
        try:
            logger.info("personal instance post request")
            data = json.loads(request.body)
            action = data['action']
            param = data['param']
            try:
                func = getattr(InstanceManager, action + '_check')
            except:
                ret = get_error_result("ParamError")
                return JsonResponse(ret, status=200,
                                    json_dumps_params={'ensure_ascii': False})
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = func(InstanceManager(), param, log_user)
        except Exception as e:
            logger.error("%s instance error:%s", action, e, exc_info=True)
            ret = get_error_result("OtherError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    @check_input("personal_instance", action="delete")
    def delete(self, request):
        try:
            data = json.loads(request.body)
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = InstanceManager().delete_check(data, log_user)
        except Exception as e:
            logger.error("delete instance error:%s", e, exc_info=True)
            ret = get_error_result("InstanceDeleteFail", name='')
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    def put(self, request):
        ret = {"code": -1, "msg": "未知异常"}
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class DesktopRandomView(APIView):
    """
    桌面组中的随机桌面管理
    """

    def get(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        return query.model_query(request, models.YzyRandomDesktop, DesktopRandomSerializer, query_dict)

    @check_input("desktop_random", need_action=True)
    def post(self, request):
        """
        :param request.body:
            {
                "action": "create",
                "param": {}
            }
        :return:
        """
        try:
            logger.info("desktop random post request")
            data = json.loads(request.body)
            action = data['action']
            param = data['param']
            try:
                func = getattr(InstanceManager, action + '_check')
            except:
                ret = get_error_result("ParamError")
                return JsonResponse(ret, status=200,
                                    json_dumps_params={'ensure_ascii': False})
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = func(InstanceManager(), param, log_user)
        except Exception as e:
            logger.error("desktop %s error:%s", action, e, exc_info=True)
            ret = get_error_result("OtherError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class DesktopStaticView(APIView):
    """
    桌面组中的静态桌面管理
    """
    def get(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        return query.model_query(request, education_model.YzyInstances, DesktopStaticSerializer, query_dict)

    @check_input("desktop_static", need_action=True)
    def post(self, request):
        """
        :param request.body:
            {
                "action": "create",
                "param": {}
            }
        :return:
        """
        try:
            logger.info("desktop static post request")
            data = json.loads(request.body)
            action = data['action']
            param = data['param']
            try:
                func = getattr(InstanceManager, action + '_check')
            except:
                ret = get_error_result("ParamError")
                return JsonResponse(ret, status=200,
                                    json_dumps_params={'ensure_ascii': False})
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = func(InstanceManager(), param, log_user)
        except Exception as e:
            logger.error("desktop %s error:%s", action, e, exc_info=True)
            ret = get_error_result("OtherError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})
