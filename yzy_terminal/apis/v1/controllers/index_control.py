from flask import current_app
import hashlib
import logging


def create_md5_token():
    logging.debug("create md5")
    #return hashlib.md5(("%s%s"% (s, key)).encode()).hexdigest()
    return hashlib.md5().hexdigest()


def deal_task(task):
    handlers = current_app.handlers
    handler = handlers.get(task.get('handler'))
    if handler:
        c = handler
        return c.deal(task)
