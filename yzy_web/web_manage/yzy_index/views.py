import traceback
import logging
import time
from django.http import Http404, HttpResponseServerError
from rest_framework.views import APIView
from web_manage.common.http import server_post
from web_manage.common.utils import JSONResponse, YzyWebPagination, get_error_result
from web_manage.yzy_resource_mgr.models import YzyResourcePools, YzyNodes, YzyHaInfo
from web_manage.yzy_edu_desktop_mgr.models import YzyInstances, YzyOperationLog
from web_manage.yzy_terminal_mgr.models import YzyTerminal
from web_manage.yzy_edu_desktop_mgr.serializers import OperationLogSerializer
from web_manage.yzy_system_mgr.system_manager.license_manager import LicenseManager
from web_manage.yzy_voi_edu_desktop_mgr.models import YzyVoiDesktop, YzyVoiTemplate, YzyVoiGroup, YzyVoiTerminal
from web_manage.yzy_voi_edu_desktop_mgr.models import YzyVoiTerminalToDesktops
from web_manage.yzy_edu_desktop_mgr.models import YzyInstanceTemplate, YzyGroup, YzyDesktop
from web_manage.yzy_user_desktop_mgr.models import YzyPersonalDesktop
from web_manage.common import constants

logger = logging.getLogger(__name__)


class SystemMonitorTopData(APIView):
    """
    get top5 data: cpu memory disk network
    """
    def post(self, request, *args, **kwargs):
        try:
            logger.debug("system monitor post request")
            statis_period = request.data.get("statis_period")
            req_data = {
                "statis_period": int(statis_period)
            }
            ret = server_post("/api/v1/index/get_top_data", req_data)
            return JSONResponse(ret)
        except Exception as err:
            logger.error("Get system monitor top data error: %s", err)
            logger.error(''.join(traceback.format_exc()))
            ret = get_error_result("OtherError")
            return JSONResponse(ret)


class ResourceStatisticData(APIView):
    """
    get resource statistic: node resource_pool instance terminal
    """
    def get(self, request, *args, **kwargs):
        try:
            logger.debug("get_resource_statistic request")
            ret = get_error_result("Success")
            ret["data"] = {}
            node_query_set = YzyNodes.objects.filter(deleted=0).all()
            online_node_cnt = len([x for x in node_query_set if x.status == "active"])
            resource_pool_cnt = YzyResourcePools.objects.filter(deleted=0).count()
            instance_query_set = YzyInstances.objects.filter(deleted=0).all()
            online_instance_cnt = len([x for x in instance_query_set if x.status == "active"])
            terminal_query_set = YzyTerminal.objects.filter(deleted=0).all()
            online_terminal_cnt = len([x for x in terminal_query_set if x.status == "1"])
            ha_info = YzyHaInfo.objects.filter(deleted=False).first()
            ret['data']['ha_enable_status'] = 0
            if ha_info:
                request_data = {
                    "ha_info_uuid": ha_info.uuid
                }
                resp = server_post("/controller/ha_status", request_data)
                ret['data']['ha_enable_status'] = resp['data']['ha_enable_status']
            _time = time.localtime()
            ret['data']['current_time'] = time.strftime("%Y-%m-%d %H:%M", _time)
            ret["data"]["online_node_cnt"] = online_node_cnt
            ret["data"]["sum_node_cnt"] = len(node_query_set)
            ret["data"]["online_instance_cnt"] = online_instance_cnt
            ret["data"]["sum_instance_cnt"] = len(instance_query_set)
            ret["data"]["online_terminal_cnt"] = online_terminal_cnt
            ret["data"]["sum_terminal_cnt"] = len(terminal_query_set)
            ret["data"]["resource_pool_cnt"] = resource_pool_cnt
            ret["data"]["alarm_node_cnt"] = 0
            ret["data"]["alarm_records_cnt"] = 0
            lic_info = LicenseManager().info()
            ret["data"]["license_status"] = lic_info['auth_type']
            ret["data"]["trail_days"] = lic_info['expire_time']
            ret["data"]["vdi_size"] = lic_info['vdi_size']
            ret["data"]["voi_size"] = lic_info['voi_size']
            ret['data']['current_version'] = 'V' + lic_info['version'].split('_')[-2] if lic_info['version'] else '0'

            logger.debug("ret: {}".format(ret))
            return JSONResponse(ret)
        except Exception as err:
            logger.error("get_resource_statistic error: %s", err)
            logger.error(''.join(traceback.format_exc()))
            ret = get_error_result("OtherError")
            return JSONResponse(ret)


class OperationLogData(APIView):
    def get_object_list(self, request, page):
        try:
            query_set = YzyOperationLog.objects.filter(deleted=False)
            admin_users = page.paginate_queryset(queryset=query_set, request=request, view=self)
            return admin_users
        except Exception as e:
            raise Http404()

    def get(self, request, *args, **kwargs):
        try:
            page = YzyWebPagination()
            query_set = YzyOperationLog.objects.filter(deleted=False).order_by('-id')
            nodes = page.paginate_queryset(queryset=query_set, request=request, view=self)
            ser = OperationLogSerializer(instance=nodes, many=True, context={'request': request})
            return page.get_paginated_response(ser.data)
        except Exception as e:
            logger.error("get operation log error:%s", e)
            return HttpResponseServerError()


