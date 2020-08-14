import os
import json
import redis
import socket
import datetime as dt
import traceback
import threading
import logging
import psutil
from flask import current_app
import common.errcode as errcode
from yzy_terminal_agent.database import api as db_api
from yzy_terminal_agent.ext_libs.bt_api_service import BtApiServiceTask
from yzy_terminal_agent.timer_tasks.base_task import BaseTask


logger = logging.getLogger(__name__)


class BtStateTask(BaseTask):
    def __init__(self, app, interval=10):
        super(BtStateTask, self).__init__(self)
        self.app = app
        # self.bt_api = BtApiServiceTask()
        self.name = 'bt_state'
        self.interval = interval
        self.now_date = '19700101'

    def process(self):
        logger.info("bt state task start .... %s"% threading.currentThread().ident)
        try:
            # import pdb; pdb.set_trace()
            task_api = db_api.YzyVoiTorrentTaskTableCtrl(self.app.db)
            tasks = task_api.select_all_task()
            # import pdb; pdb.set_trace()
            for task in tasks:
                # 更新bt任务进度
                # pass
                torrent_id = task.torrent_id
                terminal_ip = task.terminal_ip
                # BtApiServiceTask
                ret = self.app.bt_api.get_task_state(torrent_id, terminal_ip, task.type)
                if ret.get("code", -1) != 0:
                    logger.error("task[%s:%s] get state error: %s"% (torrent_id, terminal_ip, ret))
                    continue
                # task.process = progress
                # task.download_rate = download_rate
                state = ret.get("state", "")
                status = 0
                if state == "finished":
                    status = 2
                elif state in ("downloading", "seeding"):
                    status = 1
                values = {
                    "process": ret.get("progress", 0),
                    "download_rate": ret.get("download_rate", 0),
                    "state": state,
                    "status": status
                }
                task_api.update_task_values(task, values)
                logger.info("bt state update success: %s, %s"% (torrent_id, terminal_ip))
            logger.info("bt state task success ... %s"% threading.currentThread().ident)
        except Exception as err:
            current_app.db.session.rollback()
            logger.error(err, exc_info=True)
