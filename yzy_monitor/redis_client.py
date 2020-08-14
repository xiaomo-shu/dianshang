import redis
import configparser
import os
import traceback
from yzy_monitor.log import logger
from common.constants import BASE_DIR


class RedisClient(redis.StrictRedis):
    def __init__(self):
        self._host = "127.0.0.1"
        self._password = None
        self._port = 6379
        self._db = 0
        self.live_seconds = 86400  # 86400 seconds of a day
        self.init_config()
        super(RedisClient, self).__init__(host=self._host, port=self._port, password=self._password, db=self._db)

    def init_config(self):
        try:
            # work_dir = os.getcwd()
            work_dir = os.path.join(BASE_DIR, 'config')
            conf = configparser.ConfigParser()
            conf.read('{}/monitor_server.ini'.format(work_dir))
            if conf.has_option('REDIS', 'redis_host'):
                self._host = conf.get('REDIS', 'redis_host')
            if conf.has_option('REDIS', 'redis_port'):
                self._port = conf.get('REDIS', 'redis_port')
            if conf.has_option('REDIS', 'redis_password'):
                self._password = conf.get('REDIS', 'redis_password')
            if conf.has_option('REDIS', 'redis_db'):
                self._db = conf.get('REDIS', 'redis_db')
            if conf.has_option('REDIS', 'redis_ttl'):
                self.live_seconds = conf.get('REDIS', 'redis_ttl')
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))

    def ping_server(self):
        try:
            if self.ping():
                return True
            else:
                logger.error('redis ping error, please check redis service!!!')
                return False
        except Exception as err:
            logger.error(err)
            return False


