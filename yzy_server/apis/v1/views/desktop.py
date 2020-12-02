"""
桌面组和桌面的管理，包括教学桌面和个人桌面
"""
import logging
from flask.views import MethodView
from flask import request, jsonify
from common.utils import time_logger, build_result
from yzy_server.utils import abort_error
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.desktop_ctl import DesktopController, PersonalDesktopController, InstanceController


logger = logging.getLogger(__name__)


class EducationDesktopAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "create":
                """
                {
                    "name": "desktop1",
                    "owner_id: 1,
                    "group_uuid": "1c7dff98-2dda-11ea-b565-562668d3ccea",   # 桌面所属分组
                    "template_uuid": "84f0e463-2dce-11ea-a71f-562668d3ccea",
                    "pool_uuid": "e865aa50-26ee-11ea-9b67-562668d3ccea",    # 所属资源池
                    "network_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea",
                    "subnet_uuid": "5712bcb6-27b5-11ea-8c45-562668d3ccea",
                    "vcpu": 4,
                    "ram": 4,
                    "sys_restore": 1,   # 系统盘是否还原
                    "data_restore": 1,  # 数据盘是否还原
                    "instance_num": 10,
                    "prefix": "pc",     # 单个桌面名称的前缀
                    "postfix": 3,       # 单个桌面名称的后缀数字个数
                    "postfix_start": 2,
                    "create_info": {        # 发布在哪些节点以及每个节点多少个桌面
                        "172.16.1.49": 5,
                        "172.16.1.50": 5
                    }
                }
                """
                result = DesktopController().create_desktop(data)

            elif action == 'active':
                desktop_uuid = data.get("uuid", "")
                result = DesktopController().active_desktop(desktop_uuid)

            elif action == 'inactive':
                desktop_uuid = data.get("uuid", "")
                result = DesktopController().inactive_desktop(desktop_uuid)

            elif action == "start":
                desktop_uuid = data.get("uuid", "")
                result = DesktopController().start_desktop(desktop_uuid)

            elif action == "stop":
                desktop_uuid = data.get("uuid", "")
                result = DesktopController().stop_desktop(desktop_uuid)

            elif action == "hard_stop":
                desktop_uuid = data.get("uuid", "")
                result = DesktopController().stop_desktop(desktop_uuid, hard=True)

            elif action == "stop_for_node":
                desktop_uuid = data.get("uuid", "")
                node_uuid = data.get("node_uuid", "")
                result = DesktopController().stop_desktop_for_node(desktop_uuid, node_uuid)

            elif action == "reboot":
                desktop_uuid = data.get("uuid", "")
                result = DesktopController().reboot_desktop(desktop_uuid)

            elif action == "delete":
                desktop_uuid = data.get("uuid", "")
                result = DesktopController().delete_desktop(desktop_uuid)

            elif action == "update":
                result = DesktopController().update_desktop(data)

            # elif action == "list":
            #     return EducationDesktopController().get_desktop_list()
            #
            # elif action == "instance":
            #     desktop_uuid = data.get("uuid", "")
            #     return EducationDesktopController().get_instance_by_desktop(desktop_uuid)
            # elif action == "reboot":
            #     desktop_uuid = data.get("desktop_uuid", "")
            #     return DesktopController().reboot_desktop(desktop_uuid)

            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("education desktop action %s failed:%d", action, e)
            return build_result("OtherError")


class PersonalDesktopAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "create":
                """
                {
                    "name": "desktop1",
                    "owner_id": 1,
                    "template_uuid": "84f0e463-2dce-11ea-a71f-562668d3ccea",
                    "pool_uuid": "e865aa50-26ee-11ea-9b67-562668d3ccea",    # 所属资源池
                    "network_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea",
                    "subnet_uuid": "5712bcb6-27b5-11ea-8c45-562668d3ccea",
                    "allocate_type": 2,         # 系统分配-1 固定分配-2
                    "allocate_start": "172.16.1.20",
                    "vcpu": 4,
                    "ram": 4,
                    "sys_restore": 1,   # 系统盘是否还原
                    "data_restore": 1,  # 数据盘是否还原
                    "desktop_type": 1,  # 1-随机桌面 2-静态桌面
                    "groups": [],       # 随机桌面时，绑定的分组
                    "group_uuid": "",   # 静态桌面时，绑定的哪个分组
                    "allocates": [      # 静态桌面时，桌面与用户对应关系
                        {
                            "user_uuid": "",
                            "name": ""
                        },
                        ...
                    ],    
                    "instance_num": 10,
                    "prefix": "pc",     # 单个桌面名称的前缀
                    "postfix": 3,       # 单个桌面名称的后缀数字个数
                    "postfix_start": 2,
                    "create_info": {        # 发布在哪些节点以及每个节点多少个桌面
                        "172.16.1.48": 5,
                        "172.16.1.49": 5
                    }
                }
                """
                result = PersonalDesktopController().create_personal_desktop(data)

            elif action == "start":
                desktop_uuid = data.get("uuid", "")
                result = PersonalDesktopController().start_personl_desktop(desktop_uuid)

            elif action == "stop":
                desktop_uuid = data.get("uuid", "")
                result = PersonalDesktopController().stop_personal_desktop(desktop_uuid)

            elif action == "hard_stop":
                desktop_uuid = data.get("uuid", "")
                result = PersonalDesktopController().stop_personal_desktop(desktop_uuid, hard=True)

            elif action == "stop_for_node":
                desktop_uuid = data.get("uuid", "")
                node_uuid = data.get("node_uuid", "")
                result = PersonalDesktopController().stop_personal_desktop_for_node(desktop_uuid, node_uuid)

            elif action == "reboot":
                desktop_uuid = data.get("uuid", "")
                result = PersonalDesktopController().reboot_personal_desktop(desktop_uuid)

            elif action == "delete":
                desktop_uuid = data.get("uuid", "")
                result = PersonalDesktopController().delete_personal_desktop(desktop_uuid)

            elif action == "update":
                result = PersonalDesktopController().update_personal_desktop(data)

            elif action == "enter_maintenance":
                desktop_uuid = data.get("uuid", "")
                result = PersonalDesktopController().enter_maintenance(desktop_uuid)

            elif action == "exit_maintenance":
                desktop_uuid = data.get("uuid", "")
                result = PersonalDesktopController().exit_maintenance(desktop_uuid)

            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("personal desktop action %s failed:%s", action, e)
            return build_result("OtherError")


class InstanceAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "create":
                """
                {
                    "desktop_uuid": "84f0e463-2dce-11ea-a71f-562668d3ccea",
                    "desktop_type": 1,
                    "instance_num": 10,
                    "create_info": {        # 发布在哪些节点以及每个节点多少个桌面
                        "172.16.1.48": 5,
                        "172.16.1.49": 5
                    }
                }
                """
                result = InstanceController().add_instances(data)

            elif action == "delete":
                """
                {
                    "desktop_uuid": "84f0e463-2dce-11ea-a71f-562668d3ccea",
                    "desktop_type": 2,
                    "instances": [
                            {
                                "uuid": "228d4d69-73b8-4694-836b-b2eeeec64c46",
                                "name": "pc01"
                            },
                            {
                                "uuid": "e7269662-0fd8-4e1f-b933-e614016294c2",
                                "name": "pc02"
                            },
                            ...
                        ]
                }
                """
                result = InstanceController().delete_instances(data)

            elif action == "start":
                """
                {
                    "desktop_uuid": "4c41b1dc-35d6-11ea-bc23-000c295dd728",
                    "desktop_type": 2,
                    "instances": [
                            {
                                "uuid": "228d4d69-73b8-4694-836b-b2eeeec64c46",
                                "name": "pc01"
                            },
                            {
                                "uuid": "e7269662-0fd8-4e1f-b933-e614016294c2",
                                "name": "pc02"
                            },
                            ...
                        ]
                }
                """
                result = InstanceController().start_instances(data)

            elif action == "stop":
                """
                {
                    "desktop_uuid": "4c41b1dc-35d6-11ea-bc23-000c295dd728",
                    "desktop_type": 1,
                    "instances": [
                            {
                                "uuid": "228d4d69-73b8-4694-836b-b2eeeec64c46",
                                "name": "pc01"
                            },
                            {
                                "uuid": "e7269662-0fd8-4e1f-b933-e614016294c2",
                                "name": "pc02"
                            },
                            ...
                        ]
                }
                """
                result = InstanceController().stop_instances(data)

            elif action == "hard_stop":
                """
                {
                    "desktop_uuid": "4c41b1dc-35d6-11ea-bc23-000c295dd728",
                    "desktop_type": 1,
                    "instances": [
                            {
                                "uuid": "228d4d69-73b8-4694-836b-b2eeeec64c46",
                                "name": "pc01"
                            },
                            {
                                "uuid": "e7269662-0fd8-4e1f-b933-e614016294c2",
                                "name": "pc02"
                            },
                            ...
                        ]
                }
                """
                result = InstanceController().stop_instances(data, hard=True)

            elif action == "reboot":
                """
                {
                    "desktop_uuid": "4c41b1dc-35d6-11ea-bc23-000c295dd728",
                    "desktop_type": 2,
                    "instances": [
                            {
                                "uuid": "228d4d69-73b8-4694-836b-b2eeeec64c46",
                                "name": "pc01"
                            },
                            {
                                "uuid": "e7269662-0fd8-4e1f-b933-e614016294c2",
                                "name": "pc02"
                            },
                            ...
                        ]
                }
                """
                result = InstanceController().reboot_instances(data)

            elif action == "add_group":
                """
                随机桌面添加用户组
                {
                    "desktop_uuid": "ea2bbe72-593c-11ea-9631-000c295dd728",
                    "desktop_name": "desktop1",
                    "groups": [
                            {
                                "group_uuid": "",
                                "group_name": ""
                            }
                        ]
                }
                """
                result = InstanceController().add_group(data)

            elif action == "delete_group":
                """
                随机桌面删除用户组绑定
                {
                    # "desktop_uuid": "ea2bbe72-593c-11ea-9631-000c295dd728",
                    # "desktop_name": "desktop1",
                    "groups": [
                            {
                                "uuid": "",
                                "group_name": ""
                            }
                        ]
                }
                """
                result = InstanceController().delete_group(data)

            elif action == "change_bind":
                """
                静态桌面的解除绑定
                {
                    "instance_uuid": "7380f97e-74d3-11ea-b50b-000c29e84b9c",
                    "instance_name": "PC1",
                    "user_uuid": "",
                    "user_name": "sss",
                }
                """
                result = InstanceController().change_bind(data)

            # elif action == "unbind_user":
            #     """
            #     静态桌面的解除绑定
            #     {
            #         "uuid": "7380f97e-74d3-11ea-b50b-000c29e84b9c",
            #         "user_name": "sss",
            #         "instance_name": "PC1"
            #     }
            #     """
            #     return InstanceController().unbind_user(data)
            #
            # elif action == "bind_user":
            #     """
            #     静态桌面的绑定
            #     {
            #         "desktop_uuid": "7380f97e-74d3-11ea-b50b-000c29e84b9c",
            #         "user_uuid": "",
            #         "user_name": "sss",
            #         "instance_uuid": "",
            #         "instance_name": "PC1"
            #     }
            #     """
            #     return InstanceController().bind_user(data)

            elif action == "change_group":
                """
                静态桌面更换绑定的用户组
                {
                    "desktop_uuid": "",
                    "desktop_name": "",
                    "group_uuid": "",
                    "group_name": ""
                }
                """
                result = InstanceController().change_group(data)
            elif action == "console":
                """
                {
                    "uuid": "",
                    "name": ""
                }
                """
                result = InstanceController().get_console(data)
            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("instance action %s failed:%s", action, e)
            return build_result("OtherError")


api_v1.add_url_rule('/desktop/education/<string:action>', view_func=EducationDesktopAPI.as_view('education_desktop'),
                    methods=["POST"])
api_v1.add_url_rule('/desktop/personal/<string:action>', view_func=PersonalDesktopAPI.as_view('personal_desktop'),
                    methods=["POST"])
api_v1.add_url_rule('/instance/<string:action>', view_func=InstanceAPI.as_view('instance'), methods=["POST"])
