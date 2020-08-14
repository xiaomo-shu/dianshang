import os
import traceback
from flask import current_app
import common.errcode as errcode
from yzy_monitor.task_handlers.base_handler import BaseHandler, BaseProcess


class OsHandler(BaseHandler):
    def __init__(self):
        super(OsHandler, self).__init__()
        self.type = "OsHandler"

    def deal(self, task):
        p = OsHandlerProcess(task)
        r = p.process()
        return r


class OsHandlerProcess(BaseProcess):
    def __init__(self, task):
        super(OsHandlerProcess, self).__init__(task)
        self.name = os.path.basename(__file__).split('.')[0]

    def shutdown(self):
        # check service status, if running ,then do not shutdown , must manually stop all service in service.conf
        # if all service not closed, then return msg???
        # send os shutdown command
        try:
            resp = errcode.get_error_result()
            current_app.logger.debug('now shutdown...')
            os.popen('shutdown now')
            return resp
        except Exception as err:
            current_app.logger.error(err)
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    def reboot(self):
        # stop all service in service.conf
        # send os reboot command
        try:
            resp = errcode.get_error_result()
            current_app.logger.debug('now reboot...')
            os.popen('reboot')
            return resp
        except Exception as err:
            current_app.logger.error(err)
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

