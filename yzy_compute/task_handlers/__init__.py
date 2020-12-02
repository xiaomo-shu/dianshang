# -*- coding: utf-8 -*-

from .instance_handler import InstanceHandler
from .network_handler import NetworkHandler
from .template_handler import TemplateHandler
from .voi_handler import VoiHandler
from .node_handler import NodeHandler
from .ha_handler import HaHandler
from .disk_handler import DiskHandler
from .nfs_handle import  NfsHandler

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
            'NodeHandler': NodeHandler(),
            'HaHandler': HaHandler(),
            'DiskHandler': DiskHandler(),
            'NfsHandler': NfsHandler(),
        }
    except Exception as ex:
        raise Exception("load handler error")
    return handlers


if __name__ == "__main__":
    setup()