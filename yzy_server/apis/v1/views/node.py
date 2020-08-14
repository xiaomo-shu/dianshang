import logging
from flask.views import MethodView
from flask import request
from common.utils import build_result, time_logger
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.node_ctl import NodeController


logger = logging.getLogger(__name__)


class ControllerAPI(MethodView):

    node = NodeController()

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            ret = {}
            if action == "init":
                """
                {
                    "ip": "172.16.1.15",
                    "password": "123",
                    "manage_interface": "eth0",
                    "image_interface": "eth1",
                    "data_interface": "eth1",
                    "network_name": "default",
                    "switch_name": "default",
                    "switch_type": "vlan",
                    "vlan_id": 10,
                    "storages": {
                        "/opt/slow": "1,2,3,4"
                    },
                    "is_compute": false
                }
                """
                result = self.node.init_controller_node(data)
                if result:
                    return result
            # elif action == "init_compute":
            #     """
            #     {
            #         "ip": "172.16.1.49",
            #         "hostname": "host1"
            #     }
            #     """
            #     result = self.node.init_controller_to_compute(data)
            #     if result:
            #         return result
            elif action == "list":
                result = self.node.get_controller_list()
                if result:
                    return result
            return build_result("Success", ret)
        except Exception as e:
            logger.error("contorller action %s failed:%s", action, e, exc_info=True)
            return build_result("OtherError")


class NodeAPI(MethodView):

    node = NodeController()

    @time_logger
    def get(self, action):
        if action == "ha_sync":
            path = request.args.get('path', '')
            logger.info("the sync path:%s", path)
            return self.node.ha_sync(path)

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            ret = {}
            logger.debug(data)
            if action == "add":
                """
                {
                    "password": "123",
                    "ip": "172.16.1.11",
                    "network": [
                        {
                            "switch_uuid": "ec796fde-4885-11ea-8e15-000c295dd728",
                            "interface": "eth0"
                        },
                        {
                            "switch_uuid": "ec796fde-4885-11ea-8e15-000c295dd728",
                            "interface": "eth0"
                        }
                    ],
                    "manage_interface": "ens192",
                    "image_interface": "ens192"
                }
                """
                result = self.node.add_node(data)
                if result:
                    return result
            elif action == "check":
                """
                检测节点是否支持虚拟化，返回节点的基本信息，记录数据库
                {
                    "ip": "172.16.1.49",
                    "root_pwd": "123",
                    "check": False
                }
                """
                result = self.node.check_support(data)
                if result:
                    return result
            elif action == "check_password":
                result = self.node.check_password(data)
                if result:
                    return result
            elif action == "delete":
                node_uuid = data.get("uuid", "")
                return self.node.delete_node(node_uuid)
            elif action == "shutdown":
                node_uuid = data.get("uuid", "")
                timeout = data.get("timeout")
                return self.node.shutdown_node(node_uuid, timeout)
            elif action == "reboot":
                node_uuid = data.get("uuid", "")
                return self.node.reboot_node(node_uuid)
            elif action == "update":
                uuid = data.get("uuid", "")
                type = data.get("type", None)
                name = data.get("name", None)
                status = data.get("status", None)
                pool_uuid = data.get("pool_uuid", None)
                return self.node.update_node(uuid, type, status, name, pool_uuid)
            elif action == "ping":
                ip = data.get("ip", None)
                return self.node.ping_node(ip)
            elif action == "check_image_ip":
                ip = data.get("ip", None)
                master_image_nic = data.get("master_image_nic", None)
                master_image_ip = data.get("master_image_ip", None)
                return self.node.check_image_ip(ip, master_image_nic,master_image_ip)
            elif action == "update_info":
                return self.node.update_info(data)
            elif action == "restart_service":
                node_uuid = data.get("node_uuid", "")
                service_name = data.get("service_name", "")
                return self.node.restart_service(node_uuid, service_name)
            elif action == "start_service":
                node_uuid = data.get("node_uuid", "")
                service_name = data.get("service_name", "")
                return self.node.start_service(node_uuid, service_name)
            elif action == "stop_service":
                node_uuid = data.get("node_uuid", "")
                service_name = data.get("service_name", "")
                return self.node.stop_service(node_uuid, service_name)
            elif action == "mn_map_update":
                return self.node.mn_map_update_node(data)
            elif action == "in_map_update":
                return self.node.in_map_update_node(data)
            elif action == "add_ip":
                """
                添加网卡ip
                {
                    "node_uuid": "xxxxxxxxxxx",
                    "node_name": "name",
                    "nic_uuid": "xxxxxx",
                    "nic_name": "eth name1",
                    "ip": "xxxx",
                    "netmask": "xxxxxx",
                    "gateway": "xxxxxx",
                    "dns1": "xxxx",
                    "dns2": "xxxx"
                }
                """
                return self.node.add_ip_node(data)
            elif action == "update_ip":
                """
                更新网卡ip
                {
                    "uuid": "xxxx-xxxxxxxxxxxxx-xxxxxx",
                    "nic_uuid": "",
                    "nic_name": "",
                    "node_ip": "",
                    "ip": "",
                    "netmask": ""
                }
                """
                return self.node.update_ip_node(data)
            elif action == "update_gate_info":
                """
                更新网卡ip
                {
                    "nic_uuid": "xxx",
                    "nic_name": "xxx",
                    "node_ip": "xxx",
                    "gateway": "xxxxxx",
                    "dns1": "xxxx",
                    "dns2": "xxxx"
                }
                """
                return self.node.update_gate_info(data)
            elif action == "delete_ip":
                """
                删除网卡ip
                {
                    "uuid": "xxxx-xxxxxxxxxxxxx-xxxxxx",
                    "nic_uuid": "",
                    "node_ip": ""
                }
                """
                return self.node.delete_ip_node(data)
            #
            # elif action == "info_report":
            #     if not data:
            #         return build_result("ParamError")
            #
            #     ip = data.get("ip", "")
            #     hostname = data.get("hostname", "")
            #     _data = data.get("data", {})
            #     if not (ip and hostname):
            #         logger.error("node report info not ip and hostname")
            #         return build_result("ParamError")
            #     # 记录上报信息
            #     update_node_report_info(ip, hostname, _data)
            #     return build_result("Success")
            elif action == "monitor_update":
                """ 节点的监控信息更新 """
                return self.node.update_node_monitor(data)
            elif action == "add_bond":
                """添加网卡bond"""
                return self.node.add_bond(data)
            elif action == "edit_bond":
                """添加网卡bond"""
                return self.node.edit_bond(data)
            elif action == "unbond":
                """删除网卡bond"""
                return self.node.unbond(data)
            elif action == "master":
                """
                    {
                        "master_ip": "172.16.1.25"
                    }
                """
                return self.node.change_master(data)

            return build_result("Success", ret)
        except Exception as e:
            logger.error("node action %s failed:%s", action, e, exc_info=True)
            return build_result("OtherError")


api_v1.add_url_rule('/controller/<string:action>', view_func=ControllerAPI.as_view('controller'), methods=["POST"])
api_v1.add_url_rule('/node/<string:action>', view_func=NodeAPI.as_view('node'), methods=["POST", "GET"])
