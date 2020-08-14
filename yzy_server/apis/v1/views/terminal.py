"""
桌面组和桌面的管理，包括教学桌面和个人桌面
"""
import logging
from flask.views import MethodView
from flask import request
from common.utils import time_logger, build_result
from yzy_server.utils import abort_error
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.terminal_ctl import TerminalController


logger = logging.getLogger(__name__)


class TerminalPersonalAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "login":
                return TerminalController().user_login(data)
            elif action == 'logout':
                return TerminalController().user_logout(data)
            elif action == 'change_pwd':
                return TerminalController().user_password_change(data)
            elif action == 'person_desktops':
                return TerminalController().person_desktop_groups(data)
            elif action == 'instance':
                return TerminalController().person_instance(data)
            elif action == "close_instance":
                return TerminalController().person_instance_close(data)
            elif action == "group":
                return TerminalController().person_group()
            else:
                return abort_error(404)
        except Exception as e:
            logger.error("education desktop action %s failed:%d", action, e, exc_info=True)
            return build_result("OtherError")


class TerminalEduAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "edu_desktops":
                return TerminalController().edu_desktop_groups(data)
            elif action == "instance":
                return TerminalController().education_instance(data)
            elif action == "close_instance":
                return TerminalController().close_education_instance(data)
            elif action == "group":
                return TerminalController().education_group(data)
            else:
                return abort_error(404)
        except Exception as e:
            logger.error("personal desktop action %s failed:%s", action, e, exc_info=True)
            return build_result("OtherError")


class TerminalInstanceAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "list":
                return TerminalController().terminal_instance_match(data)
            elif action == "close":
                return TerminalController().terminal_instance_close(data)
            elif action == "group":
                return TerminalController().terminal_group_list(data)
            else:
                return abort_error(404)
        except Exception as e:
            logger.error("personal desktop action %s failed:%s", action, e, exc_info=True)
            return build_result("OtherError")


api_v1.add_url_rule('/terminal/personal/<string:action>', view_func=TerminalPersonalAPI.as_view('terminal_personal'),
                    methods=["POST"])
api_v1.add_url_rule('/terminal/education/<string:action>', view_func=TerminalEduAPI.as_view('terminal_education'),
                    methods=["POST"])
api_v1.add_url_rule('/terminal/instance/<string:action>', view_func=TerminalInstanceAPI.as_view('terminal_instance'),
                    methods=["POST"])
