import os
import sys
import configparser
import traceback
from flask import current_app
import common.errcode as errcode
from flask import current_app
from yzy_monitor.task_handlers.base_handler import BaseHandler, BaseProcess
from common.constants import BASE_DIR


class TimerHandler(BaseHandler):
    def __init__(self):
        super(TimerHandler, self).__init__()
        self.type = "TimerHandler"

    def deal(self, task):
        p = TimerHandlerProcess(task)
        r = p.process()
        return r


class TimerHandlerProcess(BaseProcess):
    def __init__(self, task):
        super(TimerHandlerProcess, self).__init__(task)
        self.name = os.path.basename(__file__).split('.')[0]

    def update(self):
        try:
            resp = errcode.get_error_result()
            addr = self.task.get("data").get('addr')
            node_uuid = self.task.get("data").get('node_uuid')
            current_app.logger.debug('Get addr: {}'.format(addr))
            # work_dir = os.getcwd()
            work_dir = os.path.join(BASE_DIR, 'config')
            conf = configparser.ConfigParser()
            conf.read('{}/monitor_server.ini'.format(work_dir))
            if conf.has_option('CONTROLLER', 'addr') and conf.has_option('CONTROLLER', 'node_uuid'):
                conf.set('CONTROLLER', 'addr', addr)
                conf.set('CONTROLLER', 'node_uuid', node_uuid)
                conf.write(open('{}/monitor_server.ini'.format(work_dir), 'w+'))
            else:
                current_app.logger.error('Config file monitor_server.ini error: no addr or node_uuid')
                resp = errcode.get_error_result(error="OtherError")
            # send command to ipc queue
            current_app.timer_msq.put(sys._getframe(0).f_code.co_name, block=False)
            return resp
        except Exception as err:
            current_app.logger.error(err)
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    def pause(self):
        try:
            resp = errcode.get_error_result()
            # send command to ipc queue
            current_app.timer_msq.put(sys._getframe(0).f_code.co_name, block=False)
            return resp
        except Exception as err:
            current_app.logger.error(err)
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    def resume(self):
        try:
            resp = errcode.get_error_result()
            # send command to ipc queue
            current_app.timer_msq.put(sys._getframe(0).f_code.co_name, block=False)
            return resp
        except Exception as err:
            current_app.logger.error(err)
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp
