import logging
from yzy_compute.virt.libvirt.driver import LibvirtDriver
from common import constants


class InstanceHandler(object):

    def __init__(self):
        self.type = "InstanceHandler"
        self.name = "I am InstanceHandler"

    def deal(self, task):
        p = InstanceProcess(task)
        r = p.process()
        return r


class InstanceProcess(object):
    def __init__(self, task):
        self.task = task

    def process(self):
        command = self.task.get("command")
        cmd = getattr(self, command)
        return cmd()

    def create(self):
        """
        这里的创建实际上就是桌面的开机(桌面创建时只是添加数据库记录)，实现了开机还原，以及网络设备的保证等功能
        :param task:
             {
                "command": "create",
                "handler": "InstanceHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1",
                        "base_name": "instance-00000001"
                        "ram": 1024,
                        "vcpus": 2,
                        "os_type": "linux",
                        "spice_token": "5fb01aa4-527b-400b-b9fc-8604913742b6"
                    },
                    "network_info": [
                        {
                            "fixed_ip": "172.16.1.13",
                            "netmask": "255.255.255.0",
                            "gateway": "172.16.1.254",
                            "dns_server": ["114.114.114.114"],
                            "mac_addr": "fa:16:3e:8f:be:ff",
                            "bridge": "brqa72e4f85-28",
                            "port_id": "12fb86f2-b87b-44f0-b44e-38189314bdbd"
                            "vif_info": {
                                "uuid": "",
                                "vlan_id": 1,
                                "bridge": "brqa72e4f85-28",
                                "interface": eth1
                            }
                        },
                        ...
                    ],
                    "disk_info": [
                    {
                        'uuid': '2f110de8-78d8-11ea-ad5d-000c29e84b9c',
                        'dev': 'vda',
                        'boot_index': 0,
                        'type': 'disk',
                        'disk_file': '',
                        'backing_file': '',
                        'restore': 1
                    },
                    {
                        'uuid': '2f11114e-78d8-11ea-ad5d-000c29e84b9c',
                        'dev': 'vdb',
                        'boot_index': 1,
                        'bus': 'virtio',
                        'type': 'disk',
                        'disk_file': '',
                        'backing_file': '',
                        'restore': 1
                    }
                ]
                }
            }
        """
        logging.info("InstanceHandler, create task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        if not instance.get('os_type'):
            instance['os_type'] = 'windows'
        network_info = self.task['data']['network_info']
        disk_info = self.task['data']['disk_info']
        power_on = self.task['data'].get('power_on', False)
        virt = LibvirtDriver()
        guest, _ = virt.create_instance(instance, network_info, disk_info, power_on=power_on)
        if guest:
            port = virt.get_guest_port(guest)
            result = {
                "state": guest.get_power_state(),
                "vnc_port": port['vnc_port'],
                "spice_port": port['spice_port'],
                "spice_token": ""
            }
            if _: result.update({"spice_token": instance.get("spice_token", "")})
        else:
            result = None
        logging.info("create instance return:%s", result)
        return result

    def get_status(self):
        """
        :param task:
             {
                "command": "get_status",
                "handler": "InstanceHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1"
                    }
                }
            }
        """
        logging.debug("InstanceHandler, start task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        result = LibvirtDriver().get_status(instance)
        return result

    def get_status_many(self):
        """
        :param task:
             {
                "command": "get_status_many",
                "handler": "InstanceHandler",
                "data": {
                    "instance": [{
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1"
                    }]
                }
            }
        """
        logging.debug("InstanceHandler, start task begin, data:%s", self.task)
        instances = self.task['data']['instance']
        ret = list()
        for instance in instances:
            try:
                result = LibvirtDriver().get_status(instance)
            except Exception as e:
                result = {"state": 0}
            instance.update(result)
            ret.append(instance)
        return ret

    def start(self):
        """
        :param task:
             {
                "command": "start",
                "handler": "InstanceHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1"
                    },
                    # 网络信息每次重新加载，从而保证IP和数据库的一致
                    "network_info": {}
                }
            }
        """
        logging.info("InstanceHandler, start task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        network_info = self.task['data'].get('network_info')
        result = LibvirtDriver().power_on(instance, network_info)
        return result

    def stop(self):
        """
        针对没有还原属性的stop
        :param task:
             {
                "command": "stop",
                "handler": "InstanceHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1"
                    },
                    "timeout": 10
                }
            }
        """
        logging.info("InstanceHandler, stop task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        timeout = self.task['data'].get('timeout', 10)
        result = LibvirtDriver().power_off(instance, timeout=timeout)
        return result

    # def stop_restore(self):
    #     """
    #     系统盘和数据盘都有还原属性
    #     :param task:
    #          {
    #             "command": "stop_restore",
    #             "handler": "InstanceHandler",
    #             "data": {
    #                 "instance": {
    #                     "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
    #                     "name": "instance1",
    #                     "sys_base": "",
    #                     "data_base": ""
    #                 },
    #                 "sys_restore": 1,
    #                 "data_restore": 1,
    #                 "timeout": 0
    #             }
    #         }
    #     """
    #     logging.info("InstanceHandler, stop_restore task begin, data:%s", self.task)
    #     instance = self.task['data']['instance']
    #     sys_restore = self.task['data'].get('sys_restore', True)
    #     data_restore = self.task['data'].get('data_restore', True)
    #     timeout = self.task['data'].get('timeout', 120)
    #     result = LibvirtDriver().stop_restore_instance(instance, sys_restore, data_restore, timeout)
    #     return result

    def reboot_restore(self):
        """
        重启操作，根据还原属性进行还原
        :param task:
             {
                "command": "reboot_restore",
                "handler": "InstanceHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1",
                        "base_name": "instance-00000001"
                        "ram": 1024,
                        "vcpus": 2,
                        "os_type": "windows"
                    },
                    "network_info": [],
                    "disk_info": [],
                    "sys_restore": 1,
                    "data_restore": 1
                }
            }
        """
        logging.info("InstanceHandler, stop_restore task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        network_info = self.task['data']['network_info']
        disk_info = self.task['data']['disk_info']
        sys_restore = self.task['data'].get('sys_restore', True)
        data_restore = self.task['data'].get('data_restore', True)
        guest, _ = LibvirtDriver().reboot_restore_instance(instance, network_info, disk_info, sys_restore, data_restore)
        if guest:
            port = LibvirtDriver().get_guest_port(guest)
            result = {
                "state": guest.get_power_state(),
                "vnc_port": port['vnc_port'],
                "spice_port": port['spice_port'],
                "spice_token": ""
            }
            if _: result.update({"spice_token": instance.get("spice_token", "")})
        else:
            result = None
        return result

    def delete(self):
        """
        :param task:
             {
                "command": "delete",
                "handler": "InstanceHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1",
                        "sys_base": "",
                        "data_base": ""
                    }
                }
            }
        """
        logging.info("InstanceHandler, delete task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        LibvirtDriver().delete_instance(instance)

    def reboot(self):
        """
        :param task:
        if the reboot is soft reboot, the params is below
             {
                "command": "reboot",
                "handler": "InstanceHandler",
                "data": {
                    "reboot_type": "soft",
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1"
                    }
                }
            }
        if the reboot is hard reboot, the params is below
             {
                "command": "reboot",
                "handler": "InstanceHandler",
                "data": {
                    "reboot_type": "hard",
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1"
                    },
                    "network_info": [
                        {
                        "mac_addr": "fa:16:3e:8f:be:ff",
                        "bridge": "brq0c364e42-1a",
                        "port_id": "12fb86f2-b87b-44f0-b44e-38189314bdbd"
                        },
                        ...
                    ],
                    "disk_info": [
                        {
                        "bus": "virtio",
                        "dev": "vda",
                        "uuid": "5fff45a4-527b-400b-b9fc-8604913742b6",
                        },
                        ...
                    ]
                }
            }
        """
        logging.info("InstanceHandler, reboot task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        reboot_type = self.task['data'].get('reboot_type', 'soft')
        virt = LibvirtDriver()
        guest = virt.reboot(instance, reboot_type)
        # else:
        #     network_info = self.task['data']['network_info']
        #     disk_info = self.task['data']['disk_info']
        #     guest = virt.reboot(instance, reboot_type='HARD', network_info=network_info, disk_info=disk_info)
        if guest:
            port = virt.get_guest_port(guest)
            result = {
                "state": guest.get_power_state(),
                "vnc_port": port['vnc_port'],
                "spice_port": port['spice_port'],
                "spice_token": ""
            }
        else:
            result = None
        return result

    def pause(self):
        """
        :param task:
             {
                "command": "pause",
                "handler": "InstanceHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1"
                    }
                }
            }
        """
        logging.info("InstanceHandler, pause task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        LibvirtDriver().pause(instance)

    def unpause(self):
        """
        :param task:
             {
                "command": "unpause",
                "handler": "InstanceHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1"
                    }
                }
            }
        """
        logging.info("InstanceHandler, unpause task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        LibvirtDriver().unpause(instance)

    def autostart(self):
        """
        :param task:
             {
                "command": "autostart",
                "handler": "InstanceHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1",
                        "base_name": "instance-00000001",
                    },
                    "vif_info": {
                        "uuid": "",
                        "vlan_id": 1,
                        "bridge": "brqa72e4f85-28",
                        "interface": "eth1"
                    }
                    "start": True
                }
            }
        """
        logging.info("InstanceHandler, autostart task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        vif_info = self.task['data']['vif_info']
        start = self.task['data'].get('start', False)
        LibvirtDriver().autostart(instance, vif_info, start)

    def set_ram_and_vcpu(self):
        """
        :param task:
             {
                "command": "set_ram_and_vcpu",
                "handler": "InstanceHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1",
                        "base_name": "instance-00000001",
                    },
                    "ram": 2.5,
                    "vcpu": 2
                }
            }
        """
        logging.info("InstanceHandler, set_ram_and_vcpu task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        ram = self.task['data'].get("ram", None)
        vcpu = self.task['data'].get("vcpu", None)
        LibvirtDriver().set_vcpu_and_ram(instance, vcpu, ram)

    def check_ram(self):
        """
        :param task:
             {
                "command": "check_ram",
                "handler": "InstanceHandler",
                "data": {
                    "allocated": 16
                }
            }
        """
        logging.info("InstanceHandler, check_ram task begin, data:%s", self.task)
        allocated = self.task['data']['allocated']
        result = LibvirtDriver().check_ram_available(allocated)
        return {"result": result}
