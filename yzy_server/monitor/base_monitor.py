"""
Author:      zhurong
Email:       zhurong@yzy-yf.com
Created:     2020/4/14
基础监控线程，从这里启动各个监控任务，具体的任务则在其他模块定义
"""
import time
import threading
import logging
import ctypes

from . import instance_monitor
from . import node_monitor
from . import performance_monitor
from . import task_info_monitor


logger = logging.getLogger(__name__)


class BaseMonitor(threading.Thread):

    def __init__(self, func, interval=60):
        threading.Thread.__init__(self)
        self.thread_stop = False
        self.daemon = True
        self.func = func
        self.interval = interval

    def run(self):
        # 获取线程id
        tid = ctypes.CDLL('libc.so.6').syscall(186)
        logger.info('monitor task start %s, thread_pid:%d', self.func.__name__, tid)
        while not self.thread_stop:
            try:
                logger.info('monitor task execute %s', self.func.__name__)
                self.func()
            except Exception as e:
                logger.error('monitor task run %s:%s', self.func.__name__, e, exc_info=True)

            time.sleep(self.interval)
            logger.debug('monitor status running')
        logger.info('monitor status stop:%s', self.func.__name__)

    def stop(self):
        self.thread_stop = True

    def start_thread(self):
        self.thread_stop = False


all_monitor_task = list()


def start_monitor():
    try:
        all_monitor_task.append(BaseMonitor(instance_monitor.update_instance_info, 8))
        all_monitor_task.append(BaseMonitor(instance_monitor.update_template_info, 20))
        all_monitor_task.append(BaseMonitor(instance_monitor.update_template_disk_usage, 300))
        all_monitor_task.append(BaseMonitor(node_monitor.update_node_status, 30))
        all_monitor_task.append(BaseMonitor(node_monitor.ha_sync_task, 60))
        all_monitor_task.append(BaseMonitor(performance_monitor.update_node_performance, 30))
        all_monitor_task.append(BaseMonitor(performance_monitor.clear_performance_data, 60*60))
        all_monitor_task.append(BaseMonitor(task_info_monitor.update_task_info_status, 60*60*24))
        for task in all_monitor_task:
            task.start()
    except Exception as ex:
        logging.info('monitor start_monitor error %s', str(ex))


def stop_monitor(normal=True):
    try:
        if normal:
            for task in all_monitor_task:
                task.stop()
            del all_monitor_task[:]
    except Exception as ex:
        logging.info('monitor stop_monitor error %s', str(ex))
