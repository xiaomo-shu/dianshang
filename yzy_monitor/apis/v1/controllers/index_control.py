import logging
from flask import current_app
from yzy_monitor.extensions import db
from yzy_monitor.database.models import User
import hashlib

logger = logging.getLogger(__name__)


def create_md5_token():
    logger.info("create md5")
    #return hashlib.md5(("%s%s"% (s, key)).encode()).hexdigest()
    return hashlib.md5().hexdigest()


def get_user_list():
    _l = []
    users = db.session.query(User).all()
    for user in users:
        _l.append(user.to_json())
    return _l


def deal_task(task):
    handlers = current_app.handlers
    handler = handlers.get(task.get('handler'))
    if handler:
        c = handler
        return c.deal(task)
