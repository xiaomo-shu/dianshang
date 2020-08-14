import os
import logging
import logging.config
from . import constants


LOG_CONF_PATH = os.path.join(constants.BASE_DIR, "config", "{name}.logger.conf")


def create_log_dir():
    if not os.path.exists(constants.LOG_PATH):
        try:
            os.makedirs(constants.LOG_PATH)
        except:
            pass

def load_log_config(name):
    """
    :param name: 服务名称
    使用:在服务中,from common import load_log_config，然后传入服务名即可，例如`yzy_KvmServer`，
    后续在项目中直接使用logging.info形式记录日志即可
    """
    create_log_dir()
    try:
        file_path = LOG_CONF_PATH.format(name=name)
        logging.config.fileConfig(file_path, disable_existing_loggers=False)
    except Exception as ex:
        logging.basicConfig(filename='/dev/stdout', filemode='w+',
                            level=logging.DEBUG)
        logging.error("Could not load server %s log config %s", name, str(ex))
