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
from common import constants
from common.utils import server_post
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
        with self.app.app_context():
            try:
                # import pdb; pdb.set_trace()
                task_api = db_api.YzyVoiTorrentTaskTableCtrl(current_app.db)
                up_tasks = task_api.select_upload_task_all()

                batch_no_task_dict = dict()
                for t in up_tasks:
                    batch_no = t.batch_no
                    if batch_no not in batch_no_task_dict:
                        batch_no_task_dict[batch_no] = []
                    batch_no_task_dict[batch_no].append(t.to_dict())

                for task in up_tasks:
                    # 更新bt任务进度
                    # pass
                    torrent_id = task.torrent_id
                    terminal_ip = task.terminal_ip
                    # BtApiServiceTask
                    ret = self.app.bt_api.get_task_state(torrent_id, terminal_ip, task.type)
                    logger.info("bt state task id %s %s return: %s"% (task.id, torrent_id, ret))
                    if ret.get("code", -1) != 0:
                        logger.error("task[%s:%s] get state error: %s"% (torrent_id, terminal_ip, ret))
                        continue
                    progress = int(ret.get("progress", 0))
                    state = ret.get("state", "")
                    status = constants.BT_TASK_INIT
                    if state == "finished" or progress == 100:
                        status = constants.BT_TASK_FINISH
                        state = "finished"
                    elif state == "downloading" or state == "checking":
                        status = constants.BT_TASK_CHECKING_OR_DOWNING
                    # elif state  == "seeding":
                    #     status = constants.BT_TASK_SEEDING

                    values = {
                        "process": progress,
                        "download_rate": ret.get("download_rate", 0),
                        "upload_rate": ret.get("upload_rate", 0),
                        "state": state,
                        "status": status
                    }

                    # todo 上传完需要更新模板
                    if status == constants.BT_TASK_FINISH and task.type == constants.BT_UPLOAD_TASK:
                        # 上传任务完成，判断当前批任务是否已经上传完成

                        ret = self.app.bt_api.delele_bt_task(torrent_id)
                        logger.info("delete bt state task id %s %s return: %s" % (task.id, torrent_id, ret))

                        # dir_path =
                        batch_no = task.batch_no
                        sum = task.sum
                        is_finished = True
                        disks_info = list()
                        if len(batch_no_task_dict.get(batch_no, [])) == sum:
                            batch_tasks = batch_no_task_dict.get(batch_no)
                            for t in batch_tasks:
                                if t.status != constants.BT_TASK_FINISH or t.progress != 100:
                                    is_finished = False
                                    break
                            disks_info = batch_tasks

                        if is_finished:
                            for disk_task in disks_info:
                                try:
                                    disk_uuid_upper = disk_task["disk_uuid"].replace("-", "").upper()
                                    save_dir_path = os.path.join(disk_task["save_path"], "_")
                                    target_file = os.path.join(save_dir_path, constants.VOI_FILE_PREFIX
                                                               + disk_task["disk_uuid"])
                                    if os.path.exists(save_dir_path) and os.path.isdir(save_dir_path) and \
                                            not os.path.exists(target_file):
                                        for _f in os.listdir(save_dir_path):
                                            if _f.replace("-", "").find(disk_uuid_upper) != -1:
                                                file_path = os.path.join(save_dir_path, _f)
                                                os.rename(file_path, target_file)
                                                break
                                    if not os.path.exists(target_file):
                                        logger.error("bt upload state task target file:%s not exist"% target_file)
                                        continue
                                    disk_task["disk_diff"] = target_file
                                except Exception as e:
                                    logger.error("", exc_info=True)
                                    continue

                            # 调用server 更新模板接口
                            data = {
                                "uuid": task.template_uuid,
                                "desc": "terminal %s upload update template" % task.terminal_mac,
                                "is_upload": True,
                                # "upload_diff_info": {
                                #     "disk_uuid": task.disk_uuid,
                                #     "disk_diff": target_file,
                                #     "disk_type": disk_type
                                # }
                                "upload_diff_info": disks_info
                            }
                            # ret = {"code", 0}
                            ret = server_post("/api/v1/voi/template/save", data)
                            logger.info("terminal upload update save voi template end:%s", ret)
                            if ret.get("code", -1) != 0 :
                                logger.error("terminal upload update save voi template fail %s", ret)
                                raise Exception("save template fail")
                            values.update({"deleted": 1})
                            logger.info("terminal upload update save voi template end:%s", data)
                    task_api.update_task_values(task, values)
                    logger.info("bt state update success: %s, %s"% (torrent_id, terminal_ip))
                logger.info("bt state task success ... %s"% threading.currentThread().ident)
            except Exception as err:
                current_app.db.session.rollback()
                logger.error(err, exc_info=True)
