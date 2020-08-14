import os
import re
from crontab import CronTab
import traceback
from flask import current_app
import common.errcode as errcode
from yzy_monitor.task_handlers.base_handler import BaseHandler, BaseProcess


class CrontabHandler(BaseHandler):
    def __init__(self):
        super(CrontabHandler, self).__init__()
        self.type = "CrontabHandler"

    def deal(self, task):
        p = CrontabHandlerProcess(task)
        r = p.process()
        return r


class CrontabHandlerProcess(BaseProcess):
    def __init__(self, task):
        super(CrontabHandlerProcess, self).__init__(task)
        self.name = os.path.basename(__file__).split('.')[0]

    def setup_shutdown(self):
        try:
            resp = errcode.get_error_result()
            cron = CronTab(user=True)
            cron_name = self.task.get("data").get("task_name")
            cron_time_minute = int(self.task.get("data").get("exec_minute"))
            cron_time_hour = int(self.task.get("data").get("exec_hour"))
            cron_weekly = str(self.task.get("data").get("exec_weekly"))
            cron_weekly = [x for x in re.findall('\d', cron_weekly) if x in list("01234567")]
            cron_weekly = ','.join(cron_weekly)
            jobs = cron.find_comment('front_end_controller:{}'.format(cron_name))
            for job in jobs:
                job.delete()
            job = cron.new(command='shutdown now', comment='front_end_controller:{}'.format(cron_name))
            job.setall(cron_time_minute, cron_time_hour, '*', '*', cron_weekly)
            cron.write()
            current_app.logger.debug('add crontab: {} success'.format(cron_name))
            return resp
        except Exception as err:
            current_app.logger.error(err)
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    def delete_shutdown(self):
        try:
            resp = errcode.get_error_result()
            cron = CronTab(user=True)
            cron_name = self.task.get("data").get("task_name")
            jobs = cron.find_comment('front_end_controller:{}'.format(cron_name))

            jobs_cnt = len(list(jobs))
            if jobs_cnt >= 1:
                jobs = cron.find_comment('front_end_controller:{}'.format(cron_name))
                for job in jobs:
                    job.delete()
                cron.write()
            else:
                resp = errcode.get_error_result(error="NotFoundCrontabRecord")
                return resp
            current_app.logger.debug('del crontab: {} success'.format(cron_name))
            return resp
        except Exception as err:
            current_app.logger.error(err)
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    def select_shutdown(self):
        try:
            resp = errcode.get_error_result()
            cron = CronTab(user=True)
            cron_name = self.task.get("data").get("task_name")
            jobs = cron.find_comment('front_end_controller:{}'.format(cron_name))
            jobs_cnt = len(list(jobs))
            if jobs_cnt == 1:
                jobs = cron.find_comment('front_end_controller:{}'.format(cron_name))
                resp['data'] = {}
                for job in jobs:
                    job_cmd = str(job).split('#')[0].strip()
                    resp['data']['exec_minute'] = job_cmd.split(' ')[0]
                    resp['data']['exec_hour'] = job_cmd.split(' ')[1]
                    resp['data']['exec_weekly'] = str(job_cmd.split(' ')[4])
            elif jobs_cnt >= 1:
                resp = errcode.get_error_result(error="FoundMultipleCrontabRecord")
                return resp
            else:
                resp = errcode.get_error_result(error="NotFoundCrontabRecord")
                return resp
            current_app.logger.debug('select crontab: {} success'.format(cron_name))
            return resp
        except Exception as err:
            current_app.logger.error(err)
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    def modify_shutdown(self):
        try:
            resp = errcode.get_error_result()
            cron = CronTab(user=True)
            cron_name = self.task.get("data").get("task_name")
            cron_time_minute = int(self.task.get("data").get("exec_minute"))
            cron_time_hour = int(self.task.get("data").get("exec_hour"))
            cron_weekly = str(self.task.get("data").get("exec_weekly"))
            cron_weekly = [x for x in re.findall('\d', cron_weekly) if x in list("01234567")]
            cron_weekly = ','.join(cron_weekly)
            jobs = cron.find_comment('front_end_controller:{}'.format(cron_name))
            jobs_cnt = len(list(jobs))
            if jobs_cnt >= 1:
                jobs = cron.find_comment('front_end_controller:{}'.format(cron_name))
                for job in jobs:
                    job.delete()
                    job = cron.new(command='shutdown now', comment='front_end_controller:{}'.format(cron_name))
                    job.setall(cron_time_minute, cron_time_hour, '*', '*', cron_weekly)
                    cron.write()
            elif len(list(jobs)) == 0:
                # not found
                resp = errcode.get_error_result(error="NotFoundCrontabRecord")
                return resp
            else:
                # multiple corntab jobs
                resp = errcode.get_error_result(error="FoundMultipleCrontabRecord")
                return resp
            current_app.logger.debug('modify crontab: {} success'.format(cron_name))
            return resp
        except Exception as err:
            current_app.logger.error(err)
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

