"""
Author:      zhurong
Email:       zhurong@yzy-yf.com
Created:     2020/4/14
虚拟机相关的监控
"""
import logging
import os
from common.utils import monitor_post, compute_post
from common import constants
from common import cmdutils
from yzy_server.database import apis as db_api
from yzy_server.database import models
from yzy_server.apis.v1.controllers.desktop_ctl import BaseController
# from libs.yzyRedis import yzyRedis


logger = logging.getLogger(__name__)


def update_template_info():
    templates = db_api.get_template_with_all({})
    voi_templates = db_api.get_item_with_all(models.YzyVoiTemplate, {})
    rep_data = dict()
    for item in templates:
        host_ip = item.host.ip
        _d = {
            "uuid": item.uuid,
            "name": item.name
        }
        if host_ip not in rep_data:
            rep_data[host_ip] = list()
        rep_data[host_ip].append(_d)
    for item in voi_templates:
        host_ip = item.host.ip
        _d = {
            "uuid": item.uuid,
            "name": item.name
        }
        if host_ip not in rep_data:
            rep_data[host_ip] = list()
        rep_data[host_ip].append(_d)

    for k, v in rep_data.items():
        command_data = {
            "command": "get_status_many",
            "handler": "InstanceHandler",
            "data": {
                "instance": v
            }
        }
        logger.debug("get template state in node %s", k)
        rep_json = compute_post(k, command_data)
        logger.debug("from compute get template rep_json:{}".format(rep_json))
        if rep_json.get("code", -1) != 0:
            continue
        for template in templates:
            for item in rep_json.get("data", []):
                if item["uuid"] == template.uuid:
                    if template.status in [constants.STATUS_ACTIVE, constants.STATUS_INACTIVE]:
                        if 1 == item.get("state"):
                            status = constants.STATUS_ACTIVE
                        else:
                            status = constants.STATUS_INACTIVE
                        if template.status != status:
                            logger.info("the template %s status change from %s to %s", template.name, template.status,
                                        status)
                            template.status = status
                            template.soft_update()
                    break
        for template in voi_templates:
            for item in rep_json.get("data", []):
                if item["uuid"] == template.uuid:
                    if template.status in [constants.STATUS_ACTIVE, constants.STATUS_INACTIVE]:
                        if 1 == item.get("state"):
                            status = constants.STATUS_ACTIVE
                        else:
                            status = constants.STATUS_INACTIVE
                        if template.status != status:
                            logger.info("the template %s status change from %s to %s", template.name, template.status,
                                        status)
                            template.status = status
                            template.soft_update()
                    break


# def update_instance_info():
#     instances = db_api.get_instance_with_all({})
#     rep_data = dict()
#     for instance in instances:
#         host_ip = instance.host.ip
#         spice_port = instance.spice_port
#         _d = {
#             "uuid": instance.uuid,
#             "name": instance.name,
#             "spice_port": spice_port
#         }
#         if host_ip not in rep_data:
#             rep_data[host_ip] = list()
#         rep_data[host_ip].append(_d)
#
#     # 启多线程分发调用
#     for k, v in rep_data.items():
#         spice_ports = list()
#         for i in v:
#             if i.get("spice_port"):
#                 spice_ports.append(i.get("spice_port"))
#
#         command_data = {
#             "command": "get_status_many",
#             "handler": "InstanceHandler",
#             "data": {
#                 "instance": v
#             }
#         }
#         logger.debug("get instance state in node %s", k)
#         rep_json = compute_post(k, command_data)
#         logger.debug("from compute get rep_json:{}".format(rep_json))
#         if rep_json.get("code", -1) != 0:
#             continue
#
#         # 查询监控服务端口
#         ports = ",".join(spice_ports)
#         if ports:
#             ports_status = monitor_post(k, "/api/v1/monitor/port_status", {"ports": ports})
#         else:
#             ports_status = {}
#         logger.debug("from monitor get port status:{}".format(ports_status))
#         for item in rep_json.get("data", []):
#             for instance in instances:
#                 if item["uuid"] == instance.uuid:
#                     if item.get("state") in [constants.DOMAIN_STATE['running']]:
#                         if instance.spice_port:
#                             instance.spice_link = ports_status.get("data", {}).get(instance.spice_port, False)
#                             if not instance.spice_link:
#                                 instance.allocated = 0
#                                 # desktop_group = db_api.get_personal_desktop_with_first({'uuid': instance.desktop_uuid})
#
#                         instance.status = constants.STATUS_ACTIVE
#                         logger.debug("the instance %s is active, the spice_link:%s", instance.uuid, instance.spice_link)
#                     elif item.get('state') in [constants.DOMAIN_STATE['shutdown'], constants.DOMAIN_STATE['shutoff']]:
#                         # 如果是updating等状态，不能直接更新为inactive，否则会导致遮罩层控制问题
#                         if constants.STATUS_ACTIVE == instance.status:
#                             instance.status = constants.STATUS_INACTIVE
#                         instance.spice_port = ''
#                         instance.spice_link = 0
#                         instance.allocated = 0
#                         instance.link_time = None
#
#                         # 通知终端管理 桌面关闭
#                         # 只对绑定了终端的桌面发通知
#                         if instance.terminal_mac:
#                             if instance.classify == 2:
#                                 desktop = db_api.get_personal_desktop_with_first({'uuid': instance.desktop_uuid})
#                             else:
#                                 desktop = db_api.get_desktop_by_uuid(desktop_uuid=instance.desktop_uuid)
#
#                             if desktop:
#                                 data = dict()
#                                 data['desktop_name'] = desktop.name
#                                 data['desktop_order'] = desktop.order_num
#                                 data["desktop_uuid"] = desktop.uuid
#                                 data["instance_uuid"] = instance.uuid
#                                 data["instance_name"] = instance.name
#                                 data["host_ip"] = instance.host.ip
#                                 data["port"] = instance.spice_port
#                                 data["token"] = instance.spice_token
#                                 data["os_type"] = desktop.os_type
#                                 data["terminal_mac"] = instance.terminal_mac
#
#                                 logger.info('rtn: instance.classify: %s, data: %s' % (instance.classify, data))
#                                 base_controller = BaseController()
#                                 ret = base_controller.notice_terminal_instance_close(data)
#
#                                 # 通知完成后，清除桌面与终端的绑定关系
#                                 if ret:
#                                     try:
#                                         instance.terminal_mac = None
#                                     except Exception as e:
#                                         logger.error("update instance.terminal_mac to None: %s failed: %s",
#                                                      instance.uuid, e)
#
#                                 logger.info('rtn: %s, desktop.uuid: %s, instance.terminal_mac: %s' %
#                                             (ret, desktop.uuid, instance.terminal_mac))
#
#                     logger.debug("update instance data spice_token: %s, spice_port: %s, link_time: %s" %
#                                 (instance.spice_token, instance.spice_port, instance.link_time))
#                     instance.soft_update()
#                     break

