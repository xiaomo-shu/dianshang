# -*- coding:utf-8 -*-
import os
import logging
import uuid
import time
import threading
import atexit
# import fcntl    # 只能用于linux

from flask import Flask, request
from common import constants
from yzy_terminal_agent.extensions import db, cache, _redis, scheduler, init_bt
from yzy_terminal_agent.apis.v1 import api_v1
from yzy_terminal_agent.config import config
from yzy_terminal_agent.task_handlers import setup
from yzy_terminal_agent.timer_tasks.bt_state_task import BtStateTask
# from yzy_terminal_agent.apis.v1.controllers.template_ctl import TemplateController
# from yzy_terminal_agent.apis.v1.controllers.system_ctl import CrontabController
from threading import Timer

logger = logging.getLogger(__name__)


def job_function(name):
    logging.info("%s: %s"% (name, time.time()))


def configure_scheduler(app):
    """Configure Scheduler"""
    # f = open("scheduler.lock", "wb")
    try:
        # fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        scheduler.init_app(app)
        scheduler.start()

        # 加载任务，选择了第一次请求flask后端时加载，可以选择别的方式...
        # @app.before_first_request
        def load_tasks():
            # 开启任务
            from yzy_server.crontab_tasks import run_task
            run_task(app)

        # t = Timer(5, load_tasks)
        # t.start()
        # load_tasks()
        logger.info("scheduler task init success!")
    except:
        pass

    # def unlock():
    #     logger.info("unlock the scheduler")
    #     fcntl.flock(f, fcntl.LOCK_UN)
    #     f.close()
    #
    # atexit.register(unlock)


def start_task_timer(app):
    bt_task = BtStateTask(app, 5)
    bt_task.start()


def register_extensions(app):
    _redis.init_app(app)
    db.init_app(app)
    db.app = app
    try:
        db.engine.execute(db.text("SELECT 1"))
    except Exception as e:
        logger.error("connect mysql failed:%s", e)
        retry = 3
        while True:
            logger.warning('SQL connection failed, try %s times again', retry)
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
    from common import utils
    logging.info("start create app")
    ensure_dirs(constants.TOKEN_PATH)
    ensure_dirs(constants.TEMPLATE_SCHEDULER_PATH)
    app = Flask(__name__)
    config_model = config[config_name]
    config_model.init_config()
    app.config.from_object(config[config_name])
    logger.info("setup handlers")
    #import pdb; pdb.set_trace()
    setattr(app, "handlers", setup())
    setattr(app, "db", db)
    #register_logging()
    register_extensions(app)
    setattr(app, "bt_api", init_bt())
    register_blueprints(app)
    logger.info("register request hook")
    register_request_hook(app)
    # 启动定时任务
    start_task_timer(app)
    # 初始化调度器配置
    # configure_scheduler(app)
    # 模板定时更新，gevent多workers会执行多次，怎么解决？
    # CrontabController().run_task(app)
    # TemplateController().add_scheduler_task(app)
    logger.info("create app finished")

    # register_blueprints(app)
    # register_errors(app)
    return app


