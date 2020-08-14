import logging
from web_manage.common.log import operation_record
from web_manage.common.errcode import get_error_result
from web_manage.common.http import scheduler_post
from web_manage.yzy_system_mgr import models

logger = logging.getLogger(__name__)


class CrontabTaskManager(object):

    @operation_record("创建桌面定时任务'{param[name]}'", module="crontab")
    def desktop_check(self, param, log_user=None):
        logger.info("create desktop crontab task")
        if models.YzyCrontabTask.objects.filter(name=param['name'], deleted=False, type=1).first():
            logger.error("the name %s already exists", param['name'])
            return get_error_result("CrontabTaskAlreadyExists", name=param['name'])
        ret = scheduler_post("/api/v1/system/crontab_task/instance", param)
        logger.info("create desktop crontab task %s success", param["name"])
        return ret

    @operation_record("创建节点定时任务'{param[name]}'", module="crontab")
    def node_check(self, param, log_user=None):
        logger.info("create node crontab task")
        if models.YzyCrontabTask.objects.filter(name=param['name'], deleted=False, type=2).first():
            logger.error("the name %s already exists", param['name'])
            return get_error_result("CrontabTaskAlreadyExists", name=param['name'])
        ret = scheduler_post("/api/v1/system/crontab_task/node", param)
        logger.info("create node crontab task %s success", param["name"])
        return ret

    @operation_record("创建终端定时任务'{param[name]}'", module="crontab")
    def terminal_check(self, param, log_user=None):
        logger.info("create terminal crontab task")
        if models.YzyCrontabTask.objects.filter(name=param['name'], deleted=False, type=3).first():
            logger.error("the name %s already exists", param['name'])
            return get_error_result("CrontabTaskAlreadyExists", name=param['name'])
        ret = scheduler_post("/api/v1/system/crontab_task/terminal", param)
        logger.info("create terminal crontab task %s success", param["name"])
        return ret

    @operation_record("创建警告日志定时任务'{param[name]}'", module="crontab")
    def warning_check(self, param, log_user=None):
        logger.info("create warning log crontab task")
        ret = scheduler_post("/api/v1/system/crontab_task/log", param)
        logger.info("create warning log crontab task %s success", param["name"])
        return ret

    @operation_record("创建操作日志定时任务'{param[name]}'", module="crontab")
    def operation_check(self, param, log_user=None):
        logger.info("create operation log crontab task")
        ret = scheduler_post("/api/v1/system/crontab_task/log", param)
        logger.info("create operation log crontab task %s success", param["name"])
        return ret

    def delete_crontab_task(self, tasks):
        success_num = 0
        failed_num = 0
        for task in tasks:
            logger.info("delete crontab task, name:%s, uuid:%s", task['name'], task['uuid'])
            if not models.YzyCrontabTask.objects.filter(uuid=task['uuid'], deleted=False):
                logger.info("delete crontab task failed, it is not exists")
                failed_num += 1
                continue
            ret = scheduler_post("/api/v1/system/crontab_task/delete", {"uuid": task['uuid']})
            if ret.get('code') != 0:
                logger.info("delete crontab task:%s", ret['msg'])
                failed_num += 1
            else:
                success_num += 1
                logger.info("delete crontab task success, name:%s", task['name'])
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    @operation_record("更新定时任务'{data[name]}'", module="crontab")
    def update_crontab(self, data, log_user=None):
        logger.info("update crontab task, name:%s, uuid:%s", data['name'], data['uuid'])
        if not models.YzyCrontabTask.objects.filter(uuid=data['uuid'], deleted=False):
            logger.info("update crontab task failed, it is not exists")
            return get_error_result("CrontabTaskNotExists", name=data['name'])
        ret = scheduler_post("/api/v1/system/crontab_task/update", data)
        if ret.get('code') != 0:
            logger.info("update crontab task failed:%s", ret['msg'])
        else:
            logger.info("update crontab task success, name:%s", data['name'])
        return ret

    def database_check(self, param, log_user=None):
        logger.info("add database scheduler begin")
        ret = scheduler_post("/api/v1/system/crontab_task/database", param)
        logger.info("add database scheduler end:%s", ret)
        return ret

    @operation_record("更新定时清除任务'{param[name]}'", module="crontab")
    def operation_update_check(self, param, log_user=None):
        logger.info("update log crontab task name:%s", param['name'])
        detail = models.YzyCrontabDetail.objects.filter(uuid=param['uuid'], deleted=False).first()
        if not models.YzyCrontabTask.objects.filter(uuid=detail.task_uuid, deleted=False):
            logger.info("update log crontab task failed, it is not exists")
            return get_error_result("CrontabTaskNotExists", name=param['name'])
        ret = scheduler_post("/api/v1/system/crontab_task/log_update", param)
        if ret.get('code') != 0:
            logger.info("update crontab task failed:%s", ret['msg'])
        else:
            logger.info("update crontab task success, name:%s", param['name'])
        return ret

    @operation_record("更新定时清除任务'{param[name]}'", module="crontab")
    def warning_update_check(self, param, log_user=None):
        logger.info("update log crontab task name:%s", param['name'])
        detail = models.YzyCrontabDetail.objects.filter(uuid=param['uuid'], deleted=False).first()
        if not models.YzyCrontabTask.objects.filter(uuid=detail.task_uuid, deleted=False):
            logger.info("update log crontab task failed, it is not exists")
            return get_error_result("CrontabTaskNotExists", name=param['name'])
        ret = scheduler_post("/api/v1/system/crontab_task/log_update", param)
        if ret.get('code') != 0:
            logger.info("update crontab task failed:%s", ret['msg'])
        else:
            logger.info("update crontab task success, name:%s", param['name'])
        return ret

