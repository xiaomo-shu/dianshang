# -*- coding: utf-8 -*-

import os
import sys
import logging
import traceback
from flask import current_app
from yzy_terminal.task_handlers.web_terminal_handler import WebTerminalHandler
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
            'WebTerminalHandler': WebTerminalHandler()
        }
    except Exception as err:
        logging.error(err)
        logging.error(''.join(traceback.format_exc()))
        raise Exception("load handler error")
    return handlers


if __name__ == "__main__":
    setup()
