import os
import time
import shutil
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from common.cmdutils import execute
from common import constants
from common.utils import get_error_result, upgrade_post
from . import constants as const
from .upgrade_manager import UpgradeManager


logger = logging.getLogger(__name__)


def upgrade_cluster():
    # 确保所有节点都在线
    ret = UpgradeManager().check_node_status()
    if ret.get('code', 0) != 0:
        return ret
    logger.info("start self upgrade, check node status success")
    slave_ips = ret['slaves']

    tasks = list()
    failed_nodes = list()
    url = "api/v1/index/self_upgrade"
    with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
        for node_ip in slave_ips:
            task = executor.submit(upgrade_post, node_ip, url, data={})
            tasks.append(task)
        for future in as_completed(tasks):
            res = future.result()
            if res.get("code") != 0:
                logger.error("url:%s failed: %s, msg: %s" % (url, res.get("ipaddr", ""), res.get("msg", "")))
                failed_nodes.append(res.get("ipaddr", ""))
    if failed_nodes:
        return get_error_result("UpgradeSlavesError", {"failed_nodes": failed_nodes})
    while True:
        result = []
        url = "api/v1/index/get_self_upgrade_status"
        for node_ip in slave_ips:
            try:
                ret = upgrade_post(node_ip, url, data={})
                if ret.get('code') != 0:
                    result.append(False)
                else:
                    result.append(True)
            except Exception as e:
                logger.exception("get self upgrade state in node %s failed", node_ip)
                result.append(False)

        # 所有节点升级完成
        if all(result):
            logger.info("Other host self upgrade successful")
            break

        # 每秒检测一次
        time.sleep(1)
    start_self_upgrade()
    return get_error_result()


def start_self_upgrade(cmd=False):
    # 是否是通过命令行启动的自升级程序
    logger.info("start self upgrade, cmd:%s", cmd)
    upgrade_path = os.path.join(constants.BASE_DIR, 'yzy_upgrade')
    if not cmd:
        if os.path.exists(const.SELF_UPGRADE_FILE):
            os.remove(const.SELF_UPGRADE_FILE)
        exe_cmd = [upgrade_path, "self_upgrade"]
        subprocess.Popen(exe_cmd)
        return get_error_result()
    logger.info("begin stop upgrade")
    # 停止升级服务
    stdout, stderr = execute("systemctl", "stop", "yzy-upgrade")
    if stderr:
        return get_error_result("StopServiceError", service="yzy-upgrade")
    logger.info("start replace file")
    try:
        os.remove(upgrade_path)
        source = os.path.join(const.UPGRADE_KVM_PATH, 'yzy_upgrade')
        logger.info("copy %s to %s", source, upgrade_path)
        shutil.copy2(source, upgrade_path)
    except:
        logger.exception("copy file failed", exc_info=True)
        return get_error_result("UpgradeSlavesError")
    # 重启服务
    stdout, stderr = execute("systemctl", "start", "yzy-upgrade")
    if stderr:
        return get_error_result("StartServiceError", service="yzy-upgrade")
    # 增加自升级标志
    with open(const.SELF_UPGRADE_FILE, 'w') as fd:
        fd.write("")
    return get_error_result()
