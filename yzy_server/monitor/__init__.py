import time
import threading
from . import base_monitor


def start_monitor_thread():
    """启动所有监控线程"""
    # 使用timer，是为了保证gunicorn的workers进程不会复制未完成的线程
    task = threading.Timer(10, base_monitor.start_monitor)
    task.start()


def stop_monitor_thread(wait=60):
    base_monitor.stop_monitor()
    if wait > 0:
        time.sleep(wait)
