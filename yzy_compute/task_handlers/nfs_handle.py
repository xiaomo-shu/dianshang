import logging
from yzy_compute.storage.nfs_manager import NFSManager


class NfsHandler(object):

    def __init__(self):
        self.type = "NfsHandler"
        self.name = "I am NfsHandler"

    def deal(self, task):
        p = NfsProcess(task)
        r = p.process()
        return r


class NfsProcess(object):
    def __init__(self, task):
        self.task = task

    def process(self):
        command = self.task.get("command")
        cmd = getattr(self, command)
        return cmd()

    def mount_nfs(self):
        logging.info("NfsHandler, create task begin, data:%s", self.task)
        name = self.task['data']['name']
        nfs_server = self.task['data']['nfs_server']
        return NFSManager().mount_nfs(nfs_server, name)

    def umount_nfs(self):
        logging.info("NfsHandler, create task begin, data:%s", self.task)
        name = self.task['data']['name']
        return NFSManager().umount_nfs(name)
