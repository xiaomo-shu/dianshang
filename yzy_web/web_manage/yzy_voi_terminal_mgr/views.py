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
from .voi_terminal_manager.voi_terminal_manager import voi_terminal_mgr
from ..yzy_terminal_mgr.models import YzyTerminalUpgrade
from ..yzy_terminal_mgr.serializers import YzyTerminalUpgradeSerializer
logger = logging.getLogger(__name__)


class TerminalGroupList(APIView):
    """
    终端组
    """
    def get(self, request, *args, **kwargs):
        group_type = request.GET.get("type")
        ret = voi_terminal_mgr.get_all_group(group_type)
        return JSONResponse(ret)


class GroupList(APIView):
    """
    终端分组下拉框
    """
    def get(self, request, *args, **kwargs):
        ret = voi_terminal_mgr.get_all_group_name()
        return JSONResponse(ret)


class EduGroupList(APIView):
    """
    教学分组下拉框
    """
    def get(self, request, *args, **kwargs):
        ret = voi_terminal_mgr.get_edu_group_name()
        return JSONResponse(ret)


class TerminalSortList(APIView):
    """
    终端组排序情况
    """
    def get(self, request, *args, **kwargs):
        group_uuid = request.GET.get("group_uuid", "")
        query_set = YzyVoiTerminal.objects.values("id", "terminal_id", "mac", "ip", "name", "status")
        if group_uuid:
            group_info = voi_terminal_mgr.get_group_info(group_uuid)
            if not group_info:
                raise Http404()
            group_name = group_info.name
            query_set = query_set.filter(group_uuid=group_uuid)
        else:
            query_set = query_set.filter(Q(group_uuid__isnull=True) | Q(group_uuid = ''))
            group_name = "未分组"

        group_dict = {"name": group_name, "uuid": group_uuid, "close_num": 0, "uefi_num": 0,
                      "linux_num": 0, "windows_num": 0, "u_linux_num": 0, }
        terminals = query_set.order_by("terminal_id")
        results = list()
        for terminal in terminals:
            results.append(terminal)
            if terminal["status"] == 0:
                group_dict["close_num"] += 1
            elif terminal["status"] == 1:
                group_dict["uefi_num"] += 1
            elif terminal["status"] == 2:
                group_dict["linux_num"] += 1
            elif terminal["status"] == 3:
                group_dict["windows_num"] += 1
            elif terminal["status"] == 5:
                group_dict["u_linux_num"] += 1
        # import pdb; pdb.set_trace()
        ret = get_error_result("Success")
        ret["data"] = {"results": results, "group_info": group_dict}
        return JSONResponse(ret)


class TerminalList(APIView):
    """
    终端组
    """
    def get(self, request, *args, **kwargs):
        page = YzyWebPagination()
        group_uuid = request.GET.get("uuid", "")
        group_type = request.GET.get("type")
        _filter = request.GET.get("filter")
        status = request.GET.get("status", '-1')
        query_set = YzyVoiTerminal.objects
        if group_uuid:
            group_info = voi_terminal_mgr.get_group_info(group_uuid)
            if not group_info:
                raise Http404()
            group_name = group_info.name
            query_set = query_set.filter(group_uuid=group_uuid)
        else:
            query_set = query_set.filter(Q(group_uuid__isnull=True) | Q(group_uuid = '')).order_by("terminal_id")
            group_name = "未分组"

        if status != '-1':
            query_set = query_set.filter(status=status)
        if _filter:
            query_set = query_set.filter(Q(name__contains=_filter) | Q(ip__contains=_filter))
        terminals = page.paginate_queryset(queryset=query_set, request=request, view=self)
        ser = YzyVoiTerminalSerializer(instance=terminals, many=True, context={'request': request})
        group_dict = {"name": group_name, "uuid": group_uuid, "close_num": 0, "uefi_num": 0,
                      "linux_num": 0, "windows_num": 0, "u_linux_num": 0}
        # import pdb; pdb.set_trace()
        all_terminals = query_set.all()
        for i in all_terminals:
            if i.status == 0:
                group_dict["close_num"] += 1
            elif i.status == 1:
                group_dict["uefi_num"] += 1
            elif i.status == 2:
                group_dict["linux_num"] += 1
            elif i.status == 3:
                group_dict["windows_num"] += 1
            elif i.status == 5:
                group_dict["u_linux_num"] += 1

        return page.get_paginated_response(ser.data, {"group_info": group_dict})


class TerminalOperate(APIView):
    """
    终端操作
    """
    def post(self, request, *args, **kwargs):
        ret = voi_terminal_mgr.terminal_operate(request)
        return JSONResponse(ret)


class TerminalUpgrade(APIView):
    """
    VOI文件上传
    """
    def get(self, request, *args, **kwargs):
        try:
            upgrades = YzyTerminalUpgrade.objects.filter(deleted=False, platform='VOI').order_by("-upload_at")[:10]
            ser = YzyTerminalUpgradeSerializer(instance=upgrades, many=True, context={'request': request})
            return JSONResponse(get_error_result("Success", ser.data))
        except Exception as e:
            return JSONResponse(get_error_result("OtherError"))

    def post(self, request, *args, **kwargs):
        # upgrade_package_uuid = request.data.get("upgrade_package_uuid", None)
        upgrade_file_obj = request.FILES.get("file", None)
        if not upgrade_file_obj:
            logger.error("VOI terminal upgrade file upload error")
            return JSONResponse(get_error_result("TerminalUpgradeFileError"))
        return JSONResponse(voi_terminal_mgr.upload_upgrade(upgrade_file_obj))