class SystemMonitorVoiServerDate(APIView):
    """
    获取voi首页监控数据：cpu memory disk network
    """
    def get(self, request, *args, **kwargs):
        try:
            logger.info("system monitor post request")
            req_data = {}
            ret = server_post("/api/v1/index/get_voi_data", req_data)
            return JSONResponse(ret)
        except Exception as e:
            logger.error("Get system monitor top data error: %s", e)
            logger.error(''.join(traceback.format_exc()))
            ret = get_error_result("OtherError")
            return JSONResponse(ret)


class ResourceStatisticVOIData(APIView):
    """
    获取voi首页桌面及节点信息
    """
    def get(self, request, *args, **kwargs):
        logger.debug("get node voi resource statistic request")
        resp = get_error_result("Success")
        resp['data'] = {}
        try:
            node = YzyNodes.objects.filter(deleted=False, type__in=[1, 3]).first()
            teach_template = YzyVoiTemplate.objects.filter(deleted=False, classify=constants.EDUCATION_TYPE).all()
            personal_template = YzyInstanceTemplate.objects.filter(deleted=False, classify=constants.PERSONAL_TYPE).count()
            # teach_instances = YzyInstances.objects.filter(deleted=False, classify=constants.EDUCATION_TYPE).count()
            teach_instances = 0
            for template in teach_template:
                desktops = YzyVoiDesktop.objects.filter(template=template, deleted=False).all()
                for desktop in desktops:
                    terminals = YzyVoiTerminalToDesktops.objects.filter(deleted=False, desktop_group=desktop.uuid).all()
                    teach_instances += len(terminals)
            personal_instances = YzyInstances.objects.filter(deleted=False, classify=constants.PERSONAL_TYPE).count()
            teach_desktop = YzyVoiDesktop.objects.filter(deleted=False).count()
            teach_desktop_active = YzyVoiDesktop.objects.filter(deleted=False, active=True).count()
            personal_desktop = YzyPersonalDesktop.objects.filter(deleted=False).count()
            teach_group = YzyVoiGroup.objects.filter(deleted=False).all()[:5]
            resp['data']['node_ip'] = node.ip
            resp['data']['status'] = node.status
            resp['data']['teach'] = {}
            resp['data']['teach']['teach_count'] = len(teach_template)
            resp['data']['teach']['desktop_reference'] = teach_instances
            resp['data']['personal'] = {}
            resp['data']['personal']['personal_count'] = personal_template
            resp['data']['personal']['desktop_reference'] = personal_instances
            resp['data']['teach_desktop'] = teach_desktop
            resp['data']['teach_desktop_active'] = teach_desktop_active
            resp['data']['personal_desktop'] = personal_desktop
            resp['data']['teach_group'] = []
            for teach in teach_group:
                terminal_count = YzyVoiTerminal.objects.filter(group_uuid=teach.uuid, deleted=False).all()
                terminals = terminal_count.filter(status=1).count()
                resp['data']['teach_group'].append({
                                                    "name": teach.name,
                                                    "terminal_count": len(terminal_count),
                                                    "off_line": len(terminal_count) - terminals,
                                                    "on_line": terminals
                })
            lic_info = LicenseManager().info()
            resp['data']['license_status'] = lic_info['auth_type']
            resp['data']['voi_size'] = lic_info['voi_size']
            return JSONResponse(resp)
        except Exception as e:
            logger.error("get node voi resource statistic fail %s", e)
            logger.error(''.join(traceback.format_exc()))
            ret = get_error_result("OtherError")
            return JSONResponse(ret)