def update_instance_info():
    instances = db_api.get_instance_with_all({})
    rep_data = dict()
    instance_dict = dict()
    for instance in instances:
        instance_dict[instance.uuid] = instance
        host_ip = instance.host.ip
        _d = {
            "uuid": instance.uuid,
            "name": instance.name
            # "spice_port": spice_port
        }
        if host_ip not in rep_data:
            rep_data[host_ip] = list()
        rep_data[host_ip].append(_d)

    # link_num = 0
    for k, v in rep_data.items():
        command_data = {
            "command": "get_status_many",
            "handler": "InstanceHandler",
            "data": {
                "instance": v
            }
        }
        logger.debug("get instance state in node %s", k)
        rep_json = compute_post(k, command_data)
        logger.debug("from compute get rep_json:{}".format(rep_json))
        if rep_json.get("code", -1) != 0:
            # 如果节点计算服务连接失败，则桌面都更新为关机状态
            if rep_json.get("code", -1) == 80000:
                for _d in v:
                    if instance_dict[_d["uuid"]].status != constants.STATUS_INACTIVE:
                        instance_dict[_d["uuid"]].update({"status": constants.STATUS_INACTIVE})
                        logger.info("compute service unavaiable at node: %s, update instance.status to inactive: %s", k, _d["uuid"])
            continue
        for item in rep_json.get("data", []):
            for instance in instances:
                if item["uuid"] == instance.uuid:
                    if item.get("state") in [constants.DOMAIN_STATE['running']]:
                        if constants.STATUS_INACTIVE == instance.status:
                            instance.status = constants.STATUS_ACTIVE
                            instance.soft_update()
                    elif item.get('state') in [constants.DOMAIN_STATE['shutdown'], constants.DOMAIN_STATE['shutoff']]:
                        if constants.STATUS_ACTIVE == instance.status:
                            instance.status = constants.STATUS_INACTIVE
                        # instance.spice_port = ''
                        # instance.spice_link = 0
                        # instance.allocated = 0
                        # instance.link_time = None

                        # 通知终端管理 桌面关闭
                        # 只对绑定了终端的桌面发通知
                        if instance.terminal_mac:
                            if instance.classify == 2:
                                desktop = db_api.get_personal_desktop_with_first({'uuid': instance.desktop_uuid})
                            else:
                                desktop = db_api.get_desktop_by_uuid(desktop_uuid=instance.desktop_uuid)

                            if desktop:
                                data = {
                                    'desktop_name': desktop.name,
                                    'desktop_order': desktop.order_num,
                                    'desktop_uuid': desktop.uuid,
                                    'instance_uuid': instance.uuid,
                                    'instance_name': instance.name,
                                    'host_ip': instance.host.ip,
                                    'port': instance.spice_port,
                                    'token': instance.spice_token,
                                    'os_type': desktop.os_type,
                                    'terminal_mac': instance.terminal_mac
                                }
                                logger.info('rtn: instance.classify: %s, data: %s' % (instance.classify, data))
                                base_controller = BaseController()
                                ret = base_controller.notice_terminal_instance_close(data)

                                # 通知完成后，清除桌面与终端的绑定关系
                                if ret:
                                    try:
                                        instance.terminal_mac = None
                                    except Exception as e:
                                        logger.error("update instance.terminal_mac to None: %s failed: %s",
                                                     instance.uuid, e)

                                logger.info('rtn: %s, desktop.uuid: %s, instance.terminal_mac: %s' %
                                            (ret, desktop.uuid, instance.terminal_mac))
                        instance.soft_update()
                    else:
                        pass
                    # instance.soft_update()
                    logger.debug("the instance %s state %s", instance.uuid, item.get('state', 0))
                    break
        spice_ports = list()
        for instance in instances:
            if instance.spice_port:
                spice_ports.append(instance.spice_port)

        # 查询监控服务端口
        ports = ",".join(list(set(spice_ports)))
        if ports:
            ports_status = monitor_post(k, "/api/v1/monitor/port_status", {"ports": ports})
        else:
            ports_status = {}
        logger.info("from node %s get port status:%s", k, ports_status)
        for instance in instances:
            if instance.host.ip == k and instance.spice_port:
                instance.spice_link = ports_status.get("data", {}).get(instance.spice_port, False)
                if not instance.spice_link:
                    instance.allocated = 0
                instance.soft_update()
            logger.debug("the instance %s spice_link:%s", instance.uuid, instance.spice_link)
        # link_num += list(ports_status.get("data", {}).values()).count(True)
    # try:
    #     redis = yzyRedis()
    #     redis.init_app()
    #     logger.info("the link num is %s", link_num)
    #     redis.set(constants.AUTH_SIZE_KEY, link_num)
    # except Exception as e:
    #     logger.exception("set auth link num failed:%s", e)


