import os
import time
import logging
import logging.config
import logging.handlers
from flask.logging import default_handler


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


def register_logging(app):
    logging.getLogger(__name__)
    app.logger.name = app.name
    log_dir_name = "logs"
    log_file_name = app.name + '-' + time.strftime('%Y-%m-%d', time.localtime(time.time())) + '.log'
    log_file_folder = os.path.abspath(
        os.path.dirname(__file__)) + os.sep + log_dir_name
    make_dir(log_file_folder)

    log_file_str = log_file_folder + os.sep + log_file_name
    logging_format = logging.Formatter(
            '[%(asctime)s][%(levelname)s][%(filename)s][%(funcName)s: %(lineno)s] - %(message)s')
    timeRotatingHandler = logging.handlers.TimedRotatingFileHandler(log_file_str, when="D", interval=1, backupCount=10)
    timeRotatingHandler.setFormatter(logging_format)
    timeRotatingHandler.setLevel(logging.DEBUG)
    app.logger.addHandler(timeRotatingHandler)

    default_handler.setFormatter(logging_format)
    default_handler.setLevel(logging.DEBUG)


# def register_logging(app):
#     try:
#         file_path = "logger.conf"
#         logging.config.fileConfig(file_path, disable_existing_loggers=False)
#     except Exception as ex:
#         # logging.basicConfig(filename='/dev/stdout', filemode='w+',
#         #                     level=logging.DEBUG)
#         logging.error("Could not load server %s log config %s", app.name, str(ex))

