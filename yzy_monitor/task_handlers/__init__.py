# -*- coding: utf-8 -*-

import os
import sys
import traceback
from flask import current_app
from yzy_monitor.task_handlers.crontab_handler import CrontabHandler
from yzy_monitor.task_handlers.os_handler import OsHandler
from yzy_monitor.task_handlers.service_handler import ServiceHandler
from yzy_monitor.task_handlers.timer_handler import TimerHandler
from yzy_monitor.task_handlers.file_handler import FileHandler
sys.path.append(os.getcwd())



def setup():
    """
    dynamiclly install plug-in task handler
    """
    try:
        # handlers = {}
        # path = os.path.dirname(os.path.abspath(__file__))
        # handler_dir, handler_package = os.path.split(path)
        # handler_files = os.listdir(path)
        # for file_name in handler_files:
        #     if file_name.endswith('.py') and file_name not in ('base_handler.py', '__init__.py'):
        #         full_file_name = file_name.split('.')[0]
        #         package = '%s' % handler_package + "." + full_file_name
        #         module = __import__(package, fromlist=['.'])
        #         names = full_file_name.split('_')
        #         class_name = list()
        #         for name in names:
        #             class_name.append(name.title())
        #         cls = getattr(module, ''.join(class_name))
        #         handler = cls()
        #         handlers[handler.type] = handler
        handlers = {
            'TimerHandler': TimerHandler(),
            'ServiceHandler': ServiceHandler(),
            'OsHandler': OsHandler(),
            'CrontabHandler': CrontabHandler(),
            'FileHandler': FileHandler()
        }
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        raise Exception("load handler error")
    return handlers


if __name__ == "__main__":
    setup()
