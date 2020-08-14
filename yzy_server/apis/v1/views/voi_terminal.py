"""
"""
import logging
from flask.views import MethodView
from flask import request
from common.utils import time_logger, build_result
from yzy_server.utils import abort_error
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.voi_terminal_ctl import VoiTerminalController


logger = logging.getLogger(__name__)


class VoiTerminalEduAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            logger.info("post data: {}".format(data))
            if action == "group":
                return VoiTerminalController().education_group(data)
            elif action == "desktop_bind":
                return VoiTerminalController().terminal_desktop_bind(data)
            if action == "groups":
                return VoiTerminalController().education_groups()
            if action == "create_desktop_bind":
                return VoiTerminalController().create_terminal_desktop_bind(data)
            if action == "delete_desktop_bind":
                return VoiTerminalController().delete_terminal_desktop_bind(data)
            if action == "update_desktop_bind":
                return VoiTerminalController().update_terminal_desktop_bind(data)
            if action == "desktop_ip_order":
                return VoiTerminalController().order_terminal_desktop_ip(data)
            else:
                return abort_error(404)
        except Exception as e:
            logger.error("personal desktop action %s failed:%s", action, e, exc_info=True)
            return build_result("OtherError")


class VoiTerminalShareDiskAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            logger.info("post data: {}".format(data))
            if action == "create":
                return VoiTerminalController().create_share_disk(data)
            elif action == "update":
                return VoiTerminalController().update_share_disk(data)
            else:
                return abort_error(404)
        except Exception as e:
            logger.error("personal desktop action %s failed:%s", action, e, exc_info=True)
            return build_result("OtherError")


api_v1.add_url_rule('/voi/terminal/education/<string:action>',
                    view_func=VoiTerminalEduAPI.as_view('voi_terminal_education'), methods=["POST"])
api_v1.add_url_rule('/voi/terminal/share_disk/<string:action>',
                    view_func=VoiTerminalShareDiskAPI.as_view('voi_terminal_share_disk'), methods=["POST"])
