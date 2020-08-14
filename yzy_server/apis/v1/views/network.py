import logging
from flask.views import MethodView
from flask import jsonify, request, current_app
from common.utils import build_result, time_logger
from yzy_server.utils import abort_error
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.network_ctl import NetworkController, VirtualSwitchController


logger = logging.getLogger(__name__)


class NetworkAPI(MethodView):

    def get(self, action):
        if action == "list":
            return NetworkController().get_network_list()

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            ret = {}
            # if action == "init":
            #     return NetworkController().init_network(data)

            if action == "create":
                return NetworkController().create_network(data)

            elif action == "delete":
                network_uuid = data.get("uuid", "")
                return NetworkController().delete_network(network_uuid)

            elif action == "list":
                return NetworkController().get_network_list()

            elif action == "update":
                if not data:
                    return build_result("ParamError")
                return NetworkController().update_network(data)

            return build_result("Success", ret)
        except Exception as e:
            logger.error("network action %s failed:%s", action, e)
            return build_result("OtherError")


class SubnetAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            ret = {}
            if action == "create":
                if not data:
                    return build_result("ParamError")
                return NetworkController().create_subnet(data)

            elif action == "delete":
                subnet_uuids = data.get("uuids", "")
                return NetworkController().delete_subnet(subnet_uuids)

            elif action == "update":
                return NetworkController().update_subnet(data)

            elif action == "list":
                if not data:
                    return build_result("ParamError")
                network_uuid = data.get("network_uuid", "")
                return NetworkController().get_subnets_of_network(network_uuid)
            return build_result("Success", ret)
        except Exception as e:
            logger.error("subnet action %s failed:%s", action, e)
            return build_result("OtherError")


class VirtualSwitchAPI(MethodView):

    def get(self, action):
        if action == "list":
            return VirtualSwitchController().get_vswitch_list()

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "create":
                return VirtualSwitchController().create_virtual_switch(data)

            elif action == "delete":
                vswitch_uuid = data.get("uuid", "")
                return VirtualSwitchController().delete_virtual_switch(vswitch_uuid)

            elif action == "update":
                return VirtualSwitchController().update_virtual_switchs(data)

            elif action == "update_map":
                return VirtualSwitchController().update_virtual_switch(data)

            elif action == "info":
                if not data:
                    return build_result("ParamError")
                vswitch_uuid = data.get("uuid", "")
                return VirtualSwitchController().virtual_switch_info(vswitch_uuid)

            else:
                return abort_error(404)
        except Exception as e:
            print(e)
            logger.error("vswitch action %s failed:%s", action, e)
            return build_result("OtherError")


api_v1.add_url_rule('/network/<string:action>', view_func=NetworkAPI.as_view('network'), methods=["GET", "POST"])
api_v1.add_url_rule('/subnet/<string:action>', view_func=SubnetAPI.as_view('subnet'), methods=["POST"])
api_v1.add_url_rule('/vswitch/<string:action>', view_func=VirtualSwitchAPI.as_view('vswitch'),
                    methods=["GET", "POST"])
