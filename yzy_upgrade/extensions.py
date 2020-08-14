import logging
import atexit
# import fcntl
from flask_sqlalchemy import SQLAlchemy
# from flask_apscheduler import APScheduler
from cachelib import SimpleCache
from redis import StrictRedis
import time
from flask_apscheduler import APScheduler

scheduler = APScheduler()
db = SQLAlchemy(session_options={'autocommit': True})
cache = SimpleCache()
_redis = StrictRedis()

logger = logging.getLogger(__name__)

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
