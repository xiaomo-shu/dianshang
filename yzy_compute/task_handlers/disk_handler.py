import logging
from yzy_compute.storage.lvm_manager import LVMManager


class DiskHandler(object):

    def __init__(self):
        self.type = "DiskHandler"
        self.name = "I am DiskHandler"

    def deal(self, task):
        p = DiskProcess(task)
        r = p.process()
        return r


class DiskProcess(object):
    def __init__(self, task):
        self.task = task

    def process(self):
        command = self.task.get("command")
        cmd = getattr(self, command)
        return cmd()

    def get_incre_parts(self):
        """
        获取未使用的分区（未使用定义: 1未创建为pv 2未挂载使用）
         {
            "command": "get_incre_parts",
            "handler": "DiskHandler",
            "data": {
            }
        }
        """
        logging.info("DiskHandler, get_incre_parts, data:%s", self.task)
        return LVMManager().get_unused_part()

    def vg_detail(self):
        """
        获取未使用的分区（未使用定义: 1未创建为pv 2未挂载使用）
         {
            "command": "vg_detail",
            "handler": "DiskHandler",
            "data": {
            }
        }
        """
        logging.info("DiskHandler, vg_detail, data:%s", self.task)
        return LVMManager().get_vgs()

    def extend_vg(self):
        """
        将分区创建为pv并加入到vg中
         {
            "command": "extend_vg",
            "handler": "DiskHandler",
            "data": {
                "vg_name": "SLOW",
                "paths": [
                    "/dev/sdb1",
                    "/dev/sdc"
                ]
            }
        }
        """
        logging.info("DiskHandler, extend_vg, data:%s", self.task)
        vg_name = self.task['data']['vg_name']
        paths = self.task['data']['paths']
        return LVMManager().extend_vg(vg_name, paths)

    def extend_lv(self):
        """
        扩容逻辑卷
         {
            "command": "extend_vg",
            "handler": "DiskHandler",
            "data": {
                "mount_point": "/opt/slow",
                "size": 50
            }
        }
        """
        logging.info("DiskHandler, extend_lv, data:%s", self.task)
        mount_point = self.task['data']['mount_point']
        size = self.task['data']['size']
        return LVMManager().extend_lv(mount_point, size)

    def create_lv(self):
        """
        新建逻辑卷
         {
            "command": "create_lv",
            "handler": "DiskHandler",
            "data": {
                "vg_name": "SLOW",
                "lv_name": "slow",
                "size": 50
            }
        }
        """
        logging.info("DiskHandler, create_lv, data:%s", self.task)
        vg_name = self.task['data']['vg_name']
        lv_name = self.task['data']['lv_name']
        size = self.task['data']['size']
        return LVMManager().create_lv(vg_name, lv_name, size)

    def delete_lv(self):
        """
        扩容逻辑卷
         {
            "command": "delete_lv",
            "handler": "DiskHandler",
            "data": {
                "vg_name": "SLOW",
                "lv_name": "opt_slow"
            }
        }
        """
        logging.info("DiskHandler, delete_lv, data:%s", self.task)
        vg_name = self.task['data']['vg_name']
        lv_name = self.task['data']['lv_name']
        return LVMManager().delete_lv(vg_name, lv_name)
