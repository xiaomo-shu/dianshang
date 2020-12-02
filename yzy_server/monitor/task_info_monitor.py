"""
Author:      ^_^
Email:       xxxxxx@yzy-yf.com
Created:     2020/10/15
"""
import logging
from common import constants
from yzy_server.extensions import db
from yzy_server.database import apis as db_api
from yzy_server.database import models


logger = logging.getLogger(__name__)


def update_task_info_status():
    """
    更新任务信息中定时任务的状态信息
    :return:
    """
    tasks = db_api.get_task_with_type_all([10, 11, 12])
    for task in tasks:
        if task.status == constants.TASK_COMPLETE:
            task.status = constants.TASK_QUEUE
            task.soft_update()