# -*- coding: utf-8 -*-

from yzy_compute.task_handlers.instance_handler import InstanceHandler
from yzy_compute.task_handlers.network_handler import NetworkHandler
from yzy_compute.task_handlers.template_handler import TemplateHandler
from yzy_compute.task_handlers.voi_handler import VoiHandler
from yzy_compute.task_handlers.node_handler import NodeHandler

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
        #         handler_name = ''.join(class_name)
        #         cls = getattr(module, handler_name)
        #         handler = cls()
        #         # LOG.info('install:%s' % _0.type)
        #         handlers[handler_name] = handler
        #         # LOG.info('self.handler:%s'% self.handlers)
        handlers = {
            'TemplateHandler': TemplateHandler(),
            'VoiHandler': VoiHandler(),
            'NetworkHandler': NetworkHandler(),
            'InstanceHandler': InstanceHandler(),
            'NodeHandler': NodeHandler()
        }
    except Exception as ex:
        raise Exception("load handler error")
    return handlers


if __name__ == "__main__":
    setup()