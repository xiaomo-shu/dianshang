import logging
from yzy_compute.image.node_data import NodeService


class NodeHandler(object):

    def __init__(self):
        self.type = "NodeHandler"
        self.name = "I am NodeHandler"

    def deal(self, task):
        p = NodeProcess(task)
        r = p.process()
        return r


class NodeProcess(object):
    def __init__(self, task):
        self.task = task

    def process(self):
        command = self.task.get("command")
        cmd = getattr(self, command)
        return cmd()

    def ha_sync(self):
        """
        :param task:
             {
                "command": "ha_sync",
                "handler": "NodeHandler",
                "data": {
                    "url": "",
                    "endpoint": "",
                    "path": "",
                    "md5": ""
                }
            }
        """
        logging.debug("NodeHandler, ha_sync task begin, data:%s", self.task)
        endpoint = self.task['data']['endpoint']
        url = self.task['data']['url']
        path = self.task['data']['path']
        md5 = self.task['data'].get('md5', None)
        NodeService(endpoint=endpoint).ha_sync(url, path, md5)
