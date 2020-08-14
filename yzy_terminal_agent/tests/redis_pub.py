# -*- coding: UTF-8 -*-

from test_pub_sub import RedisHelper

obj = RedisHelper()
while True:
    msg = input('>>:')
    obj.public(msg)
