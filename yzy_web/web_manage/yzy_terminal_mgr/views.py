#-*- coding:UTF-8 -*-
import os
import logging
from django.db.models import Q
from rest_framework.views import APIView

from django.utils.encoding import escape_uri_path
from django.http import Http404, FileResponse

from .models import *
from .serializers import *
from web_manage.common import constants
from web_manage.common.utils import JSONResponse, YzyWebPagination, YzyAuthentication, YzyPermission, \
                                get_error_result
from .terminal_manager.terminal_manager import terminal_mgr


logger = logging.getLogger(__name__)


class TerminalGroupList(APIView):
    """
    终端组
    """
    def get(self, request, *args, **kwargs):
        group_type = request.GET.get("type")
        ret = terminal_mgr.get_all_group(group_type)
        return JSONResponse(ret)


class UEduGroupList(APIView):
    """
    非教学终端分组下拉框
    """
    def get(self, request, *args, **kwargs):
        ret = terminal_mgr.get_not_edu_group()
        return JSONResponse(ret)


class TerminalSortList(APIView):
    """
    终端组排序情况
    """
    def get(self, request, *args, **kwargs):
        group_uuid = request.GET.get("group_uuid", "")
        query_set = YzyTerminal.objects.values("id", "terminal_id", "mac", "ip", "name", "status")
        if group_uuid:
            group_info = terminal_mgr.get_group_info(group_uuid)
            if not group_info:
                raise Http404()
            group_name = group_info.name
            query_set = query_set.filter(group_uuid=group_uuid)
        else:
            query_set = query_set.filter(Q(group_uuid__isnull=True) | Q(group_uuid = ''))
            group_name = "未分组"
        group_dict = {"name": group_name, "uuid": group_uuid, "open_num": 0, "close_num": 0}
        terminals = query_set.order_by("terminal_id")
        results = list()
        for terminal in terminals:
            results.append(terminal)
            if str(terminal["status"]) == "0":
                group_dict["close_num"] += 1
            else:
                group_dict["open_num"] += 1
        # import pdb; pdb.set_trace()
        # for i in ser.data:
        #     if i["status"] == "0":
        #         group_dict["close_num"] += 1
        #     else:
        #         group_dict["open_num"] += 1

        # ret = terminal_mgr.get_all_terminal(request, group_type, group_uuid, _filter, page)
        # return JSONResponse(ret)
        ret = get_error_result("Success")
        ret["data"] = {"results": results, "group_info": group_dict}
        return JSONResponse(ret)


class TerminalList(APIView):
    """
    终端组
    """
    # def list(self, request, *args, **kwargs):
    #     try:
    #         page = YzyWebPagination()
    #         query_set = YzyNodes.objects.filter(deleted=False, type__in=[1, 2, 3])
    #         controller_nodes = page.paginate_queryset(queryset=query_set, request=request, view=self)
    #         ser = YzyNodesSerializer(instance=controller_nodes, many=True, context={'request': request})
    #         return page.get_paginated_response(ser.data)
    #     except Exception as e:
    #         return HttpResponseServerError()

    def get(self, request, *args, **kwargs):
        page = YzyWebPagination()
        group_uuid = request.GET.get("uuid", "")
        group_type = request.GET.get("type")
        _filter = request.GET.get("filter")
        query_set = YzyTerminal.objects
        if group_uuid:
            group_info = terminal_mgr.get_group_info(group_uuid)
            if not group_info:
                raise Http404()
            group_name = group_info.name
            query_set = query_set.filter(group_uuid=group_uuid).order_by("terminal_id")
        else:
            query_set = query_set.filter(Q(group_uuid__isnull=True) | Q(group_uuid='')).order_by("terminal_id")
            group_name = "未分组"

        if _filter:
            query_set = query_set.filter(Q(name__contains=_filter) | Q(ip__contains=_filter))
        terminals = page.paginate_queryset(queryset=query_set, request=request, view=self)
        ser = YzyTerminalSerializer(instance=terminals, many=True, context={'request': request})
        group_dict = {"name": group_name, "uuid": group_uuid, "open_num": 0, "close_num": 0}
        # import pdb; pdb.set_trace()
        all_terminals = query_set.all()
        for i in all_terminals:
            if str(i.status) == "0":
                group_dict["close_num"] += 1
            else:
                group_dict["open_num"] += 1

        # ret = terminal_mgr.get_all_terminal(request, group_type, group_uuid, _filter, page)
        # return JSONResponse(ret)
        return page.get_paginated_response(ser.data, {"group_info": group_dict})


class TerminalOperate(APIView):
    """
    终端操作
    """
    def post(self, request, *args, **kwargs):
        ret = terminal_mgr.terminal_operate(request)
        return JSONResponse(ret)


class TerminalLog(APIView):
    """
    终端日志下载
    """
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        # ret = terminal_mgr.terminal_log_download(request)
        _file = request.GET.get("file", "")
        log_dir = constants.TERMINAL_LOG_PATH
        file_path = os.path.join(log_dir, _file)
        if not os.path.exists(file_path):
            return JSONResponse(get_error_result("OtherError"))

        response = FileResponse(open(file_path, 'rb'))
        response['content_type'] = "application/octet-stream"
        response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path(_file))
        return response


class TerminalUpgradePag(APIView):
    """
    终端升级包
    """

    def get(self, request, *args, **kwargs):
        try:
            upgrades = YzyTerminalUpgrade.objects.filter(deleted=False)
            ser = YzyTerminalUpgradeSerializer(instance=upgrades, many=True, context={'request': request})
            return JSONResponse(get_error_result("Success", ser.data))
        except Exception as e:
            return JSONResponse(get_error_result("OtherError"))

    def post(self, request, *args, **kwargs):
        upgrade_uuid = request.data.get("upgrade_uuid", None)
        file_obj = request.FILES.get("file", None)
        if not file_obj:
            logger.error("terminal upgrade file upload error")
            return JSONResponse(get_error_result("TerminalUpgradeFileError"))
        return JSONResponse(terminal_mgr.upload_upgrade(upgrade_uuid, file_obj))

