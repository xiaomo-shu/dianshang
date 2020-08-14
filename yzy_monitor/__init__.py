import uuid
import threading
from ipcqueue import posixmq
from flask import Flask, request
from yzy_monitor.extensions import db, init_timer, monitor_timer
from yzy_monitor.apis.v1 import api_v1
from yzy_monitor.config import config
from yzy_monitor.log import logger
from yzy_monitor.task_handlers import setup
from yzy_monitor.managers.asyn_clean_manager import AsyncCleanTask


# def create_handler():
#     return setup()

def register_extensions(app):
    db.init_app(app)
    # cache.init_app(app)


def register_blueprints(app):
    app.register_blueprint(api_v1, url_prefix='/api/v1')


def register_request_hook(app):

    @app.before_request
    def create_request_id():
        req_uuid = "req-%s" % str(uuid.uuid4())
        setattr(request, "req_uuid", req_uuid)


def register_async_thread(app):
    t = AsyncCleanTask(app)
    t.setDaemon(True)
    t.start()


def _access_control(response):
    """
    解决跨域请求
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET,HEAD,PUT,PATCH,POST,DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Max-Age'] = 86400
    return response


def create_app(config_name="dev"):
    app = Flask(__name__)
    config_model = config[config_name]
    config_model.init_config()
    app.config.from_object(config[config_name])
    setattr(app, "handlers", setup())
    setattr(app, "logger", logger)
    setattr(app, "statistic", {'cpu_util': [], 'memory_util': {}, 'disk_util': {}, 'nic_util': {}, 'disk_io_util': {}})
    # app.logger.removerHandler(default_handler)
    register_extensions(app)
    register_blueprints(app)
    register_request_hook(app)
    # register_async_thread(app)
    # register_blueprints(app)
    # register_errors(app)

    # timer process
    # create a posix ipc queue
    timer_queue = posixmq.Queue('/timer_msq')
    setattr(app, "timer_msq", timer_queue)
    timer_start = threading.Timer(2, init_timer, [timer_queue, app])
    timer_start.start()
    logger.info('create_app ok ................................................')
    return app



