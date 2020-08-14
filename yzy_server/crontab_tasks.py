# from .task import task_func
import time
import logging

from flask import current_app

logger = logging.getLogger(__name__)


class YzyAPScheduler(object):
    """调度器控制方法"""

    def add_job(self, jobid, func, args=None, **kwargs):
        """
        添加任务
        :param args:  元祖 -> （1，2）
        :param jobstore:  存储位置
        :param trigger:
                        date ->  run_date   datetime表达式
                        cron ->  second/minute/day_of_week
                        interval ->  seconds 延迟时间
                        next_run_time ->  datetime.datetime.now() + datetime.timedelta(seconds=12))
        :return:
        """
        job_def = dict(kwargs)
        job_def['id'] = jobid
        job_def['func'] = func
        job_def['args'] = args
        # job_def = self.fix_job_def(job_def)
        self.remove_job(jobid)  # 删除原job
        try:
            current_app.apscheduler.scheduler.add_job(**job_def)
        except Exception as e:
            logger.error("add job error", exc_info=True)
            return
        logger.info("add job %s success %s", jobid, time.time())

    def remove_job(self, jobid, jobstore=None):
        """删除任务"""
        if current_app.apscheduler.get_job(jobid):
            logger.info("remove job:%s", jobid)
            current_app.apscheduler.remove_job(jobid, jobstore=jobstore)

    def resume_job(self, jobid, jobstore=None):
        """恢复任务"""
        current_app.apscheduler.resume_job(jobid, jobstore=jobstore)

    def pause_job(self, jobid, jobstore=None):
        """恢复任务"""
        current_app.apscheduler.pause_job(jobid, jobstore=jobstore)


# class AsyncCleanTask(threading.Thread):
#
#     __metaclass__ = Singleton
#
#     def __init__(self, app):
#         threading.Thread.__init__(self)
#         self.app = app
#         self.name = "%s-%s" % (random.randint(1, 100000), time.time())
#
#     def sync_instance_online_state(self):
#         """ 同步虚拟机的在线状态 """
#         # {
#         #     "command": "get_status_many",
#         #     "handler": "InstanceHandler",
#         #     "data": {
#         #         "instance": [{
#         #             "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
#         #             "name": "instance1"
#         #         }]
#         #     }
#         # }
#         items = dict()
#         read_deleted = 'no'
#         instances = db_api.get_instance_all(items, read_deleted)
#         rep_data = dict()
#         for instance in instances:
#             host_ip = instance.host.ip
#             spice_port = instance.spice_port
#             _d = {
#                 "uuid": instance.uuid,
#                 "name": instance.name,
#                 "spice_port": spice_port
#             }
#             if host_ip not in rep_data:
#                 rep_data[host_ip] = list()
#             rep_data[host_ip].append(_d)
#
#         # 启多线程分发调用
#         for k, v in rep_data.items():
#             spice_ports = list()
#             for i in v:
#                 if i.get("spice_port"):
#                     spice_ports.append(i.get("spice_port"))
#
#             command_data = {
#                 "command": "get_status_many",
#                 "handler": "InstanceHandler",
#                 "data": {
#                     "instance": v
#                 }
#             }
#             logger.info("get instance state %s in node %s", str(command_data['data']), k)
#             rep_json = compute_post(k, command_data)
#             # print(rep_json)
#             rep_code = rep_json.get("code", -1)
#             if rep_code != 0:
#                 continue
#             # 查询监控服务端口
#             ports = ",".join(spice_ports)
#             ret = monitor_post(k, "/api/v1/monitor/port_status", {"ports": ports})
#             # print(ret)
#             ret_data = rep_json.get("data", [])
#             for i in ret_data:
#                 for instance in instances:
#                     uuid = instance.uuid
#                     if i["uuid"] == uuid:
#                         instance.status = 'active' if i.get("state") == 1 else "inactive"
#                     # import pdb; pdb.set_trace()
#                     spice_port = instance.spice_port
#                     if spice_port:
#                         instance.spice_link = ret.get("data", {}).get(spice_port, False)
#                     if instance.classify == constants.PERSONAL_DEKSTOP and (
#                             instance.status == 'inactive' or not instance.spice_link):
#                         instance.allocated = 0
#                     elif instance.classify == constants.PERSONAL_DEKSTOP and instance.status == 'active' and instance.spice_link:
#                         instance.allocated = 1
#
#                     instance.soft_update()
#
#     def run(self):
#         # global threads
#         # if self.name in threads:
#         #     print("%s is running"% self.name)
#         #     return
#         # threads[self.name] = None
#         while True:
#             logger.info("+++++++++++start thread:%s++++++++++++++++++++++", self.name)
#             time.sleep(5)
#
#         # with self.app.app_context():
#         #     while True:
#         #         try:
#         #             logger.info("async start: %s"% self.name)
#         #             self.sync_instance_online_state()
#         #             # print("async start : %s"% (self.name))
#         #         except Exception as e:
#         #             current_app.logger.error("AsyncCleanTaskHandler error:%s" % traceback.format_exc())
#         #         time.sleep(5)
#