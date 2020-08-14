import threading
from functools import wraps
import time
from yzy_terminal_agent.http_client import *
import os
import sys
import configparser
import traceback
from common.constants import BASE_DIR


class BaseTask(threading.Thread):
    def __init__(self, interval=20):
        threading.Thread.__init__(self)
        self.__running = threading.Event()
        self.__running.set()
        self.__pausing = threading.Event()
        self.__pausing.set()
        self.interval = interval

    def run(self):
        while self.__running.is_set():
            self.__pausing.wait()
            self.process()
            for i in range(self.interval):
                time.sleep(1)

    def pause(self):
        self.__pausing.clear()

    def resume(self):
        self.__pausing.set()


    # @timefn
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
