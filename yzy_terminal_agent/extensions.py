import logging
import atexit
# import fcntl
from flask_sqlalchemy import SQLAlchemy
# from flask_apscheduler import APScheduler
from cachelib import SimpleCache
from libs.yzyRedis import yzyRedis
import time
from common import constants
import traceback
from flask_apscheduler import APScheduler

scheduler = APScheduler()
# db = SQLAlchemy(session_options={'autocommit': True})
db = SQLAlchemy(session_options={'expire_on_commit': False})
cache = SimpleCache()
_redis = yzyRedis()

logger = logging.getLogger(__name__)



from yzy_terminal_agent.database import api as db_api
from yzy_terminal_agent.ext_libs.bt_api_service import BtApiServiceTask
def get_controller_image_ip():
    table_api = db_api.YzyNetworkIpCtrl(db)
    qry = table_api.select_controller_image_ip()
    if qry and qry.ip:
        logger.debug("select controller node image_ip: {}".format(qry.ip))
        return qry.ip
    else:
        logger.error("search controller node image_ip error")
        raise Exception("search controller node image_ip error")

def init_bt():
    try:
        image_ip = get_controller_image_ip()
        socket_port = constants.BT_SERVER_API_PORT
        bt_port = constants.BT_FILE_TRANS_PORT
        bt_timeout = 1000  # unit: seconds
        bt_api = BtApiServiceTask(image_ip, socket_port, bt_port, bt_timeout)
        return bt_api
    except Exception as err:
        logger.error("init bt server error: {}".format(err))
        logger.error(''.join(traceback.format_exc()))
        raise Exception("init bt server error: {}".format(err))

# scheduler = APScheduler()

# def init(app):
#     f = open("scheduler.lock", "wb")
#     try:
#         fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
#         t = AsyncCleanTask(app)
#         t.setDaemon(True)
#         # t.start()
#         # scheduler.init_app(app)
#         # scheduler.start()
#
#     except:
#         pass
#
#     def unlock():
#         fcntl.flock(f, fcntl.LOCK_UN)
#         f.close()
#     atexit.register(unlock)


# @scheduler.scheduler.scheduled_job(trigger='interval', id='apscheduler', seconds=2)
# def task1():
#     logger.info("test : %s"% time.time())
