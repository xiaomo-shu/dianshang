#-*- coding:UTF-8 -*-

import operator
import string
import logging
import base64
import copy


from .serializers import *
from web_manage.common.utils import JSONResponse, YzyWebPagination, YzyAuthentication, YzyPermission, create_md5, \
                            get_error_result
from web_manage.common.log import insert_operation_log
from web_manage.yzy_edu_desktop_mgr.models import YzyInstanceTemplate

from rest_framework.views import APIView
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.shortcuts import HttpResponse
from django.utils import timezone
import hashlib
import time
from rest_framework import status
from django.db.models import Q

from django.core.cache import cache
from django.http import Http404
from web_manage.yzy_system_mgr.system_manager.license_manager import LicenseManager

logger = logging.getLogger(__name__)


class LoginMix(object):

    authentication_classes = [YzyAuthentication, ]  # 添加认证
    permission_classes = [YzyPermission, ]


def make_token(user):
    ctime = str(time.time())
    hash = hashlib.md5(user.encode("utf-8"))
    hash.update(ctime.encode("utf-8"))
    return hash.hexdigest()


class AuthView(APIView):
    """登录认证"""
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        ret = get_error_result("Success")
        user = request.data.get("username")
        pwd = request.data.get("password")
        remote_ip = request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get(
            'HTTP_X_FORWARDED_FOR') else request.META.get("REMOTE_ADDR")
        user_info = None
        try:

            logger.info("user login: %s login , login ip %s"% (user, remote_ip))
            obj = YzyAdminUser.objects.filter(deleted=False, username=user).first()
            if not obj or not obj.validate_password(pwd):
                logger.error("user login error: %s login fail !!!"% user)
                ret = get_error_result("LoginFailError")
                return JSONResponse(ret)
            role = YzyRole.objects.filter(deleted=False, id=obj.role_id).first()
            if not role.enable:
                logger.error("user login error:%s account permission is disabled" % role.role)
                ret = get_error_result("AccountPermissionDisabledError")
                return JSONResponse(ret)
            if not obj.is_active:
                logger.error("user login error: %s is disabled", user)
                ret = get_error_result("AccountDisabledError")
                user_info = {
                    "id": 0,
                    "user_name": user,
                    "user_ip": remote_ip
                }
                # return JSONResponse(ret)
            else:
                ser = YzyAdminUserSerializer(instance=obj, context={'request': request})
                ret_data = dict()
                token = make_token(user)
                old_token = cache.get(obj.id)
                cache.set(obj.id, token)
                cache.set(token, obj, 60 * 60 * 24)
                # todo 清除旧token
                # if old_token:
                #     cache.delete(old_token)
                # tokens  = cache.get("441c5b7317352ff5ce9e6a024d32e074")
                ret_data.update({"token": token})
                ret_data.update({"user": ser.data})
                ret["data"] = ret_data

                # 更新
                obj.last_login = timezone.now()
                obj.login_ip = remote_ip
                obj.save()
                user_info = {
                    "id": obj.id,
                    "user_name": user,
                    "user_ip": remote_ip
                }

            lic_info = LicenseManager().info()
            # license_status = lic_info['auth_type']
            # ret["data"]["trail_days"] = lic_info['expire_time']

            # ret['data']['vdi_flag'] = True if lic_info['vdi_size'] else False
            # ret['data']['voi_flag'] = True if lic_info['voi_size'] else False
            ret["data"]["vdi_flag"] = True if lic_info.get("vdi_size", None) else False
            ret['data']['voi_flag'] = True if lic_info.get("voi_size", None) else False
        except Exception as e:
            logger.error("user login error: ", exc_info=True)
            ret = get_error_result("OtherError")

        msg = "用户：%s 在ip: %s 处登录"%(user, remote_ip)
        insert_operation_log(msg, ret["msg"], user_info)
        return JSONResponse(ret)


class AdminUserNameCheck(APIView):
    """
    管理员名称查询
    """
    def get_object_by_name(self, username, option):
        if option == "admin_user":
            role = YzyAdminUser.objects.filter(deleted=False, username=username).first()
        else:
            role = YzyRole.objects.filter(deleted=False, role=username).first()
        return role

    def post(self, request, *args, **kwargs):
        username = request.data.get("username", "")
        option = request.data.get("option", "")
        ret = get_error_result()
        user = self.get_object_by_name(username, option)
        if user:
            ret = get_error_result("AdminUsernameExist")
            return JSONResponse(ret)
        return JSONResponse(ret)


