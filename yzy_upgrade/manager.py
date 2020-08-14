# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()

import os, sys
project_dir = os.path.abspath("..")

# print(project_dir)
sys.path.insert(0, project_dir)

from gevent import pywsgi
from multiprocessing import cpu_count, Process
import logging.handlers
from abc import ABC
from flask_script import Manager
# from gunicorn.six import iteritems
from multiprocessing import cpu_count
from common import constants
from common import load_log_config
load_log_config('yzy_upgrade')
from yzy_upgrade import create_app

try:
    app = create_app("pro")
except Exception as e:
    print(e)
    exit(1)

manager = Manager(app)


@manager.command
def run():
    """
    生产模式启动命令函数
    To use: python manager.py run
    """
    from gunicorn.app.base import BaseApplication

    class serverApplication(BaseApplication, ABC):
        """
        gunicorn服务器启动类
        """

        def __init__(self, application, options):
            self.application = application
            self.options = options or {}
            super(serverApplication, self).__init__()

        def load_config(self):
            config = dict([(key, value) for key, value in self.options.items()
                           if key in self.cfg.settings and value is not None])
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application


    app.logger.setLevel(app.config.get('LOG_LEVEL', logging.INFO))
    service_config = {
        'bind': app.config.get('UPGRADE_BIND', '0.0.0.0:%d' % constants.UPGRADE_DEFAULT_PORT),
        'workers': app.config.get('WORKERS', cpu_count() * 2 + 1),
        'worker_class': 'gevent',
        'worker_connections': app.config.get('WORKER_CONNECTIONS', 10000),
        'backlog': app.config.get('BACKLOG', 2048),
        'timeout': app.config.get('TIMEOUT', 300),
        'loglevel': app.config.get('LOG_LEVEL', 'info'),
        'pidfile': app.config.get('PID_FILE', 'yzy_upgrade.pid'),
        "preload_app": True
    }

    serverApplication(app, service_config).run()


@manager.command
def debug():
    """
    windows
    debug模式启动命令函数
    To use: python manager.py debug
    """
    app.logger.setLevel(logging.DEBUG)
    app.run(host="0.0.0.0", port=constants.UPGRADE_DEFAULT_PORT, debug=True)


@manager.command
def gev():
    """ gevent """
    server = pywsgi.WSGIServer(('0.0.0.0', constants.UPGRADE_DEFAULT_PORT), app)
    server.serve_forever()


@manager.command
def mult_pro():
    server = pywsgi.WSGIServer(('0.0.0.0', constants.UPGRADE_DEFAULT_PORT), app)
    server.start()

    def serve_forever():
        server.start_accepting()
        server._stop_event.wait()

    for i in range(cpu_count()):
        p = Process(target=serve_forever)
        p.start()


@manager.command
def self_upgrade():
    from yzy_upgrade.apis.v1.controllers.self_upgrade import start_self_upgrade
    start_self_upgrade(True)


if __name__ == '__main__':
    manager.run()
