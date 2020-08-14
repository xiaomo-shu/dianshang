from flask import current_app
# from yzy_server.database.api import list_ImageTemparyInstance
import threading
import traceback
import time


class AsyncCleanTask(threading.Thread):

    def __init__(self, app):
        threading.Thread.__init__(self)
        self.app = app

    def _cleanTempVm(self):
        pass

    def run(self):
        with self.app.app_context():
            while True:
                try:
                    print("async start")
                    self._cleanTempVm()
                    # self.resetImageState()
                    # self.checkComputeNodeState()
                    # LOG.info('end clean')
                except Exception as e:
                    current_app.logger.error("AsyncCleanTaskHandler error:%s" % traceback.format_exc())
                time.sleep(30)
