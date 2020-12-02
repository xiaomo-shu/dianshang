import logging
from common.utils import time_logger
from yzy_compute.virt.libvirt.driver import LibvirtDriver
from yzy_compute.image.image_data import ImageService


class TemplateHandler(object):

    def __init__(self):
        self.type = "TemplateHandler"
        self.name = "I am TemplateHandler"

    def deal(self, task):
        p = TemplateProcess(task)
        r = p.process()
        return r


class TemplateProcess(object):
    def __init__(self, task):
        self.task = task

    def process(self):
        command = self.task.get("command")
        cmd = getattr(self, command)
        return cmd()

    # def create(self):
    #     """
    #     :param task:
    #          {
    #             "command": "create",
    #             "handler": "TemplateHandler",
    #             "data": {
    #                 "power_on": False,
    #                 "instance": {
    #                     "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
    #                     "name": "instance1",
    #                     "base_name": "instance-00000001"
    #                     "ram": 1024,
    #                     "vcpus": 2,
    #                     "os_type": "linux"
    #                 },
    #                 "network_info": [
    #                     {
    #                         "fixed_ip": "203.0.113.203",
    #                         "netmask": "255.255.255.0",
    #                         "gateway": "203.0.113.1",
    #                         "dns_server": ["114.114.114.114", "114.114.114.115"]
    #                         "mac_addr": "fa:16:3e:8f:be:ff",
    #                         "bridge": "brq0c364e42-1a",
    #                         "port_id": "12fb86f2-b87b-44f0-b44e-38189314bdbd"
    #                     },
    #                     ...
    #                 ],
    #                 "disk_info": [
    #                     {
    #                         "uuid": "dfcd91e8-30ed-11ea-9764-000c2902e179",
    #                         "dev": "vda",
    #                         "boot_index": 0,
    #                         "image_id": "196df26e-2b92-11ea-a62d-000c29b3ddb9",
    #                         "image_version": 0,
    #                         "base_path": "/opt/ssd"
    #                     },
    #                     {
    #                         "uuid": "f613f8ac-30ed-11ea-9764-000c2902e179",
    #                         "dev": "vdb",
    #                         "boot_index": -1,
    #                         "size": "50G"
    #                     }
    #                     ...
    #                 ]
    #             }
    #         }
    #     """
    #     logging.info("TemplateHandler, create task begin, data:%s", self.task)
    #     instance = self.task['data']['instance']
    #     network_info = self.task['data']['network_info']
    #     disk_info = self.task['data']['disk_info']
    #     power_on = self.task['data'].get('power_on', False)
    #     guest = LibvirtDriver().create_template(instance, network_info, disk_info, power_on=power_on)
    #     if guest:
    #         result = {
    #             "state": guest.get_power_state()
    #         }
    #     else:
    #         result = None
    #     return result

    def convert(self):
        """
        when copy a template, first generate a new base image(copy or merge the diff disk file)
        :param task:
             {
                "command": "convert",
                "handler": "TemplateHandler",
                "data": {
                    "template": {
                        "uuid": "dfcd91e8-30ed-11ea-9764-111c2902e179",
                        "backing_file": "/opt/ssd"
                        "dest_file": "dfcd91e8-30ed-11ea-9764-000c2902e179"
                        "need_convert": 0
                    }
                }
            }
        """
        logging.info("TemplateHandler, convert task begin, data:%s", self.task)
        template = self.task['data']['template']
        return ImageService().convert(template)

    def write_header(self):
        """
        write head to image file, contain vcpu, ram, md5 sum, the allocated system disk size
        :param task:
             {
                "command": "write_header",
                "handler": "TemplateHandler",
                "data": {
                        "image_path": "",
                        "vcpu": 2,
                        "ram": 1.8,
                        "disk_size": 50
                    }
                }
            }
        """
        logging.info("TemplateHandler, write head task begin, data:%s", self.task)
        data = self.task['data']
        return ImageService().write_header(data)

    def delete(self):
        """
        :param task:
             {
                "command": "delete",
                "handler": "TemplateHandler",
                "data": {
                    "image_version": 1
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1",
                        "sys_base": "",
                        "data_base": ""
                    },
                    "images": [
                        {
                            "image_id": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                            "backing_file": "/opt/ssd"
                        },
                        {
                            "image_id": "1ed81518-2b92-11ea-a62d-000c29b3ddb9",
                            "backing_file": "/opt/ssd"
                        },
                        ...
                    ]
                }
            }
        """
        logging.info("TemplateHandler, delete task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        images = self.task['data']['images']
        image_version = self.task['data']['image_version']
        LibvirtDriver().delete_template(instance, image_version, images)

    def recreate_disk(self):
        """
        :param task:
             {
                "command": "save",
                "handler": "TemplateHandler",
                "data": {
                    "disks": [
                        {
                            "disk_file": "",
                            "backing_file": ""
                        },
                        ...
                    ]
                }
            }
        """
        logging.info("TemplateHandler, recreate task begin, data:%s", self.task['data'])
        disks = self.task['data']['disks']
        ImageService().recreate_disks(disks)

    def sync(self):
        """
        :param task:
             {
                "command": "sync",
                "handler": "TemplateHandler",
                "data": {
                    "image_version": 1,
                    "task_id": "3r451518-2b92-11ea-a62d-000c29b3ddb9",
                    "endpoint": "http://controller:2222",
                    "url": "/api/v1/file",
                    "image":
                        {
                            "image_id": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                            "disk_file": "",
                            "backing_file": "",
                            "dest_path": "",
                            "md5_sum": ""
                        }
                }
            }
        """
        logging.info("TemplateHandler, sync task begin, data:%s", self.task['data'])
        image = self.task['data']['image']
        image_version = self.task['data']['image_version']
        endpoint = self.task['data']['endpoint']
        url = self.task['data']['url']
        task_id = self.task['data'].get('task_id', None)
        return ImageService(endpoint=endpoint).sync(url, image, image_version, task_id)

    def copy(self):
        """
        复制模板时，将模板的系统盘和数据盘复制一份，基础镜像不变
        :param task:
             {
                "command": "copy",
                "handler": "TemplateHandler",
                "data": {
                    "image":
                    {
                        "image_id": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                        "backing_file": "",
                        "dest_file": ""
                    }
                }
            }
        """
        logging.info("TemplateHandler, copy task begin, data:%s", self.task['data'])
        image = self.task['data']['image']
        return ImageService().copy_images(image)

    def delete_base(self):
        """
        删除基础镜像
        :param task:
             {
                "command": "delete_base",
                "handler": "TemplateHandler",
                "data": {
                    "image":
                    {
                        "disk_file": ""
                    }
                }
            }
        """
        logging.info("TemplateHandler, delete image base, data:%s", self.task['data'])
        image = self.task['data']['image']
        return ImageService().delete_image(image)

    def attach_source(self):
        """
        加载资源到虚拟机中
        :param task:
             {
                "command": "attatch_source",
                "handler": "TemplateHandler",
                "data": {
                    "instance": {
                        "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                        "name": "template1"
                    }
                    "path": "/home/test.iso"
                }
            }
        """
        logging.info("TemplateHandler, attach source task begin, data:%s", self.task['data'])
        path = self.task['data']['path']
        instance = self.task['data']['instance']
        LibvirtDriver().change_cdrom_path(instance, path)

    def detach_source(self):
        """
        弹出加载的资源
        :param task:
             {
                "command": "detach_source",
                "handler": "TemplateHandler",
                "data": {
                    "instance": {
                        "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                        "name": "template1"
                    }
                }
            }
        """
        logging.info("TemplateHandler, detach source task begin, data:%s", self.task['data'])
        path = self.task['data'].get('path', '')
        instance = self.task['data']['instance']
        LibvirtDriver().change_cdrom_path(instance, path, False)

    def detach_cdrom(self):
        """
        :param task:
             {
                "command": "detach_cdrom",
                "handler": "TemplateHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1"
                    },
                    "configdrive": true
                }
            }
        """
        logging.info("TemplateHandler, detach_cdrom task begin, data:%s", self.task['data'])
        instance = self.task['data']['instance']
        configdrive = self.task['data'].get('configdrive', True)
        return LibvirtDriver().detach_template_cdrom(instance, configdrive)

    def send_key(self):
        """
        弹出加载的资源
        :param task:
             {
                "command": "send_key",
                "handler": "TemplateHandler",
                "data": {
                    "instance": {
                        "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                        "name": "template1"
                    }
                }
            }
        """
        logging.info("TemplateHandler, send key task begin, data:%s", self.task['data'])
        instance = self.task['data']['instance']
        LibvirtDriver().send_key(instance)

    def resize(self):
        """
        :param task:
             {
                "command": "resize",
                "handler": "TemplateHandler",
                "data": {
                    # size is the add size, not disk size
                    "images": [
                        {
                            "disk_file": "",
                            "size": 50
                        },
                        {
                            "disk_file": "",
                            "size": 50
                        },
                        ...
                    ]
                }
            }
        """
        logging.info("TemplateHandler, resize task begin, data:%s", self.task['data'])
        images = self.task['data']['images']
        ImageService().resize_disk(images)

    def create_file(self):
        """
        :param task:
             {
                "command": "create_file",
                "handler": "TemplateHandler",
                "data": {
                    "file": "/opt/slow/version_1_fdafdsa",
                    "size": "50G"
                }
            }
        """
        logging.info("TemplateHandler, create file task begin, data:%s", self.task['data'])
        file = self.task['data']['file']
        size = self.task['data']['size']
        ImageService().create_qcow2_file(file, size)

    def reset(self):
        """
        重置模板
        :param task:
             {
                "command": "reset",
                "handler": "TemplateHandler",
                "data": {
                    "instance": {
                        "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                        "name": "instance1",
                        },
                    "images": [
                    {
                        "disk_file": "",
                        "backing_file": ""
                    },
                    {
                        "disk_file": "",
                        "backing_file": ""
                    },
                    ...
                    ]
                }
            }
        """
        logging.info("TemplateHandler, reset task begin, data:%s", self.task)
        instance = self.task['data']['instance']
        images = self.task['data']['images']
        LibvirtDriver().reset_instance(instance, images)

    def attach_disk(self):
        """
        添加磁盘
        :param task:
             {
                "command": "attatch_disk",
                "handler": "TemplateHandler",
                "data": {
                    "instance": {
                        "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                        "name": "template1"
                    }
                    "disk": {
                        'uuid': '2f110de8-78d8-11ea-ad5d-000c29e84b9c',
                        'dev': 'vda',
                        'disk_file': '',
                        'backing_file': "",
                        'boot_index': 0,
                        'bus': 'virtio',
                        'type': 'disk'
                    }
                }
            }
        """
        logging.info("TemplateHandler, attach disk task begin, data:%s", self.task['data'])
        disk = self.task['data']['disk']
        instance = self.task['data']['instance']
        LibvirtDriver().attach_disk(instance, disk)

    def detach_disk(self):
        """
        删除磁盘
        :param task:
             {
                "command": "detach_disk",
                "handler": "TemplateHandler",
                "data": {
                    "instance": {
                        "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                        "name": "template1",
                    },
                    "disk_file": "",
                    "backing_file": "",
                    "delete_base": true
                }
            }
        """
        logging.info("TemplateHandler, detach disk task begin, data:%s", self.task['data'])
        disk_file = self.task['data']["disk_file"]
        backing_file = self.task['data']["backing_file"]
        delete_base = self.task['data'].get('delete_base', False)
        instance = self.task['data']['instance']
        LibvirtDriver().detach_disk(instance, disk_file, backing_file, delete_base)
