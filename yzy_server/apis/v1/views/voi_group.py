"""
分组和用户的管理
"""
import os
import logging
from flask.views import MethodView
from flask import request, jsonify
from common.utils import time_logger, build_result
from yzy_server.utils import abort_error
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.voi_group_ctl import VoiGroupController


logger = logging.getLogger(__name__)


class VoiEducationGroupAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            logger.debug("post request, data:%s", data)
            if action == "create":
                """
                {
                    "name": "group1",
                    "group_type": 1,
                    "desc": "this is group1",
                    "start_ip": "",
                    "end_ip": "",
                    "dhcp": {
                        "start_ip": "172.16.1.40",
                        "end_ip": "172.16.1.54",
                        "exclude": [
                            {"start": "172.16.1.24", "end": "172.16.1.24"},
                            {"start": "172.16.1.24", "end": "172.16.1.24"}
                        ]
                    }
                }
                """
                result = VoiGroupController().create_group(data)

            elif action == "delete":
                group_uuid = data.get("uuid", "")
                result = VoiGroupController().delete_group(group_uuid)

            elif action == "update":
                """
                {
                    "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea",
                    "value": {
                        "name": "group2",
                        "desc": "",
                        "start_ip": "",
                        "end_ip": "",
                        "dhcp": {
                            "start_ip": "172.16.1.40",
                            "end_ip": "172.16.1.54",
                            "netmask": "255.255.255.0",
                            "gateway": "172.16.1.254",
                            "exclude": [
                                {"start": "172.16.1.24", "end": "172.16.1.24"},
                                {"start": "172.16.1.24", "end": "172.16.1.24"}
                            ]
                        }
                    }
                }
                """
                result = VoiGroupController().update_group(data)

            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("voi group action %s failed:%s", action, e)
            return build_result("OtherError")


api_v1.add_url_rule('/voi/group/<string:action>', view_func=VoiEducationGroupAPI.as_view('voi_group'), methods=["POST"])
