import logging
import traceback

from flask.views import MethodView
from flask import jsonify, request

from common.utils import build_result, time_logger
from yzy_compute.exception import BaseException
from yzy_compute.apis.v1 import api_v1
from yzy_compute.apis.v1.controllers.index_control import deal_task


class IndexAPI(MethodView):
    """
    the data format like below:
        {
            "command": "start",
            "handler": "InstanceHandler",
            "data": {
                ...
            }
        }
    """

    def get(self):
        try:
            data = request.get_json()
            deal_task(data)
            ret = {
                "api_version": "1.0"
            }
            return build_result('Success', ret)
        except Exception as e:
            logging.error("get failed, msg:" + traceback.format_exc())
            if isinstance(e, BaseException):
                result = {
                    "code": e.code,
                    "msg": e.message,
                    "en_msg": e.__class__.__name__
                }
                return jsonify(result)
            else:
                return build_result("OtherError", str(e))

    @time_logger
    def post(self):
        try:
            data = request.get_json()
            result = deal_task(data)
            if result and isinstance(result, dict) and 'code' in result:
                return jsonify(result)
            return build_result('Success', result)
        except Exception as e:
            logging.error("post failed,  msg:" + traceback.format_exc())
            if isinstance(e, BaseException):
                result = {
                    "code": e.code,
                    "msg": e.message,
                    "en_msg": e.__class__.__name__
                }
                return jsonify(result)
            else:
                return build_result("OtherError", str(e))


api_v1.add_url_rule('/', view_func=IndexAPI.as_view('index'), methods=['GET', "POST"])

