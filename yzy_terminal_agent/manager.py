# -*- coding: utf-8 -*-
import logging
import traceback
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
from flask_migrate import Migrate, MigrateCommand

# from gunicorn.six import iteritems
from multiprocessing import cpu_count, Process
from common import constants
from common import load_log_config

load_log_config('yzy_terminal_agent')
from yzy_terminal_agent import create_app
from yzy_terminal_agent.database.models import *


from yzy_terminal_agent.agent_servers.voi_server.voi_server import VOITerminalServer

try:
    app = create_app("pro")
except Exception as e:
    logging.error('create_app err: {}'.format(e))
    logging.error(''.join(traceback.format_exc()))
    exit(1)

voi_terminal_server = VOITerminalServer(constants.VOI_TERMINAL_LISTEN_DEFAULT_PORT)
terminal_process = Process(target=voi_terminal_server.run)


manager = Manager(app)

#migrate = Migrate(app, db)

manager.add_command('database', MigrateCommand)


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

    service_config = {
        'bind': app.config.get('VOI_TERMINAL_BIND', '0.0.0.0:50005'),
        'workers': app.config.get('WORKERS', cpu_count() * 2 + 1),
        'worker_class': 'gevent',
        'worker_connections': app.config.get('WORKER_CONNECTIONS', 10000),
        'backlog': app.config.get('BACKLOG', 2048),
        'timeout': app.config.get('TIMEOUT', 300),
        'loglevel': app.config.get('LOG_LEVEL', 'info'),
        'pidfile': app.config.get('PID_FILE', 'yzy_terminal_agent.pid'),
        "preload_app": True
    }

    terminal_process.start()
    serverApplication(app, service_config).run()


@manager.command
def debug():
    """
    windows
    debug模式启动命令函数
    To use: python manager.py debug
    """
    # voi_terminal_server = VOITerminalServer()
    # p1 = Process(target=voi_terminal_server.run, daemon=True)
    terminal_process.start()
    #app.run(host="0.0.0.0", port=constants.VOI_TERMINAL_DEFAULT_PORT, debug=True)
    server = pywsgi.WSGIServer(('0.0.0.0', constants.VOI_TERMINAL_DEFAULT_PORT), app)
    server.serve_forever()


@manager.command
def gev():
    """ gevent """
    # voi_terminal_server = VOITerminalServer()
    # p1 = Process(target=voi_terminal_server.run, daemon=True)
    terminal_process.start()
    print("start socket server success!!!")
    server = pywsgi.WSGIServer(('0.0.0.0', constants.VOI_TERMINAL_DEFAULT_PORT), app)
    server.serve_forever()


@manager.command
def mult_pro():
    server = pywsgi.WSGIServer(('0.0.0.0', constants.SERVER_DEFAULT_PORT), app)
    server.start()

    def serve_forever():
        server.start_accepting()
        server._stop_event.wait()

    for i in range(cpu_count()):
        p = Process(target=serve_forever)
        p.start()


@manager.command
def create_db():
    """
    初始化创建数据库
    :return:
    """
    db.create_all()


if __name__ == '__main__':
    # 在init_app时检查了数据库状态，打开了数据库连接，在fork子进程之前，销毁已经打开的数据库连接
    # 在fork模式下，如果不销毁，子进程和父进程拥有相同的地址空间，则子进程会有和父进程相同的文件描述符
    # 而数据库连接是tcp连接，也就是socket,在linux下就是一个文件,两个进程同时写一个连接会导致数据混乱
    #db.get_engine(app=app).dispose()
    manager.run()