class AdminUsersView(APIView):
    """
    管理员列表
    """
    def get_object(self, user_id):
        try:
            user = YzyAdminUser.objects.filter(deleted=False).get(id=user_id)
            return user
        except Exception as e:
            return None

    def get_object_list(self, request, page):
        try:
            role = request.GET.get("role", "")
            username = request.GET.get("username", "")
            query_set = YzyAdminUser.objects.filter(deleted=False)
            if role:
                query_set = query_set.filter(role_id=role)
            if username:
                query_set = query_set.filter(Q(username__contains=username) | Q(real_name__contains=username))
            admin_users = page.paginate_queryset(queryset=query_set, request=request, view=self)
            return admin_users
        except Exception as e:
            raise Http404()

    def get(self, request, *args, **kwargs):
        page = YzyWebPagination()
        admin_users = self.get_object_list(request, page)
        ser = YzyAdminUserSerializer(instance=admin_users, many=True, context={'request': request})
        return page.get_paginated_response(ser.data)

    def post(self, request, *args, **kwargs):
        ret = get_error_result("Success")

        _data = request.data
        password = _data.get("password")
        if not password:
            # ex = Exception("not input password!")
            logger.error("create admin user error: not password input")
            ret = get_error_result("NotPasswordInputError")
            # return JSONResponse(ret)
        else:
            _data.update({"password": create_md5(password)})
            ser = YzyAdminUserSerializer(data=_data, context={'request': request})
            if ser.is_valid():
                ser.save()
                # return Response(ser.data, status=status.HTTP_201_CREATED)

                # return JSONResponse()
            else:
                msg = ser.errors
                ret = get_error_result("ParamError")
                ret["msg"] = msg
        logger.info("create admin user: %s"% ret)
        msg = "创建管理员用户: %s"% _data.get("username")
        insert_operation_log(msg, ret)
        return JSONResponse(ret)

    def put(self, request, *args, **kwargs):
        try:
            _data = request.data
            user_id = _data.get("user_id")
            user = self.get_object(user_id)
            if not user:
                logger.error("admin user not exist: %s"% user_id)
                ret = get_error_result("AdminUserNotExist")
                return ret
            # username = _data.get("username") or None
            real_name = _data.get("real_name") or None
            password = _data.get("password") or None
            role_id = _data.get("role") or None
            desc = _data.get("desc", "" ) or None
            email = _data.get("email", "") or None
            # if username: user.username = username
            if real_name is not None: user.real_name = real_name
            if password: user.password = create_md5(password)
            if role_id: user.role_id = role_id
            if desc is not None: user.desc = desc
            if email is not None: user.email = email
            user.save()
            ret = get_error_result()
            msg = "修改管理员用户信息: %s" % user_id
            insert_operation_log(msg, ret)
            return JSONResponse(ret)
        except Exception as e:
            logger.error("", exc_info=True)
            return JSONResponse(get_error_result("OtherError"))

    def delete(self, request, *args, **kwargs):
        user_id = request.data.get("id", "")
        user = YzyAdminUser.objects.filter(deleted=False, id=user_id).first()
        if not user:
            logger.error("user not exist: %s", user_id)
            return JSONResponse(get_error_result("UserNotExistError"))
        if user.is_superuser:
            logger.error("Super administrator does not allow deletion:%s", user.username)
            return JSONResponse(get_error_result("SuperAdminNotDeleteError"))
        template = YzyInstanceTemplate.objects.filter(deleted=False, owner_id=user.id).first()
        if template:
            logger.error("delete admin error template under the account")
            return JSONResponse(get_error_result("TemplateUnderTheAccountError"))
        user.delete()
        ret = get_error_result("Success")
        msg = "删除管理员用户信息：%s" % user.username
        insert_operation_log(msg, ret)
        return JSONResponse(ret)


