import datetime
import logging
import os
import json
from flask import current_app
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
from yzy_server.database import apis as db_api
from yzy_server.database import models
from yzy_server.extensions import db
from yzy_server.crontab_tasks import YzyAPScheduler
from common import constants
from common.utils import get_error_result, create_uuid, single_lock, terminal_post, compute_post
# from thrift.protocol import TBinaryProtocol, TMultiplexedProtocol
# from thrift.transport import TSocket, TTransport
# from ukey import UKeyServer
# from ukey.ttypes import Registry_Info
from yzy_server.ukey_tcp_client import UkeyClient
from .desktop_ctl import InstanceController, DesktopController
from .node_ctl import NodeController
from yzy_server.utils import read_file_md5, ha_sync_file


logger = logging.getLogger(__name__)
CRONTAB_DB = 0
CRONTAB_DESKTOP = 1
CRONTAB_NODE = 2
CRONTAB_TERMINAL = 3
CRONTAB_LOG = 4
CRONTAB_COURSE_SCHEDULE = 5


class AdminAuthController(object):

    def authorization(self, username, password):
        user = db_api.get_admin_user_first({"username": username})
        if not user:
            logger.error("admin authorization usename %s not exist"% username)
            return get_error_result("UsernameError")
        ret = user.validate_password(password)
        if not ret:
            logger.error("admin authorization %s password error:[%s] "% (user.password, password))
            return get_error_result("LoginFailError")
        logger.info("admin authorization login success !!")
        return get_error_result("Success")


class DatabaseController(object):

    def get_file_size(self, file_path):

        fsize = os.path.getsize(file_path)
        fsize = fsize / float(1024 * 1024)
        return round(fsize, 2)

    def exec_back(self, db_user, db_pwd, db_name, target_file):
        """ 数据库备份 """
        try:
            database_back_path = constants.DATABASE_BACK_PATH
            if not os.path.exists(database_back_path):
                os.makedirs(database_back_path)
            back_file = os.path.join(database_back_path, target_file)
            cmd = "mysqldump -u%s -p%s %s --default_character-set=utf8 > %s" % (db_user, db_pwd, db_name, back_file)
            os.system(cmd)
            return back_file
        except Exception as e:
            logger.error("database back error: %s.sql"% target_file, exc_info=True)
            return False

    def database_back(self, db_user, db_pwd, db_name):
        logger.info("begin to backup database")
        node = db_api.get_controller_node()
        time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        target_file = "%s.bak" % time_stamp
        back_file = self.exec_back(db_user, db_pwd, db_name, target_file)
        md5_sum = ""
        status = 0
        if not back_file:
            logger.error("request database back fail")
            status = 1
            # return get_error_result("DatabaseBackFail")
        else:
            md5_sum = read_file_md5(back_file)

        values = {
            "name": target_file,
            "type": 0,
            "path": back_file,
            "size": self.get_file_size(back_file),
            "node_uuid": node.uuid,
            "status": status,
            "md5_sum": md5_sum
        }
        try:
            db_api.create_database_back(values)
            logger.info("database back [%s] success", back_file)
        except Exception as e:
            logging.info("database back failed:%s", e)
            return get_error_result("DatabaseBackFail")
        return get_error_result("Success", data={"path": back_file})

    def delete_backup(self, data):
        backup_id = data.get("id", '')
        backup = db_api.get_database_backup_first({"id": backup_id})
        if not backup:
            return get_error_result("DatabaseBackNotExist", name=data["name"])
        try:
            os.remove(backup.path)
        except:
            pass
        backup.soft_delete()
        logger.info("delete the backup success, id:%s", backup_id)
        return get_error_result("Success")


