
import logging
import traceback
from flask.views import MethodView
from yzy_server.utils import abort_error
from flask import jsonify, request, current_app
from common.utils import build_result, time_logger
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.index_control import IndexController


logger = logging.getLogger(__name__)


class IndexAPI(MethodView):
    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            logger.debug("action: {}, data: {}".format(action, data))
            if action == "get_top_data":
                statis_period = data.get("statis_period", None)
                if statis_period:
                    result = IndexController().get_top_data(statis_period)
                    return result
            else:
                result = abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.error("index action %s failed:%s", action, e)
            logger.error(''.join(traceback.format_exc()))
            return build_result("OtherError")


api_v1.add_url_rule('/index/<string:action>', view_func=IndexAPI.as_view('index'), methods=["POST"])
