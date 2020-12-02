import logging
from common import constants
from yzy_compute import exception
from yzy_compute.network.linuxbridge_agent import LinuxBridgeManager
from yzy_compute.network.bond_mgr import BondManager


class NetworkHandler(object):

    def __init__(self):
        self.type = "NetworkHandler"
        self.name = "I am NetworkHandler"

    def deal(self, task):
        p = NetworkProcess(task)
        r = p.process()
        return r


class NetworkProcess(object):
    def __init__(self, task):
        self.task = task

    def process(self):
        command = self.task.get("command")
        cmd = getattr(self, command)
        return cmd()

    def create(self):
        """
        :param task:
        if network type is vlan
             {
                "command": "create",
                "handler": "NetworkHandler",
                "data": {
                    "network_id": "5b0503ba-1af4-11ea-baa2-000c2902e179",
                    "network_type": "vlan",
                    "physical_interface": "ens224",
                    "vlan_id": 1001
                }
            }
        if network type is flat
             {
                "command": "create",
                "handler": "NetworkHandler",
                "data": {
                    "network_id": "5b0503ba-1af4-11ea-baa2-000c2902e179",
                    "network_type": "flat",
                    "physical_interface": "ens224"
                }
            }
        """
        logging.info("NetworkHandler, create task begin, data:%s", self.task)
        network_id = self.task['data']['network_id']
        network_type = self.task['data']['network_type']
        physical_interface = self.task['data']['physical_interface']
        if constants.FLAT_NETWORK_TYPE == network_type:
            LinuxBridgeManager().create_flat_network(network_id, physical_interface)
        elif constants.VLAN_NETWORK_TYPE == network_type:
            vlan_id = self.task['data']['vlan_id']
            LinuxBridgeManager().create_vlan_network(network_id, physical_interface, vlan_id)
        else:
            raise exception.UndefinedNetworkType(type=network_type)
        return

    def delete(self):
        """
        :param task:
             {
                "command": "delete",
                "handler": "NetworkHandler",
                "data": {
                    "network_id": "5b0503ba-1af4-11ea-baa2-000c2902e179",
                    "vlan_id": "1001"
                }
            }
        """
        logging.info("NetworkHandler, delete task begin, data:%s", self.task)
        network_id = self.task['data']['network_id']
        vlan_id = self.task['data'].get('vlan_id')
        LinuxBridgeManager().network_delete(network_id, vlan_id)
        return

    def ping(self):
        return "ok"

    def bond(self):
        """
        :param task:
             {
                "command": "bond",
                "handler": "NetworkHandler",
                "data": {
                    "ip_list":[
                        {
                            "ip": "",
                            "netmask": ""
                        },
                        ...
                    ],
                    "gate_info": {
                        "gateway": "192.168.1.254",
                        "dns1": "8.8.8.8",
                        "dns2": "",
                    },
                    "bond_info": {
                        "dev": "bond0",
                        "mode": 1,
                        "slaves": ["eth0", "eth1"]
                    }
                }
            }
        """
        logging.info("NetworkHandler, bond task begin, data:%s", self.task)
        bond_info = self.task['data']['bond_info']
        ip_list = self.task['data']['ip_list']
        gate_info = self.task["data"].get("gate_info", None)
        return BondManager().config_bond(bond_info, ip_list, gate_info, remove_slaves=[], new_flag=True)

    def edit_bond(self):
        """
        :param task:
             {
                "command": "edit_bond",
                "handler": "NetworkHandler",
                "data": {
                    "ip_list":[
                        {
                            "ip": "",
                            "netmask": ""
                        },
                        ...
                    ],
                    "gate_info": {
                        "gateway": "192.168.1.254",
                        "dns1": "8.8.8.8",
                        "dns2": "",
                    },
                    "bond_info": {
                        "dev": "bond0",
                        "mode": 1,
                        "slaves": ["eth0", "eth1"]
                    },
                    "remove_slaves": ["eth2"]
                }
            }
        """
        logging.info("NetworkHandler, edit_bond task begin, data:%s", self.task)
        bond_info = self.task['data']['bond_info']
        ip_list = self.task['data']['ip_list']
        gate_info = self.task["data"].get("gate_info", None)
        remove_slaves = self.task['data']['remove_slaves']
        return BondManager().config_bond(bond_info, ip_list, gate_info, remove_slaves, new_flag=False)

    def unbond(self):
        """
        :param task:
             {
                "command": "unbond",
                "handler": "NetworkHandler",
                "data": {
                    "slaves": [
                        {
                            "nic": "eth0",
                            "ip_list":[
                                {
                                    "ip": "",
                                    "netmask": "",
                                    "gateway": "192.168.1.254",
                                    "dns1": "8.8.8.8",
                                    "dns2": "",
                                },
                                ...
                            }
                        },
                        ...
                    ],
                    "bond_name": "bond0"
                }
            }
        """
        logging.info("NetworkHandler, unbond task begin, data:%s", self.task)
        bond_name = self.task['data']['bond_name']
        slaves = self.task['data']['slaves']
        return BondManager().unbond(bond_name, slaves)

    def set_ip(self):
        """
        :param task:
         {
            "command": "set_ip",
            "handler": "NetworkHandler",
            "data": {
                    "name": "eth0",
                    "ip_infos"[
                        {
                            "ip": "172.16.1.31",
                            "netmask": "255.255.255.0"
                        },
                        ...
                    ],
                    "gate_info": {
                        "gateway": "172.16.1.254",
                        "dns1": "8.8.8.8",
                        "dns2": "114.114.114.114"
                    },
                    "net_info": {
                        "network_id": "",
                        "physical_interface": ""
                    }
            }
        }
        """
        logging.info("NetworkHandler, set ip task begin, data:%s", self.task)
        return BondManager().add_ip_info(self.task['data'])
