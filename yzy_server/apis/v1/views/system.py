"""
系统管理模块
"""
import logging
from flask.views import MethodView
from flask import request, current_app, jsonify
from common.utils import time_logger, build_result
from yzy_server.utils import abort_error
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.system_ctl import DatabaseController, CrontabController, \
    AdminAuthController, LogSetupManager, StrategyManager


logger = logging.getLogger(__name__)


class AdminAuthAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            username = data.get("username", "")
            password = data.get("password")
            result = AdminAuthController().authorization(username, password)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("database back action %s failed:%d", action, e)
            return build_result("OtherError")


class DatabaseManagerAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "backup":
                """ 数据库备份 """
                db_user = current_app.config.get("DATABASE_USER", "")
                db_password = current_app.config.get("DATABASE_PASSWORD", "")
                db_name = current_app.config.get("DATABASE_NAME", "")
                result = DatabaseController().database_back(db_user, db_password, db_name)
            elif action == "delete":
                result = DatabaseController().delete_backup(data)
            # elif action == "download":
            #     result = DatabaseController().download_backup(data)
            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("database back action %s failed:%d", action, e)
            return build_result("OtherError")


class CrontabManagerAPI(MethodView):
    """
    定时任务接口
    """

    @time_logger
    def post(self, action):
        """
            {
                "count": 10,
                "node_uuid": "xxxxxxxxxx",
                "node_name": "name",
                "status": 0,
                "cron": {
                    "type": "day",			# week, month
                    "values": [1,2,3,4,5,6,7]
                    "hour": 1,
                    "minute": 10
                },
                "data": ["xxxxxxxxxxxxxx", "xxxxxxxxxxx", "xxxxxxxxxxxxxx"]
            }
        """
        try:
            data = request.get_json()
            if action == "database":
                result = CrontabController().database_back_crontab(data)
            elif action == "instance":
                result = CrontabController().add_instance_crontab(data)
            elif action == "node":
                result = CrontabController().add_node_crontab(data)
            elif action == "terminal":
                result = CrontabController().add_terminal_crontab(data)
            elif action == "log":
                result = CrontabController().add_log_crontab(data)
            elif action == "log_update":
                result = CrontabController().update_log_crontab(data)
            elif action == "update":
                """
                {
                    "uuid": "",
                    "name": "",
                    "value": {
                        "name": "",
                        "desc": "",
                        "status": 1,
                        "cron": [
                            {
                                "uuid": "",
                                "cmd": "off",
                                "type": "week",
                                "values": [1,2],
                                "hour": 14,
                                "minute": 12
                            },
                            ...
                        ]
                        "data" : [
                            {
                                "desktop_uuid": "",
                                "instances": {
                                    "uuid": "",
                                    "name": ""
                                }
                            }
                        ]
                    }
                }
                """
                result = CrontabController().update_crontab_task(data)
            elif action == "delete":
                task_uuid = data.get('uuid', '')
                result = CrontabController().delete_crontab_task(task_uuid)
            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("crontab action %s failed:%s", action, e)
            return build_result("OtherError")


class WarnSetupManagerAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "create":
                result = LogSetupManager().create_record(data)
            elif action == "update":
                result = LogSetupManager().update_record(data)
            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("warn setup action %s failed:%s", action, e)
            return build_result("OtherError")


class StrategyManagerAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "set_system_time":
                result = StrategyManager().set_system_time(data)
            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("set system time failed:%s", e)
            return build_result("OtherError")


api_v1.add_url_rule('/system/database/<string:action>', view_func=DatabaseManagerAPI.as_view('database_manager'),
                    methods=["POST"])

api_v1.add_url_rule('/system/crontab_task/<string:action>', view_func=CrontabManagerAPI.as_view('add_crontab_manager'),
                    methods=["POST"])

api_v1.add_url_rule('/system/admin/auth', view_func=AdminAuthAPI.as_view('admin-auth'), methods=["POST"])


api_v1.add_url_rule('/system/warn/setup/<string:action>', view_func=WarnSetupManagerAPI.as_view('log_setup_manager'),
                    methods=["POST"])

api_v1.add_url_rule('/system/strategy/<string:action>', view_func=StrategyManagerAPI.as_view('strategy_set_manager'),
                    methods=["POST"])