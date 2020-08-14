# -*- coding: utf-8 -*-
import os, multiprocessing
import json
from common.utils import _ConfigParser
from configparser import ConfigParser
from common.constants import BASE_DIR

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class BaseConfig:
    """
    生产配置
    """
    DEBUG = False

    _LOCALES = ['en_US', 'zh_Hans_CN']
    BABEL_DEFAULT_LOCALE = _LOCALES[0]
    SECRET_KEY = os.getenv('SECRET_KEY', 'a secret string')

    # gunicorn配置
    default_workers = multiprocessing.cpu_count() * 2 + 1
    if default_workers > 8:
        default_workers = 8
    WORKERS = default_workers
    WORKER_CONNECTIONS = 10000
    BACKLOG = 64
    TIMEOUT = 60
    LOG_LEVEL = 'DEBUG'
    LOG_DIR_PATH = os.path.join(os.path.dirname(__file__), 'logs')
    LOG_FILE_MAX_BYTES = 1024 * 1024 * 100
    LOG_FILE_BACKUP_COUNT = 10
    PID_FILE = 'yzy_monitor.pid'

    # redis
    REDIS_HOST = "127.0.0.1"
    REDIS_PASSWORD = ""
    REDIS_PORT = 6379
    REDIS_DB = 0

    @classmethod
    def init_config(cls, config_path="monitor_server.ini"):
        conf = _ConfigParser()
        if config_path == "monitor_server.ini":
            config_path = os.path.join(BASE_DIR, "config", config_path)
        conf.read(config_path)
        _d = conf.to_dict()
        for k, v in _d.items():
            if isinstance(v, dict):
                for i, j in v.items():
                    if j.lower() in ('false', 'true'):
                        j = True if j.lower() == 'true' else False
                    setattr(cls, i.upper(), j)
        cls.get_service_list()

    @classmethod
    def get_service_list(cls, config_file="monitor_services.ini"):
        setattr(cls, 'SERVICES', [])
        cf = ConfigParser()
        if config_file == "monitor_services.ini":
            config_file = os.path.join(BASE_DIR, "config", config_file)
        cf.read(config_file)
        options = cf.options("SERVICES")
        for op in options:
            m_flag = cf.getboolean("SERVICES", op)
            if m_flag:
                cls.SERVICES.append(op)


class DevelopmentConfig(BaseConfig):
    DEBUG = True  # before __init__
    # pass

    def __init__(self, config_path="monitor_server.ini"):
        if config_path == "monitor_server.ini":
            config_path = os.path.join(BASE_DIR, "config", config_path)
        super(DevelopmentConfig, self).__init__(config_path)
        super(DevelopmentConfig, self).get_service_list()


class ProductionConfig(BaseConfig):

    def __init__(self, config_path="monitor_server.ini"):
        if config_path == "monitor_server.ini":
            config_path = os.path.join(BASE_DIR, "config", config_path)
        super(ProductionConfig, self).__init__(config_path)
        super(DevelopmentConfig, self).get_service_list()


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
    WTF_CSRF_ENABLED = False


config = {
    'dev': DevelopmentConfig,
    'pro': ProductionConfig,
    'test': TestingConfig
}
