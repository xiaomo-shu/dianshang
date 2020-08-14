"""
Author:      zhurong
Email:       zhurong@yzy-yf.com
Created:     2020/4/20
系统管理部分的接口
"""
import logging
import datetime
import os
import tarfile
import copy

from rest_framework.views import APIView
from django.utils import timezone
from django.utils.encoding import escape_uri_path
from urllib.parse import quote
from django.http import JsonResponse, FileResponse
from web_manage.common.general_query import GeneralQuery
from web_manage.common.config import SERVER_CONF
from web_manage.common.errcode import get_error_result
from web_manage.common.utils import YzyWebPagination, create_md5, create_uuid
from web_manage.yzy_edu_desktop_mgr import models as education_model
from web_manage.yzy_edu_desktop_mgr import serializers as education_serializer
from web_manage.common.schemas import check_input
from web_manage.common.log import insert_operation_log
from .serializers import *
from . models import *
from web_manage.common.http import server_post
from .system_manager.database_back_manager import DatabaseBackManager
from .system_manager.crontab_manager import CrontabTaskManager
from .system_manager.license_manager import LicenseManager
from .system_manager.log_manager import LogSetupManager
from web_manage.yzy_terminal_mgr.terminal_manager.terminal_manager import TerminalManager
from web_manage.yzy_resource_mgr.models import YzyNodes, YzyResourcePools
from web_manage.common import constants

logger = logging.getLogger(__name__)


