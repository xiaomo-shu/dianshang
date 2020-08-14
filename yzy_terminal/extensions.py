import signal
import fcntl
import atexit
import time
import threading
import logging
import queue
from cachelib import SimpleCache
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
import yzy_terminal.thrift_services as thrift_services

db = SQLAlchemy()
cache = SimpleCache()
xx = 3


def start_thrift_server(app):
    f = open('thirft_server.lock', 'w+')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # start a timer to start thrift thread
        terminal_thread = threading.Timer(5, thrift_services.setup_and_start, args=[app])
        terminal_thread.start()
    except Exception as e:
        f.close()
        logging.error(e)
        return

    def exit_app_handler():
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()
    atexit.register(exit_app_handler)

