import logging
from yzy_compute.virt.libvirt.voi_driver import VoiLibvirtDriver


class VoiHandler(object):

    def __init__(self):
        self.type = "VoiHandler"
        self.name = "I am VoiHandler"

    def deal(self, task):
        p = VoiProcess(task)
        r = p.process()
        return r


class VoiProcess(object):
    def __init__(self, task):
        self.task = task

    def process(self):
        command = self.task.get("command")
        cmd = getattr(self, command)
        return cmd()

    def create(self):
        """
        :param task:
             {
                "command": "create",
                "handler": "VoiHandler",
                "data": {
                    "power_on": False,
                    "configdrive": True,
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1",
                        "base_name": "instance-00000001"
                        "ram": 1024,
                        "vcpus": 2,
                        "os_type": "linux"
                        "spice": False
                    },
                    "network_info": [
                        {
                            "fixed_ip": "203.0.113.203",
                            "netmask": "255.255.255.0",
                            "gateway": "203.0.113.1",
                            "dns_server": ["114.114.114.114", "114.114.114.115"]
                            "mac_addr": "fa:16:3e:8f:be:ff",
                            "bridge": "brq0c364e42-1a",
                            "port_id": "12fb86f2-b87b-44f0-b44e-38189314bdbd",
                            "model": "virtio"
                        },
                        ...
                    ],
                    "disk_info": [
                        {
                            "uuid": "dfcd91e8-30ed-11ea-9764-000c2902e179",
                            "dev": "vda",
                            "boot_index": 0,
                            "image_id": "196df26e-2b92-11ea-a62d-000c29b3ddb9",
                            "image_version": 0,
                            "base_path": "/opt/ssd/instances"
                        },
                        {
                            "uuid": "f613f8ac-30ed-11ea-9764-000c2902e179",
                            "dev": "vdb",
                            "boot_index": -1,
                            "size": "50G",
                            "base_path": "/opt/ssd/instances"
                        }
                        ...
                    ]
                }
            }
        """
        logging.info("VoiHandler, create task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        network_info = self.task['data']['network_info']
        disk_info = self.task['data']['disk_info']
        power_on = self.task['data'].get('power_on', False)
        iso = self.task['data'].get('iso', False)
        configdrive = self.task['data'].get('configdrive', True)
        guest, _ = VoiLibvirtDriver().create_voi_template(instance, network_info, disk_info,
                                                          power_on=power_on, iso=iso, configdrive=configdrive)
        if guest:
            port = VoiLibvirtDriver().get_guest_port(guest)
            result = {
                "state": guest.get_power_state(),
                "vnc_port": port['vnc_port']
            }
        else:
            result = None
        return result

    def delete(self):
        """
        :param task:
             {
                "command": "delete",
                "handler": "VoiHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1"
                    },
                    "images": [
                        {
                            "image_path": "/opt/ssd/instance/voi-1d07aaa0-2b92-11ea-a62d-000c29b3ddb9"
                        },
                        ...
                    ]
                }
            }
        """
        logging.info("VoiHandler, delete task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        images = self.task['data']['images']
        VoiLibvirtDriver().delete_voi_template(instance, images)

    def save(self):
        """
        :param task:
             {
                "command": "save",
                "handler": "VoiHandler",
                "data": {
                    "version": 1,
                    "images":[
                        {
                            "image_id": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                            "base_path": "",
                            "need_commit": True,
                        }
                    ]
                }
            }
        """
        logging.info("VoiHandler, save task begin, data:%s", self.task['data'])
        images = self.task['data']['images']
        image_version = self.task['data']['version']
        return VoiLibvirtDriver().save_template(image_version, images)

    def attach_source(self):
        """
        加载资源到虚拟机中
        :param task:
             {
                "command": "attatch_source",
                "handler": "VoiHandler",
                "data": {
                    "instance": {
                        "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                        "name": "template1"
                    }
                    "path": "/home/test.iso"
                }
            }
        """
        logging.info("VoiHandler, attach source task begin, data:%s", self.task['data'])
        path = self.task['data']['path']
        instance = self.task['data']['instance']
        VoiLibvirtDriver().change_cdrom_path(instance, path)

    def detach_source(self):
        """
        弹出加载的资源
        :param task:
             {
                "command": "detach_source",
                "handler": "VoiHandler",
                "data": {
                    "instance": {
                        "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                        "name": "template1"
                    }
                }
            }
        """
        logging.info("VoiHandler, detach source task begin, data:%s", self.task['data'])
        path = self.task['data'].get('path', '')
        instance = self.task['data']['instance']
        VoiLibvirtDriver().change_cdrom_path(instance, path, False)

    def detach_cdrom(self):
        """
        :param task:
             {
                "command": "detach_cdrom",
                "handler": "VoiHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1"
                    },
                    "configdrive": true
                }
            }
        """
        logging.info("VoiHandler, detach_cdrom task begin, data:%s", self.task['data'])
        instance = self.task['data']['instance']
        configdrive = self.task['data'].get('configdrive', True)
        return VoiLibvirtDriver().detach_iso_template(instance, configdrive)

    def rollback(self):
        """
        :param task:
             {
                "command": "rollback",
                "handler": "VoiHandler",
                "data": {
                    "rollback_version": 0,
                    "cur_version": 1,
                    "images":[
                        {
                            "image_id": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                            "base_path": ""
                        }
                    ]
                }
            }
        """
        logging.info("VoiHandler, rollback task begin, data:%s", self.task['data'])
        images = self.task['data']['images']
        rollback_version = self.task['data']['rollback_version']
        cur_version = self.task['data']['cur_version']
        return VoiLibvirtDriver().rollback(rollback_version, cur_version, images)

    def create_file(self):
        """
        根据模板系统盘的版本信息创建base文件以及差异文件
        :param task:
             {
                "command": "create_file",
                "handler": "VoiHandler",
                "data": {
                    "instance": {
                        "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                        "name": "template1"
                    }
                    "disk_info": {
                        'uuid': '2f110de8-78d8-11ea-ad5d-000c29e84b9c',
                        'dev': 'vda',
                        'image_id': '47b2807a-78a6-11ea-8454-000c29e84b9c',
                        'boot_index': 0,
                        'bus': 'virtio',
                        'type': 'disk',
                        'base_path': '/opt/slow/instances'
                    }
                    "version": 0
                }
            }
        """
        logging.info("VoiHandler, create file task begin, data:%s", self.task['data'])
        instance = self.task['data']['instance']
        disk = self.task['data']['disk_info']
        version = self.task['data']['version']
        VoiLibvirtDriver().create_data_file(instance, disk, version)

    def create_share(self):
        """
        根据模板系统盘的版本信息创建base文件以及差异文件
        :param task:
             {
                "command": "create_share",
                "handler": "VoiHandler",
                "data": {
                    "disk_info": {
                        'uuid': '2f110de8-78d8-11ea-ad5d-000c29e84b9c',
                        'base_path': '/opt/slow/instances'
                    }
                    "version": 0
                }
            }
        """
        logging.info("VoiHandler, create share task begin, data:%s", self.task['data'])
        disk = self.task['data']['disk_info']
        version = self.task['data']['version']
        VoiLibvirtDriver().create_share_disk(disk, version)

    def delete_share(self):
        """
        根据模板系统盘的版本信息创建base文件以及差异文件
        :param task:
             {
                "command": "create_share",
                "handler": "VoiHandler",
                "data": {
                    "disk_info": {"uuid" : "xxxxxxxxxxxxxx", "base_path": "xxx" },
                    "version": 0
                }
            }
        """
        logging.info("VoiHandler, create share task begin, data:%s", self.task['data'])
        disk = self.task['data']['disk_info']
        version = self.task['data']['version']
        VoiLibvirtDriver().delete_share_disk(disk, version)

    # def detach_disk(self):
    #     """
    #     删除磁盘
    #     :param task:
    #          {
    #             "command": "detach_disk",
    #             "handler": "VoiHandler",
    #             "data": {
    #                 "instance": {
    #                     "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
    #                     "name": "template1",
    #                 },
    #                 "data_base": "",
    #                 "disk_uuid": "",
    #                 "delete_base": true
    #             }
    #         }
    #     """
    #     logging.info("VoiHandler, detach disk task begin, data:%s", self.task['data'])
    #     base_path = self.task['data']["data_base"]
    #     disk_uuid = self.task['data']['disk_uuid']
    #     delete_base = self.task['data'].get('delete_base', False)
    #     instance = self.task['data']['instance']
    #     VoiLibvirtDriver().detach_disk(instance, base_path, disk_uuid, delete_base)

    def resize(self):
        """
        :param task:
             {
                "command": "resize",
                "handler": "VoiHandler",
                "data": {
                    # size is the add size, not disk size
                    "images": [
                        {
                            "image_id": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                            "base_path": "",
                            "size": 50
                        },
                        {
                            "image_id": "1ed81518-2b92-11ea-a62d-000c29b3ddb9",
                            "base_path": "",
                            "size": 50
                        },
                        ...
                    ]
                }
            }
        """
        logging.info("VoiHandler, resize task begin, data:%s", self.task['data'])
        images = self.task['data']['images']
        VoiLibvirtDriver().resize_disk(images)

    def copy(self):
        """
        复制模板
        :param task:
             {
                "command": "copy",
                "handler": "VoiHandler",
                "data": {
                    "version": 1,
                    "images":[
                        {
                            "image_path": "",
                            "dest_path": ""
                        },
                        ...
                    ]
                }
            }
        """
        logging.info("VoiHandler, copy task begin, data:%s", self.task['data'])
        images = self.task['data']['images']
        return VoiLibvirtDriver().copy_images(images)

    def convert(self):
        """
        when copy a template, first generate a new base image(copy or merge the diff disk file)
        :param task:
             {
                "command": "convert",
                "handler": "VoiHandler",
                "data": {
                    "template": {
                        "need_convert": False,
                        "image_path": ""
                        "new_path": "dfcd91e8-30ed-11ea-9764-000c2902e179"
                    }
                }
            }
        """
        logging.info("VoiHandler, convert task begin, data:%s", self.task)
        template = self.task['data']['template']
        return VoiLibvirtDriver().convert(template)

    def reset(self):
        """
        重置模板
        :param task:
             {
                "command": "reset",
                "handler": "VoiHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1",
                        },
                    "images": [
                    {
                        "image_path": "",
                        "backing_path": ""
                    },
                    {
                        "image_path": "",
                        "backing_path": ""
                    },
                    ...
                    ]
                }
            }
        """
        logging.info("VoiHandler, reset task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        images = self.task['data']['images']
        VoiLibvirtDriver().reset_instance(instance, images)

    def create_pool(self):
        """
        创建storagePool
        :param task:
             {
                "command": "create_pool",
                "handler": "VoiHandler",
                "data": {
                    "pool_name": "",
                    "path": "",
            }
        """
        logging.info("VoiHandler, create_pool task begin, data:%s", self.task)
        pool_name = self.task['data']['pool_name']
        path = self.task['data']['path']
        VoiLibvirtDriver().create_storage_by_name(pool_name, path)

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
        VoiLibvirtDriver().set_vcpu_and_ram(instance, vcpu, ram)
