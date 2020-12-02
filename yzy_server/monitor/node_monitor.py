"""
Author:      zhurong
Email:       zhurong@yzy-yf.com
Created:     2020/4/14
节点相关的监控
"""
import logging
import datetime
import os
from common import constants, cmdutils
from common.config import SERVER_CONF
from common.utils import monitor_post, icmp_ping, create_uuid, compute_post
from yzy_server.database import apis as db_api
from yzy_server.database import models
from yzy_server.utils import read_file_md5, get_template_storage_path, notify_backup_sync_file


logger = logging.getLogger(__name__)


def update_node_status():
    # 启用HA后，主备控节点的type是动态的，先检查HA信息，确保节点type是正确的
    update_ha_master()

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
                    cpu_ratio = 0
                    if ret.get('code') == 0:
                        cpu_info = ret['data']
                        cpu_ratio = cpu_info["utilization"]
                        node.cpu_utilization = cpu_info["utilization"]
                    node.soft_update()
                    if cpu_ratio >= 95:
                        status = constants.STATUS_ERROR
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


def update_ha_master():
    is_vip, is_master, is_backup = False, False, False
    current_ip = None
    ha_info_obj = db_api.get_ha_info_first()
    if ha_info_obj:
        # logger.info("ha_info before monitor update: %s" % ha_info_obj.dict())

        # 获取本机所有启用网口的ip，查看本节点的ip在ha_info表中是master_ip还是backup_ip
        code, out = cmdutils.run_cmd("""ip -br a |grep ' UP ' |grep -o '[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*'""", ignore_log=True)
        if code != 0:
            logger.error(out)
        else:
            ip_list = [ip for ip in out.strip('\n').split('\n')]
            for ip in ip_list:
                if ip == ha_info_obj.vip:
                    is_vip = True
                elif ip == ha_info_obj.master_ip:
                    is_master = True
                elif ip == ha_info_obj.backup_ip:
                    is_backup = True

            if not is_vip:
                logger.error("server running without vip[%s]" % ha_info_obj.vip)
            else:
                if not is_master and not is_backup:
                    logger.error("server running without master_ip[%s], backup_ip[%s]" % (ha_info_obj.master_ip, ha_info_obj.backup_ip))
                elif is_master and is_backup:
                    logger.error("server running with both master_ip[%s], backup_ip[%s]" % (ha_info_obj.master_ip, ha_info_obj.backup_ip))
                elif is_master and not is_backup:
                    current_ip = ha_info_obj.master_ip
                elif not is_master and is_backup:
                    # 如果发现本节点的ip在ha_info表中是backup_ip，说明notify.sh脚本中调用server服务/node/master接口去更新数据库的操作失败了
                    # 检查并修正ha_info表中的ip
                    current_ip = ha_info_obj.backup_ip
                    ha_info_obj.master_ip, ha_info_obj.backup_ip = ha_info_obj.backup_ip, ha_info_obj.master_ip
                    logger.info("update ha_info[%s] master_ip from %s to %s",
                                (ha_info_obj.uuid, ha_info_obj.backup_ip, ha_info_obj.master_ip))

                if current_ip:
                    # current_ip所在节点应该为master，检查并修正ha_info表中node_uuid、nic、nic_uuid
                    current_node_obj = db_api.get_node_by_ip(current_ip)
                    if current_node_obj.uuid == ha_info_obj.backup_uuid:
                        ha_info_obj.master_uuid, ha_info_obj.backup_uuid = ha_info_obj.backup_uuid, ha_info_obj.master_uuid
                        logger.info("update ha_info[%s] master_uuid from %s to %s",
                                    (ha_info_obj.uuid, ha_info_obj.backup_uuid, ha_info_obj.master_uuid))
                    current_ip_obj = db_api.get_nic_ip_by_ip(current_ip)
                    if current_ip_obj.nic_uuid == ha_info_obj.backup_nic_uuid:
                        ha_info_obj.master_nic_uuid, ha_info_obj.backup_nic_uuid = ha_info_obj.backup_nic_uuid, ha_info_obj.master_nic_uuid
                        logger.info("update ha_info[%s] master_nic_uuid from %s to %s",
                                    (ha_info_obj.uuid, ha_info_obj.backup_nic_uuid, ha_info_obj.master_nic_uuid))
                    if ha_info_obj.master_nic != ha_info_obj.backup_nic and current_ip_obj.name == ha_info_obj.backup_nic:
                        ha_info_obj.master_nic, ha_info_obj.backup_nic = ha_info_obj.backup_nic, ha_info_obj.master_nic
                        logger.info("update ha_info[%s] master_nic from %s to %s",
                                    (ha_info_obj.uuid, ha_info_obj.backup_nic, ha_info_obj.master_nic))
                    ha_info_obj.soft_update()

                    # 检查并修正backup_uuid节点的type
                    real_backup_node_obj = db_api.get_node_by_uuid(ha_info_obj.backup_uuid)
                    if real_backup_node_obj.type not in [constants.ROLE_SLAVE_AND_COMPUTE, constants.ROLE_SLAVE]:
                        wrong_type = real_backup_node_obj.type
                        if real_backup_node_obj.type in [constants.ROLE_MASTER_AND_COMPUTE, constants.ROLE_COMPUTE]:
                            real_backup_node_obj.type = constants.ROLE_SLAVE_AND_COMPUTE
                        else:
                            real_backup_node_obj.type = constants.ROLE_SLAVE
                        real_backup_node_obj.soft_update()
                        logger.info("update real_backup_node[%s] role from %s to %s", real_backup_node_obj.ip, wrong_type,
                                    real_backup_node_obj.type)

                    # 检查并修正master_uuid节点的type
                    if current_node_obj.type not in [constants.ROLE_MASTER, constants.ROLE_MASTER_AND_COMPUTE]:
                        wrong_type = current_node_obj.type
                        if wrong_type in [constants.ROLE_SLAVE_AND_COMPUTE, constants.ROLE_COMPUTE]:
                            current_node_obj.type = constants.ROLE_MASTER_AND_COMPUTE
                        else:
                            current_node_obj.type = constants.ROLE_MASTER
                        current_node_obj.soft_update()
                        logger.info("update current_node[%s] role from %s to %s", current_node_obj.ip, wrong_type,
                                    current_node_obj.type)

                    # 检查并修正yzy_template、yzy_voi_template表的模板宿主机uuid
                    templates = db_api.get_template_with_all({})
                    for template in templates:
                        if constants.SYSTEM_DESKTOP == template.classify:
                            continue
                        if template.host_uuid != current_node_obj.uuid:
                            template.host_uuid = current_node_obj.uuid
                            template.soft_update()
                            logger.info("update template %s host_uuid to %s", template.name, current_node_obj.uuid)

                    voi_templates = db_api.get_voi_template_with_all({})
                    for template in voi_templates:
                        if constants.SYSTEM_DESKTOP == template.classify:
                            continue
                        if template.host_uuid != current_node_obj.uuid:
                            template.host_uuid = current_node_obj.uuid
                            template.soft_update()
                            logger.info("update voi template %s host_uuid to %s", template.name, current_node_obj.uuid)


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
        if isinstance(v, dict) and k not in ['/', '/home', '/boot', '/boot/efi']:
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


