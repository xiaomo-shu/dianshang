import logging
import uuid
import os
from flask import Flask, request

from yzy_compute.apis.v1 import api_v1
from yzy_compute.task_handlers import setup
from yzy_compute.managers.async_clean_manager import AsyncCleanTask
from yzy_compute.virt.libvirt.driver import LibvirtDriver
from common import constants


def register_blueprints(app):
    app.register_blueprint(api_v1, url_prefix='/api/v1')


def register_request_hook(app):

    @app.before_request
    def create_request_id():
        req_uuid = "req-%s" % str(uuid.uuid4())
        setattr(request, "req_uuid", req_uuid)


def ensure_dirs(dir_path):
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as exc:
            pass


def create_app():
    logging.info("start create app")
    ensure_dirs(constants.QEMU_AUTO_START_DIR)
    app = Flask(__name__)
    # config_model = config[config_name]
    # config_model.init_config()
    # config_model = {"port": 5000}
    # app.config.from_object(config_model)
    logging.info("setup handlers")
    setattr(app, "handlers", setup())
    # register_logging(app)
    logging.info("register blueprints")
    register_blueprints(app)
    logging.info("register request hook")
    register_request_hook(app)
    LibvirtDriver().autostart_instance()
    return app
