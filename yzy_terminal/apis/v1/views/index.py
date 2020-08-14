import logging
from flask.views import MethodView
from flask import jsonify, request, current_app
from common.utils import build_result, time_logger
from yzy_terminal.apis.v1 import api_v1
from yzy_terminal.apis.v1.controllers.index_control import create_md5_token, deal_task


class IndexAPI(MethodView):
    def get(self):
        data = request.get_json()
        deal_task(data)
        return jsonify({
            "api_version": "1.0"
        })

    @time_logger
    def post(self):
        data = request.get_json()
        logging.debug('request msg: \n{}'.format(data))
        resp = deal_task(data)
        logging.debug('response msg: \n{}'.format(resp))
        return jsonify(resp)


api_v1.add_url_rule('/terminal/task', view_func=IndexAPI.as_view('task'), methods=['GET', "POST"])
