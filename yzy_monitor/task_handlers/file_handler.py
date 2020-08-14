import os
import traceback
from flask import current_app
import common.errcode as errcode
from yzy_monitor.task_handlers.base_handler import BaseHandler, BaseProcess


class FileHandler(BaseHandler):
    def __init__(self):
        super(FileHandler, self).__init__()
        self.type = "FileHandler"

    def deal(self, task):
        p = FileHandlerProcess(task)
        r = p.process()
        return r


class FileHandlerProcess(BaseProcess):
    def __init__(self, task):
        super(FileHandlerProcess, self).__init__(task)
        self.name = os.path.basename(__file__).split('.')[0]

    def delete_file(self):
        # check service status, if running ,then do not shutdown , must manually stop all service in service.conf
        # if all service not closed, then return msg???
        # send os shutdown command
        try:
            resp = errcode.get_error_result()
            file_name = self.task.get("data").get("file_name")
            current_app.logger.info('delete file: {}'.format(file_name))
            os.popen('rm -rf {}'.format(file_name))
            return resp
        except Exception as err:
            current_app.logger.error(err)
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp


