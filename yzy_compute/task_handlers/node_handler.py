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

    def ha_sync_voi(self):
        """
        :param task:
             {
                "command": "ha_sync_voi",
                "handler": "NodeHandler",
                "data": {
                    "url": "",
                    "endpoint": "",
                    "paths": [],
                    "voi_template_list": [],
                    "voi_ha_domain_info: [],
                }
            }
        """
        logging.debug("NodeHandler, ha_sync task begin, data:%s", self.task)
        endpoint = self.task['data']['endpoint']
        url = self.task['data']['url']
        paths = self.task['data']['paths']
        voi_template_list = self.task['data'].get('voi_template_list', None)
        voi_ha_domain_info = self.task['data'].get('voi_ha_domain_info', None)
        return NodeService(endpoint=endpoint).ha_sync_voi(url, paths, voi_template_list, voi_ha_domain_info)

    def ha_sync_file(self):
        """
        :param task:
             {
                "command": "ha_sync_file",
                "handler": "NodeHandler",
                "data": {
                    "url": "",
                    "endpoint": "",
                    "paths": [],
                    "check_path": ""
                }
            }
        """
        logging.debug("NodeHandler, ha_sync_file task begin, data:%s", self.task)
        endpoint = self.task['data']['endpoint']
        url = self.task['data']['url']
        paths = self.task['data']['paths']
        check_path = self.task['data'].get('check_path', None)
        return NodeService(endpoint=endpoint).ha_sync_file(url, paths, check_path)

    # def data_sync_status(self):
    #     """
    #     :param task:
    #          {
    #             "command": "data_sync_status",
    #             "handler": "NodeHandler",
    #             "data": {
    #                 "paths": []
    #             }
    #         }
    #     """
    #     logging.debug("NodeHandler, data_sync_status task begin, data:%s", self.task)
    #     paths = self.task['data']['paths']
    #     return NodeService().get_data_sync_status(paths)

    def set_ntp_sync(self):
        """
        :param task:
             {
                "command": "set_ntp_sync",
                "handler": "NodeHandler",
                "data": {
                    "controller_ip": ""
                }
            }
        """
        logging.debug("NodeHandler, set_ntp_sync task begin, data:%s", self.task)
        controller_ip = self.task['data']['controller_ip']
        return NodeService().set_ntp(controller_ip)

    def config_ntp_server(self):
        """
        :param task:
             {
                "command": "config_ntp_server",
                "handler": "NodeHandler",
                "data": {
                    "ipaddr": "192.168.10.10",
                    "netmask": "255.255.255.0"
                }
            }
        """
        logging.debug("NodeHandler, config_ntp_server task begin, data:%s", self.task)
        ipaddr = self.task['data']['ipaddr']
        netmask = self.task['data']['netmask']
        return NodeService().config_ntp(ipaddr, netmask)

    def set_node_datetime(self):
        """
        :param task:
            {
                "command": "set_node_datetime",
                "handler:  "NodeHandler",
                "data": {
                    "datetime": "2020-11-23 15:52"
                }
            }
        :return:
        """
        logging.debug("NodeHandler, set_node_datetime task begin, data:%s", self.task)
        _datetime = self.task['data']['datetime']
        time_zone = self.task['data']['time_zone']
        ntp_server = self.task['data']['ntp_server']
        if ntp_server:
            return NodeService().set_ntp_time(ntp_server)
        else:
            return NodeService().set_system_time(_datetime, time_zone)
