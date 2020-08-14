import os
import logging
import traceback
from functools import wraps
import time
import json
from jsonschema import validate
import common.errcode as errcode
from flask import current_app
from yzy_terminal.thrift_protocols.terminal import ConnectService
from yzy_terminal.redis_client import RedisClient
from yzy_terminal.thrift_protocols.terminal.ttypes import *
from common.constants import BASE_DIR


def timefn(fn):
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        logging.debug("@timefn:" + fn.__name__ + " took " + str(t2 - t1) + " seconds")
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
        self.rds = RedisClient()

    def process(self):
        command = self.task.get("command")
        if hasattr(self, str(command)):  # and self.check_json_msg():
            cmd = getattr(self, command)
            return cmd()
        else:
            resp = errcode.get_error_result(error="MessageError")
            return resp

    def show(self):
        logging.info(self.task.get("command"))
        return

    def mac_to_oprot(self, mac):
        if mac not in current_app.mac_token.keys():
            logging.warning("mac not in cache {}".format(current_app.mac_token.keys()))
            return False
        token_id = current_app.mac_token[mac]
        if token_id not in current_app.token_client.keys():
            logging.warning("token_id not in cache {}".format(current_app.token_client.keys()))
            return False
        else:
            return current_app.token_client[token_id]

    def send_thrift_cmd(self, mac, cmd):
        try:
            oprot = self.mac_to_oprot(mac)
            if not oprot:
                return False
            conn_client = ConnectService.Client(oprot)
            conn_client.Command(cmd)
            logging.debug("Send terminal: mac {}, cmd {}".format(mac, cmd))
            return True
        except Exception as err:
            print("exception {}".format(err))
            return False

    @timefn
    def check_json_msg(self):
        try:
            # schema_dir = os.getcwd() + '/json_schema/'
            schema_dir = os.path.join(BASE_DIR, 'terminal', 'json_schema/')
            schema_file = schema_dir + self.name + '_' + self.task.get("command") + '.schema'
            validate(instance=self.task, schema=json.load(open(schema_file, 'r')))
            return True
        except Exception as err:
            logging.error(err)
            return False
