import logging
from flask.views import MethodView
from flask import request, jsonify
from common.utils import time_logger, build_result
from yzy_server.utils import abort_error
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.voi_desktop_ctl import VoiDesktopController
from yzy_server.database import apis as db_api
from yzy_server.database import models
from common.utils import voi_terminal_post

logger = logging.getLogger(__name__)


class VoiEducationDesktopAPI(MethodView):

    @time_logger
    def notify_terminal(self, desktop_group_uuid=None, group_uuid=None):
        # get group_uuid
        logger.info("desktop_group_uuid={}, group_uuid={}".format(desktop_group_uuid, group_uuid))
        if not group_uuid and desktop_group_uuid:
            qry = db_api.get_item_with_first(models.YzyVoiDesktop, {'uuid': desktop_group_uuid})
            group_uuid = qry.group_uuid
        if not group_uuid:
            logger.error('group_uuid is null, do not notify terminals')
            return
        requst_data = {
            "handler": "WebTerminalHandler",
            "command": "update_desktop_group_notify",
            "data": {
                "group_uuid": group_uuid
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", requst_data)
        if ret.get("code", -1) != 0:
            logger.error("voi_terminal_post request: {}, ret: {}".format(requst_data, ret))
            return ret
        logger.info("voi_terminal_post request: {}, ret: {}".format(requst_data, ret))

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            logger.debug("post request, data:%s", data)
            if action == "create":
                """
                {
                    "name": "desktop2",
                    "owner_id": "",
                    "group_uuid": "d02cd368-5396-11ea-ad80-000c295dd728",
                    "template_uuid": "6f1006c0-56d1-11ea-aec0-000c295dd728",
                    "sys_restore": 1,
                    "data_restore": 1,
                    "prefix": "pc",
                    "show_info": 1,
                    "auto_update": 1,
                    "use_bottom_ip": True,
                    "ip_detail": {
                        "auto": False,
                        "start_ip":  "192.168.12.12",
                        "netmask": "255.255.255.0",
                        "gateway": "192.168.12.254",
                        "dns_master": "",
                        "dns_slave": ""
                    }
                }
                """
                result = VoiDesktopController().create_voi_desktop(data)
                group_uuid = data.get("group_uuid", "")
                if result.get("code", -1) == 0:
                    self.notify_terminal(None, group_uuid)

            elif action == 'active':
                desktop_uuid = data.get("uuid", "")
                result = VoiDesktopController().active_voi_desktop(desktop_uuid)
                if result.get("code", -1) == 0:
                    self.notify_terminal(desktop_uuid)

            elif action == 'inactive':
                desktop_uuid = data.get("uuid", "")
                result = VoiDesktopController().inactive_voi_desktop(desktop_uuid)
                if result.get("code", -1) == 0:
                    self.notify_terminal(desktop_uuid)

            elif action == 'default':
                desktop_uuid = data.get("uuid", "")
                result = VoiDesktopController().set_default_voi_desktop(desktop_uuid)
                if result.get("code", -1) == 0:
                    self.notify_terminal(desktop_uuid)

            elif action == "delete":
                desktop_uuid = data.get("uuid", "")
                result = VoiDesktopController().delete_voi_desktop(desktop_uuid)
                if result.get("code", -1) == 0:
                    self.notify_terminal(desktop_uuid)

            elif action == "update":
                desktop_uuid = data.get("uuid", "")
                result = VoiDesktopController().update_voi_desktop(data)
                if result.get("code", -1) == 0:
                    self.notify_terminal(desktop_uuid)

            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.error("voi education desktop action %s failed:%d", action, e, exc_info=True)
            return build_result("OtherError")


api_v1.add_url_rule('/voi/desktop/education/<string:action>', view_func=VoiEducationDesktopAPI.
                    as_view('voi_education_desktop'), methods=["POST"])