class CrontabController(object):
    """
    {
        "count": 10,
        "node_uuid": "xxxxxxxxxx",
        "node_name": "name",
        "status": 0,
        "cron": {
            "type": "day",			# week, month
            "values": [1,2,3,4,5,6,7]
            "hour": 1,
            "minute": 10
        },
        "data": ["xxxxxxxxxxxxxx", "xxxxxxxxxxx", "xxxxxxxxxxxxxx"]
    }
    """

    def run_task(self, app):
        # 查询数据库的crontab信息 -> 定时任务信息
        with app.app_context():
            res = db_api.get_crontab_tasks()
            # 遍历添加任务
            shche = YzyAPScheduler()
            for rs in res:
                if 1 == rs.status:
                    detail = db_api.get_crontab_detail_all({"task_uuid": rs.uuid})
                    for item in detail:
                        params = dict()
                        params["hour"] = item.hour
                        params["minute"] = item.minute
                        cycle = item.cycle
                        if cycle == "week":
                            params["day_of_week"] = item.values
                            # weeks = rs.values.split(",")
                            # if len(set(weeks)) == 7:
                            #     params["day_of_week"] = "0-6"
                            # else:
                            #     params["day_of_week"] = ",".join(list(set(weeks)))
                        elif cycle == "month":
                            params["day"] = item.values if item.values else constants.SCHEDULER_MONTH_DAY
                        elif cycle == "course":
                            params = json.loads(item.values)
                        else:
                            pass
                        kwargs = json.loads(item.params)
                        # 如果是数据库定时任务，在这里把用户名和密码传进去
                        if 0 == rs.type:
                            kwargs["db_user"] = app.config.get("DATABASE_USER", "")
                            kwargs["db_password"] = app.config.get("DATABASE_PASSWORD", "")
                            kwargs["db_name"] = app.config.get("DATABASE_NAME", "")
                        func = getattr(self, item.func)

                        # 如果是课表定时任务，需要使用OrTrigger
                        if rs.type == 5:
                            cron_trigger_list = list()
                            for cron_dict in params["cron"]:
                                cron_trigger_list.append(CronTrigger(
                                    start_date=params["start_date"],
                                    end_date=params["end_date"],
                                    hour=cron_dict["hour"],
                                    minute=cron_dict["minute"]
                                ))
                            trigger = OrTrigger(cron_trigger_list)
                        else:
                            trigger = CronTrigger(**params)
                        shche.add_job(jobid=item.uuid, func=func, trigger=trigger, kwargs=kwargs)
                        logger.info("add crontab work, func:%s, params:%s", func.__name__, params)

    def check_cron(self, cron_dict):
        """ 检测cron 参数"""
        logger.info("start check cron dict: %s", cron_dict)
        if not cron_dict or not isinstance(cron_dict, dict):
            logger.error("cron dict error")
            return False
        _type = cron_dict.get("type")
        if _type not in ("day", "week", "month"):
            logger.error("cron dict type error")
            return False
        values = cron_dict.get("values", [])
        day_of_week = None
        if _type == "week":
            values = list(set(values))
            if not values or not isinstance(values, list):
                return False
            if any([i not in range(0, 7) for i in values]):
                return False
            day_of_week = ",".join([str(i) for i in values])
        hour = cron_dict.get("hour")
        if hour not in range(0, 24):
            return False
        minute = cron_dict.get("minute")
        if minute not in range(0, 60):
            return False
        kwargs = dict()
        kwargs["hour"] = cron_dict.get("hour")
        kwargs["minute"] = cron_dict.get("minute")
        if day_of_week:
            kwargs["day_of_week"] = day_of_week
        else:
            if _type == "month":
                kwargs["day"] = cron_dict.get('day', constants.SCHEDULER_MONTH_DAY)
        logger.info("convert cron to kwargs: %s", kwargs)
        return kwargs

    def to_date(self, cycle):
        today = datetime.datetime.today()
        if cycle == 'day':
            date = today
        elif cycle == 'week':
            date = today - datetime.timedelta(days=7)
        elif cycle == 'month':
            date = today - datetime.timedelta(days=30)
        else:
            date = today
        return date

    def database_back(self, db_user, db_pwd, db_name):
        time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        target_file = "%s.bak" % time_stamp
        back_file = DatabaseController().exec_back(db_user, db_pwd, db_name, target_file)
        if not back_file:
            logger.error("request database back fail")
            return False
        # 查找主控节点
        node = db_api.get_controller_node()
        if not node:
            logger.error("request database back fail ,not controller node")
            return False
        values = {
            "name": target_file,
            "type": 1,
            "path": back_file,
            "size": DatabaseController().get_file_size(back_file),
            "node_uuid": node.uuid,
            "md5_sum": read_file_md5(back_file)
        }
        try:
            # 如果启用了HA，把数据库备份文件同步给备控，未启用则不同步
            ha_sync_file([{"path": back_file}])
            db_api.create_database_back(values)
            logger.info("database back [%s] success", back_file)
        except Exception as e:
            logging.info("database back failed:%s", e)
            return False
        return True

    # @single_lock
    # def database_back_func_with_lock(self, **kwargs):
    #     self.database_back_func(**kwargs)

    def database_back_func(self, count, db_user, db_password, db_name, **kwargs):
        """ 数据库备份 """
        logger.info("database back exec: %s ", kwargs)
        try:
            result = self.database_back(db_user=db_user, db_pwd=db_password, db_name=db_name)
            if result:
                backups = db_api.get_database_backup_all({})
                if len(backups) > count:
                    for backup in backups[:-count]:
                        logger.info("delete backup %s", backup.name)
                        try:
                            os.remove(backup.path)
                        except:
                            pass
                        backup.soft_delete()
        except Exception as e:
            logger.error("database back exec fail: %s", e)
        logger.info("database back exec success !!!")

    # @single_lock
    # def instance_crontab_func_with_lock(self, **kwargs):
    #     self.instance_crontab_func(**kwargs)

    def instance_crontab_func(self, cmd, data, task_uuid):
        """ 桌面定时任务 """
        logger.info("instance crontab exec: %s start", cmd)
        task_obj = db_api.get_task_info_first({"task_uuid": task_uuid})
        task_obj.update({"status": constants.TASK_RUNNING})
        task_obj.soft_update()
        for item in data:
            if "on" == cmd:
                InstanceController().start_instances(item)
            elif "off" == cmd:
                InstanceController().stop_instances(item)
            else:
                logger.error("invalid cmd:%s", cmd)
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
        logger.info("exec instances crontab task success")
        task_obj.update({"status": constants.TASK_COMPLETE})
        task_obj.soft_update()
        return

    # @single_lock
    # def node_crontab_func_with_lock(self, **kwargs):
    #     self.node_crontab_func(**kwargs)

    def node_crontab_func(self, cmd, data, task_uuid):
        """ 节点定时任务 """
        logger.info("node crontab exec: %s start", cmd)
        task_obj = db_api.get_task_info_first({"task_uuid": task_uuid})
        task_obj.update({"status": constants.TASK_RUNNING})
        task_obj.soft_update()
        for item in data:
            if "off" == cmd:
                from yzy_server import create_app
                app = create_app()
                with app.app_context():
                    NodeController().shutdown_node(item['uuid'])
            else:
                logger.error("invalid cmd:%s", cmd)
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
        logger.info("exec node crontab task success")
        task_obj.update({"status": constants.TASK_COMPLETE})
        task_obj.soft_update()
        return

    # @single_lock
    # def terminal_crontab_func_with_lock(self, **kwargs):
    #     self.terminal_crontab_func(**kwargs)

    def terminal_crontab_func(self, cmd, data, task_uuid):
        """ 终端定时任务 """
        logger.info("terminal crontab exec %s start", cmd)
        task_obj = db_api.get_task_info_first({"task_uuid": task_uuid})
        task_obj.update({"status": constants.TASK_RUNNING})
        task_obj.soft_update()
        mac_list = []
        for item in data:
            mac_list.append(item['mac'])
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "shutdown",
            "data": {
                "mac_list": ','.join(mac_list),
            }
        }
        if cmd == "off":
            logger.info("terminal task off, req_data:%s", req_data)
            ret = terminal_post("/api/v1/terminal/task", req_data)
            logger.info("terminal task end, ret:%s", ret)
            # if disposable:
            #     task = db_api.get_crontab_first({"type": 3})
            #     detail = db_api.get_crontab_detail_first({"task_uuid": task.uuid})
            #     date = datetime.datetime.today()
            #     week_values = detail.values.split(',')
            #     week_values.remove(str(date.weekday()))
            #     detail.values = ','.join(week_values)
            #     detail.soft_update()
        else:
            logger.error("invalid cmd:%s", cmd)
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()

        logger.info("exec node crontab task success")
        task_obj.update({"status": constants.TASK_COMPLETE})
        task_obj.soft_update()
        return

    # @single_lock
    # def log_crontab_func_with_lock(self, **kwargs):
    #     self.log_crontab_func(**kwargs)

    def log_crontab_func(self, name, data):
        """ 日志定时清除 """
        logger.info("log crontab exec start")
        date = self.to_date(data)
        if name == "operation_log_cron":
            logs = db_api.get_operation_log_all(date)
        elif name == "warning_log_cron":
            logs = db_api.get_warning_log_all(date)
        else:
            logs = []
            logger.error("invalid name:%s", name)
        for log in logs:
            log.deleted = 1
            db.session.flush()

    def database_back_crontab(self, params):
        """添加一个crontab任务"""
        logger.info("params:%s", params)
        count = params.get("count")
        node_uuid = params.get("node_uuid")
        status = params.get("status", 0)
        cron_dict = params.get("cron", {})
        # 判断node
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            logger.error("add database back crontab fail, node: %s not exist", node_uuid)
            return get_error_result("NodeNotExist")
        # 如果是禁用，则直接返回
        database_crontab = db_api.get_crontab_first({'type': 0})
        if database_crontab:
            detail = db_api.get_crontab_detail_first({"task_uuid": database_crontab.uuid})
            if not detail:
                return get_error_result("CrontabTaskNotExists", name='db_backup')
        if 0 == status:
            if database_crontab:
                YzyAPScheduler().remove_job(detail.uuid)
                database_crontab.status = status
                database_crontab.soft_update()
                if detail:
                    detail.params = json.dumps({"count": count, "node_uuid": node_uuid})
                    detail.soft_update()
            else:
                task_uuid = create_uuid()
                task = {
                    "uuid": task_uuid,
                    "desc": params.get("desc", ""),
                    "name": "db_back_task:%s" % datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
                    "type": CRONTAB_DB,
                    "status": status
                }
                detail_value = {
                    "uuid": create_uuid(),
                    "task_uuid": task_uuid,
                    "func": "database_back_func",
                    "params": json.dumps({"count": count, "node_uuid": node_uuid}),
                }
                db_api.create_crontab_task(task)
                db_api.create_crontab_detail(detail_value)
                logger.info("add database back task success")
            return get_error_result("Success")

        job_kwargs = self.check_cron(cron_dict)
        if not job_kwargs:
            logger.error("cron dict check error")
            return get_error_result("ParamError")

        if not database_crontab:
            task_uuid = create_uuid()
            job_id = create_uuid()
        else:
            task_uuid = database_crontab.uuid
            job_id = detail.uuid
        try:
            _kwargs = dict()
            _kwargs["db_user"] = current_app.config.get("DATABASE_USER", "")
            _kwargs["db_password"] = current_app.config.get("DATABASE_PASSWORD", "")
            _kwargs["db_name"] = current_app.config.get("DATABASE_NAME", "")
            _kwargs["node_uuid"] = node_uuid
            _kwargs["count"] = count
            trigger = CronTrigger(**job_kwargs)
            YzyAPScheduler().add_job(jobid=job_id, trigger=trigger, func=self.database_back_func, kwargs=_kwargs)
        except Exception as e:
            logger.error("add database back crontab fail:%s", e, exc_info=True)
            return get_error_result("DatabaseBackCrontabError")
        # 下面只获取要更新的值
        task_value = {
            "desc": params.get("desc", ""),
            "status": status
        }
        detail_value = {
            "hour": cron_dict["hour"],
            "minute": cron_dict["minute"],
            "cycle": cron_dict["type"],
            "values": job_kwargs.get("day_of_week", "") if cron_dict["type"] == "week" else job_kwargs.get("day"),
            "params": json.dumps({"count": count, "node_uuid": node_uuid})
        }
        if not database_crontab:
            try:
                task_value["name"] = "db_back_task:%s" % datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                task_value["type"] = CRONTAB_DB
                task_value["uuid"] = task_uuid
                detail_value["uuid"] = job_id
                detail_value["task_uuid"] = task_uuid
                detail_value["func"] = "database_back_func"
                db_api.create_crontab_task(task_value)
                db_api.create_crontab_detail(detail_value)
                logger.info("add database back task success")
                return get_error_result("Success")
            except Exception as e:
                logger.error("add database back task %s error: %s", job_id, e)
                YzyAPScheduler().remove_job(job_id)
                return get_error_result('DatabaseBackCrontabError')
        database_crontab.update(task_value)
        database_crontab.soft_update()
        detail.update(detail_value)
        detail.soft_update()
        logger.info("update database back task success")
        return get_error_result("Success")

    def add_instance_crontab(self, params):
        """
        桌面定时任务
        {
            "name": "定时任务名称",
            "desc": "定时任务描述",
            "status": 1,
            "cron": [
                {
                    "cmd": "on",
                    "type": "week",
                    "values": [0,1,2],
                    "hour": 8,
                    "minute": 58
                },
                {
                    "cmd": "off",
                    "type": "week",
                    "values": [0,1,2],
                    "hour": 8,
                    "minute": 58
                }
            ],
            "data": [
                {
                    "desktop_uuid": "4c41b1dc-35d6-11ea-bc23-000c295dd728",
                    "desktop_name": "1",
                    "instances": [
                            {
                                "uuid": "228d4d69-73b8-4694-836b-b2eeeec64c46",
                                "name": "pc01"
                            },
                            {
                                "uuid": "e7269662-0fd8-4e1f-b933-e614016294c2",
                                "name": "pc02"
                            },
                            ...
                        ]
                },
                ...
            ]
        }
        """
        cron_list = params.get("cron", [])
        status = params.get("status", 1)
        task_uuid = create_uuid()
        # 添加任务信息记录
        task_data = {
            "uuid": create_uuid(),
            "task_uuid": task_uuid,
            "name": constants.NAME_TYPE_MAP[10],
            "status": constants.TASK_QUEUE,
            "type": 10
        }
        db_api.create_task_info(task_data)

        if 0 == status:
            task_value = {
                "uuid": task_uuid,
                "name": params["name"],
                "type": CRONTAB_DESKTOP,
                "desc": params.get("desc", ""),
                "status": status
            }
            db_api.create_crontab_task(task_value)
            logger.info("add instance crontab task success")
            return get_error_result("Success")

        # 判断提交的桌面uuid列表是否都存在
        logger.info("check if instance exist")
        _data = params.get("data", [])
        item = dict()
        instances = db_api.get_instance_with_all(item)
        _instance_uuids = list()
        for instance in instances:
            _instance_uuids.append(instance.uuid)

        for item in _data:
            for instance in item['instances']:
                if instance['uuid'] not in _instance_uuids:
                    logger.error("add instance crontab error, uuid: %s not exist", instance['uuid'])
                    return get_error_result("InstanceNotExist", name=instance['name'])
        logger.info("start add instance crontab task")
        # task_uuid = create_uuid()
        task_value = {
            "uuid": task_uuid,
            "name": params["name"],
            "desc": params.get("desc", ""),
            "type": CRONTAB_DESKTOP,
            "status": status
        }
        for cron_dict in cron_list:
            job_kwargs = self.check_cron(cron_dict)
            if not job_kwargs:
                logger.error("cron dict check error")
                return get_error_result("ParamError")
            job_id = create_uuid()
            _kwargs = {
                "cmd": cron_dict["cmd"],
                "data": _data,
                "task_uuid": task_uuid
            }
            try:
                trigger = CronTrigger(**job_kwargs)
                YzyAPScheduler().add_job(jobid=job_id, trigger=trigger, func=self.instance_crontab_func,
                                         kwargs=_kwargs)
            except Exception as e:
                logger.error("add instance %s crontab failed:%s", cron_dict["cmd"], e, exc_info=True)
                return get_error_result("AddInstanceCrontabError")

            # 添加到数据库
            detail_value = {
                "uuid": job_id,
                "task_uuid": task_uuid,
                "hour": cron_dict["hour"],
                "minute": cron_dict["minute"],
                "cycle": cron_dict["type"],
                "values": job_kwargs.get("day_of_week", "") if cron_dict["type"] == "week" else job_kwargs.get("day"),
                "func": "instance_crontab_func",
                "params": json.dumps(_kwargs)
            }
            try:
                db_api.create_crontab_detail(detail_value)
                logger.info("add instances %s crontab task success", cron_dict["cmd"])
            except Exception as e:
                logger.error("add instances %s crontab task error: %s", cron_dict["cmd"], e)
                YzyAPScheduler().remove_job(job_id)
                return get_error_result('AddInstanceCrontabError')
        db_api.create_crontab_task(task_value)
        return get_error_result("Success")

    def add_node_crontab(self, params):
        """
        节点定时任务
        {
            "name": "定时任务名称",
            "desc": "定时任务描述",
            "status": 0,
            "cron": [
                {
                    "cmd": "on",
                    "type": "day",			# week, month
                    "values": [1,2,3,4,5,6,7]
                    "hour": 1,
                    "minute": 10
                },
                ...
            ]
            "data": [
                {
                    "uuid": "",
                    "name": ""
                },
                ...
            ]
        }
        """
        cmd = params.get("cmd", "")
        cron_list = params.get("cron", [])
        status = params.get("status", 1)
        task_uuid = create_uuid()
        # 添加任务信息数据记录
        task_data = {
            "uuid": create_uuid(),
            "task_uuid": task_uuid,
            "name": constants.NAME_TYPE_MAP[11],
            "status": constants.TASK_QUEUE,
            "type": 11
        }
        db_api.create_task_info(task_data)
        if 0 == status:
            value = {
                "uuid": task_uuid,
                "name": params["name"],
                "type": CRONTAB_NODE,
                "status": status
            }
            db_api.create_crontab_task(value)
            logger.info("add node crontab task success")
            return get_error_result("Success")

        # 判断提交的节点信息是否都存在
        _data = params.get("data", [])
        nodes = db_api.get_node_with_all({})
        nodes_uuid = list()
        for node in nodes:
            nodes_uuid.append(node.uuid)
        for item in _data:
            if item['uuid'] not in nodes_uuid:
                logger.error("add node crontab error, node: %s not exist", item['uuid'])
                return get_error_result("NodeNotExistMsg", hostname=item['name'])

        logger.info("start add node crontab task")
        # task_uuid = create_uuid()
        # 添加到数据库
        task_value = {
            "uuid": task_uuid,
            "name": params['name'],
            "desc": params.get('desc', ''),
            "type": CRONTAB_NODE,
            "status": status
        }
        for cron_dict in cron_list:
            job_kwargs = self.check_cron(cron_dict)
            if not job_kwargs:
                logger.error("cron dict check error")
                return get_error_result("ParamError")

            job_id = create_uuid()
            _kwargs = {
                "cmd": cmd,
                "data": _data,
                "task_uuid": task_uuid
            }
            try:
                trigger = CronTrigger(**job_kwargs)
                YzyAPScheduler().add_job(jobid=job_id, trigger=trigger, func=self.node_crontab_func, kwargs=_kwargs)
            except Exception as e:
                logger.error("add node %s crontab failed:%s", cmd, e, exc_info=True)
                return get_error_result("AddNodeCrontabError")

            detail_value = {
                "uuid": job_id,
                "task_uuid": task_uuid,
                "hour": cron_dict["hour"],
                "minute": cron_dict["minute"],
                "cycle": cron_dict["type"],
                "values": job_kwargs.get("day_of_week", "") if cron_dict["type"] == "week" else job_kwargs.get("day"),
                "func": "node_crontab_func",
                "params": json.dumps(_kwargs)
            }
            try:
                db_api.create_crontab_detail(detail_value)
                logger.info("add node %s crontab task success", cmd)
            except Exception as e:
                logger.error("add node %s crontab task error: %s", cmd, e)
                YzyAPScheduler().remove_job(job_id)
                return get_error_result('AddNodeCrontabError')
        db_api.create_crontab_task(task_value)
        return get_error_result()

    def add_terminal_crontab(self, data):
        cmd = data.get("cmd", '')
        status = data.get("status", 1)
        cron_list = data.get("cron", [])
        task_uuid = create_uuid()
        # 添加任务信息数据记录
        task_data = {
            "uuid": create_uuid(),
            "task_uuid": task_uuid,
            "name": constants.NAME_TYPE_MAP[12],
            "status": constants.TASK_QUEUE,
            "type": 12
        }
        db_api.create_task_info(task_data)

        if status == 0:
            task_data = {
                "uuid": task_uuid(),
                "name": data["name"],
                "desc": data["desc"],
                "status": status,
                "type": CRONTAB_TERMINAL
            }
            db_api.create_crontab_task(task_data)
            logger.info("add terminal crontab task success")
            return get_error_result("Success")

        _data = data.get('data', [])
        for item in _data:
            if not db_api.get_terminal_with_all({"mac": item["mac"]}):
                logger.error("add terminal crontab error, terminal: %s not exist", item["mac"])
                return get_error_result("AddTerminalCrontabError")

        logger.info("start add terminal crontab task")
        # task_uuid = create_uuid()
        task_data = {
            "uuid": task_uuid,
            "name": data['name'],
            "type": CRONTAB_TERMINAL,
            "desc": data['desc'],
            "status": status
        }
        for cron_dict in cron_list:
            job_kwargs = self.check_cron(cron_dict)
            if not job_kwargs:
                logger.error("cron dict check error")
                return get_error_result("ParamError")

            job_id = create_uuid()
            _kwargs = {
                "cmd": cmd,
                "data": _data,
                "task_uuid": task_uuid
            }
            try:
                trigger = CronTrigger(**job_kwargs)
                YzyAPScheduler().add_job(jobid=job_id, trigger=trigger, func=self.terminal_crontab_func, kwargs=_kwargs)
            except Exception as e:
                logger.error("add terminal %s crontab failed:%s", cmd, e, exc_info=True)
                return get_error_result("AddTerminalCrontabError")

            detail_data = {
                "uuid": job_id,
                "task_uuid": task_uuid,
                "hour": cron_dict["hour"],
                "minute": cron_dict["minute"],
                "cycle": cron_dict["type"],
                "values": job_kwargs.get("day_of_week", "") if cron_dict["type"] == "week" else job_kwargs.get("day"),
                "func": "terminal_crontab_func",
                "params": json.dumps(_kwargs)
            }
            try:
                db_api.create_crontab_detail(detail_data)
                logger.info("add terminal %s crontab task success", cmd)
            except Exception as e:
                YzyAPScheduler().remove_job(job_id)
                logger.error("add terminal %s crontab task error:%s", cmd, e, exc_info=True)
                return get_error_result("AddTerminalCrontabError")
        db_api.create_crontab_task(task_data)
        return get_error_result()

    def add_log_crontab(self, data):
        """
        添加操作日志、警告日志定时清理任务
        :param data:
        :return:
        """
        cron = db_api.get_crontab_first({"name": data["name"]})
        status = data.get('status', 1)
        cron_dict = data.get('cron', '')
        if cron:
            return get_error_result("CrontabTaskAlreadyExists", name=cron.name)
        job_kwargs = self.check_cron(cron_dict)
        if not job_kwargs:
            logger.error("cron dict check error")
            return get_error_result("ParamError")
        _kwargs = {
            "name": data['name'],
            "data": cron_dict['type']
        }
        uuid = create_uuid()
        if status != 0:
            try:
                trigger = CronTrigger(**job_kwargs)
                YzyAPScheduler().add_job(jobid=uuid, trigger=trigger, func=self.log_crontab_func, kwargs=_kwargs)
            except Exception as e:
                logger.error("create warning log crontab fail:%s", e, exc_info=True)
                return get_error_result("AddWarningLogCronError")
        cron_task_data = {
            "uuid": uuid,
            "name": data['name'],
            "type": CRONTAB_LOG,
            "status": status,
        }
        cron_detail_data = {
            "uuid": create_uuid(),
            "task_uuid": uuid,
            "hour": cron_dict['hour'],
            "minute": cron_dict['minute'],
            "cycle": cron_dict['type'],
            "values": job_kwargs.get("day_of_week", "") if cron_dict["type"] == "week" else job_kwargs.get("day"),
            "func": 'log_crontab_func',
            "params": json.dumps(_kwargs)
        }
        try:
            db_api.create_crontab_task(cron_task_data)
            db_api.create_crontab_detail(cron_detail_data)
            logger.info("create warning log crontab success")
            return get_error_result("Success")
        except Exception as e:
            logger.error("create warning log crontab fail")
            YzyAPScheduler().remove_job(uuid)
            return get_error_result("AddWarningLogCronError")

    def update_log_crontab(self, data):
        cron = db_api.get_crontab_first({"name": data["name"]})
        status = data.get('status', '')
        cron_dict = data.get('cron', '')
        if status == 0:
            YzyAPScheduler().remove_job(cron.uuid)
            cron.status = status
            cron.soft_update()
            return get_error_result("Success")
        job_kwargs = self.check_cron(cron_dict)
        if not job_kwargs:
            logger.error("cron dict check error")
            return get_error_result("ParamError")
        _kwargs = {
            "name": data['name'],
            "data": cron_dict['type']
        }
        try:
            trigger = CronTrigger(**job_kwargs)
            YzyAPScheduler().add_job(jobid=cron.uuid, trigger=trigger, func=self.log_crontab_func, kwargs=_kwargs)
        except Exception as e:
            logger.error("update warning log crontab fail:%s", e, exc_info=True)
            return get_error_result("UpdateWarningLogCronError")
        try:
            detail = db_api.get_crontab_detail_first({"task_uuid": cron.uuid})
            detail_values = {
                "hour": cron_dict['hour'],
                "minute": cron_dict['minute'],
                "cycle": cron_dict['type'],
                "values": job_kwargs.get("day_of_week", "") if cron_dict["type"] == "week" else job_kwargs.get(
                    "day"),
                "params": json.dumps(_kwargs)
            }
            cron.update({"status": status})
            detail.update(detail_values)
            cron.soft_update()
            detail.soft_update()
            logger.info("update warning log crontab success")
            return get_error_result("Success")
        except Exception as e:
            logger.error("update warning log crontab fail:%s", e, exc_info=True)
            YzyAPScheduler().remove_job(cron.uuid)
            return get_error_result("UpdateWarningLogCronError")

    def update_crontab_task(self, data):
        try:
            update_value = data['value']
            # 目前定时任务固定最多就2条
            task = db_api.get_crontab_first({"uuid": data["uuid"]})
            if not task:
                return get_error_result("CrontabTaskNotExists", name=data.get("name", ""))
            detail = db_api.get_crontab_detail_all({"task_uuid": data["uuid"]})
            # 如果未启用，则删除所有定时任务
            if 0 == update_value['status']:
                for item in detail:
                    YzyAPScheduler().remove_job(item.uuid)

            _data = update_value.get("data", [])
            # 查找修改和删除的
            for item in detail:
                find = False
                for cron_dict in update_value.get('cron', []):
                    job_kwargs = self.check_cron(cron_dict)
                    if not job_kwargs:
                        logger.error("cron dict check error")
                        continue
                    # 查找到则直接进行替换，不管有没有修改
                    if cron_dict.get('uuid') and cron_dict['uuid'] == item.uuid:
                        find = True
                        _kwargs = {
                            "cmd": cron_dict['cmd'],
                            "data": _data,
                            "task_uuid": data["uuid"]
                        }
                        # 只有启动情况下才替换实际任务
                        if update_value['status'] != 0:
                            try:
                                func = getattr(self, item.func)
                                trigger = CronTrigger(**job_kwargs)
                                YzyAPScheduler().add_job(jobid=cron_dict['uuid'], trigger=trigger,
                                                         func=func, kwargs=_kwargs)
                            except Exception as e:
                                logger.error("add instance %s crontab failed:%s", cron_dict['cmd'], e, exc_info=True)
                                continue
                        detail_value = {
                            "hour": cron_dict["hour"],
                            "minute": cron_dict["minute"],
                            "cycle": cron_dict["type"],
                            "values": job_kwargs.get("day_of_week", "") if cron_dict["type"] == "week" else job_kwargs.get("day"),
                            "params": json.dumps(_kwargs)
                        }
                        item.update(detail_value)
                        item.soft_update()
                        logger.info("update crontab %s task success", item.uuid)
                        break
                # 没有查找到，则删除这条定时任务
                if not find:
                    YzyAPScheduler().remove_job(item.uuid)
                    item.soft_delete()
                    logger.info("delete crontab task %s", item.uuid)
            # 查找增加的
            for cron_dict in update_value.get('cron', []):
                if not cron_dict.get('uuid'):
                    job_kwargs = self.check_cron(cron_dict)
                    if not job_kwargs:
                        logger.error("cron dict check error")
                        continue
                    _kwargs = {
                        "cmd": cron_dict['cmd'],
                        "data": _data,
                        "task_uuid": data["uuid"]
                    }
                    detail_uuid = create_uuid()
                    if 1 == task.type:
                        func = self.instance_crontab_func
                    elif 2 == task.type:
                        func = self.node_crontab_func
                    else:
                        func = self.terminal_crontab_func
                    # 只有启动情况下才添加实际任务
                    if update_value['status'] != 0:
                        try:
                            trigger = CronTrigger(**job_kwargs)
                            YzyAPScheduler().add_job(jobid=detail_uuid, trigger=trigger, func=func, kwargs=_kwargs)
                        except Exception as e:
                            logger.error("add instance %s crontab failed:%s", cron_dict['cmd'], e, exc_info=True)
                            continue
                    detail_value = {
                        "uuid": detail_uuid,
                        "task_uuid": task.uuid,
                        "hour": cron_dict["hour"],
                        "minute": cron_dict["minute"],
                        "cycle": cron_dict["type"],
                        "values": job_kwargs.get("day_of_week", "") if cron_dict["type"] == "week" else job_kwargs.get("day"),
                        "func": func.__name__,
                        "params": json.dumps(_kwargs)
                    }
                    db_api.create_crontab_detail(detail_value)
                    logger.info("add crontab task, task_uuid:%s, detail:%s", task.uuid, detail_uuid)
            task_value = {
                "name": update_value["name"],
                "status": update_value['status'],
                "desc": update_value.get("desc", ""),
            }
            task.update(task_value)
            task.soft_update()
        except Exception as e:
            logger.error("update crontab task %s error:%s", data.get("name", ""), e)
            return get_error_result("CrontabUpdateError", info="")
        return get_error_result("Success")

    def delete_crontab_task(self, task_uuid):
        try:
            task = db_api.get_crontab_first({"uuid": task_uuid})
            detail = db_api.get_crontab_detail_all({"task_uuid": task_uuid})
            for item in detail:
                YzyAPScheduler().remove_job(item.uuid)
                item.soft_delete()
            task.soft_delete()
            logger.info("delete crontab task %s success", task_uuid)
        except Exception as e:
            logger.error("delete crontab task error:%s", e)
            return get_error_result("CrontabDeleteError")
        return get_error_result("Success")


    def rollback_course_schedule_crontab(self, task_uuid, job_uuid):
        try:
            YzyAPScheduler().remove_job(job_uuid)
        except Exception:
            pass

        task_obj = db_api.get_crontab_first({"uuid": task_uuid})
        if task_obj:
            task_obj.soft_delete()

        detail_obj = db_api.get_crontab_detail_first({"uuid": job_uuid})
        if detail_obj:
            detail_obj.soft_delete()

        logger.info("rollback task_uuid[%s], job_uuid[%s] success" % (task_uuid, job_uuid))


    def course_schedule_crontab_func(self, term_uuid, crontab_time_list, weeks_num_map, job_uuid):
        """ 课表定时任务 """
        if not db_api.get_crontab_detail_first({"uuid": job_uuid}):
            logger.info("no job_uuid[%s] in yzy_crontab_detail, return" % job_uuid)
            return

        logger.info("course_schedule crontab exec job_uuid[%s]: start" % job_uuid)

        try:
            now = datetime.datetime.today()
            # 找出今天所在周的所有教学分组的启用课表
            for k, v in weeks_num_map.items():
                week_start_obj = datetime.datetime.strptime(v[0], "%Y/%m/%d")
                week_end_obj = datetime.datetime.strptime(v[1], "%Y/%m/%d")
                if week_start_obj <= now <= week_end_obj:
                    cs_obj_list = db_api.get_course_schedule_with_all({
                        "term_uuid": term_uuid,
                        "week_num": int(k),
                        "status": constants.COURSE_SCHEDULE_ENABLED
                    })

                    if cs_obj_list:
                        logger.info("this week course_schedule count: %d" % len(cs_obj_list))
                    else:
                        logger.info("this week course_schedule count: 0")

                    for cs_obj in cs_obj_list:
                        logger.info("this week course_schedule_uuid[%s], group_uuid[%s]" % (cs_obj.uuid, cs_obj.group_uuid))
                        # 查找该教学分组课表下今天本节是否有课
                        for _d in crontab_time_list:
                            if now.hour == _d["hour"] and now.minute == _d["minute"]:
                                course_obj = db_api.get_course_with_first({
                                    "course_template_uuid": cs_obj.course_template_uuid,
                                    "weekday": now.isoweekday(),
                                    "course_num": int(_d["course_num"])
                                })
                                logger.info("this course_num[%s], cmd_dict: %s, course: %s" % (str(_d["course_num"]), _d, course_obj))
                                # 如果今天本节有课，根据当前是上课时间（active），还是下课时间（inactive），执行对应操作
                                if course_obj:
                                    if _d["cmd"] == "active":
                                        try:
                                            DesktopController().active_desktop(course_obj.desktop_uuid)
                                            DesktopController().start_desktop(course_obj.desktop_uuid)
                                            logger.info("active course_schedule success: uuid[%s] term_uuid[%s] group_uuid[%s] "
                                                        "course_template_uuid[%s] week_num[%s] weekday[%s] course_num[%s]" %
                                                        (cs_obj.uuid, cs_obj.term_uuid, cs_obj.group_uuid, cs_obj.course_template_uuid,
                                                         cs_obj.week_num, course_obj.weekday, course_obj.course_num))
                                        except Exception as e:
                                            logger.error("active course_schedule failed: uuid[%s] term_uuid[%s] group_uuid[%s] "
                                                        "course_template_uuid[%s] week_num[%s] weekday[%s] course_num[%s]: %s" %
                                                        (cs_obj.uuid, cs_obj.term_uuid, cs_obj.group_uuid, cs_obj.course_template_uuid,
                                                         cs_obj.week_num, course_obj.weekday, course_obj.course_num, str(e)))

                                    elif _d["cmd"] == "inactive":
                                        try:
                                            DesktopController().inactive_desktop(course_obj.desktop_uuid)
                                            logger.info("inactive course_schedule success: uuid[%s] term_uuid[%s] group_uuid[%s] "
                                                        "course_template_uuid[%s] week_num[%s] weekday[%s] course_num[%s]" %
                                                        (cs_obj.uuid, cs_obj.term_uuid, cs_obj.group_uuid, cs_obj.course_template_uuid,
                                                         cs_obj.week_num, course_obj.weekday, course_obj.course_num))
                                        except Exception as e:
                                            logger.error("inactive course_schedule failed: uuid[%s] term_uuid[%s] group_uuid[%s] "
                                                        "course_template_uuid[%s] week_num[%s] weekday[%s] course_num[%s]: %s" %
                                                        (cs_obj.uuid, cs_obj.term_uuid, cs_obj.group_uuid, cs_obj.course_template_uuid,
                                                         cs_obj.week_num, course_obj.weekday, course_obj.course_num, str(e)))
                                    else:
                                        logger.error("invalid cmd:%s", _d["cmd"])

            logger.info("exec course_schedule crontab task job_uuid[%s] success" % job_uuid)
        except Exception as e:
            logger.error("exec course_schedule crontab task job_uuid[%s] failed: %s" % (job_uuid, str(e)))
        return

    def check_course_schedule_crontab(self, cron_dict):
        pass

    def add_course_schedule_crontab(self, params):
        """
        课表定时任务
        {
            "name": "course_schedule_cron",
            "desc": "2020年下学期定时任务",
            "start_date": "2020-09-01",
            "end_date": "2020-09-06",
            "cron": [
                {
                    "hour": 8,
                    "minute": 0,
                    "cmd": "active"
                },
                {
                    "hour": 8,
                    "minute": 45,
                    "cmd": "inactive"
                },
                ...
            ],
            "status": 1,
            "term_uuid": "",
            "weeks_num_map": {
                "1": ["2020/08/31, "2020/09/06"],
                "2": ["2020/09/07, "2020/09/13"],
                 ...
            }
        }
        """
        logger.info("start add course_schedule crontab task %s" % params)
        task_uuid = create_uuid()
        job_uuid = create_uuid()
        try:
            task_value = {
                "uuid": task_uuid,
                "name": params.pop("name"),
                "desc": params.pop("desc"),
                "type": CRONTAB_COURSE_SCHEDULE,
                "status": params.pop("status")
            }

            cron_trigger_list = list()
            for cron_dict in params["cron"]:
                cron_trigger_list.append(CronTrigger(
                    start_date=params["start_date"],
                    end_date=params["end_date"],
                    hour=cron_dict["hour"],
                    minute=cron_dict["minute"]
                ))
            trigger = OrTrigger(cron_trigger_list)
            _kwargs = {
                "term_uuid": params.pop("term_uuid"),
                "crontab_time_list": params["cron"],
                "weeks_num_map": params.pop("weeks_num_map"),
                "job_uuid": job_uuid
            }
            YzyAPScheduler().add_job(jobid=job_uuid, trigger=trigger, func=self.course_schedule_crontab_func, kwargs=_kwargs)

            detail_value = {
                "uuid": job_uuid,
                "task_uuid": task_uuid,
                "hour": 0,
                "minute": 0,
                "cycle": "course",
                "values": json.dumps(params),
                "func": "course_schedule_crontab_func",
                "params": json.dumps(_kwargs)
            }

            db_api.create_crontab_task(task_value)
            db_api.create_crontab_detail(detail_value)
            logger.info("add course_schedule crontab task success: %s", task_value)
        except Exception as e:
            logger.exception("add course_schedule crontab task error: %s", str(e), exc_info=True)
            self.rollback_course_schedule_crontab(task_uuid, job_uuid)
            return False

        return task_uuid

    def remove_course_crontab_job(self, task_uuid):
        try:
            task_obj = db_api.get_crontab_first({"uuid": task_uuid})
            if task_obj:
                detail_obj_list = db_api.get_crontab_detail_all({"task_uuid": task_uuid})
                for detail_obj in detail_obj_list:
                    YzyAPScheduler().remove_job(detail_obj.uuid)
                    detail_obj.soft_delete()
                task_obj.soft_delete()
            logger.info("remove course crontab task[%s] success" % task_uuid)
            return True
        except Exception as e:
            logger.exception("remove course crontab task[%s] failed: %s" % (task_uuid, str(e)), exc_info=True)
            return False



