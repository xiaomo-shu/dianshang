import requests
import inspect
import traceback
from functools import wraps
from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES
from yzy_terminal_agent.database import api as db_api
from common.utils import create_uuid

BEGIN = 'begin'
END = 'end'
RUNNING = 'running'
ERROR = 'error'


def abort_error(code, message=None, **kwargs):
    if message is None:
        message = HTTP_STATUS_CODES.get(code, '')

    response = jsonify(code=code, msg=message, data={}, **kwargs)
    response.status_code = code
    return response


def insert_operation_log(msg, result, log_user=None):
    if log_user is None:
        uid = None
        uname = "admin"
        user_ip = ''
    else:
        uid = log_user["id"]
        uname = log_user["user_name"]
        user_ip = log_user["user_ip"]
    values = {
        "content": msg,
        "result": result,
        "user_id": uid,
        "user_name": uname,
        "user_ip": user_ip
    }
    db_api.add_operation_log(values)


def operation_record(msg=""):
    """
    记录操作日志
    :param msg: 操作日志内容，如果操作日志中包含参数，则使用{参数名}格式的字符串，例如：
            添加资源池{pool_name}，pool_name是函数中的某个参数，如果pool_name包含在字典
            中，则是{pool[pool_name]}这种格式
    :return:
    """
    def wrapper1(func):
        @wraps(func)
        def wrapper2(*args, **kwargs):
            arg_dict = inspect.getcallargs(func, *args, **kwargs)
            ex = None
            ret = None
            result = 'OK'
            try:
                ret = func(*args, **kwargs)
                data = ret.get_json()
                if not data.get('code') == 0:
                    result = data.get('msg', 'unknown error')
            except Exception as ex:
                result = str(ex)
                traceback.print_exc()
            if msg == "":
                logmsg = "Call {} {}".format(func.__name__, result)
            else:
                logmsg = msg.format(**arg_dict)
            user = arg_dict.get('log_user', None)
            try:
                insert_operation_log(logmsg, result, user)
            except:
                pass

            if ex is not None:
                raise ex
            return ret
        return wrapper2
    return wrapper1


class HttpClient:
    def __init__(self, app=None):
        self.app = app
        self.command_data = {}
        self.data = {}
        self.json_data = {}

    def set_command(self, command, handler, data):
        if not isinstance(data, dict):
            raise Exception("the data is not dict")

        _d = {
            "command": command,
            "handler": handler,
            "data": data
        }
        self.command_data = _d

    def set_data(self, data):
        if not isinstance(data, dict):
            raise Exception("the data is not dict")
        self.data = data

    def set_json(self, data):
        if not isinstance(data, dict):
            raise Exception("the data is not dict")
        self.json_data = data

    def compute_post(self):
        url = self.app.config[""]
        response = requests.post()


class TaskBase(object):

    def add_task(self, task_id, status, context, progress=0, image_id=None, host_uuid=None, version=0):
        values = {
            'task_id': task_id,
            'status': status,
            'context': context,
            'progress': progress,
            'image_id': image_id if image_id else '',
            'host_uuid': host_uuid,
            'version': version
        }
        step = db_api.get_task_step(task_id)
        values['step'] = step + 1
        if status == BEGIN or status == RUNNING:
            values['progress'] = values['step'] * 4 if values['step'] * 4 else 98
            if values['progress'] >= 100:
                values['progress'] = 99
        elif status == ERROR:
            values['progress'] = values['step'] * 4
            if values['progress'] >= 100:
                values['progress'] = 99
        else:
            values['progress'] = 100
        db_api.add_task_info(values)


class Task(TaskBase):
    def __init__(self, image_id="", host_uuid='', version=0):
        super(Task, self).__init__()
        self.image_id = image_id
        self.host_uuid = host_uuid
        self.version = version

    def _format_context(self, context, *args):
        try:
            message = context % args
        except (ValueError, TypeError):
            message = context.format(*args)
        return message

    def begin(self, task_id, context, *args):
        context = self._format_context(context, *args)
        self.add_task(task_id, BEGIN, context, image_id=self.image_id, host_uuid=self.host_uuid, version=self.version)

    def next(self, task_id, context, *args):
        context = self._format_context(context, *args)
        self.add_task(task_id, RUNNING, context, image_id=self.image_id, host_uuid=self.host_uuid, version=self.version)

    def end(self, task_id, context, *args):
        context = self._format_context(context, *args)
        self.add_task(task_id, END, context, image_id=self.image_id, host_uuid=self.host_uuid, version=self.version)

    def error(self, task_id, context, *args):
        context = self._format_context(context, *args)
        self.add_task(task_id, ERROR, context, image_id=self.image_id, host_uuid=self.host_uuid, version=self.version)


