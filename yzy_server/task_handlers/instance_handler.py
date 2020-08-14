# -*- coding: utf-8 -*-


class InstanceHandler():

    def __init__(self):
        self.type = "instanceHandle"
        self.name = "I am instanceHandle"

    def deal(self, task):
        p = InstanceProcess(task)
        r = p.process()
        return r


class InstanceProcess():
    def __init__(self, task):
        self.task = task

    def process(self):
        command = self.task.get("command")
        cmd = getattr(self,command)
        return cmd()

    def show(self):
        print(self.task.get("command"))
        return
