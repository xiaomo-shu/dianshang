# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()

import os
import sys
project_dir = os.path.abspath("..")

sys.path.insert(0, project_dir)

import logging.handlers
from abc import ABC
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

# from gunicorn.six import iteritems
from multiprocessing import cpu_count
from yzy_terminal import create_app
from yzy_terminal.database.models import *
from common import constants

# register logging
from common import load_log_config
load_log_config('yzy_terminal')

app = create_app("pro")

manager = Manager(app)

#migrate = Migrate(app, db)

manager.add_command('database', MigrateCommand)


@manager.command
def run_gevent():
    from gevent import pywsgi
    ip, port = app.config.get('BIND', '0.0.0.0:%d' % constants.TERMINAL_DEFAULT_PORT).split(':')
    server = pywsgi.WSGIServer((ip, int(port)), app)
    server.serve_forever()


@manager.command
def debug_gevent():
    from gevent import pywsgi
    ip, port = app.config.get('BIND', '0.0.0.0:%d' % constants.TERMINAL_DEFAULT_PORT).split(':')
    server = pywsgi.WSGIServer((ip, int(port)), app)
    server.serve_forever()



@manager.command
def run_gunicorn():
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

    service_config = {
        'bind': app.config.get('BIND', '0.0.0.0:%d' % constants.TERMINAL_DEFAULT_PORT),
        'workers': app.config.get('WORKERS', cpu_count() * 2 + 1),
        'worker_class': 'gevent',
        'worker_connections': app.config.get('WORKER_CONNECTIONS', 10000),
        'backlog': app.config.get('BACKLOG', 2048),
        'timeout': app.config.get('TIMEOUT', 60),
        'loglevel': app.config.get('LOG_LEVEL', 'info'),
        'pidfile': app.config.get('PID_FILE', 'yzy_terminal.pid'),
    }
    serverApplication(app, service_config).run()


@manager.command
def debug():
    """
    windows
    debug模式启动命令函数
    To use: python manager.py debug
    """
    app.run(host='0.0.0.0', port=50003, debug=True)

@manager.command
def create_db():
    """
    初始化创建数据库
    :return:
    """
    db.create_all()


if __name__ == '__main__':
    manager.run()
