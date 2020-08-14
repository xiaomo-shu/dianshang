import traceback
import logging
from django.http import Http404, HttpResponseServerError
from rest_framework.views import APIView
from web_manage.common.http import server_post, monitor_post
from web_manage.common.utils import JSONResponse, YzyWebPagination, get_error_result
from web_manage.yzy_monitor_mgr.models import YzyNodes2
from web_manage.common.general_query import GeneralQuery
from web_manage.yzy_monitor_mgr.serializers import YzyNodesSerializer2
from concurrent.futures import ThreadPoolExecutor, as_completed
from web_manage.common import constants
from web_manage.yzy_monitor_mgr.models import YzyNodeNetworkInfo2, YzyInterfaceIp2
from django.db.models import Q


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
            logger.info("post request: {}".format(request))
            data = request.data
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
