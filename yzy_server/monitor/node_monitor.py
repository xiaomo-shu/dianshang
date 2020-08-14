"""
Author:      zhurong
Email:       zhurong@yzy-yf.com
Created:     2020/4/14
节点相关的监控
"""
import logging
import datetime
from common import constants
from common.config import SERVER_CONF
from common.utils import monitor_post, icmp_ping, create_uuid, compute_post
from yzy_server.database import apis as db_api
from yzy_server.database import models


logger = logging.getLogger(__name__)


def update_node_status():
    nodes = db_api.get_node_with_all({'deleted': False})
    for node in nodes:
        is_restart = False
        is_shutdowning = False
        if node.status == constants.STATUS_DELETING:
            continue
        if node.status == constants.STATUS_SHUTDOWNING:
            is_shutdowning = True
        #     continue
        logger.debug("node %s updateing", node.name)
        status = constants.STATUS_ACTIVE
        if node.status == constants.STATUS_RESTARTING:
            restart_time = node.updated_at
            now = datetime.datetime.utcnow()
            if float(str(now - restart_time).split(":")[-1]) <= 120:
                if not icmp_ping(node.ip, count=2):
                    continue
                is_restart = True
        if not icmp_ping(node.ip, count=3):
            if not is_restart:
                status = constants.STATUS_SHUTDOWN
        # rep_json = check_node_status(node.ip)
        # if rep_json.get('code') != 0:
        #     status = constants.STATUS_SHUTDOWN
        else:
            try:
                ret = monitor_post(node.ip, 'api/v1/monitor/memory', {})
                if ret.get('code') == 0:
                    mem_info = ret['data']
                    node.running_mem = mem_info["available"]/1024/1024/1024
                    node.total_mem = mem_info['total']/1024/1024/1024
                    node.mem_utilization = mem_info["utilization"]
                    ret = monitor_post(node.ip, 'api/v1/monitor/cpu', {})
                    if ret.get('code') == 0:
                        cpu_info = ret['data']
                        node.cpu_utilization = cpu_info["utilization"]
                    node.soft_update()
                    ret = monitor_post(node.ip, 'api/v1/monitor/service', {})
                    if ret.get('code') == 0:
                        services = ret['data']
                        not_running_services = list(filter(lambda service: services[service] != 'running', services.keys()))
                        if node.type in [constants.ROLE_MASTER_AND_COMPUTE, constants.ROLE_MASTER]:
                            node_services = constants.MASTER_SERVICE
                        elif node.type in [constants.ROLE_SLAVE_AND_COMPUTE, constants.ROLE_COMPUTE]:
                            node_services = constants.COMPUTE_SERVICE
                        else:
                            node_services = []
                        update_service_status(node, services, node_services)
                        for service in not_running_services:
                            if service in node_services:
                                logger.error("service %s is not running", service)
                                status = constants.STATUS_ERROR
                                break
                    else:
                        status = constants.STATUS_ERROR
                else:
                    status = constants.STATUS_ERROR
            except Exception as e:
                logger.error("get service status error:%s", e, exc_info=True)
                status = constants.STATUS_ERROR
        if node.status != status:
            if status == constants.STATUS_ERROR and is_restart and node.type not in [1, 3]:
                continue
            elif status == constants.STATUS_ERROR and is_shutdowning and node.type not in [1, 3]:
                continue
            logger.info("node %s status change from %s to %s", node.ip, node.status, status)
            node.status = status
            node.soft_update()
        # 只要节点没关机，就可以请求monitor服务去获取磁盘使用信息
        if status != constants.STATUS_SHUTDOWN:
            update_node_storage(node.ip, node.uuid)


