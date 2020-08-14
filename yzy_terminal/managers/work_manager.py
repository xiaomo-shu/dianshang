# -*- coding: utf-8 -*-
import json
import threading
import logging


class worker(threading.Thread):

    def __init__(self,thread_name, q, controller):
        super(worker, self).__init__(name=thread_name)
        # self.thread_id = thread_id
        self.queue = q
        self.controller = controller

    def run(self):
        while True:
            try:
                task = self.queue.get()
                if task is not None:
                    req_body,on_response = task
                    recv_task = json.loads(req_body)
                    #LOG.info("%s exec task:%s" % (self.thread_id,recv_task))
                    handler = self.controller.getHandler(recv_task.get('task_type'))

                    if CONF.gobal.time_state == 1:
                        resp = {'errcode':'-8888','msg':'Time state exception!!!'}
                    else:
                        if handler is not None:
                            resp = handler.handle(recv_task,is_rawTask=True)
                        else:
                            resp = {'errcode':'-9999','msg':'Not found handler'}
                    on_response(resp)
            except:
                fault = traceback.format_exc()
                resp = {'errcode':'-9999','msg':'%s' % fault}
                on_response(resp)
                logging.error('%s exec async error:%s' % (self.getName(), fault))


class workManager():

    def __init__(self, task_queue, controllers):
        self.works = []
        self.task_queue = task_queue
        self.controllers = controllers

    def worksMonitor(self):
        _dea_workers = []
        for work in self.works:
            """:type : worker"""
            if not work.is_alive():
                _dea_workers.append(work)
        for _w in _dea_workers:
            if _w in self.works:
                thread_name = _w.getName()
                self.works.remove(_w)
                work = worker(thread_name, self.task_queue, self.controllers)
                work.setDaemon(True)
                work.start()
                self.works.append(work)

    def start(self, num):

        for i in range(num):
            thread_name = 'AsyncCallThread-%s' % i
            work = worker(thread_name, self.task_queue, self.controllers)
            work.setDaemon(True)
            work.start()
            self.works.append(work)



