"""
分组和用户的管理
"""
import os
import logging
from urllib.parse import quote
from flask.views import MethodView
from flask import request, Response, jsonify
from common.utils import time_logger, build_result
from yzy_server.utils import abort_error
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.group_ctl import GroupController, GroupUserController


logger = logging.getLogger(__name__)


class EducationGroupAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "create":
                """
                {
                    "name": "group1",
                    "group_type": 1,
                    "desc": "this is group1",
                    "network_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea",
                    "subnet_uuid": "5712bcb6-27b5-11ea-8c45-562668d3ccea",
                    "start_ip": "",
                    "end_ip": ""
                }
                """
                result = GroupController().create_group(data)

            elif action == "delete":
                group_uuid = data.get("uuid", "")
                result = GroupController().delete_group(group_uuid)

            elif action == "update":
                """
                {
                    "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea",
                    "value": {
                        "name": "group2",
                        "desc": "",
                        "network_uuid": "",
                        "subnet_uuid": "",
                        "start_ip": "",
                        "end_ip": ""
                    }
                }
                """
                result = GroupController().update_group(data)

            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("group action %s failed:%s", action, e)
            return build_result("OtherError")


class GroupUserAPI(MethodView):

    @time_logger
    def get(self, action):
        if action == "download":
            flag = True
            fullfilename = request.args.get('path')
            # if not fullfilename:
            #     flag = False
            #     fullfilename = "/opt/导入模板.xlsx"

            def send_file():
                store_path = fullfilename
                with open(store_path, 'rb') as targetfile:
                    while 1:
                        data = targetfile.read(5 * 1024 * 1024)  # 每次读取5M
                        if not data:
                            break
                        yield data
                try:
                    if flag:
                        os.remove(fullfilename)
                except OSError as e:
                    pass

            response = Response(send_file(), content_type='application/octet-stream; charset=UTF-8')
            filename = quote(fullfilename.split('/')[-1])
            response.headers["Content-disposition"] = "attachment; filename*=UTF-8''{}" .format(filename)
            return response

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "create":
                """
                {
                    "group_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea"
                    "user_name": "user1",
                    "passwd": "password",
                    "name": "john",
                    "phone": "13144556677",
                    "email": "345673456@qq.com",
                    "enabled": 1
                }
                """
                result = GroupUserController().create_user(data)

            elif action == "multi_create":
                """
                {
                    "group_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea"
                    "prefix": "user1",
                    "postfix": 2,
                    "postfix_start": 3,
                    "user_num": 10,
                    "passwd": "12345",
                    "enabled": 1
                }
                """
                result = GroupUserController().multi_create_user(data)

            elif action == "delete":
                uuid = data.get("uuid", [])
                result = GroupUserController().delete_user(uuid)

            elif action == "enable":
                uuid = data.get("uuid", [])
                result = GroupUserController().enable_user(uuid)

            elif action == "disable":
                uuid = data.get("uuid", [])
                result = GroupUserController().disable_user(uuid)

            elif action == "reset_passwd":
                uuid = data.get("uuid", [])
                result = GroupUserController().reset_passwd(uuid)

            elif action == "export":
                result = GroupUserController().export_user(data)

            elif action == "import":
                result = GroupUserController().import_user(data)

            elif action == "move":
                """
                {
                    "group_uuid": "",
                    "users": [
                        "",
                        ...
                    ]
                }
                """
                result = GroupUserController().move_user(data)

            elif action == "update":
                """
                {
                    "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea",
                    "value": {
                        "group_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea"
                        "user_name": "user1",
                        "passwd": "password",
                        "name": "john",
                        "phone": "13144556677",
                        "email": 345673456@qq.com",
                        "enabled": 1
                    }
                }
                """
                result = GroupUserController().update_user(data)

            else:
                result = abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("group user action %s failed:%s", action, e)
            return build_result("OtherError")


api_v1.add_url_rule('/group/<string:action>', view_func=EducationGroupAPI.as_view('group'), methods=["POST"])
api_v1.add_url_rule('/group/user/<string:action>', view_func=GroupUserAPI.as_view('user'), methods=["GET", "POST"])
