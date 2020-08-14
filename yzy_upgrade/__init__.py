# -*- coding:utf-8 -*-
import os
import logging
import uuid
import time
import atexit
import fcntl    # 只能用于linux

from flask import Flask, request
from common import constants
from yzy_upgrade.extensions import db, cache, _redis, scheduler
from yzy_upgrade.apis.v1 import api_v1
from yzy_upgrade.config import config
from yzy_upgrade.log import register_logging
# from yzy_upgrade.task_handlers import setup
# from yzy_upgrade.monitor import start_monitor_thread
# from yzy_upgrade.apis.v1.controllers.template_ctl import TemplateController
# from yzy_upgrade.apis.v1.controllers.system_ctl import CrontabController
# from threading import Timer
# from yzy_server.apis.v1.controllers.node_ctl import NodeController

logger = logging.getLogger(__name__)


def register_extensions(app):
    db.init_app(app)
    db.app = app


def register_blueprints(app):
    app.register_blueprint(api_v1, url_prefix='/api/v1')


def register_request_hook(app):

    @app.before_request
    def create_request_id():
        req_uuid = "req-%s" % str(uuid.uuid4())
        setattr(request, "req_uuid", req_uuid)

    @app.after_request
    def _access_control(response):
        """
        解决跨域请求
        """
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET,HEAD,PUT,PATCH,POST,DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Max-Age'] = 86400
        return response


def ensure_dirs(dir_path):
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as exc:
            pass


def create_app(config_name="dev"):
    logging.info("start create app")
    app = Flask(__name__)
    config_model = config[config_name]
    config_model.init_config()
    app.config.from_object(config[config_name])
    register_logging(app)
    register_extensions(app)
    register_blueprints(app)
    logger.info("register request hook")
    register_request_hook(app)
    logger.info("create app finished")

    # register_blueprints(app)
    # register_errors(app)
    # NodeController().start_service('20b62439-d912-4c42-b7b3-63908b0ab538', 'mariadb')
    # NodeController().start_service('20b62439-d912-4c42-b7b3-63908b0ab538', 'nginx')
    # NodeController().start_service('20b62439-d912-4c42-b7b3-63908b0ab538', 'redis')
    # NodeController().start_service('20b62439-d912-4c42-b7b3-63908b0ab538', 'yzy-server')
    # NodeController().start_service('20b62439-d912-4c42-b7b3-63908b0ab538', 'yzy-terminal')
    # NodeController().stop_service('609287a5-30db-4699-9532-5ce5d4242e87', ['nginx', 'redis'])
    return app


