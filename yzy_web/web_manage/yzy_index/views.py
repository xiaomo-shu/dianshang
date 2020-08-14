import traceback
import logging
from django.http import Http404, HttpResponseServerError
from rest_framework.views import APIView
from web_manage.common.http import server_post
from web_manage.common.utils import JSONResponse, YzyWebPagination, get_error_result
from web_manage.yzy_resource_mgr.models import YzyResourcePools, YzyNodes
from web_manage.yzy_edu_desktop_mgr.models import YzyInstances, YzyOperationLog
from web_manage.yzy_terminal_mgr.models import YzyTerminal
from web_manage.yzy_edu_desktop_mgr.serializers import OperationLogSerializer
from web_manage.yzy_system_mgr.system_manager.license_manager import LicenseManager

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
