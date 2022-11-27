import logging
import requests
import inspect
import traceback
import os
import shutil
import tarfile
from functools import wraps
from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES
from yzy_server.database import apis as db_api
from yzy_upgrade.apis.v1.controllers import constants


logger = logging.getLogger(__name__)

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


def chunks(file_obj, offset=None, chunk_size=64 * 2 ** 10):
        """

        :param file_obj:
        :param offset:
        :param chunk_size:
        :return:
        """
        chunk_size = chunk_size
        try:
            file_obj.seek(offset)
        except:
            pass

        while True:
            data = file_obj.read(chunk_size)
            if not data:
                break
            yield data

def decompress_package(package_path):
    if os.path.exists(constants.UPGRADE_TMP_PATH):
        shutil.rmtree(constants.UPGRADE_TMP_PATH)

    os.makedirs(constants.UPGRADE_TMP_PATH)

    try:
        with tarfile.open(package_path, "r") as fd:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(fd, constants.UPGRADE_TMP_PATH)
        logger.info("Extract upgrade package to %s successful.", constants.UPGRADE_TMP_PATH)
        return True
    except Exception:
        logger.exception("Upgrade package format fail", exc_info=True)
        return False


# import socket
# try:
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     s.connect(('8.8.8.8', 80))
#     IP = s.getsockname()[0]
#     print(IP)
# finally:
#     s.close()
#
#
# def insert_rollback_task(params):
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             logger.info('++++++++++func.__name__:%s' % func.__name__)
#             rollback_func = getattr(Rollback, func.__name__, "")
#             if params.pop("use_origin_params", False):
#                 constants.ROLLBACK_TASK.append(
#                     {"ip": IP, "rollback_func": rollback_func, "args": [], "kwargs": kwargs})
#             else:
#                 constants.ROLLBACK_TASK.append(
#                     {"ip": IP, "rollback_func": rollback_func, "args": [], "kwargs": params})
#             logger.info('++++++++++ROLLBACK_TASK: %s' % constants.ROLLBACK_TASK)
#             return func(*args, **kwargs)
#         return wrapper
#     return decorator
#
#
# def run_rollback_tasks():
#     failed_func = list()
#     for task in constants.ROLLBACK_TASK:
#         ret = task["rollback_func"].__call__(*task['args'], **task['kwargs'])
#         if not ret:
#             logger.error("rollback_func: %s failed, args: %s, kwargs: %s" % (task["rollback_func"], task['args'], task['kwargs']))
#             failed_func.append(task["rollback_func"].__name__)
#         else:
#             logger.info("rollback_func: %s success" % task["rollback_func"])
#     if failed_func:
#         return get_error_result("RollbackServiceError", data={"failed_func": failed_func})
#     else:
#         return get_error_result()
#
#
# class Rollback(object):
#
#     @staticmethod
#     def stop_services(master=False):
#         try:
#             if master:
#                 logger.info("restart yzy-server")
#                 stdout, stderr = execute("systemctl", "restart", "yzy-server")
#                 if stderr:
#                     return False
#                 logger.info("restart yzy-web")
#                 stdout, stderr = execute("systemctl", "restart", "yzy-web")
#                 if stderr:
#                     return False
#                 logger.info("restart nginx")
#                 stdout, stderr = execute("systemctl", "restart", "nginx")
#                 if stderr:
#                     return False
#                 logger.info("restart yzy-terminal")
#                 stdout, stderr = execute("systemctl", "restart", "yzy-terminal")
#                 if stderr:
#                     return False
#                 # logger.info("restart yzy-terminal-agent")
#                 # stdout, stderr = execute("systemctl", "restart", "yzy-terminal-agent")
#                 # if stderr:
#                 #     return get_error_result("StartServiceError", service="yzy-terminal-agent")
#
#             logger.info("restart yzy-compute")
#             stdout, stderr = execute("systemctl", "restart", "yzy-compute")
#             if stderr:
#                 return False
#             logger.info("restart yzy-monitor")
#             stdout, stderr = execute("systemctl", "restart", "yzy-monitor")
#             if stderr:
#                 return False
#
#         except Exception as e:
#             logger.exception("rollback _stop_services failed: %s" % str(e), exc_info=True)
#             return False
#
#         return True
#
#     @staticmethod
#     def _backup_yzy_server():
#         # 清空备份目录
#         try:
#             if os.path.exists(constants.UPGRADE_BACKUP_PATH):
#                 shutil.rmtree(constants.UPGRADE_BACKUP_PATH, True)
#         except Exception as e:
#             logger.exception("rollback _backup_yzy_server failed: %s" % str(e), exc_info=True)
#             return False
#         return True
#
#     @staticmethod
#     def _copy_dir(source_path, dest_path):
#         try:
#             for name in os.listdir(source_path):
#                 file_path = os.path.join(source_path, name)
#                 if name in ['yzy_upgrade']:
#                     continue
#                 if os.path.isdir(file_path):
#                     logger.info("copy %s to %s", file_path, os.path.join(dest_path, name))
#                     shutil.copytree(file_path, os.path.join(dest_path, name))
#                 else:
#                     logger.info("copy %s to %s", file_path, os.path.join(dest_path, name))
#                     shutil.copy2(file_path, os.path.join(dest_path, name))
#         except Exception as e:
#             logger.exception("rollback _copy_dir failed: %s" % str(e), exc_info=True)
#             return False
#         return True
