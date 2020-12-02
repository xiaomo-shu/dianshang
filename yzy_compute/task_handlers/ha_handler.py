import logging
from yzy_compute.ha.ha_mgr import HaManager



class HaHandler(object):

    def __init__(self):
        self.type = "HaHandler"
        self.name = "I am HaHandler"

    def deal(self, task):
        p = HaProcess(task)
        r = p.process()
        return r


class HaProcess(object):
    def __init__(self, task):
        self.task = task

    def process(self):
        command = self.task.get("command")
        cmd = getattr(self, command)
        return cmd()

    def enable_ha(self):
        """
         {
            "command": "enable_ha",
            "handler": "HaHandler",
            "data": {
                "vip": "172.16.1.199",
                "netmask": "255.255.255.0",
                "sensitivity": 60,
                "quorum_ip": "172.16.1.254",
                "master_ip": "172.16.1.66",
                "backup_ip": "172.16.1.88",
                "master_nic": "eth0",
                "backup_nic": "eth0"
            }
        }
        """
        logging.info("HaHandler, enable_ha task begin, data:%s", self.task)
        vip = self.task['data']['vip']
        netmask = self.task['data']['netmask']
        sensitivity = self.task['data'].get('sensitivity', 60)
        quorum_ip = self.task['data']['quorum_ip']
        master_ip = self.task['data']['master_ip']
        backup_ip = self.task['data']['backup_ip']
        master_nic = self.task['data']['master_nic']
        backup_nic = self.task['data']['backup_nic']
        paths = self.task['data']['paths']
        voi_template_list = self.task['data']['voi_template_list']
        voi_xlms = self.task['data']['voi_xlms']
        voi_ha_domain_info = self.task['data']['voi_ha_domain_info']
        post_data = self.task['data']['post_data']
        return HaManager().enable_ha(vip, netmask, sensitivity, quorum_ip, master_ip, backup_ip, master_nic, backup_nic,
                                     paths, voi_template_list, voi_xlms, voi_ha_domain_info, post_data)

    def config_backup(self):
        """
         {
            "command": "config_backup",
            "handler": "HaHandler",
            "data": {
                "vip": "172.16.1.199",
                "netmask": "255.255.255.0",
                "sensitivity": 60,
                "quorum_ip": "172.16.1.254",
                "master_ip": "172.16.1.66",
                "backup_ip": "172.16.1.88",
                "backup_nic": "eth0"
            }
        }
        """
        logging.info("HaHandler, config_backup task begin, data:%s", self.task)
        vip = self.task['data']['vip']
        netmask = self.task['data']['netmask']
        sensitivity = self.task['data'].get('sensitivity', 60)
        quorum_ip = self.task['data']['quorum_ip']
        master_ip = self.task['data']['master_ip']
        backup_ip = self.task['data']['backup_ip']
        backup_nic = self.task['data']['backup_nic']
        return HaManager().config_backup(vip, netmask, sensitivity, quorum_ip, master_ip, backup_ip, backup_nic)

    def start_backup(self):
        """
         {
            "command": "start_backup",
            "handler": "HaHandler",
            "data": {
            }
        }
        """
        logging.info("HaHandler, start_backup task begin, data:%s", self.task)
        return HaManager().start_backup()

    def disable_ha(self):
        """
         {
            "command": "disable_ha",
            "handler": "HaHandler",
            "data": {
                "vip_host_ip": "172.16.1.66",
                "peer_host_ip": "172.16.1.88"
            }
        }
        """
        logging.info("HaHandler, disable_ha task begin, data:%s", self.task)
        vip_host_ip = self.task['data']['vip_host_ip']
        peer_host_ip = self.task['data']['peer_host_ip']
        paths = self.task['data'].get('paths', [])
        voi_template_list = self.task['data'].get('voi_template_list', None)
        voi_xlms = self.task['data'].get('voi_xlms', None)
        post_data = self.task['data'].get('post_data', None)
        return HaManager().disable_ha(vip_host_ip, peer_host_ip, paths, voi_template_list, voi_xlms, post_data)

    def disable_backup(self):
        """
         {
            "command": "disable_backup",
            "handler": "HaHandler",
            "data": {
            }
        }
        """
        paths = self.task['data'].get('paths', [])
        voi_template_list = self.task['data'].get('voi_template_list', None)
        voi_xlms = self.task['data'].get('voi_xlms', None)
        logging.info("HaHandler, disable_backup task begin, data:%s", self.task)
        return HaManager().execute_disable_backup(paths, voi_template_list, voi_xlms)

    def switch_ha_master(self):
        """
         {
            "command": "switch_ha_master",
            "handler": "HaHandler",
            "data": {
                "new_vip_host_ip": "172.16.1.88",
                "vip": "172.16.1.199"
            }
        }
        """
        logging.info("HaHandler, switch_ha_master task begin, data:%s", self.task)
        new_vip_host_ip = self.task['data']['new_vip_host_ip']
        vip = self.task['data']['vip']
        return HaManager().switch_ha_master(new_vip_host_ip, vip)

    def check_vip(self):
        """
         {
            "command": "check_vip",
            "handler": "HaHandler",
            "data": {
                "vip": "172.16.1.199"
            }
        }
        """
        logging.info("HaHandler, check_vip task begin, data:%s", self.task)
        vip = self.task['data']['vip']
        return HaManager().check_vip(vip)

    def check_backup_ha_status(self):
        """
         {
            "command": "check_backup_ha_status",
            "handler": "HaHandler",
            "data": {
                "quorum_ip": "172.16.1.254",
                "sensitivity": 60
            }
        }
        """
        logging.info("HaHandler, check_backup_ha_status task begin, data:%s", self.task)
        quorum_ip = self.task['data'].get('quorum_ip', None)
        sensitivity = self.task['data'].get('sensitivity', None)
        paths = self.task['data'].get('paths', list())
        return HaManager().check_backup_ha_status(quorum_ip, sensitivity, paths)
