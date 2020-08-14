import json
import logging
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from web_manage.common.errcode import get_error_result
from django.http import JsonResponse
from rest_framework.views import APIView

from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.schemas import check_input
from web_manage.common.http import server_post
from web_manage.common.general_query import GeneralQuery
from . import models as voi_education_model
from .serializers import *
from .edu_manager.template_manager import VoiTemplateManager
from .edu_manager.desktop_manager import VoiDesktopManager


logger = logging.getLogger(__name__)


class VoiTemplateView(APIView):

    def get(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        classify = query_dict.get('classify__icontains', None)
        if classify:
            query_dict.pop('classify__icontains')
            query_dict['classify'] = classify
        group_uuid = query_dict.get('group', None)
        if group_uuid:
            return query.model_query(request, voi_education_model.YzyVoiTemplateGroups,
                                     VoiTemplateGroupSerializer, query_dict)
        else:
            state = query_dict.get('state', None)
            if state:
                # 1-模板展示列表 2-桌面组查询模板的展示
                query_dict.pop('state')
                data = request.GET
                _mutable = data._mutable
                data._mutable = True
                data['state'] = state
                data._mutable = _mutable
            return query.model_query(request, voi_education_model.YzyVoiTemplate, VoiTemplateSerializer, query_dict)

    @check_input('voi_template', need_action=True)
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
            try:
                logger.info("voi template post request")
                data = request.data
                action = data['action']
                param = data['param']
                func = getattr(VoiTemplateManager, action+'_check')
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
            ret = func(VoiTemplateManager(), param, log_user)
        except Exception as e:
            logger.error("voi template %s error:%s", action, e, exc_info=True)
            ret = get_error_result("OtherError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    @check_input('voi_template', action="delete")
    def delete(self, request):
        """
        需要支持批量删除
        {
            "templates": [
                    {
                        "name": "template2",
                        "uuid": "f309f8a2-5c51-11ea-9b12-000c295dd728"
                    },
                    {
                        "name": "template1",
                        "uuid": "655a1b9c-592a-11ea-b491-000c295dd728"
                    }
                ]
        }
        """
        try:
            data = request.data
            templates = data.get('templates', [])
            names = list()
            for template in templates:
                names.append(template['name'])
            ret = VoiTemplateManager().delete_templates(templates)
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            msg = "删除模板'%s'" % ('/'.join(names))
            insert_operation_log(msg, ret['msg'], log_user, module="voi_template")
        except Exception as e:
            logger.error("delete voi template error:%s", e, exc_info=True)
            ret = get_error_result("TemplateDeleteFail", name='')
            msg = "删除模板'%s'" % ('/'.join(names))
            insert_operation_log(msg, str(e), log_user, module="voi_template")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    def put(self, request):
        try:
            logger.info("update voi template")
            data = request.data
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = VoiTemplateManager().update_template(data, log_user)
        except Exception as e:
            logger.error("update voi template error:%s", e, exc_info=True)
            ret = get_error_result("TemplateUpdateError", name=data.get('name', ''))
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class VoiTemplateIPaddrView(APIView):

    def get(self, request, *args, **kwargs):
        try:
            info = request.GET.dict()
            if not info.get('subnet_uuid'):
                return get_error_result("ParamError")
            ipaddr = VoiTemplateManager().allocate_ipaddr(info['subnet_uuid'])
            ret = get_error_result("Success", ipaddr)
            return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})
        except Exception as e:
            logger.error("get template ipaddr error:%s", e, exc_info=True)
            ret = get_error_result("ReturnError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})


class VoiTemplateOperateView(APIView):

    def get(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        return query.model_query(request, voi_education_model.YzyVoiTemplateOperate,
                                 VoiTemplateOperateSerializer, query_dict)


class VoiEducationGroupView(APIView):
    """
    教学分组接口
    """

    def get(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        group_type = query_dict.get('group_type__icontains', None)
        if group_type:
            query_dict.pop('group_type__icontains')
            query_dict['group_type'] = group_type
        return query.model_query(request, voi_education_model.YzyVoiGroup, VoiGroupSerializer, query_dict)

    @operation_record("创建教学分组{data[name]}", module="voi_education_group")
    def create_group(self, data, log_user=None):
        """
        :param data:
            {
                "name": "group1",
                "group_type": 1,
                "desc": "this is group2",
                "start_ip": "172.16.1.40",
                "end_ip": "172.16.1.60"
            }
        :return:
        """
        if voi_education_model.YzyVoiGroup.objects.filter(name=data['name'], deleted=False):
            logger.error("create voi education group error,it's already exists")
            return get_error_result("GroupAlreadyExists", name=data['name'])
        groups = voi_education_model.YzyVoiGroup.objects.filter(group_type=1, deleted=False)
        for group in groups:
            flag_a = ipaddress.ip_network(data['start_ip']).compare_networks(ipaddress.ip_network(group.start_ip))
            flag_b = ipaddress.ip_network(group.end_ip).compare_networks(ipaddress.ip_network(data['start_ip']))
            flag_c = ipaddress.ip_network(data['end_ip']).compare_networks(ipaddress.ip_network(group.start_ip))
            flag_d = ipaddress.ip_network(group.end_ip).compare_networks(ipaddress.ip_network(data['end_ip']))
            flag_e = ipaddress.ip_network(group.start_ip).compare_networks(ipaddress.ip_network(data['start_ip']))
            flag_f = ipaddress.ip_network(data['end_ip']).compare_networks(ipaddress.ip_network(group.end_ip))
            if (flag_a >= 0 and flag_b >= 0) or (flag_c >= 0 and flag_d >= 0) or (flag_e >= 0 and flag_f >= 0):
                return get_error_result("IpAddressConflictError")
        ret = server_post("/api/v1/voi/group/create", data)
        return ret

    @check_input('voi_edu_group', action="create")
    def post(self, request):
        try:
            logger.info("create voi education group")
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
            logger.error("create education group error:%s", e, exc_info=True)
            ret = get_error_result("GroupCreateError", name=data.get('name', ''))
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    def delete_group(self, group):
        logger.info("delete voi group, name:%s, uuid:%s", group['name'], group['uuid'])
        if not voi_education_model.YzyVoiGroup.objects.filter(uuid=group['uuid'], deleted=False):
            logger.info("delete voi group error, it is not exists")
            return get_error_result("GroupNotExists", name=group['name'])
        ret = server_post("/api/v1/voi/group/delete", {"uuid": group['uuid']})
        if ret.get('code') != 0:
            logger.info("delete voi group failed:%s", ret['msg'])
            return ret
        else:
            logger.info("delete voi group success, name:%s, uuid:%s", group['name'], group['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def delete_groups(self, groups):
        if len(groups) == 1:
            return self.delete_group(groups[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for group in groups:
                future = executor.submit(self.delete_group, group)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    @check_input('voi_edu_group', action="delete")
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
            msg = "删除教学分组'%s'" % ('/'.join(names))
            insert_operation_log(msg, ret['msg'], log_user, module="voi_education_group")
            logger.info("delete voi group end")
        except Exception as e:
            logger.error("delete education group error:%s", e, exc_info=True)
            ret = get_error_result("GroupDeleteError")
            msg = "删除教学分组'%s'" % ('/'.join(names))
            insert_operation_log(msg, ret['msg'], log_user, module="voi_education_group")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    def update_group(self, data):
        if not voi_education_model.YzyVoiGroup.objects.filter(uuid=data['uuid'], deleted=False):
            logger.info("update voi education group error, it is not exists")
            return get_error_result("GroupNotExists", name=data['name'])
        if data['name'] != data['value']['name']:
            if voi_education_model.YzyVoiGroup.objects.filter(name=data['value']['name'], deleted=False):
                return get_error_result("GroupAlreadyExists", name=data['value']['name'])
        groups = voi_education_model.YzyVoiGroup.objects.filter(group_type=1, deleted=False)
        for group in groups:
            if group.uuid != data['uuid']:
                flag_a = ipaddress.ip_network(data['value']['start_ip']).\
                    compare_networks(ipaddress.ip_network(group.start_ip))
                flag_b = ipaddress.ip_network(group.end_ip)\
                    .compare_networks(ipaddress.ip_network(data['value']['start_ip']))
                flag_c = ipaddress.ip_network(data['value']['end_ip']).\
                    compare_networks(ipaddress.ip_network(group.start_ip))
                flag_d = ipaddress.ip_network(group.end_ip).\
                    compare_networks(ipaddress.ip_network(data['value']['end_ip']))
                flag_e = ipaddress.ip_network(group.start_ip).\
                    compare_networks(ipaddress.ip_network(data['value']['start_ip']))
                flag_f = ipaddress.ip_network(data['value']['end_ip']).\
                    compare_networks(ipaddress.ip_network(group.end_ip))
                if (flag_a >= 0 and flag_b >= 0) or (flag_c >= 0 and flag_d >= 0) or (flag_e >= 0 and flag_f >= 0):
                    logger.info("update voi group failed, ipaddress conflict")
                    return get_error_result("IpAddressConflictError")
        ret = server_post("/api/v1/voi/group/update", data)
        if ret.get('code') != 0:
            logger.info("update voi group failed:%s", ret['msg'])
            return ret
        else:
            logger.info("update voi group success, uuid:%s", data['uuid'])
        return get_error_result("Success")

    @check_input('voi_edu_group', action="update")
    def put(self, request):
        """
        {
            "uuid": "02063e92-52ca-11ea-ba2e-000c295dd728",
            "name": "group1",
            "value": {
                "name": "group2",
                "desc": "this is group2",
                "start_ip": "172.16.1.40",
                "end_ip": "172.16.1.50"
            }
        }
        """
        try:
            logger.info("update voi education group")
            data = json.loads(request.body)
        except Exception as e:
            logger.error("get request data error:%s", e)
            return JsonResponse(get_error_result("MessageError"), status=200,
                                json_dumps_params={'ensure_ascii': False})
        try:
            msg = "更新教学分组'%s'" % data['name']
            ret = self.update_group(data)
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            insert_operation_log(msg, ret['msg'], log_user, module="voi_education_group")
            logger.info("update voi group end")
        except Exception as e:
            logger.error("update voi education group error:%s", e, exc_info=True)
            ret = get_error_result("GroupUpdateError", name=data.get('name', ''))
            insert_operation_log(msg, ret['msg'], log_user, module="voi_education_group")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class VoiDesktopGroupView(APIView):
    """
    教学桌面组接口
    """

    def get(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        group_uuid = query_dict.get('group__icontains', None)
        if group_uuid:
            query_dict.pop('group__icontains')
            query_dict['group'] = group_uuid
        return query.model_query(request, voi_education_model.YzyVoiDesktop, VoiDesktopSerializer, query_dict)

    @check_input("voi_edu_desktop", need_action=True)
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
            logger.info("voi desktop group post request")
            data = json.loads(request.body)
            action = data['action']
            param = data['param']
            try:
                func = getattr(VoiDesktopManager, action + '_check')
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
            ret = func(VoiDesktopManager(), param, log_user)
        except Exception as e:
            logger.error("%s voi desktop group error:%s", action, e, exc_info=True)
            ret = get_error_result("OtherError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    @check_input("voi_edu_desktop", action="delete")
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
            ret = VoiDesktopManager().delete_check(data, log_user)
        except Exception as e:
            logger.error("delete desktop group error:%s", e, exc_info=True)
            ret = get_error_result("DesktopDeleteFail")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    @check_input("voi_edu_desktop", action="update")
    def put(self, request):
        """
        {
            "name": "desktop1"
            "uuid": "acdbfa10-56e8-11ea-8e10-000c295dd728",
            "value": {
                "name": "desktop2"
            }
        }
        """
        try:
            logger.info("update desktop group")
            data = json.loads(request.body)
        except Exception as e:
            logger.error("get request data error:%s", e)
            return JsonResponse(get_error_result("MessageError"), status=400,
                                json_dumps_params={'ensure_ascii': False})
        try:
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = VoiDesktopManager().update_desktop(data, log_user)
        except Exception as e:
            logger.error("update education group error:%s", e, exc_info=True)
            ret = get_error_result("GroupUpdateError", name=data.get('name', ''))
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class EducationVoiInstanceView(APIView):
    def get(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        return GeneralQuery().model_query(request, models.YzyVoiTerminalToDesktops,
                                          VoiTerminalToDesktopsSerializer, query_dict)