class AdminUserEnableView(APIView):

    def post(self, request):
        enable = request.data.get("enable", 1)
        _id = request.data.get("id", "")
        option = request.data.get("option", "")
        if option == "role":
            yzy_role = YzyRole.objects.filter(deleted=False, id=_id).first()
            if yzy_role:
                yzy_role.enable = enable
                yzy_role.save()
                logger.info("update role enable success")
                return JSONResponse(get_error_result("Success"))
        elif option == "admin_user":
            user = YzyAdminUser.objects.filter(deleted=False, id=_id).first()
            if user:
                user.is_active = enable
                user.save()
                logger.info("update admin user enable success")
                return JSONResponse(get_error_result("Success"))
        else:
            logger.error("update fail param error:%s", option)
            return JSONResponse(get_error_result("ParameterError"))
        return JSONResponse(get_error_result("ParameterError"))


class RolesView(APIView):
    """
       角色列表
    """

    def get_object_list(self, request, page):
        try:
            query_set = YzyRole.objects.filter(deleted=False)
            roles = page.paginate_queryset(queryset=query_set, request=request, view=self)
            return roles
        except Exception as e:
            raise Http404()

    def get(self, request, *args, **kwargs):
        page = YzyWebPagination()
        roles = self.get_object_list(request, page)
        ser = YzyRoleSerializer(instance=roles, many=True, context={'request': request})
        return page.get_paginated_response(ser.data)

    def post(self, request):
        ret = get_error_result()
        _data = request.data
        _data.update({"enable": 1})
        ser = YzyRoleSerializer(data=_data, context={'request': request})
        if ser.is_valid():
            ser.save()
        else:
            msg = ser.errors
            ret = get_error_result("ParameterError")
            ret["msg"] = msg
        logger.info("create admin user: %s" % ret)
        msg = "创建角色信息: %s" % _data.get("role")
        insert_operation_log(msg, ret)
        return JSONResponse(ret)

    def put(self, request):
        _id = request.data.get("id")
        desc = request.data.get("desc", '')
        name = request.data.get("role", '')
        role = YzyRole.objects.filter(deleted=False, id=_id).first()
        if not role:
            logger.error("update role fail: role not exits")
            return JSONResponse(get_error_result("RoleNotExistError"))
        if role.role != name and YzyRole.objects.filter(deleted=False, role=name).all():
            logger.error("update role fail: name exits")
            return JSONResponse(get_error_result("NameAlreadyUseError"))
        role.role = name
        role.desc = desc
        role.save()
        ret = get_error_result("Success")
        msg = "更新角色信息：%s" % role.role
        insert_operation_log(msg, ret)
        return JSONResponse(ret)

    def delete(self, request):
        _id = request.data.get("id", "")
        role = YzyRole.objects.filter(deleted=False, id=_id).first()
        user = YzyAdminUser.objects.filter(deleted=False, role=_id).first()
        if not role:
            logger.error("role not exist: %s", _id)
            return JSONResponse(get_error_result("UserNotExistError"))
        if user:
            logger.error("the role is already referenced")
            return JSONResponse(get_error_result("RoleAlreadyReferencedError"))
        if user and user.is_superuser:
            logger.error("Super administrator does not allow deletion:%s", role.role)
            return JSONResponse(get_error_result("SuperAdminNotDeleteError"))
        role.delete()
        ret = get_error_result("Success")
        msg = "删除角色信息：%s" % role.role
        insert_operation_log(msg, ret)
        return JSONResponse(ret)