def update_service_status(node, services, node_services):
    """
    :param node: node object of db
    :param services: the query result of node services
    :param node_services: the service which node must have
    :return:
    """
    try:
        service_names = services.keys()
        exist_services = db_api.get_service_by_node_uuid(node.uuid)
        exist_service_names = list(map(lambda node_service: node_service.name, exist_services))
        not_exist_service_names = list(
            filter(lambda service_name: service_name not in exist_service_names, service_names))
        if not_exist_service_names and len(not_exist_service_names) > 0:
            service_list = list()
            # 不属于节点应监测的服务不添加
            for name in not_exist_service_names:
                if name in node_services:
                    service_uuid = create_uuid()
                    value = {
                        'uuid': service_uuid,
                        'node_uuid': node.uuid,
                        'name': name,
                        'status': services[name]
                    }
                    service_list.append(value)
                    logger.info("add service %s in node:%s", name, node.name)
            if service_list:
                db_api.insert_with_many(models.YzyNodeServices, service_list)
                logger.info("add info to db success")
        if exist_service_names and len(exist_service_names) > 0:
            for name in exist_service_names:
                if name in node_services:
                    for service in exist_services:
                        if service.name == name:
                            if service.status != services[name]:
                                logger.info("node %s service %s status change from %s to %s", node.ip,
                                            service.name, service.status, services[name])
                                service.status = services[name]
                                service.soft_update()
                                logger.info("update server %s status to %s", service.name, services[name])
                            break
    except Exception as e:
        logger.error("update error:%s", e)


def update_node_storage(ipaddr, node_uuid):
    """
    更新节点的存储信息
    """
    logger.debug("update node %s storages", ipaddr)
    url = "/api/v1/monitor/disk"
    rep_json = monitor_post(ipaddr, url, None)
    if rep_json["code"] != 0:
        logger.error("get node:%s storage info fail" % ipaddr)
        return

    storages = db_api.get_node_storage_all({"node_uuid": node_uuid})
    data = rep_json.get("data", {})
    logger.debug("disk usage info:%s", rep_json)
    for k, v in data.items():
        if isinstance(v, dict) and k not in ['/', '/home', '/boot']:
            for storage in storages:
                if storage.path == k:
                    if storage.used != int(v['used']) or storage.free != int(v['free']):
                        storage.used = v['used']
                        storage.free = v['free']
                        storage.total = v['total']
                        storage.soft_update()
                        logger.info("update node %s path %s usage, value:%s", ipaddr, k, v)
                    break
    logger.debug("update node %s storages end", ipaddr)
    # 下面是更新网卡信息
    rep_json = monitor_post(ipaddr, 'api/v1/monitor/network', {})
    if rep_json["code"] != 0:
        logger.error("get node:%s network info fail" % ipaddr)
        return
    data = rep_json.get("data", {})
    nics = db_api.get_nics_all({"node_uuid": node_uuid})
    for k, v in data.items():
        if isinstance(v, dict):
            for nic in nics:
                if nic.nic == k:
                    if v['stat'] and 2 != nic.status:
                        nic.status = 2
                        nic.soft_update()
                        logger.info("update node %s nic %s status, value:%s", ipaddr, k, v['stat'])
                    if not v['stat'] and 1 != nic.status:
                        nic.status = 1
                        nic.soft_update()
                        logger.info("update node %s nic %s status, value:%s", ipaddr, k, v['stat'])
                    break
    logger.debug("update node %s nic status end", ipaddr)
    return


def sync_request(ipaddr, path):
    controller_image = db_api.get_controller_image()
    bind = SERVER_CONF.addresses.get_by_default('server_bind', '')
    if bind:
        port = bind.split(':')[-1]
    else:
        port = constants.SERVER_DEFAULT_PORT
    endpoint = "http://%s:%s" % (controller_image.ip, port)
    command_data = {
        "command": "ha_sync",
        "handler": "NodeHandler",
        "data": {
            "path": path,
            "endpoint": endpoint,
            "url": constants.HA_SYNC_URL,
        }
    }
    logger.info("sync the file %s to %s", path, ipaddr)
    rep_json = compute_post(ipaddr, command_data, timeout=600)
    logger.info("sync the file %s to %s end, rep_json:%s", path, ipaddr, rep_json)
    return rep_json


def ha_sync_task():
    """
    同步iso库文件和数据库备份文件到备控
    """
    nodes = db_api.get_node_with_all({})
    flag = False
    for node in nodes:
        if node.type in [constants.ROLE_SLAVE, constants.ROLE_SLAVE_AND_COMPUTE]:
            flag = True
            break
    if flag:
        isos = db_api.get_item_with_all(models.YzyIso, {})
        for iso in isos:
            sync_request(node.ip, iso.path)
        db_backs = db_api.get_item_with_all(models.YzyDatabaseBack, {})
        for backup in db_backs:
            sync_request(node.ip, backup.path)

