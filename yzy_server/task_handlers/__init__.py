# -*- coding: utf-8 -*-

import os, sys
import logging
import traceback
from yzy_server.task_handlers.instance_handler import InstanceHandler


def setup():
    """
    dynamiclly install plug-in task handler
    """
    try:
        # handlers = {}
        # path = os.path.dirname(__file__)
        # handler_dir, handler_package = os.path.split(path)
        # handler_files = os.listdir(path)
        # for file_name in handler_files:
        #     if file_name.endswith('.py') and file_name not in ('base_handler.py', '__init__.py', 'task.py'):
        #         full_file_name = file_name.split('.')[0]
        #         package = '%s' % handler_package + "." + full_file_name
        #         module = __import__(package, fromlist=['.'])
        #         names = full_file_name.split('_')
        #         class_name = list()
        #         for name in names:
        #             class_name.append(name.title())
        #         cls = getattr(module, ''.join(class_name))
        #         handler = cls()
        #         # LOG.info('install:%s' % _0.type)
        #         handlers[handler.type] = handler
        #         # LOG.info('self.handler:%s'% self.handlers)
        handlers = {
            'instanceHandle': InstanceHandler()
        }
    except Exception as ex:
        raise Exception("load handler error")
    return handlers



if __name__ == "__main__":
    setup()
