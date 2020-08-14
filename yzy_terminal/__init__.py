import uuid
import time
import threading
import logging
from ipcqueue import posixmq
from flask import Flask, request
from yzy_terminal.extensions import db
from yzy_terminal.extensions import start_thrift_server
from yzy_terminal.apis.v1 import api_v1
from yzy_terminal.config import config
from yzy_terminal.task_handlers import setup
from yzy_terminal.managers.asyn_clean_manager import AsyncCleanTask


# def create_handler():
#     return setup()

def register_extensions(app):
    db.init_app(app)
    db.app = app
    try:
        db.engine.execute(db.text("SELECT 1"))
    except Exception as e:
        logging.error("connect mysql failed:%s", e)
        retry = 3
        while True:
            logging.warning('SQL connection failed, try %s times again', retry)
            retry -= 1
            time.sleep(10)
            try:
                db.engine.execute(db.text("SELECT 1"))
                break
            except Exception as e:
                if retry == 0:
                    raise e


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


def start_test(app_input):
    while True:
        print('=====================================================================')
        print('main thread 11111111111 app_input.token_client {} '.format(app_input.token_client))
        print('main thread 11111111111 app_input.mac_token {} '.format(app_input.mac_token))
        print('=====================================================================')
        time.sleep(2)


def create_app(config_name="dev"):
    app = Flask(__name__)
    config_model = config[config_name]
    config_model.init_config()
    app.config.from_object(config[config_name])
    setattr(app, "handlers", setup())
    setattr(app, "token_client", {})
    setattr(app, "mac_token", {})
    setattr(app, "token_status", {})
    setattr(app, "order_lock", threading.Lock())
    setattr(app, "db", db)
    register_extensions(app)
    register_blueprints(app)
    register_request_hook(app)
    # register_async_thread(app)
    # register_errors(app)

    # create a posix ipc queue
    thrift_queue = posixmq.Queue('/thrift_msq')
    setattr(app, "thrift_msq", thrift_queue)
    # thrift server process
    timer_start = threading.Timer(2, start_thrift_server, [app])
    timer_start.start()
    return app