def update_template_disk_usage():
    """更新模板的磁盘使用，目前暂时只适配windows"""
    templates = db_api.get_template_with_all({})
    voi_templates = db_api.get_item_with_all(models.YzyVoiTemplate, {})
    if templates or voi_templates:
        node = db_api.get_controller_node()
        node_uuid = node.uuid
        template_sys = db_api.get_template_sys_storage(node_uuid)
        template_data = db_api.get_template_data_storage(node_uuid)
        if not (template_sys and template_data):
            logging.error("there is not storage path, skip")
        sys_path = os.path.join(template_sys.path, 'instances')
        data_path = os.path.join(template_data.path, 'datas')

    for template in templates:
        if constants.STATUS_INACTIVE == template.status:
            devices = db_api.get_devices_by_instance(template.uuid)
            for disk in devices:
                if constants.IMAGE_TYPE_SYSTEM == disk.type:
                    instance_dir = os.path.join(sys_path, template.uuid)
                elif constants.IMAGE_TYPE_DATA == disk.type:
                    instance_dir = os.path.join(data_path, template.uuid)
                else:
                    continue
                file_path = os.path.join(instance_dir, constants.DISK_FILE_PREFIX + disk.uuid)
                try:
                    stdout, stderror = cmdutils.execute('virt-df -a %s' % file_path,
                                                        shell=True, timeout=20, run_as_root=True)
                    logger.info("virt-df execute end, stdout:%s, stderror:%s", stdout, stderror)
                    result = [int(item) for item in stdout.split(' ') if item.strip() and item.isdigit()]
                    if result:
                        # 一个磁盘分区包括三个数字，总数、使用数和剩余数。windows系统盘默认有个保留分区
                        logger.info("get disk %s result:%s", disk.device_name, result)
                        if constants.IMAGE_TYPE_SYSTEM == disk.type:
                            used = result[4]
                        else:
                            used = result[1]
                        size_gb = round(used/(1024*1024), 2)
                        logger.info("get template %s disk %s used size:%s", template.name, disk.device_name, size_gb)
                        disk.used = size_gb
                        disk.soft_update()
                except:
                    pass

    for template in voi_templates:
        if constants.STATUS_INACTIVE == template.status:
            devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {'instance_uuid': template.uuid})
            for disk in devices:
                base_path = sys_path if disk.type == constants.IMAGE_TYPE_SYSTEM else data_path
                file_path = os.path.join(base_path, constants.VOI_FILE_PREFIX + disk.uuid)
                try:
                    stdout, stderror = cmdutils.execute('virt-df -a %s' % file_path,
                                                        shell=True, timeout=20, run_as_root=True)
                    logger.info("virt-df execute end, stdout:%s, stderror:%s", stdout, stderror)
                    result = [int(item) for item in stdout.split(' ') if item.strip() and item.isdigit()]
                    if result:
                        # 一个磁盘分区包括三个数字，总数、使用数和剩余数。windows系统盘默认有个保留分区
                        logger.info("get disk %s result:%s", disk.device_name, result)
                        if constants.IMAGE_TYPE_SYSTEM == disk.type:
                            used = result[4]
                        else:
                            used = result[1]
                        size_gb = round(used/(1024*1024), 2)
                        logger.info("get template %s disk %s used size:%s", template.name, disk.device_name, size_gb)
                        disk.used = size_gb
                        disk.soft_update()
                except:
                    pass
