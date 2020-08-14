import os
import traceback
from functools import wraps
import time
import json
from jsonschema import validate
import common.errcode as errcode
from flask import current_app
from common.constants import BASE_DIR


def timefn(fn):
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        current_app.logger.debug("@timefn:" + fn.__name__ + " took " + str(t2 - t1) + " seconds")
        return result
    return measure_time


class BaseHandler(object):
    def __init__(self):
        self.type = "BaseHandler"

    def deal(self, task):
        """\
        This is the main deal object. You should override
        this method in a subclass to provide the intended behaviour
        for your particular evil schemes.
        """
        raise NotImplementedError()


class BaseProcess(object):
    def __init__(self, task):
        self.task = task
        self.name = None

    def process(self):
        command = self.task.get("command")
        #if hasattr(self, str(command)) and self.check_json_msg():
        if hasattr(self, str(command)):
            cmd = getattr(self, command)
            return cmd()
        else:
            resp = errcode.get_error_result(error="MessageError")
            return resp

    def show(self):
        current_app.logger.info(self.task.get("command"))
        return

    @timefn
    def check_json_msg(self):
        try:
            # schema_dir = os.getcwd() + '/json_schema/'
            schema_dir = os.path.join(BASE_DIR, 'yzy_monitor', 'json_schema/')
            schema_file = schema_dir + self.name + '_' + self.task.get("command") + '.schema'
            validate(instance=self.task, schema=json.load(open(schema_file, 'r')))
            return True
        except Exception as err:
            current_app.logger.error(err)
            return False
