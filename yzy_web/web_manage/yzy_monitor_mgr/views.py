import traceback
import logging
import time
from django.http import Http404, HttpResponseServerError
from django.utils.encoding import escape_uri_path
from django.http import JsonResponse, FileResponse
from rest_framework.views import APIView
from web_manage.common.http import server_post, monitor_post, voi_terminal_post
from web_manage.common.utils import JSONResponse, YzyWebPagination, get_error_result
from web_manage.yzy_monitor_mgr.models import YzyNodes2
from web_manage.common.general_query import GeneralQuery
from web_manage.yzy_monitor_mgr.serializers import YzyNodesSerializer2, YzyWarningInfoSerializer, \
    YzyWarningInfoDesktopSerializer, TerminalMonitorSerializer
from concurrent.futures import ThreadPoolExecutor, as_completed
from web_manage.common import constants
from web_manage.yzy_monitor_mgr.models import YzyNodeNetworkInfo2, YzyInterfaceIp2, YzyVoiTerminalPerformance, \
    YzyVoiTerminalHardWare
from django.db.models import Q
from web_manage.yzy_edu_desktop_mgr.models import YzyInstances
from web_manage.yzy_voi_edu_desktop_mgr.models import YzyVoiTerminal
from web_manage.yzy_resource_mgr.models import YzyNodes


logger = logging.getLogger(__name__)


