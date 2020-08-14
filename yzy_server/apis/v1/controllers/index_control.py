import logging
import traceback
import datetime as dt
import numpy as np
from common import constants
from common.utils import monitor_post, build_result
from yzy_server.database import apis as db_api
from common.errcode import get_error_result
from common import constants
from common.config import SERVER_CONF
from concurrent.futures import ThreadPoolExecutor, as_completed


logger = logging.getLogger(__name__)


class IndexController(object):
    def get_top_data(self, statis_period):
        logger.debug("get nodes resource_statis top5 data, period {}".format(statis_period))
        url = "/api/v1/monitor/resource_statis"
        request_data = {"statis_period": statis_period}
        all_node_cpu_info = []
        all_node_memory_info = []
        all_node_disk_info = []
        all_node_nic_info = []
        # get all nodes ip
        try:
            nodes = db_api.get_node_with_all({'status': constants.STATUS_ACTIVE})
            workers = len(nodes) if len(nodes) > 0 else 1
            all_task = []
            with ThreadPoolExecutor(max_workers=workers) as executor:
                for node in nodes:
                    # get node system resource perf statistic info
                    request_data.update({
                        "node_name": node.name,
                        "node_uuid": node.uuid,
                        "node_ip": node.ip
                    })
                    future = executor.submit(monitor_post, node.ip, url, request_data)
                    all_task.append(future)
                for future in as_completed(all_task):
                    rep_json = future.result()
                    logger.info("rep:%s", rep_json)
                    if rep_json["code"] != 0:
                        logger.error("get node:{}} resource_statis info fail".format(rep_json))
                        continue
                    node_name = rep_json.get("data").get("node_name", "")
                    node_uuid = rep_json.get("data").get("node_uuid", "")
                    node_ip = rep_json.get("data").get("node_ip", "")
                    all_node_cpu_info.append((node_name, rep_json["data"]["cpu_util"]))
                    all_node_memory_info.append((node_name, rep_json["data"]["memory_util"]))
                    # get all ssd disk path, then sum
                    storages = db_api.get_node_storage_all({'node_uuid': node_uuid})
                    disk_ssd = [0, 0]
                    for storage in storages:
                        if storage.type == 1 and storage.path in rep_json["data"]["disk_util"].keys():  # 1-ssd  2-sata
                            logger.debug(storage.path)
                            disk_ssd[0] += rep_json["data"]["disk_util"][storage.path]["total"]
                            disk_ssd[1] += rep_json["data"]["disk_util"][storage.path]["used"]
                    all_node_disk_info.append((node_name,
                                               '%0.2f' % (disk_ssd[1] / disk_ssd[0] * 100) if disk_ssd[0] else 0,
                                               disk_ssd[0], disk_ssd[1]))
                    # just manage network nic, from yzy_node_network_info , yzy_interface_ip is_manage
                    manage_network_name = db_api.get_node_manage_nic_name(node_uuid)
                    logger.debug(manage_network_name)
                    if manage_network_name and manage_network_name in rep_json["data"]["nic_util"].keys():
                        all_node_nic_info.append((node_name,
                                                  rep_json["data"]["nic_util"][manage_network_name]["sum_bytes_avg"],
                                                  rep_json["data"]["nic_util"][manage_network_name]["sum_bytes_max"]))
            resp = get_error_result("Success")
            resp["data"] = {}
            resp["data"]['utc'] = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
            all_node_cpu_info.sort(key=lambda x: float(x[1]), reverse=True)
            resp["data"]["cpu_util"] = all_node_cpu_info[0:5]
            all_node_memory_info.sort(key=lambda x: float(x[1]), reverse=True)
            resp["data"]["memory_util"] = all_node_memory_info[0:5]
            all_node_disk_info.sort(key=lambda x: float(x[1]), reverse=True)
            resp["data"]["disk_util"] = all_node_disk_info[0:5]
            all_node_nic_info.sort(key=lambda x: float(x[1]), reverse=True)
            resp["data"]["nic_util"] = all_node_nic_info[0:5]
            return resp
        except Exception as err:
            logger.error("err {}".format(err))
            logger.error(''.join(traceback.format_exc()))
            return build_result("OtherError")

    def get_node_statistic(self):
        return get_error_result("Success")

    def get_instance_statistic(self):
        return get_error_result("Success")

    def get_terminal_statistic(self):
        return get_error_result("Success")

    def get_operation_log(self):
        return get_error_result("Success")


def create_md5_token(key, s):
    logger.info("create md5")
    return hashlib.md5(("%s%s"% (s, key)).encode()).hexdigest()

def get_user_list():
    _l = []
    users = db.session.query(User).all()
    for user in users:
        _l.append(user.to_json())
    return _l
    def get_instance_statistic(self):
        return get_error_result("Success")

    def get_terminal_statistic(self):
        return get_error_result("Success")

def deal_task(task):
    print(current_app.handlers)
    handlers = current_app.handlers
    handler = handlers.get("instanceHandle")
    if handler:
        c = handler
        c.deal(task)
    def get_operation_log(self):
        return get_error_result("Success")