class PermissionsView(APIView):
    """
    权限设置
    """

    def get_menu_ids(self, role_id):
        objs = YzyRolePermission.objects.filter(role=role_id).all()
        ids = [obj.menu_id for obj in objs]
        return ids

    def get_menus(self, ids=None):
        try:
            if not ids:
                menus = []
            else:
                query_set = YzyMenuPermission.objects.filter(id__in=ids).all()
                menus = query_set.all()
            return menus
        except Exception as e:
            raise Http404()

    def get(self, request, *args, **kwargs):
        role_id = kwargs.get("role")
        role = YzyRole.objects.filter(deleted=False, id=role_id).first()
        if not role:
            logger.error("get permissions fail role not exits:%s", role_id)
            return JSONResponse(get_error_result("ParameterError"))
        user = YzyAdminUser.objects.filter(deleted=False, role=role.id).first()
        ids = self.get_menu_ids(role_id)
        menu_list = self.parse_data(ids, user)
        return JSONResponse({"options": menu_list}, status=status.HTTP_200_OK)

    def parse_data(self, ids, user):
        query_set = YzyMenuPermission.objects.filter(deleted=False).all()
        if not user or not user.is_superuser:
            query_set = query_set.exclude(name="administratorManagement")
        menus = query_set.all()
        menu_list = []
        person_list = []
        for menu in menus:
            if menu.pid:
                person_list.append({"title": menu.title, "id": menu.id, "pid": menu.pid})

        for person in person_list:
            mode = []
            for menu in menus:
                if menu.pid == person['id'] and menu.type != 4:
                    is_check = True if menu.id in ids else False
                    mode.append({"title": menu.title, "id": menu.id, "ischeck": is_check})
                    if person['title'] not in ['VDI场景', 'VOI场景']:
                        person['check_children'] = True
                if menu.pid == person['id'] and person['title'] == '资源池管理' and menu.title == '基础镜像':
                    is_check = True if menu.id in ids else False
                    mode.append({"title": menu.title, "id": menu.id, "ischeck": is_check})
                    person['check_children'] = True

            person['mode'] = mode
            index = 0
            for i in mode:
                if i['ischeck']:
                    index += 1
            if len(mode) == 0:
                person['ischeck'] = True if person['id'] in ids else False
            else:
                person['ischeck'] = False if index < len(mode) else True

        for menu in menus:
            if not menu.pid:
                mode = []
                data_dict = {}
                data_dict['title'] = menu.title
                data_dict['id'] = menu.id
                for person in person_list:
                    if person['pid'] == menu.id:
                        mode.append(person)
                    data_dict['mode'] = mode
                index = 0
                for i in mode:
                    if i['ischeck']:
                        index += 1
                if len(mode) == 0:
                    data_dict['ischeck'] = True if menu.id in ids else False
                else:
                    data_dict['ischeck'] = False if index < len(mode) else True
                menu_list.append(data_dict)
        menu_list[0]['ischeck'] = True
        return menu_list

    def put(self, request, *args, **kwargs):
        role_id = kwargs.get("role")
        user = request.user
        options = request.data.get("options")
        if not (role_id and options):
            logger.error("update permission fail: parameter error")
            ret = get_error_result("ParameterError")
            return JSONResponse(ret, status=status.HTTP_200_OK)
        role = YzyRole.objects.filter(deleted=False, id=role_id).first()
        if not role:
            logger.error("update permission fail: role not exist")
            ret = get_error_result("RoleNotExistError")
            return JSONResponse(ret, status=status.HTTP_200_OK)
        if not user.is_superuser:
            ret = get_error_result("SuperAdminOnlySetError")
            return JSONResponse(ret, status=status.HTTP_200_OK)
        menu_ids = []
        self.get_ids(options, menu_ids)
        _menus = self.get_menus(menu_ids)
        try:
            role.menus.clear()
        except Exception as e:
            logger.error("update permission fail: %s" % e, exc_info=True)
            ret = get_error_result("OtherError")
            return JSONResponse(ret, status=status.HTTP_200_OK)
        for menu in _menus:
            p = YzyRolePermission(role=role, menu=menu)
            p.save()
        ret = {"code": 0, "msg": "成功"}
        return JSONResponse(ret, status=status.HTTP_200_OK)

    def get_ids(self, options, menu_ids):
        for option in options:
            if option and option['ischeck']:
                menu_ids.append(option['id'])
            if option and option.get('mode'):
                self.get_ids(option['mode'], menu_ids)