class ResourceStatisticFuseData(APIView):
    """
    融合版首页静态资源数据
    """
    def get(self, request, *args, **kwargs):
        logger.debug("get fuse resource statistic data")
        resp = get_error_result()
        resp['data'] = {}
        try:
            # 获取资源概况数据
            resource_pools = YzyResourcePools.objects.filter(deleted=False).count()
            nodes = YzyNodes.objects.filter(deleted=False).all()
            error_nodes = nodes.filter(status=constants.STATUS_ERROR).count()
            boot_nodes = nodes.filter(status__in=[constants.STATUS_ERROR, constants.STATUS_ACTIVE, constants.STATUS_UPDATING]).count()
            lic_info = LicenseManager().info()

            # 资源池及授权信息组织
            _time = time.localtime()
            resp['data']['current_time'] = time.strftime("%Y-%m-%d %H:%M", _time)
            resp['data']['resource_pool'] = resource_pools
            resp['data']['server_count'] = len(nodes)
            resp['data']['boot_server'] = boot_nodes
            resp['data']['error_server'] = error_nodes
            resp['data']['vdi_auth'] = lic_info['vdi_size']
            resp['data']['voi_auth'] = lic_info['voi_size']
            # resp['data']['idv_auth'] = lic_info['idv_size']
            resp['data']['auth_status'] = lic_info['auth_type']
            resp['data']['expiration_date'] = lic_info['expire_time']
            resp['data']['current_version'] = 'V' + lic_info['version'].split('_')[-2] if lic_info['version'] else '0'
            logger.debug("get resource pools and auth data success")

            # 获取云桌面数据
            voi_desktops = YzyVoiTerminal.objects.filter(deleted=False).all()
            vdi_desktops = YzyInstances.objects.filter(deleted=False, classify__in=[1, 2]).all()
            idv_desktops = []
            teach_desktops = vdi_desktops.filter(classify=constants.EDUCATION_TYPE).all()
            teach_power = teach_desktops.filter(status=constants.STATUS_ACTIVE).count()
            teach_shutdown = len(teach_desktops) - teach_power
            personal_desktops = vdi_desktops.filter(classify=constants.PERSONAL_TYPE).all()
            personal_power = personal_desktops.filter(status=constants.STATUS_ACTIVE).count()
            personal_shutdown = len(personal_desktops) - personal_power
            voi_desktop_power = 0
            for desktop in voi_desktops:
                if desktop.status != 0:
                    voi_desktop_power += 1
            voi_desktop_shutdown = len(voi_desktops) - voi_desktop_power

            # 云桌面数据组织
            resp['data']['desktop_count'] = len(voi_desktops) + len(vdi_desktops) + len(idv_desktops)
            resp['data']['teach_desktop'] = []
            resp['data']['teach_desktop'].append({"name": "vdi",
                                                  "power_num": teach_power,
                                                  "shutdown_num": teach_shutdown})
            resp['data']['teach_desktop'].append({"name": "voi",
                                                  "power_num": voi_desktop_power,
                                                  "shutdown_num": voi_desktop_shutdown})
            resp['data']['personal_desktop'] = []
            resp['data']['personal_desktop'].append({"name": "vdi",
                                                     "power_num": personal_power,
                                                     "shutdown_num": personal_shutdown})
            resp['data']['personal_desktop'].append({"name": "voi",
                                                     "power_num": 0,
                                                     "shutdown_num": 0})
            logger.debug("get instances data success")

            # 获取终端信息
            vdi_terminals = YzyTerminal.objects.filter(deleted=False).all()
            terminal_count = len(vdi_terminals) + len(voi_desktops)
            terminal_power = vdi_terminals.filter(status=1).count()
            terminal_shutdown = len(vdi_terminals) - terminal_power

            # 终端信息组织
            resp['data']['terminal_count'] = terminal_count
            resp['data']['terminal'] = []
            resp['data']['terminal'].append({"name": "vdi",
                                             "power_num": terminal_power,
                                             "shutdown_num": terminal_shutdown})
            resp['data']['terminal'].append({"name": "voi",
                                             "power_num": voi_desktop_power,
                                             "shutdown_num": voi_desktop_shutdown})
            logger.debug("get terminal data success")

            # 获取教室信息
            class_list = []
            vdi_groups = YzyGroup.objects.filter(deleted=False).all()
            for group in vdi_groups:
                terminals = YzyTerminal.objects.filter(deleted=False, group_uuid=group.uuid).all()
                on_line = terminals.filter(status=1).count()
                class_list.append({"name": group.name, "instances": len(terminals), "on_line": on_line})

            voi_class_list = []
            voi_groups = YzyVoiGroup.objects.filter(deleted=False).all()
            for group in voi_groups:
                terminals = YzyVoiTerminal.objects.filter(deleted=False, group_uuid=group.uuid).all()
                on_line = terminals.exclude(status=0).count()
                voi_class_list.append({"name": group.name, "instances": len(terminals), "on_line": on_line})
            # 教室信息组织
            resp['data']['groups'] = {}
            resp['data']['groups']['vdi'] = {}
            resp['data']['groups']['voi'] = {}
            # resp['data']['groups']['idv'] = {}
            resp['data']['groups']['vdi']['class_room'] = len(vdi_groups)
            resp['data']['groups']['vdi']['instance_on_line'] = terminal_power
            resp['data']['groups']['vdi']['instance_count'] = len(vdi_terminals)
            vdi_ratio = teach_power / len(teach_desktops) if len(teach_desktops) != 0 else 0
            resp['data']['groups']['vdi']['ratio'] = '%0.2f' % (vdi_ratio * 100)
            resp['data']['groups']['voi']['class_room'] = len(voi_groups)
            resp['data']['groups']['voi']['instance_on_line'] = voi_desktop_power
            resp['data']['groups']['voi']['instance_count'] = len(voi_desktops)
            voi_ratio = voi_desktop_power / len(voi_desktops) if len(voi_desktops) != 0 else 0
            resp['data']['groups']['voi']['ratio'] = '%0.2f' % (voi_ratio * 100)
            resp['data']['class_list'] = class_list
            resp['data']['voi_class_list'] = voi_class_list
            logger.debug("get class room data success")
            return JSONResponse(resp)
        except Exception as e:
            logger.error("get node fuse resource statistic fail %s", e, exc_info=True)
            ret = get_error_result("OtherError")
            return JSONResponse(ret)
