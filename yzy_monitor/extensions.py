import signal
import fcntl
import atexit
import time
import threading
import queue
from cachelib import SimpleCache
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from yzy_monitor.log import logger
import yzy_monitor.timer_tasks as timer_tasks


db = SQLAlchemy()
cache = SimpleCache()


def init_timer(msq, app):
    # start timer to monitor
    f = open('monitor_time.lock', 'w+')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        tasks = timer_tasks.setup_and_start(app)
        for task in tasks:
            task.start()
        # start a timer to loop recv ipc queue msq to control timer thread
        queue_monitor = threading.Timer(5, monitor_timer, [msq, tasks])
        queue_monitor.start()
    except Exception as e:
        f.close()
        # current_app.logger.error(e)
        return

    def exit_app_handler():
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()
        # free ipc queue
        timer_queue = current_app.timer_msq
        timer_queue.close()
        timer_queue.unlink()
    atexit.register(exit_app_handler)


def monitor_timer(msq, handlers):
    # default pause timer handlers
    for timer in handlers:
        exec_func = getattr(timer, "pause")
        if timer.name == "statistic":
            continue
        logger.debug('timer = {}'.format(timer.name)) 
        exec_func()
    while True:
        # 1. get queue msg ['pause', 'resume', 'update']
        try:
            cmd_msg = msq.get(block=False)
            for timer in handlers:
                exec_func = getattr(timer, cmd_msg)
                exec_func()
                logger.info('monitor_timer exec: {}'.format(cmd_msg))
        except Exception as err:
            if type(err) is queue.Empty:
                #logger.debug('timer_queue no msq, go to sleep 5 seconds...')
                pass
            else:
                logger.error('monitor_timer error: {}'.format(err))
        # 2. exec thread process
        time.sleep(5)