class MenusView(APIView):
    """
    菜单视图
    """
    authentication_classes = [YzyAuthentication, ]  # 添加认证
    permission_classes = [YzyPermission,]

    def get(self, request, *args, **kwargs):
        user = request.user
        _role = user.role
        permissions = user.role.yzyrolepermission_set.all()
        menu_ids = []
        for permission in permissions:
            menu_ids.append(permission.menu_id)
        menus = self.get_menus(menu_ids)
        if user.is_superuser:
            menus = YzyMenuPermission.objects.filter(deleted=False).all()
        router_list = self.parse_data(menus, user)
        return JSONResponse({"routers": router_list}, status=status.HTTP_200_OK)

    def get_menus(self, ids=None):
        try:
            if not ids:
                menus = []
            else:
                query_set = YzyMenuPermission.objects.filter(id__in=ids).all()
                query_set = query_set.exclude(name='administratorManagement').all()
                menus = query_set.all()
            return menus
        except Exception as e:
            raise Http404()

    def parse_data(self, menus, user):
        permissions = YzyMenuPermission.objects.filter(deleted=False, type__in=[1, 3, 4]).all()
        children = []
        router_list = []
        names = ['teachTem', 'teachgroup', 'teachDeskGroup']
        for permission in permissions:
            if permission.pid or permission.name == 'home':
                data_dict = {}
                data_dict['path'] = permission.path
                data_dict['name'] = permission.name
                data_dict['type'] = permission.type
                data_dict['component'] = permission.component
                data_dict['pid'] = permission.pid
                data_dict['id'] = permission.id
                data_dict['meta'] = {}
                data_dict['meta']['title'] = permission.title
                data_dict['meta']['breadNum'] = permission.bread_num
                data_dict['meta']['oneMenu'] = {}
                data_dict['meta']['permissions'] = []
                if permission.name != 'home':
                    record = YzyMenuPermission.objects.get(id=permission.pid)
                    data_dict['meta']['oneMenu']['type'] = permission.path.split('/')[
                        1] if permission.path else permission.name
                    if permission.type == 4 and permission.title != "详情" or permission.name in names:
                        record = YzyMenuPermission.objects.get(id=record.pid)
                    data_dict['meta']['oneMenu']['name'] = record.title
                else:
                    data_dict['meta']['permissions'].append(
                        {"title": permission.title, "name": permission.name, "permission": permission.permission})
                children.append(data_dict)

        menu_types = YzyMenuPermission.objects.filter(deleted=False, type=4).all()
        menu_pids = set()
        for child in children:
            for menu in menus:
                if menu.pid == child['id']:
                    child['meta']['permissions'].append({"title": menu.title, "name": menu.name,
                                                         "permission": menu.permission})
                menu_pids.add(menu.pid)
                menu_pids.add(menu.id)
                if child['name'] == menu.name and menu.name in names and menu.type == 1:
                    child['meta']['permissions'].append(
                        {"title": "VDI场景", "name": "terminalVDI", "permission": None})
                if child['name'] == menu.name and menu.name in names and menu.type == 5:
                    if not child['meta']['permissions']:
                        child['id'] = menu.id
                    child['meta']['permissions'].append(
                        {"title": "VOI场景", "name": "terminalVOI", "permission": None})
            for _type in menu_types:
                if _type.pid == child['id']:
                    child['meta']['permissions'].append({"title": _type.title, "name": _type.name,
                                                         "permission": _type.permission})
                menu_pids.add(_type.id)
        c_children = copy.deepcopy(children)
        for i in range(len(c_children)):
            if c_children[i]['name'] == 'home':
                continue
            if not user.is_superuser:
                if c_children[i]['id'] not in menu_pids or c_children[i]['name'] == "administratorManagement":
                    element = c_children[i]
                    if element in children:
                        children.remove(element)

        info = {}
        info['path'] = '/main'
        info['name'] = 'Main'
        info['component'] = 'main'
        # info['is_auth'] = True
        info['redirect'] = '/home/home'
        info['meta'] = {}
        info['meta']['title'] = '云桌面管理平台主页'
        info['meta']['login'] = True
        info['children'] = children
        router_list.append(info)
        return router_list


class PasswordCheckView(APIView):

    def post(self, request, *args, **kwargs):
        pwd = request.data.get("password", "")
        obj = YzyAdminUser.objects.filter(username="admin").first()
        if not obj or not obj.validate_password(pwd):
            logger.error("user password check error: %s password check fail!!!" % "admin")
            ret = get_error_result("PasswordCheckError")
            return JSONResponse(ret)
        return JSONResponse(get_error_result("Success"))

