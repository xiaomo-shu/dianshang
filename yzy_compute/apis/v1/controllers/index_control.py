import logging
from flask import current_app
import hashlib


def create_md5_token(key, s):
    logging.info("create md5")
    return hashlib.md5(("%s%s"% (s, key)).encode()).hexdigest()


def deal_task(task):
    handlers = current_app.handlers
    handler = handlers.get(task.get('handler', 'InstanceHandler'))
    if handler:
        c = handler
        result = c.deal(task)
        # 保证json序列化，这个判断并不完整，如果字典或者列表中值也有不能json序列化的，还是会出错
        if type(result) in [dict, list, tuple, str, int, float, bool]:
            return result

