# -*- coding: utf-8 -*-
import multiprocessing
import os
from common.utils import _ConfigParser
from common import constants

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class BaseConfig:
    """
    生产配置
    """
    DEBUG = False

    _LOCALES = ['en_US', 'zh_Hans_CN']
    BABEL_DEFAULT_LOCALE = _LOCALES[0]
    SECRET_KEY = os.getenv('SECRET_KEY', 'a secret string')

    # 数据库配置
    DATABASE_HOST = '127.0.0.1'
    DATABASE_PORT = 3306
    DATABASE_USER = 'root'
    DATABASE_PASSWORD = '123qwe,.'
    DATABASE_NAME = 'yzy_kvm_db'
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db_name}?charset=utf8" \
        .format(**{"user": DATABASE_USER, "password": DATABASE_PASSWORD, "host": DATABASE_HOST,
                   "port": DATABASE_PORT, "db_name": DATABASE_NAME})
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 5
    SQLALCHEMY_POOL_RECYCLE = 60 * 60
    # SQLALCHEMY_POOL_TIMEOUT = 28800

    # gunicorn配置
    default_workers = multiprocessing.cpu_count() * 2 + 1
    if default_workers > constants.DEFAULT_MAX_WORKER:
        default_workers = constants.DEFAULT_MAX_WORKER
    WORKERS = default_workers
    WORKER_CONNECTIONS = 10000
    BACKLOG = 64
    TIMEOUT = 1800
    # LOG_LEVEL = 'DEBUG'
    # LOG_DIR_PATH = os.path.join(os.path.dirname(__file__), 'logs')
    # LOG_FILE_MAX_BYTES = 1024 * 1024 * 100
    # LOG_FILE_BACKUP_COUNT = 10
    PID_FILE = 'yzy_terminal_agent.pid'

    # redis
    REDIS_HOST = "127.0.0.1"
    REDIS_PASSWORD = ""
    REDIS_PORT = 6379
    REDIS_DB = 0

    @classmethod
    def init_config(cls, config_path=constants.CONFIG_PATH):
        conf = _ConfigParser()
        conf.read(config_path)
        _d = conf.to_dict()
        for k, v in _d.items():
            if isinstance(v, dict):
                for i, j in v.items():
                    if j.lower() in ('false', 'true'):
                        j = True if j.lower() == 'true' else False
                    setattr(cls, i.upper(), j)


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # pass

    def __init__(self, config_path=constants.CONFIG_PATH):
        super(DevelopmentConfig, self).__init__(config_path)


class ProductionConfig(BaseConfig):

    def __init__(self, config_path=constants.CONFIG_PATH):
        super(ProductionConfig, self).__init__(config_path)


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
    WTF_CSRF_ENABLED = False


config = {
    'dev': DevelopmentConfig,
    'pro': ProductionConfig,
    'test': TestingConfig
}