import json
import logging
from flask.views import MethodView
from flask import jsonify, request, current_app
from common.utils import build_result, time_logger
from yzy_terminal_agent.ext_libs.redis_pub_sub import RedisMessageCenter
from yzy_terminal_agent.apis.v1 import api_v1
from yzy_terminal_agent.apis.v1.controllers.terminal_ctl import TerminalTaskHandler
from yzy_terminal_agent.apis.v1.controllers.web_control import WebTaskHandler


class IndexAPI(MethodView):

    def get(self):
        # data = request.get_json()
        # deal_task(data)
        return jsonify({
            "api_version": "1.0"
        })

    @time_logger
    def post(self):
        data = request.get_json()
        logging.debug(data)
        # deal_task(data)
        msg_center = RedisMessageCenter()
        try:
            msg = json.dumps(data)
            msg_center.public(msg)
        except Exception as e:
            print(e)
        # insert redis for 24 hours
        ret = {
            "api_version": "1.0"
        }
        return build_result("Success", ret)


class WebTaskView(MethodView):

    def get(self):
        pass

    def post(self):
        data = request.get_json()
        ret = WebTaskHandler().deal_process(data)
        return ret


class TerminalTaskView(MethodView):

    def get(self):
        pass

    def post(self):
        data = request.get_json()
        ret = TerminalTaskHandler().deal_process(data)
        return ret


api_v1.add_url_rule('/voi/terminal/command/', view_func=WebTaskView.as_view('web_task'), methods=['GET', "POST"])
api_v1.add_url_rule('/voi/terminal/task/', view_func=TerminalTaskView.as_view('terminal_task'), methods=['GET', "POST"])
