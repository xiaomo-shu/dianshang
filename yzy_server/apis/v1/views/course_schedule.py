"""
排课管理
"""
import logging
from flask.views import MethodView
from flask import request, jsonify
from common.utils import time_logger, build_result
from yzy_server.utils import abort_error
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.course_schedule_ctl import TermController, CourseScheduleController


logger = logging.getLogger(__name__)


class TermAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "create":
                result = TermController().create(data)

            elif action == "update":
                result = TermController().update(data)

            elif action == "delete":
                result = TermController().delete(data)

            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.error("course_schedule action %s failed:%s", action, e)
            return build_result("OtherError")


class CourseScheduleAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()

            if action == "update":
                result = CourseScheduleController().update(data)

            elif action == "delete":
                result = CourseScheduleController().delete(data)

            elif action == "apply":
                result = CourseScheduleController().apply(data)

            elif action == "enable":
                result = CourseScheduleController().enable(data)

            elif action == "disable":
                result = CourseScheduleController().disable(data)

            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("course_schedule action %s failed:%s", action, e)
            return build_result("OtherError")


api_v1.add_url_rule('/course_schedule/<string:action>', view_func=CourseScheduleAPI.as_view('course'), methods=["POST"])
api_v1.add_url_rule('/term/<string:action>', view_func=TermAPI.as_view('term'), methods=["POST"])