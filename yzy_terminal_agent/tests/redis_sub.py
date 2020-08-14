# -*- coding: UTF-8 -*-
from test_pub_sub import RedisHelper

obj = RedisHelper()
redis_sub = obj.subscribe()

while True:
    msg = redis_sub.parse_response()
    print(msg)
    print("hello........")