class CrontabTaskView(APIView):
    """
    定时任务
    """
    def contab_type_switch(self, cron_type):
        cron_type = str(cron_type)
        if "0" == cron_type:
            _filter = (0, )
        elif "1" == cron_type:
            _filter = (1, 2)
        elif "2" == cron_type:
            _filter = (3, )
        elif "3" == cron_type:
            _filter = (4, )
        else:
            _filter = (0, )
        return _filter

    def get(self, request, *args, **kwargs):
        """
        定时任务获取
        0-数据库定时任务，1-桌面定时任务，2-主机定时任务，3-终端定时任务
        """
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        cron_type = query_dict.get('cron_type__icontains', None)
        if cron_type:
            query_dict.pop('cron_type__icontains')
            # cron_type = self.contab_type_switch(cron_type)
            query_dict['type'] = cron_type
        cron_type = query_dict.get('cron_type', None)
        if cron_type:
            query_dict.pop('cron_type')
            # cron_type = self.contab_type_switch(cron_type)
            query_dict['type'] = cron_type
        return query.model_query(request, YzyCrontabTask, YzyCrontabTaskSerializer, query_dict)

    @check_input("crontab_task", need_action=True)
    def post(self, request):
        try:
            logger.info("crontab task desktop post request")
            try:
                data = request.data
                action = data['action']
                param = data['param']
                func = getattr(CrontabTaskManager, action + '_check')
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
            ret = func(CrontabTaskManager(), param, log_user)
        except Exception as e:
            logger.error("crontab task desktop error:%s", e, exc_info=True)
            ret = get_error_result("OtherError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    @check_input('crontab_task', action="delete")
    def delete(self, request):
        """
        {
            "tasks": [
                    {
                        "uuid": "",
                        "name": "group1"
                    }
                ]
        }
        """
        try:
            data = request.data
            tasks = data.get('tasks', [])
            names = list()
            for task in tasks:
                names.append(task['name'])
            ret = CrontabTaskManager().delete_crontab_task(tasks)
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            msg = "删除桌面定时任务'%s'" % ('/'.join(names))
            insert_operation_log(msg, ret['msg'], log_user, module="crontab")
        except Exception as e:
            logger.error("delete desktop crontab task error:%s", e, exc_info=True)
            ret = get_error_result("GroupDeleteError")
            msg = "删除桌面定时任务'%s'" % ('/'.join(names))
            insert_operation_log(msg, ret['msg'], log_user, module="crontab")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    def put(self, request):
        try:
            logger.info("update crontab task")
            data = request.data
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = CrontabTaskManager().update_crontab(data, log_user)
        except Exception as e:
            logger.error("update crontab task error:%s", e, exc_info=True)
            ret = get_error_result("CrontabTaskUpdateError", name=data.get('name', ''))
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class DatabaseBackView(APIView):
    """
    数据库备份记录
    """

    def get(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        return query.model_query(request, YzyDatabaseBack, YzyDatabaseBackSerializer, query_dict)

    @check_input("database", need_action=False)
    def post(self, request):
        try:
            logger.info("database post request")
            try:
                data = request.data
                action = data.get("action", "backup")
                param = data.get("param")
                func = getattr(DatabaseBackManager, action+'_check')
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
            ret = func(DatabaseBackManager(), param, log_user)
        except Exception as e:
            logger.error("backup database error:%s", e, exc_info=True)
            ret = get_error_result("OtherError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    def delete(self, request):
        """
        {
            "id": 1,
            "name": ""
        }
        """
        try:
            data = request.data
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = DatabaseBackManager().delete_check(data, log_user)
        except Exception as e:
            logger.error("delete desktop group error:%s", e, exc_info=True)
            ret = get_error_result("DesktopDeleteFail")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class DatabaseDownloadView(APIView):

    authentication_classes = []

    def get(self, request, *args, **kwargs):
        try:
            backup_id = request.query_params.get('id')
            backup = YzyDatabaseBack.objects.filter(id=backup_id, deleted=False).first()
            if not backup:
                logger.error("database backup is not exists")
                return JsonResponse(get_error_result("DatabaseBackNotExist", name=backup_id))
            logger.info("begin to download file:%s", backup.path)
            response = FileResponse(open(backup.path, 'rb'))
            response['Content-Type'] = "application/octet-stream; charset=UTF-8"
            response['Access-Control-Allow-Origin'] = "*"
            filename = quote(backup.path.split('/')[-1])
            response["Content-disposition"] = "attachment; filename*=UTF-8''{}".format(filename)
            return response
        except Exception as e:
            logger.error("download database backup failed:%s", e, exc_info=True)
            return JsonResponse(get_error_result("DatabaseDownloadError"))


class OperationLogView(APIView):

    @property
    def del_ranges(self):
        return ["week", "month", "three_month", "half_year", "year"]

    def to_date(self, del_range):
        today = datetime.datetime.today()
        if del_range == "week":
            date = today + datetime.timedelta(days=-7)
        elif del_range == "month":
            date = today + datetime.timedelta(days=-30)
        elif del_range == "three_month":
            date = today + datetime.timedelta(days=-30 * 3)
        elif del_range == "half_year":
            date = today + datetime.timedelta(days=-30 * 6)
        elif del_range == "year":
            date = today + datetime.timedelta(days=-365)
        else:
            date = today + datetime.timedelta(days=-365 * 10)
        return date

    def get(self, request, *args, **kwargs):
        user_id = request.GET.get("user_id", "")
        date = request.GET.get("date", "")
        page = YzyWebPagination()
        query_set = education_model.YzyOperationLog.objects.filter(deleted=False)
        if user_id:
            query_set = query_set.filter(user_id=user_id)
        if date:
            filter_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            tz = timezone.get_default_timezone()
            start = filter_date.replace(tzinfo=tz)
            end = start + datetime.timedelta(days=1)
            query_set = query_set.filter(created_at__range=[start, end])

        operates = page.paginate_queryset(queryset=query_set, request=request, view=self)
        ser = education_serializer.OperationLogSerializer(instance=operates, many=True, context={'request': request})
        return page.get_paginated_response(ser.data)

    def delete(self, request, *args, **kwargs):
        _data = request.data
        ids = _data.get("ids")
        del_range = _data.get("del_range")
        query_set = education_model.YzyOperationLog.objects
        if ids and isinstance(ids,list):
            query_set = query_set.filter(id__in=ids)
            operates = query_set.all()
        elif del_range in self.del_ranges:
            _date = self.to_date(del_range)
            tz = timezone.get_default_timezone()
            utc_date = _date.astimezone(tz)
            query_set = query_set.filter(created_at__lt=utc_date)
            operates = query_set.all()
        else:
            operates = []
        # operates = query_set.all()
        for i in operates:
            i.delete()
        ret = get_error_result()
        return JsonResponse(ret)


operation_log_mer = OperationLogView()


class WarningLogView(APIView):
    def get(self, request, *args, **kwargs):
        option = request.GET.get('option', '')
        date = request.GET.get('date', '')
        page = YzyWebPagination()
        query_set = YzyWarningLog.objects.filter(deleted=False)
        if option:
            query_set = query_set.filter(option=option)
        if date:
            filter_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            tz = timezone.get_default_timezone()
            start = filter_date.replace(tzinfo=tz)
            end = start + datetime.timedelta(days=1)
            query_set = query_set.filter(created_at__range=[start, end])

        warning_logs = page.paginate_queryset(queryset=query_set, request=request, view=self)
        ser = YzyWarningLogSerializer(instance=warning_logs, many=True, context={'request': request})
        return page.get_paginated_response(ser.data)

    def delete(self, request):
        _data = request.data
        ids = _data.get("ids")
        del_range = _data.get("del_range")
        query_set = YzyWarningLog.objects
        if ids and isinstance(ids, list):
            query_set = query_set.filter(number_id__in=ids)
            warnings = query_set.all()
        elif del_range in operation_log_mer.del_ranges:
            _date = operation_log_mer.to_date(del_range)
            tz = timezone.get_default_timezone()
            utc_date = _date.astimezone(tz)
            query_set = query_set.filter(created_at__lt=utc_date)
            warnings = query_set.all()
        else:
            warnings = []
        for warning in warnings:
            warning.delete()
        ret = get_error_result()
        return JsonResponse(ret)


class LogSetupCronView(APIView):

    def get(self, request, *args, **kwargs):
        ret = get_error_result("Success")
        uuid = request.GET.get("uuid", '')
        detail = YzyCrontabDetail.objects.filter(uuid=uuid).first()
        ser = YzyCrontabDetailSerializer(instance=detail, context={"request": request})
        ret['data'] = ser.data if detail else None
        return JsonResponse(ret)

    @check_input("crontab_task", need_action=True)
    def post(self, request):
        try:
            logger.info("crontab task log post request")
            try:
                data = request.data
                action = data['action']
                param = data['param']
                func = getattr(CrontabTaskManager, action + '_check')
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
            param['name'] = action + '_log_cron'
            ret = func(CrontabTaskManager(), param, log_user)
        except Exception as e:
            logger.error("crontab task warning log error:%s", e, exc_info=True)
            ret = get_error_result("OtherError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})

    @check_input("update_crontab_task", need_action=True)
    def put(self, request):
        try:
            logger.info("crontab task log post request")
            try:
                data = request.data
                action = data['action']
                param = data['param']
                func = getattr(CrontabTaskManager, action + '_update_check')
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
            param['name'] = action + '_log_cron'
            ret = func(CrontabTaskManager(), param, log_user)
        except Exception as e:
            logger.error("crontab task warning log error:%s", e, exc_info=True)
            ret = get_error_result("OtherError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class WarningLogSetupView(APIView):

    def get(self, request, *args, **kwargs):
        ret = get_error_result("Success")
        record = YzyWarnSetup.objects.filter(deleted=False).first()
        node = YzyNodes.objects.filter(deleted=False, type__in=[1, 3]).first()
        ser = YzyWarnSetupSerializer(instance=record, context={"request": request})
        ret['data'] = ser.data if record else None
        ret['control'] = {"name": node.name, "uuid": node.uuid}
        node_name = self.get_node_name(request)
        ret['node_name'] = node_name
        return JsonResponse(ret)

    def get_node_name(self, request):
        pool_name = list()
        pools = YzyResourcePools.objects.filter(deleted=False).all()
        for pool in pools:
            nodes = YzyNodes.objects.filter(deleted=False, resource_pool=pool.uuid).exclude(type__in=[1, 3]).all()
            for node in nodes:
                nodes_name = list()
                nodes_name.append({"name": node.name, "uuid": node.uuid})
                pool_name.append({"name": pool.name, "node_name": nodes_name})
        # ser = YzyStandbyControlSerializer(instance=pools, many=True, context={"request": request})
        # return ser.data
        return pool_name

    @check_input("warn_setup", action='create')
    def post(self, request):
        try:
            data = request.data
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            result = LogSetupManager().create_warn_setup(data, log_user)
        except Exception as e:
            logger.error("create warn setup record fail:%s", e, exc_info=True)
            ret = get_error_result("CreateWarnSetupFailError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(result)

    @check_input("warn_setup", action='update')
    def put(self, request):
        try:
            data = request.data
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            result = LogSetupManager().update_warn_setup(data, log_user)
        except Exception as e:
            logger.error("update warn setup record fail:%s", e, exc_info=True)
            ret = get_error_result("UpdateWarnSetupFailError")
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(result)


class ExportLogView(APIView):

    authentication_classes = []

    def get(self, request, *args, **kwargs):
        _file = request.GET.get("file", "")
        log_dir = constants.LOG_DOWN_PATH
        file_path = os.path.join(log_dir, _file)
        if not os.path.exists(file_path):
            return JsonResponse(get_error_result("OtherError"))

        response = FileResponse(open(file_path, 'rb'))
        response['content_type'] = "application/octet-stream"
        response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path(_file))
        return response

    def post(self, request):
        start_date = request.data.get('start_date', '')
        end_date = request.data.get('end_date', '')
        try:
            ret = self.get_log_file(start_date, end_date)
        except Exception as e:
            logger.error("log pack fail:%s", e)
            ret = get_error_result("OtherError")
        return ret

    def get_log_file(self, start_date, end_date):
        try:
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        except Exception as e:
            ret = get_error_result("ParamError")
            return JsonResponse(ret)
        if not os.path.exists(constants.LOG_DOWN_PATH):
            os.makedirs(constants.LOG_DOWN_PATH)
        time_stamp = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        name = "系统日志-" + time_stamp
        log_down_path = os.path.join(constants.LOG_DOWN_PATH, name)
        log_down_path = log_down_path + ".tar.gz"
        tar = tarfile.open(log_down_path, "w:gz")
        logger.info("open log down path %s success", log_down_path)
        log_files = os.listdir(constants.LOG_FILE_PATH)
        if start_date and end_date:
            c_log_files = copy.deepcopy(log_files)
            for file in c_log_files:
                end_str = file.split('.')[-1]
                try:
                    log_date = datetime.datetime.strptime(end_str, "%Y-%m-%d")
                except:
                    log_files.remove(file)
                    continue
                if not (start_date <= log_date <= end_date):
                    log_files.remove(file)
        for file in log_files:
            log_file = os.path.join(constants.LOG_FILE_PATH, file)
            if os.path.exists(log_file):
                tar.add(log_file)
        logger.info("write data success")
        tar.close()

        down_path = log_down_path.split('/')[-1]
        host = TerminalManager().get_all_object(YzyNodes, {"type": [1, 3]}, False)
        down_url = "http://%s:%s/api/v1.0/system/logs/export/?file=%s" % \
                   (host.ip, constants.WEB_DEFAULT_PORT, down_path)
        ret = get_error_result("Success", {"down_url": down_url})
        return JsonResponse(ret)


class AuthView(APIView):

    def get(self, request, *args, **kwargs):
        result = LicenseManager().info()
        ret = get_error_result("Success", result)
        return JsonResponse(ret)

    def post(self, request):
        try:
            data = request.data
            sn = data['sn']
            org_name = data['org_name']
            log_user = {
                "id": request.user.id if request.user.id else 1,
                "user_name": request.user.username,
                "user_ip": request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR')
                else request.META.get("REMOTE_ADDR")
            }
            ret = LicenseManager().activation(sn, org_name, log_user)
        except Exception as e:
            logger.error("activate license error:%s", e, exc_info=True)
            ret = {"result": False}
            return JsonResponse(ret, status=200,
                                json_dumps_params={'ensure_ascii': False})
        return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})


class AuthUkeyView(APIView):

    def get(self, request, *args, **kwargs):
        result = LicenseManager().get_ukey()
        ret = get_error_result("Success", result)
        return JsonResponse(ret)


class VoiSetupView(APIView):

    def get(self, request, *args, **kwargs):
        date_str = datetime.datetime.now().date().strftime('%Y%m%d')
        digital_list = sorted([int(x) for x in list(date_str)])
        zero_cnts = digital_list.count(0)
        tmp_num = zero_cnts
        for x in range(zero_cnts):
            digital_list[x] = tmp_num
            tmp_num -= 1
        digital_str_list = [str(x) for x in digital_list]
        offline_passwd = ''.join(digital_str_list)
        ret = get_error_result("Success", {"offline_passwd": offline_passwd})
        return JsonResponse(ret)


class UpgradeView(APIView):

    def get(self, request, *args, **kwargs):
        try:
            version = ""
            server_version = ""
            version_file = os.path.join(constants.BASE_DIR, 'version')
            if os.path.exists(version_file):
                with open(version_file, 'r') as fd:
                    version = fd.read().strip()
            server_file = "/etc/os-release"
            with open(server_file, 'r') as fd:
                lines = fd.readlines()
                for line in lines:
                    if line.startswith("VARIANT="):
                        server_version = line.split('=')[-1].replace('"', '').strip()
                        break
            controller = YzyNodes.objects.filter(deleted=False, type__in=[1, 3]).first()
            if SERVER_CONF.has_section('company'):
                site_name = SERVER_CONF.company.get_by_default("name", "")
            else:
                site_name = ""
            result = {
                "version": version,
                "server_version": server_version,
                "master_name": controller.name if controller else "",
                "master_ip": controller.ip if controller else "",
                "site_name": site_name
            }
            ret = get_error_result("Success", result)
        except Exception as e:
            logger.exception("get upgrade info failed:%s", e, exc_info=True)
            ret = get_error_result("OtherError")
        return JsonResponse(ret)
