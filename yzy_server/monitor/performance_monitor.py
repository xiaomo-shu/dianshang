"""
Author:      ^_^
Email:       xxxxxx@yzy-yf.com
Created:     2020/7/23
"""
import logging
import json
import datetime as dt
from common import constants
from common.utils import monitor_post, icmp_ping, create_uuid
from yzy_server.extensions import db
from yzy_server.database import apis as db_api
from yzy_server.database import models


logger = logging.getLogger(__name__)


def update_node_performance():
    nodes = db_api.get_node_with_all({'deleted': False})
    for node in nodes:
        try:
            if node.status == constants.STATUS_ACTIVE:
                ret = monitor_post(node.ip, 'api/v1/monitor/resource_perf_for_database', {'statis_period': 30})
                if ret.get('code') == 0:
                    ret_data = ret.get("data", {})
                    node_utc = ret_data.get("utc", 0)
                    node_datetime = dt.datetime.fromtimestamp(node_utc)
                    insert_data = {
                        "node_uuid": node.uuid,
                        "node_datetime": node_datetime,
                        "monitor_info": json.dumps(ret_data)
                    }
                    logger.debug("insert monitor performance data success, node_ip: {}, data: {}".format(node.ip, ret))
                    db_api.add_monitor_half_min(insert_data)
                else:
                    logger.error("monitor server error, node_ip:{}, ret: {}".format(node.ip, ret))
        except Exception as e:
            logger.error("get service status error:%s", e, exc_info=True)


def clear_performance_data():
    try:
        last_days = 8
        db_api.clear_monitor_half_min(last_days)
        logger.debug("delete performance monitor data of last {} days data".format(last_days))
    except Exception as e:
        logger.error("clear_performance_data error:%s", e, exc_info=True)