class MonitorNodeInfo(APIView):
    def get(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        return query.model_query(request, YzyNodes2, YzyNodesSerializer2, query_dict)


class MonitorNodeHisPerformance(APIView):
    def get(self, request, *args, **kwargs):
        pass

    def get_mange_nic(self, uuid):
        try:
            nics = YzyNodeNetworkInfo2.objects.filter(Q(deleted=False), Q(node_uuid=uuid)).all()
            if nics:
                interfaces = [x.uuid for x in nics]
                manage_nic = YzyInterfaceIp2.objects.filter(deleted=False,
                                                           nic_uuid__in = interfaces,
                                                           is_manage=1).first()
                if manage_nic:
                    return manage_nic.name
            return None
        except Exception as err:
            logger.error("get manage nic error:%s", err, exc_info=True)
            return None

    def update_nic_order(self, data):
        if not data:
            return data
        try:
            node_uuid = data.get("node_uuid", None)
            manage_nic_name = self.get_mange_nic(node_uuid)
            if manage_nic_name:
                nics_data_tmp = dict()
                nics_data = data.get('nic_util', {})
                nics_data_tmp[manage_nic_name] = nics_data[manage_nic_name]
                nics_data_tmp.update({x: nics_data[x] for x in nics_data.keys() if x != manage_nic_name})
                data['nic_util'].clear()
                data['nic_util'] = nics_data_tmp
            return data
        except Exception as err:
            logger.error("update manage nic order error:%s", err, exc_info=True)
            return data

    def post(self, request):
        try:
            logger.info("post request: {}".format(request))
            data = request.data
            statis_hours = data.get('statis_hours', 0)
            step_minutes = data.get('step_minutes', 0)
            node_uuid = data.get('node_uuid', "")
            if not (statis_hours and step_minutes and node_uuid):
                pass
            request_data = {
                "statis_hours": statis_hours,
                "step_minutes": step_minutes,
                "node_uuid": node_uuid
            }
            ret = server_post('/api/v1/monitor/node/get_history_perf', request_data)
            _data = ret.get("data", {}).copy()
            if _data:
                ret['data'].clear()
                ret['data'] = self.update_nic_order(_data)
            return JSONResponse(ret)
        except Exception as e:
            logger.error("get node history performance data error:%s", e, exc_info=True)
            ret = get_error_result("OtherError")
            return JSONResponse(ret)


class MonitorNodeCurPerformance(APIView):
    def get(self, request, *args, **kwargs):
        pass

    def get_object_by_uuid(self, model, uuid):
        try:
            obj = model.objects.filter(deleted=False).get(uuid=uuid)
            return obj
        except Exception as err:
            logger.error("get_object_by_uuid error:%s", err, exc_info=True)
            return None

    def get_all_nodes_object(self, model):
        try:
            objs = model.objects.filter(deleted=False).all()
            return objs
        except Exception as err:
            logger.error("get_all_nodes_object error:%s", err, exc_info=True)
            return None

    def get_mange_nic(self, uuid):
        try:
            nics = YzyNodeNetworkInfo2.objects.filter(Q(deleted=False), Q(node_uuid=uuid)).all()
            if nics:
                interfaces = [x.uuid for x in nics]
                manage_nic = YzyInterfaceIp2.objects.filter(deleted=False,
                                                           nic_uuid__in = interfaces,
                                                           is_manage=1).first()
                if manage_nic:
                    return manage_nic.name
            return None
        except Exception as err:
            logger.error("get manage nic error:%s", err, exc_info=True)
            return None

    def update_nic_order(self, data):
        if not data:
            return data
        try:
            node_uuid = data.get("node_uuid", None)
            manage_nic_name = self.get_mange_nic(node_uuid)
            if manage_nic_name:
                nics_data_tmp = dict()
                nics_data = data.get('nic_util', {})
                nics_data_tmp[manage_nic_name] = nics_data[manage_nic_name]
                nics_data_tmp.update({x: nics_data[x] for x in nics_data.keys() if x != manage_nic_name})
                data['nic_util'].clear()
                data['nic_util'] = nics_data_tmp
            return data
        except Exception as err:
            logger.error("update manage nic order error:%s", err, exc_info=True)
            return data

    def post(self, request):
        try:
            data = request.data
            logger.info("post request: %s", data)
            statis_period = data.get('statis_period', 0)
            node_uuid = data.get('node_uuid', "")
            is_all_nodes = data.get('is_all_nodes', 0)
            if not (statis_period and is_all_nodes):
                pass

            url = '/api/v1/monitor/resource_perf_for_web'
            request_data = {
                "handler": "ServiceHandler",
                "command": "resource_perf_for_web",
                "statis_period": statis_period
            }
            if not is_all_nodes:
                node = self.get_object_by_uuid(YzyNodes2, uuid=node_uuid)
                if not node:
                    logger.error("node [%s] not exist!" % node_uuid)
                    return get_error_result("NodeNotExist")
                request_data.update({
                    "node_uuid": node.uuid,
                    "node_name": node.name
                })
                ret = monitor_post(node.ip, url, request_data)
                _data = ret.get("data", {}).copy()
                if _data:
                    ret['data'].clear()
                    ret['data'] = self.update_nic_order(_data)
                return JSONResponse(ret)
            else:
                nodes = self.get_all_nodes_object(YzyNodes2)
                node_list = [{"ip": node.ip, "node_uuid": node.uuid, "node_name": node.name} for node in nodes]
                if not node_list:
                    logger.error("no node exist!")
                    return get_error_result("NodeNotExist")
                all_task = []
                resp = get_error_result("Success", data=[])
                with ThreadPoolExecutor(max_workers=len(node_list)) as executor:
                    for node in node_list:
                        request_data.update({
                            "node_uuid": node['node_uuid'],
                            "node_name": node['node_name']
                        })
                        logger.info('monitor_post: {}, node_ip: {}'.format(request_data, node['ip']))
                        future = executor.submit(monitor_post, node['ip'], url, request_data)
                        all_task.append(future)
                    if len(node_list) >= 1:
                        for future in as_completed(all_task):
                            result = future.result()
                            logger.info('result: {}'.format(result))
                            if result.get("code") == 0:
                                _data = result.get("data", {}).copy()
                                if _data:
                                    result['data'].clear()
                                    result['data'] = self.update_nic_order(_data)
                                resp["data"].append(result['data'])
                    return JSONResponse(resp)
        except Exception as e:
            logger.error("get node history performance data error:%s", e, exc_info=True)
            ret = get_error_result("OtherError")
            return JSONResponse(ret)


class WarningInformation(APIView):
    """
    预警信息-云桌面在线监控中心
    """

    def get(self, request, *args, **kwargs):
        search_type = request.GET.get("search_type")
        uuid = request.GET.get("uuid")
        if search_type == "detail":
            return self.get_desktop_info(request, uuid)
        else:
            return self.get_node_info(request)

    def get_node_info(self, request):
        logger.debug("start get node info")
        resp = get_error_result("Success")
        try:
            nodes = YzyNodes.objects.filter(deleted=False).all()
            power_nodes = nodes.exclude(status=constants.STATUS_SHUTDOWN).count()
            resp['data'] = {}
            resp['data']['curr_time'] = time.strftime('%Y/%m/%d %H:%M', time.localtime())
            resp['data']['node_total'] = len(nodes)
            resp['data']['power_node'] = power_nodes
            resp['data']['shutdown_node'] = len(nodes) - power_nodes

            instances = YzyInstances.objects.filter(deleted=False).all()
            # voi_instances = YzyVoiTerminal.objects.filter(deleted=False).all()
            power_desktop = instances.filter(status=constants.STATUS_ACTIVE).count()
            error_desktop = instances.exclude(message='').count()
            resp['data']['desktop_total'] = len(instances)
            resp['data']['power_desktop'] = power_desktop
            resp['data']['shutdown_desktop'] = len(instances) - power_desktop
            resp['data']['error_desktop'] = error_desktop

            page = YzyWebPagination()
            controller_nodes = page.paginate_queryset(queryset=nodes, request=request, view=self)
            ser = YzyWarningInfoSerializer(instance=controller_nodes, many=True, context={'request': request})
            resp['data']['nodes'] = ser.data
            logger.info("get node info success: %s", nodes)
            return JSONResponse(resp)
        except Exception as e:
            logger.error("get node info error:%s", e, exc_info=True)
            ret = get_error_result("OtherError")
            return JSONResponse(ret)

    def get_desktop_info(self, request, uuid):
        logger.debug("start get instance info")
        resp = get_error_result("Success")
        try:
            node = YzyNodes.objects.filter(deleted=False, uuid=uuid).first()
            if not node:
                logger.error("get desktop info error: ParameterError")
                ret = get_error_result("ParameterError")
                return JSONResponse(ret)
            resp['data'] = {}
            instances = YzyInstances.objects.filter(deleted=False, host=node).all()
            power_instance = instances.filter(status=constants.STATUS_ACTIVE).count()
            error_instance = instances.exclude(message='').count()
            resp['data']['node_name'] = node.name
            resp['data']['power_instance'] = power_instance
            resp['data']['error_instance'] = error_instance
            resp['data']['total_instance'] = len(instances)
            resp['data']['shutdown_instance'] = len(instances) - power_instance

            page = YzyWebPagination()
            desktops = page.paginate_queryset(queryset=instances, request=request, view=self)
            ser = YzyWarningInfoDesktopSerializer(instance=desktops, many=True, context={'request': request})
            resp['data']['instances'] = ser.data
            logger.info("get instance info success: %s", desktops)
            return JSONResponse(resp)
        except Exception as e:
            logger.error("get instance info error:%s", e, exc_info=True)
            ret = get_error_result("OtherError")
            return JSONResponse(ret)


class MonitorTerminal(APIView):
    """
    终端监控
    """

    def get(self, request, *args, **kwargs):
        terminal_uuid = request.GET.get("terminal_uuid")
        terminal = YzyVoiTerminalPerformance.objects.filter(deleted=False, terminal_uuid=terminal_uuid).first()
        terminal_obj = YzyVoiTerminal.objects.filter(deleted=False, uuid=terminal_uuid).first()
        if not terminal:
            logger.error("get terminal monitor error: param error")
            return JSONResponse(get_error_result("ParameterError"))
        if not terminal_obj:
            logger.error("get terminal monitor error: terminal not exist")
            return JSONResponse(get_error_result("TerminalNotExistError"))
        if not terminal_obj.status:
            logger.error("get terminal monitor error: terminal status inactive")
            return JSONResponse(get_error_result("TerminalOfflineError"))
        ser = TerminalMonitorSerializer(instance=terminal, context={"request": request})
        return JSONResponse(ser.data)

    def post(self, request):
        terminal_uuid = request.data.get("uuid")
        option = request.data.get("option")
        if not (terminal_uuid and option):
            logger.error("post request error: param error")
            return JSONResponse(get_error_result("ParameterError"))
        if option == "terminal_hardware":
            return self.get_hardware(terminal_uuid)
        elif option == "export_resources":
            return self.get_terminal_resources(terminal_uuid)
        else:
            logger.error("option error:%s", option)
            return JSONResponse(get_error_result("ParameterError"))

    def get_terminal_resources(self, terminal_uuid):
        req_data = {
            "terminal_uuid": terminal_uuid
        }
        ret = server_post("/api/v1/monitor/terminal/export_resources", req_data)
        if ret.get("code", -1) == 0:
            _file = constants.TERMINAL_RESOURCES_PATH.split("/")[-1]
            response = FileResponse(open(constants.TERMINAL_RESOURCES_PATH, 'rb'))
            response['content_type'] = "application/octet-stream"
            response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path(_file))
            return response
        return JSONResponse(ret)

    def get_hardware(self, terminal_uuid):
        req_data = {
            "terminal_uuid": terminal_uuid
        }
        ret = server_post("/api/v1/monitor/terminal/terminal_hardware", req_data)
        if ret.get("code", -1) == 0:
            _file = constants.TERMINAL_HARDWARE_PATH.split("/")[-1]
            response = FileResponse(open(constants.TERMINAL_HARDWARE_PATH, 'rb'))
            response['content_type'] = "application/octet-stream"
            response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path(_file))
            return response
        return JSONResponse(ret)


