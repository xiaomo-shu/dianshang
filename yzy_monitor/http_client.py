import requests
import json


class HttpClient(object):
    def __init__(self):
        pass

    def request(self, url, method, **kwargs):
        # customize http message
        kwargs['headers']['Accept'] = 'application/json'
        if 'body' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs['body'])
            del kwargs['body']
        # send request
        response = requests.request(method, url, timeout=(10, 60), **kwargs)
        # check response status, parse body
        body = None
        if response.text:
            if response.status_code == 400:   # need?
                if ('Connection refused' in response.text) or ('actively refused' in response.text):
                    raise ConnectionRefusedError(response.text)
            body = json.loads(response.text)
        return response, body

    def post(self, url="http://controller:2222", **kwargs):
        resp, body = self.request(url, 'POST', **kwargs)
        return resp, body