class LicenseManager(object):

    def get_auth_info(self):
        # config = configparser.ConfigParser()
        # config.read(constants.CONFIG_PATH)
        # if "license" in config.sections():
        #     sn = config.get('license', 'sn', fallback=None)
        #     org_name = config.get('license', 'org_name', fallback=None)
        # else:
        #     sn = None
        #     org_name = None

        # auth = db_api.get_item_with_first(models.YzyAuth, {})
        # if auth:
        #     sn = auth.sn
        #     org_name = auth.organization
        # else:
        #     sn = None
        #     org_name = None
        # try:
        #     registry_info = Registry_Info()
        #     if sn and org_name:
        #         sn = sn.replace('-', '')
        #         sn_array = bytearray(16)
        #         for index in range(int(len(sn) / 2)):
        #             sn_char = sn[index * 2:index * 2 + 2]
        #             sn_array[index] = int(sn_char, 16)
        #         unitname_array = bytearray(org_name, encoding='utf_16_le')
        #         unitname_array.extend(bytearray(256 - len(unitname_array)))
        #         registry_info = Registry_Info(sn_array, unitname_array)
        #
        #     transport = TSocket.TSocket('localhost', 9000)
        #     transport = TTransport.TBufferedTransport(transport)
        #     protocol = TBinaryProtocol.TBinaryProtocol(transport)
        #     protocol = TMultiplexedProtocol.TMultiplexedProtocol(protocol, "UKeyService")
        #     client = UKeyServer.Client(protocol)
        #     transport.open()
        #
        #     auth_info = client.GetAuthorInfo(registry_info)
        #     expire_time = auth_info.ExpireDays
        #     try:
        #         vdi_size = auth_info.VDITotalSize
        #         voi_size = auth_info.VOITotalSize
        #     except:
        #         vdi_size = 1
        #         voi_size = 1
        #     transport.close()
        #     logger.info("use_type:%s, expire_time:%s, vdi_size:%s, voi_size:%s, delay_days:%s",
        #                 auth_info.useType, expire_time, vdi_size, voi_size, auth_info.DelayDays)
        #     return {
        #         "auth_type": auth_info.useType,
        #         "expire_time": expire_time,
        #         "delay_days": auth_info.DelayDays,
        #         "vdi_size": vdi_size,
        #         "voi_size": voi_size
        #     }
        # except Exception as e:
        #     logger.exception("get auth info failed:%s", e)
        #     return {
        #         "auth_type": 0
        #     }

        try:
            client = UkeyClient()
            auth_info = client.get_auth_info()
            logger.info("auth_info: %s, %s", type(auth_info), auth_info)
            return {
                "auth_type": auth_info["use_type"],
                "expire_time": auth_info["expire_day"],
                "vdi_size": auth_info["vdi_num"],
                "voi_size": auth_info["voi_num"]
            }
        except Exception as e:
            logger.exception("get auth info failed: %s", str(e))
            return {
                "auth_type": 0,
                "expire_time": 0,
                "vdi_size": 0,
                "voi_size": 0
            }


