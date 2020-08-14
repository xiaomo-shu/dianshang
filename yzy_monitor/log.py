import os
import time
import logging
import logging.handlers


#logging.basicConfig(format='[%(asctime)s][%(levelname)s][%(threadName)s][%(filename)s][%(funcName)s: %(lineno)s] - %(message)s',\
#                    level=logging.INFO)
#logger = logging.getLogger('yzy_terminal')

def make_dir(make_dir_path):
    """
    生成文件夹
    :param make_dir_path:
    :return:
    """
    path = make_dir_path.strip()
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def register_logging():
    logger = logging.getLogger('yzy_monitor')
    #log_file_name = logger.name + '-' + time.strftime('%Y-%m-%d', time.localtime(time.time())) + '.log'
    log_file_name = logger.name + '.log'
    log_file_folder = "/var/log/yzy_kvm/"
    make_dir(log_file_folder)
    log_file_str = log_file_folder + os.sep + log_file_name
    logging_format = logging.Formatter(
            '[%(asctime)s][%(levelname)s][%(threadName)s][%(filename)s][%(funcName)s: %(lineno)s] - %(message)s')
    time_rotating_handler = logging.handlers.TimedRotatingFileHandler(log_file_str, when="d", interval=1, backupCount=2)
    time_rotating_handler.setFormatter(logging_format)
    time_rotating_handler.setLevel(logging.DEBUG)
    logger.addHandler(time_rotating_handler)
    return logger


logger = register_logging()