def ha_sync_task():
    """
    通知备控检查文件同步情况，下载缺少的，删除多余的
    范围：iso库、数据库备份文件、VOI模板的实际启动盘、base盘、差异盘、种子文件
    """
    ha_info_obj = db_api.get_ha_info_first()
    if ha_info_obj:
        paths = list()
        for iso in db_api.get_item_with_all(models.YzyIso, {}):
            paths.append({"path": iso.path, "md5": iso.md5_sum})
        if paths:
            notify_backup_sync_file(ha_info_obj.master_ip, ha_info_obj.backup_ip, paths, check_path=os.path.dirname(paths[0]["path"]))

        backs = list()
        for backup in db_api.get_item_with_all(models.YzyDatabaseBack, {}):
            backs.append({"path": backup.path, "md5": backup.md5_sum})
        if backs:
            notify_backup_sync_file(ha_info_obj.master_ip, ha_info_obj.backup_ip, backs, check_path=os.path.dirname(backs[0]["path"]))

        templates = list()
        sys_base, data_base = get_template_storage_path(ha_info_obj.master_uuid)
        for dir_path in [sys_base, os.path.join(sys_base, constants.IMAGE_CACHE_DIRECTORY_NAME),
                         data_base, os.path.join(data_base, constants.IMAGE_CACHE_DIRECTORY_NAME)]:
            find_file_to_sync(dir_path, templates)
        find_xml_to_sync("/etc/libvirt/qemu/", templates)
        if templates:
            # 模板不删除多余的，容易导致正在刚创建的模板磁盘文件被删除
            notify_backup_sync_file(ha_info_obj.master_ip, ha_info_obj.backup_ip, templates)


def find_file_to_sync(dir_path, ret_list):
    # VOI模板磁盘文件
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        if file_path.endswith(constants.IMAGE_CACHE_DIRECTORY_NAME):
            continue
        if os.path.isfile(file_path):
            logger.info("start reading: %s", file)
            ret_list.append({"path": file_path, "md5": read_file_md5(file_path)})
            logger.info("finish reading: %s", file)

def find_xml_to_sync(dir_path, ret_list):
    # VOI模板XML文件
    for file in os.listdir(dir_path):
        if file.startswith(constants.VOI_BASE_NAME[:3]):
            file_path = os.path.join(dir_path, file)
            ret_list.append({"path": file_path, "md5": read_file_md5(file_path)})
