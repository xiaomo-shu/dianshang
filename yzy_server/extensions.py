from flask_sqlalchemy import SQLAlchemy
from cachelib import SimpleCache
from redis import StrictRedis
from flask_apscheduler import APScheduler

scheduler = APScheduler()
db = SQLAlchemy(session_options={'autocommit': True})
cache = SimpleCache()
_redis = StrictRedis()
