from common.config import SERVER_CONF
import common.constants as constants
from common.http import HTTPClient
import common.errcode as errcode
from flask import current_app
import traceback
import logging

logger = logging.getLogger(__name__)


class HttpClient(object):
    def __init__(self):
        pass

    def post(self, url, data={}):
        bind = SERVER_CONF.addresses.get_by_default('server_bind', '')
        if bind:
            port = bind.split(':')[-1]
        else:
            port = constants.SERVER_DEFAULT_PORT
        endpoint = 'http://%s:%s' % ("127.0.0.1", port)
        http_client = HTTPClient(endpoint, timeout=60)
        headers = {
            "Content-Type": "application/json"
        }
        try:
            resp, body = http_client.post(url, data=data, headers=headers)
        except Exception as e:
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp
        return body
