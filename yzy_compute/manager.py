import os
import sys
project_dir = os.path.abspath("..")
sys.path.insert(0, project_dir)

import logging
from abc import ABC
from multiprocessing import cpu_count

from gevent import monkey
from flask_script import Manager
# from gunicorn.six import iteritems
monkey.patch_all()

from yzy_compute import create_app
# register logging
from common import load_log_config
load_log_config('yzy_compute')

from common.config import SERVER_CONF as CONF
from common import constants

app = create_app()
manager = Manager(app)


@manager.command
def run():
    """
    生产模式启动命令函数
    To use: python manager.py run
    """
    from gunicorn.app.base import BaseApplication

    class ServerApplication(BaseApplication, ABC):
        """
        gunicorn服务器启动类
        """

        def __init__(self, application, options):
            self.application = application
            self.options = options or {}
            super(ServerApplication, self).__init__()

        def load_config(self):
            config = dict([(key, value) for key, value in self.options.items()
                           if key in self.cfg.settings and value is not None])
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    default_workers = cpu_count() * 2 + 1
    if default_workers > constants.DEFAULT_MAX_WORKER:
        default_workers = constants.DEFAULT_MAX_WORKER
    service_config = {
        'bind': CONF.addresses.get_by_default('compute_bind', '0.0.0.0:%d' % constants.COMPUTE_DEFAULT_PORT),
        'workers': CONF.addresses.get_by_default('workers', default_workers),
        'worker_class': 'gevent',
        'worker_connections': CONF.addresses.get_by_default('worker_connnections', 10000),
        'backlog': CONF.addresses.get_by_default('backlog', 2048),
        'timeout': CONF.addresses.get_by_default('timeout', 3600),
        'pidfile': CONF.addresses.get_by_default('pid_file', 'yzy_compute.pid'),
    }
    logging.info("start manager run")
    base_path = os.path.abspath('.')
    try:
        os.remove(os.path.join(base_path, 'yzy_compute.pid'))
    except:
        pass
    ServerApplication(app, service_config).run()


@manager.command
def debug():
    """
    windows
    debug模式启动命令函数
    To use: python manager.py debug
    """
    print(app.config.get('BIND', '0.0.0.0:%d' % constants.COMPUTE_DEFAULT_PORT))
    app.logger.setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', port=constants.COMPUTE_DEFAULT_PORT, debug=True)


if __name__ == '__main__':
    manager.run()
