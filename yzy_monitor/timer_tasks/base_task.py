import threading
from functools import wraps
import time
from yzy_monitor.http_client import *
import os
import sys
import configparser
import traceback
from yzy_monitor.log import logger
from common.constants import BASE_DIR


def timefn(fn):
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        logger.debug("@timefn:" + fn.__name__ + " took " + str(t2 - t1) + " seconds")
        return result
    return measure_time


class BaseTask(threading.Thread):
    def __init__(self, interval=20):
        threading.Thread.__init__(self)
        self.__running = threading.Event()
        self.__running.set()
        self.__pausing = threading.Event()
        self.__pausing.set()
        self.interval = interval
        self.node_uuid = ""
        self.server_url = self.get_config()

    def get_config(self):
        try:
            # get server url
            server_url = None
            # work_dir = os.getcwd()
            work_dir = os.path.join(BASE_DIR, 'config')
            conf = configparser.ConfigParser()
            conf.read('{}/monitor_server.ini'.format(work_dir))
            if conf.has_option('CONTROLLER', 'addr') and conf.has_option('CONTROLLER', 'node_uuid'):
                server_url = conf.get('CONTROLLER', 'addr')
                self.node_uuid = conf.get('CONTROLLER', 'node_uuid')
            return server_url
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            return None

    def run(self):
        if self.server_url:
            while self.__running.is_set():
                self.__pausing.wait()
                self.process()
                time.sleep(self.interval)

    def pause(self):
        self.__pausing.clear()

    def resume(self):
        self.__pausing.set()

    def update(self):
        self.pause()
        self.server_url = self.get_config()
        logger.info('update url: {}'.format(self.server_url))
        self.resume()

    # add error resent
    def request(self, **kwargs):
        http_client = HttpClient()
        resp = None
        body = None
        try:
            resp, body = http_client.post(url=self.server_url, **kwargs)
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
        return resp, body

    @timefn
    def process(self):
        """\
        This is the mainloop of a worker process. You should override
        this method in a subclass to provide the intended behaviour
        for your particular evil schemes.
        """
        raise NotImplementedError()


"""\
    def stop(self):
        self.__pausing.set()
        self.__running.clear()
"""
