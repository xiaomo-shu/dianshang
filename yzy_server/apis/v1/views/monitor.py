import logging
from flask.views import MethodView
from flask import request
from common.utils import build_result, time_logger
from yzy_server.utils import abort_error
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.monitor_ctl import MonitorNodeController


logger = logging.getLogger(__name__)


class MonitorNodeAPI(MethodView):

    controller = MonitorNodeController()

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            ret = {}
            logger.debug(data)
            if action == "get_history_perf":
                """
                {
                    "node_uuid": "xxxxxxxxxxxxxxxxxxxxxxxx",
                    "statis_hours": 1,
                    "step_minutes": 0.5
                }
                """
                result = self.controller.get_history_perf(data)
                if result:
                    return result
            else:
                return abort_error(404)
            return build_result("Success", ret)
        except Exception as e:
            logger.error("monitor node action %s failed:%s", action, e, exc_info=True)
            return build_result("OtherError")


api_v1.add_url_rule('/monitor/node/<string:action>', view_func=MonitorNodeAPI.as_view('monitor_node'), methods=["POST"])