class LogSetupManager(object):

    def create_record(self, data):
        status = data.get('status')
        option = data.get('option')
        if not (status and option):
            logger.error("create warn setup record fail: param error")
            return get_error_result("ParamError")
        if db_api.get_warn_setup_first({}):
            logger.error("warn setup record exists")
            return get_error_result("WarnSetupRecordExistsError")
        setup_values = {
            "status": status,
            "option": json.dumps(option),
        }
        try:
            db_api.create_warn_setup(setup_values)
            logger.info("create warn setup record success")
            return get_error_result("Success")
        except Exception as e:
            logger.error("create warn setup record fail: %s", e)
            return get_error_result("CreateWarnSetupFailError")

    def update_record(self, data):
        status = data.get('status', '')
        option = data.get('option', '')
        record = db_api.get_warn_setup_first({})
        if not record:
            logger.error("update warn setup record fail: not exists")
            return get_error_result("UpdateWarnSetupFailError")
        update_values = {
            "status": status,
            "option": json.dumps(option),
        }
        try:
            record.update(update_values)
            record.soft_update()
            logger.info("update warn setup record success")
            return get_error_result("Success")
        except Exception as e:
            logger.error("update warn setup record fail:%s", e)
            return get_error_result("UpdateWarnSetupFailError")


class StrategyManager(object):

    def set_system_time(self, data):
        date = data.get("date")
        node_ip = data.get("node_ip")
        time_zone = data.get("time_zone")
        ntp_server = data.get("ntp_server")
        request_data = {
            "command": "set_node_datetime",
            "handler": "NodeHandler",
            "data": {
                "datetime": date,
                "time_zone": time_zone,
                "ntp_server": ntp_server
            }
        }
        logger.debug("set node system time, data:%s", data)
        return compute_post(node_ip, request_data)
