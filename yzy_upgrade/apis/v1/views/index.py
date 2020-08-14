import logging
import traceback
from flask.views import MethodView
from flask import jsonify, request
from common.utils import time_logger, build_result
from yzy_upgrade.utils import abort_error
from yzy_upgrade.apis.v1 import api_v1
from yzy_upgrade.apis.v1.controllers.index_control import IndexController
from yzy_upgrade.apis.v1.controllers.self_upgrade import start_self_upgrade, upgrade_cluster


logger = logging.getLogger(__name__)


class IndexAPI(MethodView):
    def __init__(self):
        self.index_controller = IndexController()

    @time_logger
    def get(self, action):
        try:
            data = request.args
            logger.debug("action: {}, data: {}".format(action, data))

            if action == "check":
                result = self.index_controller.check()
            elif action == "download":
                return self.index_controller.download_package(data)
            elif action == "get_self_upgrade_status":
                return self.index_controller.get_self_upgrade_status()
            else:
                return abort_error(404)

            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")

        except Exception as e:
            logger.error("index action %s failed:%s", action, e)
            logger.error("".join(traceback.format_exc()))
            return build_result("OtherError")

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            logger.debug("action: {}, data: {}".format(action, data))

            if action == "upload_and_publish":
                data = request.files.get("file", None)
                result = self.index_controller.upload_and_publish(data)
            elif action == "sync":
                result = self.index_controller.sync(data)
            elif action == "start_upgrade":
                result = self.index_controller.start_upgrade()
            elif action == "stop_slave_services":
                result = self.index_controller.stop_slave_services()
            elif action == "rollback_slave_services":
                result = self.index_controller.rollback_slave_services()
            elif action == "upgrade_slave":
                result = self.index_controller.upgrade_slave()
            elif action == "rollback_slave_upgrade":
                result = self.index_controller.rollback_slave_upgrade()
            elif action == "cluster_self_upgrade":
                result = upgrade_cluster()
            elif action == "self_upgrade":
                result = start_self_upgrade()
            elif action == "get_self_upgrade_status":
                result = self.index_controller.get_self_upgrade_status()
            else:
                return abort_error(404)

            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")

        except Exception as e:
            logger.exception("index action %s failed:%s", action, e)
            return build_result("OtherError")


api_v1.add_url_rule("/index/<string:action>", view_func=IndexAPI.as_view("index"), methods=["GET", "POST"])
