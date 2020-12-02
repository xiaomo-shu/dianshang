# -*- coding:utf-8 -*-
import time
import threading
import logging
import random
import string
import os
import json

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
# from .terminal_ctl import TerminalController
from yzy_server.database import apis as db_api
from yzy_server.database import models
from common import constants
from common.config import FileOp
from common.errcode import get_error_result
from common.utils import create_uuid, compute_post, find_ips, terminal_post
from yzy_server.extensions import db
from yzy_server.utils import sync_func_to_ha_backup, sync_compute_post_to_ha_backup_with_network_info


logger = logging.getLogger(__name__)


def generate_mac(used_macs):
    flag = True
    mac_address = None
    while flag:
        base_mac = "fa:16:3e:00:00:00".split(':')
        mac = [int(base_mac[0], 16), int(base_mac[1], 16),
               int(base_mac[2], 16), random.randint(0x00, 0xff),
               random.randint(0x01, 0xff), random.randint(0x00, 0xff)]

        if base_mac[3] != '00':
            mac[3] = int(base_mac[3], 16)
        mac_address = ':'.join(map(lambda x: "%02x" % x, mac))
        if mac_address not in used_macs:
            used_macs.append(mac_address)
            flag = False
    return mac_address


def generate_ips(ips, used_ips):
    for ipaddr in ips:
        if ipaddr not in used_ips:
            used_ips.append(ipaddr)
            return ipaddr


class BaseController(object):

    def __init__(self):
        self.app = None
        self.used_macs = list()
        self.used_ips = list()

    def get_used_macs(self):
        template_macs = db_api.get_template_mac()
        voi_macs = db_api.get_voi_template_mac()
        instance_macs = db_api.get_instance_mac()
        used_macs = template_macs + instance_macs + voi_macs
        return used_macs

    def get_education_used_ipaddr(self, subnet_uuid):
        template_ips = db_api.get_template_ipaddr()
        voi_ips = db_api.get_voi_template_ipaddr()
        personal_ips = db_api.get_personal_ipaddr(subnet_uuid)
        used_ips = template_ips + personal_ips + voi_ips
        return list(set(used_ips))

    def get_personal_used_ipaddr(self, subnet_uuid):
        template_ips = db_api.get_template_ipaddr()
        voi_ips = db_api.get_voi_template_ipaddr()
        education_ips = db_api.get_education_ipaddr(subnet_uuid)
        personal_ips = db_api.get_personal_ipaddr(subnet_uuid)
        used_ips = template_ips + education_ips + personal_ips + voi_ips
        return list(set(used_ips))

    def _get_instance_storage_path(self, node_uuid=None):
        if not node_uuid:
            node = db_api.get_controller_node()
            node_uuid = node.uuid
        instance_sys = db_api.get_instance_sys_storage(node_uuid)
        instance_data = db_api.get_instance_data_storage(node_uuid)
        if not (instance_sys and instance_data):
            return None, None
        sys_path = os.path.join(instance_sys.path, 'instances')
        data_path = os.path.join(instance_data.path, 'datas')
        return {"path": sys_path, "uuid": instance_sys.uuid, 'free': instance_sys.free}, \
               {"path": data_path, "uuid": instance_data.uuid, 'free': instance_data.free}

    def _get_storage_path_with_uuid(self, sys_storage, data_storage):
        template_sys = db_api.get_node_storage_first({"uuid": sys_storage})
        template_data = db_api.get_node_storage_first({"uuid": data_storage})
        if not (template_sys and template_data):
            return None, None
        sys_path = os.path.join(template_sys.path, 'instances')
        data_path = os.path.join(template_data.path, 'datas')
        return sys_path, data_path

    def create_disk_info(self, data, sys_base, data_base, image_path, disk_generate=True):
        """
        生成模板的磁盘信息
        :return:
            [
                {
                    "uuid": "dfcd91e8-30ed-11ea-9764-000c2902e179",
                    "dev": "vda",
                    "boot_index": 0,
                    "size": "50G",
                    "disk_file": "",
                    "backing_file": ""
                },
                {
                    "uuid": "f613f8ac-30ed-11ea-9764-000c2902e179",
                    "dev": "vdb",
                    "boot_index": -1,
                    "size": "50G",
                    "disk_file": ""
                },
                ...
            ]
        """
        _disk_list = []
        if not disk_generate:
            _disk_list.append(data['system_disk'])
            for disk in data['data_disks']:
                _disk_list.append(disk)
            return _disk_list
        sys_base_dir = os.path.join(sys_base, data['uuid'])
        data_base_dir = os.path.join(data_base, data['uuid'])
        system_disk_dict = {
            "uuid": data['system_disk']['uuid'],
            # "bus": data['system_disk'].get('bus', 'virtio'),
            "bus": 'virtio',
            "dev": "vda",
            "boot_index": 0,
            "size": "%dG" % int(data['system_disk']['size']),
            "disk_file": "%s/%s%s" % (sys_base_dir, constants.DISK_FILE_PREFIX, data['system_disk']['uuid']),
            "backing_file": image_path
        }
        _disk_list.append(system_disk_dict)

        zm = string.ascii_lowercase

        for disk in data.get('data_disks', []):
            _d = dict()
            inx = int(disk["inx"])
            size = int(disk["size"])
            disk_uuid = create_uuid()
            _d["uuid"] = disk_uuid
            _d["bus"] = disk.get('bus', 'virtio')
            _d["boot_index"] = inx + 1
            _d["size"] = "%dG" % size
            _d["dev"] = "vd%s" % zm[inx + 1]
            _d['disk_file'] = "%s/%s%s" % (data_base_dir, constants.DISK_FILE_PREFIX, disk_uuid)
            _disk_list.append(_d)
        logger.debug("get disk info")
        return _disk_list

    def notice_terminal_instance_close(self, data):
        """ 通知终端管理 桌面关闭
        {
            "handler": "WebTerminalHandler",
            "command": "desktop_close_notice",
            "data": {
                "group": {
                    "name": "桌面组名称",
                    "id": 11,
                    "desc": "桌面组描述",
                    "uuid": "23333333334444444444"
                },
                "ip": "172.16.1.33",
                "port": 5059,
                "desktop_name": "VM01",
                "token": "5059234234SFASDFSFDAS",
                "os_type": "win10",
                "dsk_uuid": "234safdasfasdf23234",
                "terminal_mac": "00:0c:29:b1:24:74"
            }
        }

        ,
        "desktop_name": desktop.name,
                "desktop_order": desktop.order_num,
                "desktop_desc": desktop.desc,
                "desktop_uuid": desktop.uuid,
                "instance_uuid": instance.uuid,
                "instance_name": instance.name,
                "host_ip": node.ip,
                "port": instance.spice_port,
                "token": instance.spice_token,
                "os_type": desktop.os_type,
                "terminal_mac": instance.terminal_mac
        """
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "desktop_close_notice",
            "data":{
                "group": {
                    "name": data["desktop_name"],
                    "uuid": data["desktop_uuid"],
                    "id": data["desktop_order"],
                    # "desc": data["desktop_desc"]
                },
                "ip": data["host_ip"],
                "port": data["port"],
                "token": data["token"],
                "instance_name": data["instance_name"],
                "instance_uuid": data["instance_uuid"],
                "terminal_mac": data["terminal_mac"]
            }
        }

        count = 0
        while count < 3:
            try:
                ret = terminal_post("/api/v1/terminal/task", req_data)
                if ret.get("code", -1) == 0:
                    logger.info("terminal notice instance close success")
                    break
                logger.error("terminal notice instance close fail: %s"% ret)
                count += 1
            except Exception as e:
                logger.error("", exc_info=True)
                count += 1
            time.sleep(1)

        return True

    # def create_instance(self, desktop, subnet, instance, version, sys_base, data_base, power_on=True):
    #     try:
    #         # 如果是教学桌面，需要查看同一分组下的桌面组对应的桌面有没有开启
    #         if constants.EDUCATION_DESKTOP == instance.classify:
    #             all_desktop = db_api.get_desktop_with_all({"group_uuid": desktop.group_uuid})
    #             for item in all_desktop:
    #                 if item.uuid != desktop.uuid:
    #                     exist = db_api.get_instance_with_first({"desktop_uuid": item.uuid,
    #                                                             "terminal_id": instance.terminal_id})
    #                     if exist and constants.STATUS_ACTIVE == exist.status:
    #                         logger.error("the instance %s already active", exist.uuid)
    #                         return False
    #         info = {
    #             "id": instance.id,
    #             "uuid": instance.uuid,
    #             "name": instance.name,
    #             "vcpu": desktop.vcpu,
    #             "ram": desktop.ram,
    #             "os_type": desktop.os_type
    #         }
    #         node = db_api.get_node_by_uuid(instance.host_uuid)
    #         instance_info = self._get_instance_info(info)
    #         net = db_api.get_interface_by_network(desktop.network_uuid, node.uuid)
    #         vif_info = {
    #             "uuid": net.YzyNetworks.uuid,
    #             "vlan_id": net.YzyNetworks.vlan_id,
    #             "interface": net.nic,
    #             "bridge": constants.BRIDGE_NAME_PREFIX + net.YzyNetworks.uuid[:constants.RESOURCE_ID_LENGTH]
    #         }
    #         network_info = self.create_network_info(vif_info, instance.port_uuid, instance.mac,
    #                                                 subnet, instance.ipaddr)
    #         devices = db_api.get_devices_by_instance(instance.uuid)
    #         disk_info = self._get_instance_disk(devices, version, sys_base, data_base,
    #                                             desktop.sys_restore, desktop.data_restore)
    #         rep_json = self._create_instance(node.ip, instance_info, network_info, disk_info, power_on)
    #         if power_on and rep_json['code'] == 0:
    #             # token记录，用于vnc web访问
    #             file_path = os.path.join(constants.TOKEN_PATH, instance.uuid)
    #             content = '%s: %s:%s' % (instance.uuid, node.ip, rep_json['data']['vnc_port'])
    #             logger.info("write instance token info:%s", instance.uuid)
    #             FileOp(file_path, 'w').write_with_endline(content)
    #     except Exception as e:
    #         logger.error("create instance:%s failed:%s", instance.name, e, exc_info=True)
    #         instance.message = str(e)
    #         instance.status = constants.STATUS_ERROR
    #         instance.soft_update()
    #         return False
    #     if power_on:
    #         instance.status = constants.STATUS_ACTIVE
    #         instance.up_time = datetime.utcnow()
    #         if rep_json['data'].get("spice_token"):
    #             logger.info("add spice token info, data:%s", rep_json['data'])
    #             instance.spice_token = rep_json["data"]["spice_token"]
    #         instance.spice_port = rep_json["data"]['spice_port']
    #     else:
    #         instance.status = constants.STATUS_INACTIVE
    #     instance.message = ''
    #     instance.soft_update()
    #     time.sleep(0.5)
    #     return True

    def create_instance(self, desktop, subnet, instance, sys_base, data_base, power_on=True, terminal=False):
        try:
            node = db_api.get_node_by_uuid(instance.host_uuid)
            # 如果是教学桌面，需要查看同一分组下的桌面组对应的桌面有没有开启
            if constants.EDUCATION_DESKTOP == instance.classify:
                all_desktop = db_api.get_desktop_with_all({"group_uuid": desktop.group_uuid})
                for item in all_desktop:
                    if item.uuid != desktop.uuid:
                        exist = db_api.get_instance_with_first({"desktop_uuid": item.uuid,
                                                                "terminal_id": instance.terminal_id})
                        if exist:
                            if terminal:
                                if constants.STATUS_ACTIVE == exist.status:
                                    logger.info("terminal start, shutdown this instance")
                                    node = db_api.get_node_by_uuid(exist.host_uuid)
                                    timeout = 0 if item.sys_restore else 70
                                    try:
                                        self._stop_instance(node.ip, {"uuid": exist.uuid, "name": exist.name}, timeout)
                                        # exist.spice_token = ''
                                    except:
                                        pass
                                # 清掉其他桌面的终端信息
                                exist.spice_port = ''
                                exist.spice_link = 0
                                exist.allocated = 0
                                exist.link_time = None
                                exist.terminal_mac = None
                                exist.soft_update()
                                logger.info("clean up instance %s link info", exist.name)
                                continue
                            elif constants.STATUS_ACTIVE == exist.status:
                                return get_error_result("InstanceStartConflict", desktop_name=item.name, name=exist.name)
                command_data = {
                    "command": "check_ram",
                    "handler": "InstanceHandler",
                    "data": {
                        "allocated": desktop.ram
                    }
                }
                rep_json = compute_post(node.ip, command_data)
                if rep_json.get('code') != 0 or not rep_json.get('data', {}).get('result', True):
                    logger.error("can not allocate memory")
                    return get_error_result("ResourceAllocateError")

            info = {
                "id": instance.id,
                "uuid": instance.uuid,
                "name": instance.name,
                "vcpu": desktop.vcpu,
                "ram": desktop.ram,
                "os_type": desktop.os_type,
                "spice_token": instance.spice_token
            }
            instance_info = self._get_instance_info(info)
            net = db_api.get_interface_by_network(desktop.network_uuid, node.uuid)
            if not net:
                logger.error("node %s network info %s error", node.uuid, desktop.network_uuid)
                return get_error_result("NodeNetworkInfoError")

            vif_info = {
                "uuid": net.YzyNetworks.uuid,
                "vlan_id": net.YzyNetworks.vlan_id,
                "interface": net.nic,
                "bridge": constants.BRIDGE_NAME_PREFIX + net.YzyNetworks.uuid[:constants.RESOURCE_ID_LENGTH]
            }
            network_info = self.create_network_info(vif_info, instance.port_uuid, instance.mac,
                                                    subnet, instance.ipaddr)
            devices = db_api.get_devices_by_instance(instance.uuid)
            ins_sys, ins_data = self._get_storage_path_with_uuid(instance.sys_storage, instance.data_storage)
            disk_info = self._get_instance_disk(instance.uuid, devices, sys_base, data_base, ins_sys, ins_data,
                                                desktop.sys_restore, desktop.data_restore)
            rep_json = self._create_instance(node.ip, instance_info, network_info, disk_info, power_on)
            if power_on and rep_json['code'] == 0:
                # token记录，用于vnc web访问
                file_path = os.path.join(constants.TOKEN_PATH, instance.uuid)
                content = '%s: %s:%s' % (instance.uuid, node.ip, rep_json['data']['vnc_port'])
                logger.info("write instance token info, uuid:%s, name:%s", instance.uuid, instance.name)
                FileOp(file_path, 'w').write_with_endline(content)
        except Exception as e:
            logger.error("create instance failed, uuid:%s, name:%s, error:%s",
                         instance.uuid, instance.name, e, exc_info=True)
            instance.message = str(e)
            instance.status = constants.STATUS_ERROR
            instance.soft_update()
            return get_error_result("InstanceStartFail", name=instance.name, data=str(e))
        if power_on:
            instance.status = constants.STATUS_ACTIVE
            if rep_json['data'].get("spice_token"):
                instance.up_time = datetime.utcnow()
                logger.info("add spice token info, uuid:%s, name:%s", instance.uuid, instance.name)
                # instance.spice_token = rep_json["data"]["spice_token"]
            instance.spice_port = rep_json["data"]['spice_port']
        else:
            instance.status = constants.STATUS_INACTIVE
        instance.message = ''
        instance.up_time = datetime.utcnow()
        instance.soft_update()
        time.sleep(0.5)
        logger.info("create instance return, spice_token:%s, spice_port:%s", instance.spice_token, instance.spice_port)
        return get_error_result(data={"spice_token": instance.spice_token, "spice_port": instance.spice_port})

    def stop_instance(self, instance, desktop, personal=False, hard=False, timeout=None):

        info = {
            "uuid": instance.uuid,
            "name": instance.name
        }
        logger.info("stop instance begin:%s, timeout:%s", info, timeout)
        node = db_api.get_node_by_uuid(instance.host_uuid)
        try:
            # 强制关机流程
            if hard:
                logger.info("hard stop instance")
                self._stop_instance(node.ip, info, timeout=0)
            else:
                # 个人桌面不管还原不还原，不强制关机
                if personal:
                    logger.info("personal instance stop, timeout:120")
                    self._stop_instance(node.ip, info, timeout=timeout or 120)

                else:
                    # 系统盘属性为重启还原的虚拟机，关机时直接断电
                    if desktop.sys_restore:
                        logger.info("education instance stop, timeout:0")
                        self._stop_instance(node.ip, info, timeout=0)
                    else:
                        logger.info("education instance stop, timeout:120")
                        self._stop_instance(node.ip, info, timeout=timeout or 120)

            file_path = os.path.join(constants.TOKEN_PATH, instance.uuid)
            try:
                logger.info("delete token file:%s", file_path)
                os.remove(file_path)
            except:
                pass
            terminal_mac = instance.terminal_mac
            instance.status = constants.STATUS_INACTIVE
            instance.spice_port = ''
            instance.spice_link = 0
            # instance.spice_token = ''
            instance.message = ''
            instance.terminal_mac = None
            instance.soft_update()
            # 通知终端管理服务
            data = {
                "desktop_name": desktop.name,
                "desktop_order": desktop.order_num,
                # "desktop_desc": desktop.desc,
                "desktop_uuid": desktop.uuid,
                "instance_uuid": instance.uuid,
                "instance_name": instance.name,
                "host_ip": node.ip,
                "port": instance.spice_port,
                "token": instance.spice_token,
                "os_type": desktop.os_type,
                "terminal_mac": terminal_mac
            }
            # 通知终端管理服务
            t = threading.Thread(target=self.notice_terminal_instance_close, args=(data,))
            t.start()
            logger.info("stop end, return")
            return True
        except Exception as e:
            logger.error("stop instance failed:%s", e, exc_info=True)
            return False

    def delete_instance(self, instance, sys_base, data_base):
        deleted = True
        info = {
            "uuid": instance.uuid,
            "name": instance.name,
            "sys_base": sys_base,
            "data_base": data_base
        }
        logger.info("delete instance begin:%s", info)
        node = db_api.get_node_by_uuid(instance.host_uuid)
        try:
            self._delete_instance(node.ip, info)
        except:
            deleted = False
        devices = db_api.get_devices_by_instance(instance.uuid)
        for device in devices:
            device.soft_delete()
        instance.soft_delete()
        try:
            token_file = os.path.join(constants.TOKEN_PATH, instance.uuid)
            os.remove(token_file)
        except:
            pass
        logger.info("delete instance %s end", instance.uuid)
        return deleted

    def reboot_instance(self, desktop, subnet, instance, sys_base, data_base):
        try:
            # 如果是教学桌面，需要查看同一分组下的桌面组对应的桌面有没有开启
            if constants.EDUCATION_DESKTOP == instance.classify:
                all_desktop = db_api.get_desktop_with_all({"group_uuid": desktop.group_uuid})
                for item in all_desktop:
                    if item.uuid != desktop.uuid:
                        exist = db_api.get_instance_with_first({"desktop_uuid": item.uuid,
                                                                "terminal_id": instance.terminal_id})
                        if exist and constants.STATUS_ACTIVE == exist.status:
                            logger.error("the instance %s already active", exist.uuid)
                            return get_error_result("InstanceStartConflict", desktop_name=item.name, name=exist.name)
            info = {
                "id": instance.id,
                "uuid": instance.uuid,
                "name": instance.name,
                "vcpu": desktop.vcpu,
                "ram": desktop.ram,
                "os_type": desktop.os_type,
                "spice_token": instance.spice_token
            }
            node = db_api.get_node_by_uuid(instance.host_uuid)
            instance_info = self._get_instance_info(info)
            instance_info['sys_base'] = sys_base
            instance_info['data_base'] = data_base
            net = db_api.get_interface_by_network(desktop.network_uuid, node.uuid)
            if not net:
                logger.error("node %s network info %s error", node.uuid, desktop.network_uuid)
                return get_error_result("NodeNetworkInfoError")

            vif_info = {
                "uuid": net.YzyNetworks.uuid,
                "vlan_id": net.YzyNetworks.vlan_id,
                "interface": net.nic,
                "bridge": constants.BRIDGE_NAME_PREFIX + net.YzyNetworks.uuid[:constants.RESOURCE_ID_LENGTH]
            }
            network_info = self.create_network_info(vif_info, instance.port_uuid, instance.mac,
                                                    subnet, instance.ipaddr)
            devices = db_api.get_devices_by_instance(instance.uuid)
            ins_sys, ins_data = self._get_storage_path_with_uuid(instance.sys_storage, instance.data_storage)
            disk_info = self._get_instance_disk(instance.uuid, devices, sys_base, data_base, ins_sys, ins_data,
                                                desktop.sys_restore, desktop.data_restore)
            rep_json = self._reboot_restore_instance(node.ip, instance_info, network_info, disk_info,
                                                     desktop.sys_restore, desktop.data_restore)
            # token记录，用于vnc web访问
            file_path = os.path.join(constants.TOKEN_PATH, instance.uuid)
            content = '%s: %s:%s' % (instance.uuid, node.ip, rep_json['data']['vnc_port'])
            logger.info("write instance token info, uuid:%s, name:%s", instance.uuid, instance.name)
            FileOp(file_path, 'w').write_with_endline(content)
        except Exception as e:
            logger.error("reboot instance failed, uuid:%s, name:%s, error:%s",
                         instance.uuid, instance.name, e, exc_info=True)
            instance.message = str(e)
            instance.status = constants.STATUS_ERROR
            return get_error_result("InstanceRebootFail", name=instance.name, data=str(e))
        instance.status = constants.STATUS_ACTIVE
        instance.message = ''
        instance.up_time = datetime.utcnow()
        if rep_json['data'].get("spice_token"):
            logger.info("add spice token, uuid:%s, name:%s", instance.uuid, instance.name)
            # instance.spice_token = rep_json["data"]["spice_token"]
        instance.spice_port = rep_json["data"]['spice_port']
        instance.soft_update()
        logger.info("reboot instance success, uuid:%s, spice_token:%s", instance.uuid, instance.spice_token)
        return get_error_result()

    def _get_instance_disk(self, uuid, devices, sys_base, data_base,
                           ins_sys, ins_data, sys_restore=True, data_restore=True):
        disks = list()
        for device in devices:
            base_dir = sys_base if constants.IMAGE_TYPE_SYSTEM == device.type else data_base
            ins_base = ins_sys if constants.IMAGE_TYPE_SYSTEM == device.type else ins_data
            info = {
                "uuid": device.uuid,
                "dev": device.device_name,
                "boot_index": device.boot_index,
                "bus": device.disk_bus,
                "type": device.source_device,
                "disk_file": os.path.join(ins_base, uuid, constants.DISK_FILE_PREFIX + device.uuid),
                "backing_file": os.path.join(base_dir, constants.IMAGE_CACHE_DIRECTORY_NAME,
                                             constants.IMAGE_FILE_PREFIX % str(1) + device.image_id),
                "restore": sys_restore if constants.IMAGE_TYPE_SYSTEM == device.type else data_restore
            }
            disks.append(info)
        logger.info("get disk info success")
        return disks

    def create_network_info(self, vif_info, port_uuid, mac_addr, subnet, fixed_ip=None):
        """
        创建应用模板相关的网络信息
        :return:
            {
                "fixed_ip": "172.16.1.13",
                "netmask": "255.255.255.0",
                "gateway": "172.16.1.254",
                "dns_server": ["114.114.114.114"],
                "mac_addr": "fa:16:3e:8f:be:ff",
                "bridge": "brqa72e4f85-28",
                "port_id": "12fb86f2-b87b-44f0-b44e-38189314bdbd"
                "vif_info": {
                    "uuid": "",
                    "vlan_id": 1,
                    "bridge": "brqa72e4f85-28",
                    "interface": eth1
                }
            }
        """
        _network_info = []
        _d = dict()
        _d["fixed_ip"] = fixed_ip
        _d["mac_addr"] = mac_addr
        if subnet:
            _d["netmask"] = subnet['netmask']
            _d["gateway"] = subnet['gateway']
            # _d["netmask"] = subnet.netmask
            # _d["gateway"] = subnet.gateway
            if subnet['dns1']:
                _d["dns_server"] = [subnet['dns1']]
            if subnet['dns2']:
                _d["dns_server"].append(subnet['dns2'])

        _d["bridge"] = vif_info["bridge"]
        _d["port_id"] = port_uuid
        _d["vif_info"] = vif_info
        _network_info.append(_d)
        logger.debug("get network info, uuid:%s", vif_info["uuid"])
        return _network_info

    def _get_instance_info(self, data, template=False, voi=False):
        if voi:
            base = constants.VOI_BASE_NAME
        elif template:
            base = constants.TEMPLATE_BASE_NAME
        else:
            base = constants.INSTANCE_BASE_NAME
        _os_type = ""
        os_type = data['os_type'].lower()
        if os_type.startswith("win"):
            _os_type = "windows"
        elif os_type == "linux":
            _os_type = "linux"

        # spice_token = create_uuid()

        instance_info = {
            "uuid": data['uuid'],
            "name": data['name'],
            "base_name": base % data['id'],
            "ram": float(data['ram']) * 1024,
            "vcpus": data['vcpu'],
            "os_type": _os_type,
            "spice_token": data.get('spice_token')
        }
        # 模板不开启spice端口
        if voi or template:
            instance_info['spice'] = False
            instance_info.pop("spice_token")
        logger.debug("get instance info, uuid:%s, name:%s", instance_info['uuid'], instance_info['name'])
        return instance_info

    def _start_desktop(self, desktop, subnet):
        template = db_api.get_instance_template(desktop.template_uuid)
        if not template:
            return get_error_result("TemplateNotExist")
        sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
        if not (sys_base and data_base):
            return get_error_result("InstancePathNotExist")

        logger.info("get intances in desktop:%s", desktop.name)
        instances = db_api.get_instance_by_desktop(desktop.uuid)
        all_task = list()
        failed_num = 0
        success_num = 0
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for instance in instances:
                logger.info("start instance %s thread", instance.uuid)
                future = executor.submit(self.create_instance, desktop, subnet, instance, sys_base, data_base)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        # 提交线程中的数据库更新，在线程中的commit不生效，why？
        db.session.flush()
        logger.info("start desktop %s end, success:%s, failed:%s", desktop.name, success_num, failed_num)
        # if failed_num > 0:
        #     return get_error_result("DesktopStartError", name=desktop.name,
        #                         data={"failed_num": failed_num, "success_num": success_num})
        # else:
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def _stop_desktop(self, desktop, personal=False, hard=False):
        """
        关机操作，根据桌面组进行所有桌面的关机。对于系统盘还原的情况，就是强制关机
        """
        logger.info("get intances in desktop:%s", desktop.name)
        instances = db_api.get_instance_by_desktop(desktop.uuid)
        all_task = list()
        failed_num = 0
        success_num = 0
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for instance in instances:
                logger.info("stop instance %s thread", instance.uuid)
                future = executor.submit(self.stop_instance, instance, desktop, personal, hard)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if not result:
                    failed_num += 1
                else:
                    success_num += 1
        logger.info("stop desktop %s end, success:%s, failed:%s", desktop.name, success_num, failed_num)
        db.session.flush()
        # if failed_num > 0:
        #     return get_error_result("DesktopStopError", name=desktop.name,
        #                         data={"failed_num": failed_num, "success_num": success_num})
        # else:
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def _stop_desktop_for_node(self, desktop, node, personal=False):
        """
        关机操作，根据桌面组进行所有桌面的关机。对于系统盘还原的情况，就是强制关机
        """
        logger.info("get intances in desktop:%s", desktop.name)
        instances = db_api.get_instance_by_desktop_and_node(desktop.uuid, node.uuid)
        all_task = list()
        failed_num = 0
        success_num = 0
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for instance in instances:
                logger.info("stop instance %s thread", instance.uuid)
                future = executor.submit(self.stop_instance, instance, desktop, personal, timeout=90)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if not result:
                    failed_num += 1
                else:
                    success_num += 1
        logger.info("stop desktop %s end, success:%s, failed:%s", desktop.name, success_num, failed_num)
        db.session.flush()
        # if failed_num > 0:
        #     return get_error_result("DesktopStopError", name=desktop.name,
        #                         data={"failed_num": failed_num, "success_num": success_num})
        # else:
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    # def _start_desktop(self, desktop, subnet):
    #     logger.info("get intances in desktop:%s", desktop.name)
    #     instances = db_api.get_instance_by_desktop(desktop.uuid)
    #     version = db_api.get_template_version(desktop.template_uuid)
    #     sys_base, data_base = self._get_instance_storage_path()
    #     if instances:
    #         count = 0
    #         base_host = instances[0].host_uuid
    #     for instance in instances:
    #         try:
    #             self.create_instance(desktop, subnet, instance, version, sys_base, data_base)
    #             if instance.host_uuid == base_host:
    #                 count += 1
    #             else:
    #                 count = 1
    #                 base_host = instance.host_uuid
    #             if count >= 10:
    #                 time.sleep(10)
    #                 count = 0
    #         except Exception as e:
    #             logger.error("start desktop failed:%s", e)
    #             return build_result("InstanceStartFail", name=instance.name)
    #     logger.info("start desktop %s success", desktop.name)
    #     return build_result("Success")

    # def _stop_desktop(self, desktop, personal=False):
    #     """
    #     关机操作，根据桌面组进行所有桌面的关机。
    #     """
    #     sys_restore = desktop.sys_restore
    #     logger.info("get intances in desktop:%s", desktop.name)
    #     instances = db_api.get_instance_by_desktop(desktop.uuid)
    #     for instance in instances:
    #         info = {
    #             "uuid": instance.uuid,
    #             "name": instance.name
    #         }
    #         node = db_api.get_node_by_uuid(instance.host_uuid)
    #         try:
    #             # 个人桌面不管还原不还原，都不强制关机
    #             if personal:
    #                 self._stop_instance(node.ip, info, timeout=120)
    #             else:
    #                 # 系统盘属性为重启还原的虚拟机，关机时直接删除
    #                 if sys_restore:
    #                     self._stop_instance(node.ip, info, timeout=0)
    #                 else:
    #                     self._stop_instance(node.ip, info, timeout=120)
    #             instance.status = "inactive"
    #             instance.soft_update()
    #             file_path = os.path.join(constants.TOKEN_PATH, instance.uuid)
    #             try:
    #                 logger.info("delete token file:%s", file_path)
    #                 os.remove(file_path)
    #             except:
    #                 pass
    #         except Exception as e:
    #             logger.error("stop desktop failed:%s", e)
    #             return build_result("InstanceStopFail", name=instance.name)
    #     logger.info("stop desktop %s success", desktop.name)
    #     return build_result("Success")

    def _reboot_desktop(self, desktop, subnet):
        """
        重启操作，根据盘的还原属性进行还原，即相当于关机再开机
        """
        template = db_api.get_instance_template(desktop.template_uuid)
        if not template:
            return get_error_result("TemplateNotExist")
        sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
        if not (sys_base and data_base):
            return get_error_result("InstancePathNotExist")

        logger.info("get intances in desktop:%s", desktop.name)
        instances = db_api.get_instance_by_desktop(desktop.uuid)
        all_task = list()
        failed_num = 0
        success_num = 0
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for instance in instances:
                logger.info("reboot instance %s thread", instance.uuid)
                future = executor.submit(self.reboot_instance, desktop, subnet, instance, sys_base, data_base)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        db.session.flush()
        logger.info("reboot desktop %s end, success:%s, failed:%s", desktop.name, success_num, failed_num)
        # if failed_num > 0:
        #     return get_error_result("DesktopRebootError", name=desktop.name,
        #                         data={"failed_num": failed_num, "success_num": success_num})
        # else:
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def _delete_desktop(self, desktop):
        """
        删除桌面组，不管什么类型桌面，全部删除
        """
        template = db_api.get_instance_template(desktop.template_uuid)
        if not template:
            return get_error_result("TemplateNotExist")

        logger.info("get intances in desktop:%s", desktop.name)
        instances = db_api.get_instance_by_desktop(desktop.uuid)
        all_task = list()
        failed_num = 0
        success_num = 0
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for instance in instances:
                logger.info("delete instance %s thread", instance.uuid)
                sys_base, data_base = self._get_storage_path_with_uuid(instance.sys_storage, instance.data_storage)
                future = executor.submit(self.delete_instance, instance, sys_base, data_base)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if not result:
                    failed_num += 1
                else:
                    success_num += 1

        db.session.flush()
        # if failed_num > 0:
        #     return get_error_result("DesktopDeleteFail", name=desktop.name,
        #                         data={"failed_num": failed_num, "success_num": success_num})
        # else:
        desktop.soft_delete()
        logger.info("delete desktop %s success, success:%s, failed:%s", desktop.name, success_num, failed_num)
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def _create_instance(self, ipaddr, instance_info, network_info, disk_info, power_on=True):
        command_data = {
            "command": "create",
            "handler": "InstanceHandler",
            "data": {
                "instance": instance_info,
                "network_info": network_info,
                "disk_info": disk_info,
                "power_on": power_on
            }
        }
        logger.info("create instance %s in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("create instance:%s failed, node:%s, error:%s", instance_info['name'], ipaddr, rep_json.get('data'))
            message = rep_json['data'] if rep_json.get('data', None) else rep_json['msg']
            raise Exception(message)
        return rep_json

    def _start_instance(self, ipaddr, instance_info, network_info):
        command_data = {
            "command": "start",
            "handler": "InstanceHandler",
            "data": {
                "instance": instance_info,
                "network_info": network_info
            }
        }

        # 如果启用了HA，在备控上也同步执行对VOI模板的操作，未启用则不同步
        sync_compute_post_to_ha_backup_with_network_info(command_data)

        logger.info("start instance %s in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("start instance failed, node:%s, error:%s", ipaddr, rep_json.get('data'))
            message = rep_json['data'] if rep_json.get('data', None) else rep_json['msg']
            raise Exception(message)
        return rep_json

    # def _stop_restore_instance(self, ipaddr, instance_info, sys_restore, data_restore, timeout=120):
    #     """
    #     系统盘还原，data_restore标识数据盘是否还原
    #     """
    #     command_data = {
    #         "command": "stop_restore",
    #         "handler": "InstanceHandler",
    #         "data": {
    #             "instance": instance_info,
    #             "sys_restore": sys_restore,
    #             "data_restore": data_restore,
    #             "timeout": timeout
    #         }
    #     }
    #     logger.info("stop_restore instance %s in node %s", instance_info['uuid'], ipaddr)
    #     rep_json = compute_post(ipaddr, command_data)
    #     if rep_json.get("code", -1) != 0:
    #         logger.error("stop_restore instance failed, node:%s, error:%s", ipaddr, rep_json.get('data'))
    #         raise Exception("stop_restore instance failed")
    #     return rep_json

    def _reboot_restore_instance(self, ipaddr, instance_info, network_info, disk_info, sys_restore, data_restore):
        command_data = {
            "command": "reboot_restore",
            "handler": "InstanceHandler",
            "data": {
                "instance": instance_info,
                "network_info": network_info,
                "disk_info": disk_info,
                "sys_restore": sys_restore,
                "data_restore": data_restore
            }
        }
        logger.info("reboot instance %s in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("reboot instance failed, node:%s, error:%s", ipaddr, rep_json.get('data'))
            message = rep_json['data'] if rep_json.get('data', None) else rep_json['msg']
            raise Exception(message)
        return rep_json

    def _stop_instance(self, ipaddr, instance_info, timeout=10):
        """
        timeout标识是否强制关机
        """
        command_data = {
            "command": "stop",
            "handler": "InstanceHandler",
            "data": {
                "instance": instance_info,
                "timeout": timeout
            }
        }

        # 如果启用了HA，在备控上也同步执行对VOI模板的操作，未启用则不同步
        sync_func_to_ha_backup(compute_post, command_data, timeout=150)

        logger.info("stop instance %s in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data, timeout=150)
        if rep_json.get("code", -1) != 0:
            logger.error("stop instance failed, node:%s, error:%s", ipaddr, rep_json.get('data'))
            message = rep_json['data'] if rep_json.get('data', None) else rep_json['msg']
            raise Exception(message)
        return rep_json

    def _delete_instance(self, ipaddr, instance_info):
        command_data = {
            "command": "delete",
            "handler": "InstanceHandler",
            "data": {
                "instance": instance_info
            }
        }
        logger.info("delete instance %s in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("delete instance failed, node:%s, error:%s", ipaddr, rep_json.get('data'))
            message = rep_json['data'] if rep_json.get('data', None) else rep_json['msg']
            raise Exception(message)
        return rep_json

    def _reboot_instance(self, ipaddr, instance_info, reboot_type="soft"):
        command_data = {
            "command": "reboot",
            "handler": "InstanceHandler",
            "data": {
                "reboot_type": reboot_type,
                "instance": instance_info
            }
        }

        # 如果启用了HA，在备控上也同步执行对VOI模板的操作，未启用则不同步
        sync_func_to_ha_backup(compute_post, command_data, timeout=180)

        logger.info("soft reboot instance %s in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data, timeout=180)
        if rep_json.get("code", -1) != 0:
            logger.error("soft reboot instance failed, node:%s, error:%s", ipaddr, rep_json.get('data'))
            message = rep_json['data'] if rep_json.get('data', None) else rep_json['msg']
            raise Exception(message)
        return rep_json

    def _hard_reboot_instance(self, ipaddr, instance_info, network_info, disk_info):
        command_data = {
            "command": "reboot",
            "handler": "InstanceHandler",
            "data": {
                "reboot_type": "hard",
                "instance": instance_info,
                "network_info": network_info,
                "disk_info": disk_info
            }
        }
        logger.info("hard reboot instance %s in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data, timeout=180)
        if rep_json.get("code", -1) != 0:
            logger.error("hard reboot instance failed, node:%s, error:%s", ipaddr, rep_json.get('data'))
            message = rep_json['data'] if rep_json.get('data', None) else rep_json['msg']
            raise Exception(message)
        return rep_json

    def _get_instance_status(self, ipaddr, instance_info):
        """
        获取虚拟机的一些信息，包括运行状态、vnc端口号等
        """
        command_data = {
            "command": "get_status",
            "handler": "InstanceHandler",
            "data": {
                "instance": instance_info
            }
        }
        logger.debug("get instance %s status in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("get instance status failed, node:%s, error:%s", ipaddr, rep_json.get('data'))
        return rep_json

    def _autostart(self, ipaddr, instance_info, vif_info, start=True):
        command_data = {
            "command": "autostart",
            "handler": "InstanceHandler",
            "data": {
                "instance": instance_info,
                "vif_info": vif_info,
                "start": start
            }
        }
        logger.info("set instance %s autostart %s in node %s", instance_info['uuid'], start, ipaddr)
        rep_json = compute_post(ipaddr, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("set instance autostart failed, node:%s, error:%s", ipaddr, rep_json.get('data'))
        return rep_json


class DesktopController(BaseController):

    def _check_params(self, data):
        if not data:
            return False
        name = data.get('name', '')
        group_uuid = data.get('group_uuid', '')
        pool_uuid = data.get('pool_uuid', '')
        template_uuid = data.get('template_uuid', '')
        network_uuid = data.get('network_uuid', '')
        subnet_uuid = data.get('subnet_uuid', '')
        if not (name and group_uuid and pool_uuid and template_uuid and network_uuid and subnet_uuid):
            return False
        logger.info("check params ok")
        return True

    def create_desktop(self, data):
        """
        创建教学桌面组，仅仅插入数据库记录，不启动桌面
        :param data:
            {
                "name": "desktop1",
                "owner_id": 1,
                "group_uuid": "1c7dff98-2dda-11ea-b565-562668d3ccea",   # 桌面所属分组
                "template_uuid": "84f0e463-2dce-11ea-a71f-562668d3ccea",
                "pool_uuid": "e865aa50-26ee-11ea-9b67-562668d3ccea",    # 所属资源池
                "network_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea",
                "subnet_uuid": "5712bcb6-27b5-11ea-8c45-562668d3ccea",
                "vcpu": 4,
                "ram": 4,
                "sys_restore": 1,   # 系统盘是否还原
                "data_restore": 1,   # 系统盘是否还原
                "instance_num": 10,
                "prefix": "pc",     # 单个桌面名称的前缀
                "postfix": 3,       # 单个桌面名称的后缀数字个数
                "postfix_start": 2,
                "create_info": {        # 发布在哪些节点以及每个节点多少个桌面
                    "agent1": 5,
                    "agent2": 5
                }
            }
        :return:
        """
        if not self._check_params(data):
            return get_error_result("ParamError")

        template = db_api.get_instance_template(data['template_uuid'])
        if not template:
            logger.error("instance template: %s not exist", data['template_uuid'])
            return get_error_result("TemplateNotExist")
        if constants.PERSONAL_DEKSTOP == template.classify:
            return get_error_result("TemplatePersonalError", name=template.name)

        subnet = db_api.get_subnet_by_uuid(data['subnet_uuid'])
        if not subnet:
            logger.error("subnet: %s not exist", data['subnet_uuid'])
            return get_error_result("SubnetNotExist")

        # 检测可用IP是否充足
        unused_ips = list()
        if not subnet.enable_dhcp:
            self.education_used_ips = self.get_education_used_ipaddr(subnet.uuid)
            all_ips = find_ips(subnet.start_ip, subnet.end_ip)
            for ip in all_ips:
                if ip not in self.education_used_ips:
                    unused_ips.append(ip)
            logger.info("get unused ips")
            if len(unused_ips) < data['instance_num']:
                return get_error_result("IPNotEnough")

        sys_base, data_base = self._get_instance_storage_path()
        if not (sys_base and sys_base):
            return get_error_result("InstancePathNotExist")

        # add desktop
        last_desktop = db_api.get_desktop_order_by_order_num({})
        desktop_uuid = create_uuid()
        desktop_value = {
            "uuid": desktop_uuid,
            "owner_id": data['owner_id'],
            "name": data['name'],
            "group_uuid": data['group_uuid'],
            "pool_uuid": data['pool_uuid'],
            "template_uuid": data['template_uuid'],
            "network_uuid": data['network_uuid'],
            "subnet_uuid": data['subnet_uuid'],
            "vcpu": data['vcpu'],
            "ram": data['ram'],
            "os_type": template.os_type,
            "sys_restore": data['sys_restore'],
            "data_restore": data['data_restore'],
            "instance_num": data['instance_num'],
            "prefix": data['prefix'],
            "postfix": data['postfix'],
            "postfix_start": data.get('postfix_start', 1),
            "order_num": (last_desktop.order_num + 1) if last_desktop else 1,
            "active": False
        }
        # add instance
        self.used_macs = self.get_used_macs()
        instances = list()
        disks = list()
        # devices = db_api.get_devices_by_instance(template.uuid)
        devices = db_api.get_devices_with_all({"instance_uuid": template.uuid})
        postfix = int(data['postfix'])
        postfix_start = data.get('postfix_start', 1)
        terminal_id = 1
        for ipaddr, num in data['create_info'].items():
            node = db_api.get_node_with_first({'ip': ipaddr})
            for i in range(num):
                # 桌面名称是前缀加几位数字
                if len(str(postfix_start)) < postfix:
                    post = '0' * (postfix - len(str(postfix_start))) + str(postfix_start)
                else:
                    post = str(postfix_start)
                instance_name = data['prefix'] + post
                instance_uuid = create_uuid()
                mac = generate_mac(self.used_macs)
                instance_value = {
                    "uuid": instance_uuid,
                    "name": instance_name,
                    "host_uuid": node.uuid,
                    "desktop_uuid": desktop_uuid,
                    "sys_storage": sys_base['uuid'],
                    "data_storage": data_base['uuid'],
                    "classify": 1,
                    "terminal_id": terminal_id,
                    "status": constants.STATUS_INACTIVE,
                    # 不同桌面组相同终端序号的IP时分配是一样的
                    "ipaddr": '' if subnet.enable_dhcp else generate_ips(unused_ips, self.education_used_ips),
                    "mac": mac,
                    "port_uuid": create_uuid(),
                    "spice_token": create_uuid()
                }
                terminal_id += 1
                instances.append(instance_value)
                postfix_start += 1
                for disk in devices:
                    info = {
                        "uuid": create_uuid(),
                        "type": disk.type,
                        "device_name": disk.device_name,
                        "image_id": disk['uuid'],
                        "instance_uuid": instance_uuid,
                        "boot_index": disk.boot_index,
                        "size": disk.size
                    }
                    disks.append(info)
        try:
            db_api.create_desktop(desktop_value)
            db_api.insert_with_many(models.YzyInstances, instances)
            db_api.insert_with_many(models.YzyInstanceDeviceInfo, disks)
            logger.info("create desktop %s success", data['name'])
        except Exception as e:
            logging.info("insert desktop info to db failed:%s", e)
            return get_error_result("DesktopCreateFail", name=data['name'])
        return get_error_result("Success", desktop_value)

    def active_desktop(self, desktop_uuid):
        desktop = db_api.get_desktop_by_uuid(desktop_uuid)
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        desktop.active = True
        desktop.soft_update()
        logger.info("active desktop %s success", desktop.name)
        return get_error_result("Success")

    def inactive_desktop(self, desktop_uuid):
        desktop = db_api.get_desktop_by_uuid(desktop_uuid)
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        self._stop_desktop(desktop)
        desktop.active = False
        desktop.soft_update()
        logger.info("inactive desktop %s success", desktop.name)
        return get_error_result("Success")

    def start_desktop(self, desktop_uuid):
        """
        开机操作，根据桌面组进行所有桌面的开机。在开机时实现还原
        """
        desktop = db_api.get_desktop_by_uuid(desktop_uuid)
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        subnet = db_api.get_subnet_by_uuid(desktop.subnet_uuid)
        if not subnet:
            logger.error("subnet: %s not exist", desktop.subnet_uuid)
            return get_error_result("SubnetNotExist")

        return self._start_desktop(desktop, subnet)

    def stop_desktop(self, desktop_uuid, hard=False):
        """
        关机操作，根据桌面组进行所有桌面的关机。关机不进行还原的处理
        """
        desktop = db_api.get_desktop_by_uuid(desktop_uuid)
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        ret = self._stop_desktop(desktop, hard=hard)
        return ret

    def stop_desktop_for_node(self, desktop_uuid, node_uuid):
        """
        关机操作，根据桌面组进行所有桌面的关机。关机不进行还原的处理
        """
        desktop = db_api.get_desktop_by_uuid(desktop_uuid)
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            logger.error("node %s not exist", node_uuid)
            return get_error_result("NodeNotExist", name="")
        return self._stop_desktop_for_node(desktop, node)

    def reboot_desktop(self, desktop_uuid):
        """
        重启操作，根据盘的还原属性进行还原，即相当于关机再开机
        """
        desktop = db_api.get_desktop_by_uuid(desktop_uuid)
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        subnet = db_api.get_subnet_by_uuid(desktop.subnet_uuid)
        if not subnet:
            logger.error("subnet: %s not exist", desktop.subnet_uuid)
            return get_error_result("SubnetNotExist")
        desktop.active = False
        desktop.soft_update()
        ret = self._reboot_desktop(desktop, subnet)
        desktop.active = True
        desktop.soft_update()
        return ret

    def delete_desktop(self, desktop_uuid):
        """
        删除桌面组，不管什么类型桌面，全部删除
        """
        desktop = db_api.get_desktop_by_uuid(desktop_uuid)
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        # 教学桌面组有关联课表时，不能删除
        if db_api.get_course_with_all({"desktop_uuid": desktop_uuid}):
            return get_error_result("DesktopInUseByCourseSchedule", name=desktop.name)
        return self._delete_desktop(desktop)

    def update_desktop(self, data):
        """
        :param data:
        {
            "uuid": "",
            "value": {
                "name": ""
            }
        }
        :return:
        """
        desktop_uuid = data.get('uuid', '')
        desktop = db_api.get_desktop_by_uuid(desktop_uuid)
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        try:
            # 如果修改了教学桌面组的名称，需要对应修改yzy_course_template.desktops字段
            if data['value']['name'] != desktop.name:
                course_template_uuid_list = db_api.get_distinct_course_template_uuids_by_course(
                    {"desktop_uuid": desktop_uuid})
                for ct_uuid in course_template_uuid_list:
                    ct_obj = db_api.get_course_template_with_first({"uuid": ct_uuid[0]})
                    if ct_obj:
                        d_map = json.loads(ct_obj.desktops)
                        if desktop_uuid in d_map.keys():
                            d_map[desktop_uuid] = data['value']['name']
                            ct_obj.desktops = json.dumps(d_map)
                            logger.info("update desktop name[%s] to course_template[%s]" % (data['value']['name'], ct_uuid[0]))

            desktop.update(data['value'])
            desktop.soft_update()
        except Exception as e:
            logger.error("update desktop %s failed:%s", desktop_uuid, e)
            return get_error_result("DesktopUpdateFail", name=desktop.name)
        logger.info("update desktop %s success", desktop_uuid)
        return get_error_result("Success")


class PersonalDesktopController(BaseController):

    def _check_params(self, data):
        if not data:
            return False
        name = data.get('name', '')
        pool_uuid = data.get('pool_uuid', '')
        template_uuid = data.get('template_uuid', '')
        if not (name and pool_uuid and template_uuid):
            return False
        logger.info("check personal params ok")
        return True

    # def get_static_value(self, desktop_uuid, name, uuid, allocates):
    #     for allocate in allocates:
    #         if name == allocate['name']:
    #             info = {
    #                 "uuid": create_uuid(),
    #                 "desktop_uuid": desktop_uuid,
    #                 # "group_uuid": allocate['group_uuid'],
    #                 "user_uuid": allocate['user_uuid'],
    #                 "instance_uuid": uuid
    #             }
    #             return info
    #     return

    def get_static_user(self, name, allocates):
        for allocate in allocates:
            if name == allocate['name']:
                return allocate['user_uuid']
        return ''

    def create_personal_desktop(self, data):
        """
        创建个人桌面组，仅仅插入数据库记录，不启动桌面
        """
        if not self._check_params(data):
            return get_error_result("ParamError")

        template = db_api.get_instance_template(data['template_uuid'])
        if not template:
            logger.error("instance template: %s not exist", data['template_uuid'])
            return get_error_result("TemplateNotExist")
        if constants.EDUCATION_DESKTOP == template.classify:
            return get_error_result("TemplateEducationError", name=template.name)

        subnet_uuid = data.get('subnet_uuid', None)
        if subnet_uuid:
            subnet = db_api.get_subnet_by_uuid(data['subnet_uuid'])
            if not subnet:
                logger.error("subnet: %s not exist", data['subnet_uuid'])
                return get_error_result("SubnetNotExist")
            # 系统分配和固定分配，固定分配时有设置起始IP
            if constants.ALLOCATE_SYS_TYPE == data['allocate_type']:
                start_ip = subnet.start_ip
            else:
                start_ip = data['allocate_start']
            unused_ips = list()
            # 检测可用IP是否充足
            if not subnet.enable_dhcp:
                personal_used_ips = self.get_personal_used_ipaddr(subnet.uuid)
                all_ips = find_ips(start_ip, subnet.end_ip)
                if start_ip not in all_ips:
                    return get_error_result("IPNotInRange", ipaddr=start_ip)
                for ip in all_ips:
                    if ip not in personal_used_ips:
                        unused_ips.append(ip)
                logger.info("get unused ips")
                if len(unused_ips) < data['instance_num']:
                    return get_error_result("IPNotEnough")
        sys_base, data_base = self._get_instance_storage_path()
        if not (sys_base and sys_base):
            return get_error_result("InstancePathNotExist")
        try:
            # add personal desktop
            last_desktop = db_api.get_personal_desktop_order_by_order_num({})
            desktop_uuid = create_uuid()
            desktop_value = {
                "uuid": desktop_uuid,
                "name": data['name'],
                "owner_id": data['owner_id'],
                "pool_uuid": data['pool_uuid'],
                "template_uuid": data['template_uuid'],
                "network_uuid": data.get('network_uuid', ''),
                "subnet_uuid": data.get('subnet_uuid', ''),
                "allocate_type": data['allocate_type'],
                "allocate_start": data.get('allocate_start', ''),
                "vcpu": data['vcpu'],
                "ram": data['ram'],
                "os_type": template.os_type,
                "sys_restore": data['sys_restore'],
                "data_restore": data['data_restore'],
                "instance_num": data['instance_num'],
                "prefix": data['prefix'],
                "postfix": data['postfix'],
                "postfix_start": data.get('postfix_start', 1),
                "desktop_type": data['desktop_type'],
                "group_uuid": data.get('group_uuid', ''),
                "order_num": (last_desktop.order_num + 1) if last_desktop else 1
            }
            links = list()
            if constants.RANDOM_DESKTOP == data['desktop_type']:
                for group_uuid in data.get('groups', []):
                    info = {
                        "uuid": create_uuid(),
                        "group_uuid": group_uuid,
                        "desktop_uuid": desktop_uuid
                    }
                    links.append(info)
            # add instance
            self.used_macs = self.get_used_macs()
            instances = list()
            disks = list()
            # devices = db_api.get_devices_by_instance(template.uuid)
            devices = db_api.get_devices_with_all({"instance_uuid": template.uuid})
            postfix = int(data['postfix'])
            postfix_start = data.get('postfix_start', 1)
            for ipaddr, num in data['create_info'].items():
                node = db_api.get_node_with_first({"ip": ipaddr})
                for i in range(num):
                    # 桌面名称是前缀加几位数字
                    if len(str(postfix_start)) < postfix:
                        post = '0' * (postfix - len(str(postfix_start))) + str(postfix_start)
                    else:
                        post = str(postfix_start)
                    instance_name = data['prefix'] + post
                    instance_uuid = create_uuid()
                    mac = generate_mac(self.used_macs)
                    if constants.STATIC_DESKTOP == data['desktop_type']:
                        self.get_static_user(instance_name, data.get('allocates', []))
                    instance_value = {
                        "uuid": instance_uuid,
                        "name": instance_name,
                        "host_uuid": node.uuid,
                        "desktop_uuid": desktop_uuid,
                        "sys_storage": sys_base['uuid'],
                        "data_storage": data_base['uuid'],
                        "classify": 2,
                        "status": constants.STATUS_INACTIVE,
                        "ipaddr": generate_ips(unused_ips, self.used_ips) if data.get('subnet_uuid', '') else '',
                        "mac": mac,
                        "port_uuid": create_uuid(),
                        "user_uuid": self.get_static_user(instance_name, data.get('allocates', []))
                        if constants.STATIC_DESKTOP == data['desktop_type'] else '',
                        "spice_token": create_uuid()
                    }
                    instances.append(instance_value)
                    postfix_start += 1
                    for disk in devices:
                        info = {
                            "uuid": create_uuid(),
                            "type": disk.type,
                            "device_name": disk.device_name,
                            "image_id": disk['uuid'],
                            "instance_uuid": instance_uuid,
                            "boot_index": disk.boot_index,
                            "size": disk.size
                        }
                        disks.append(info)

            db_api.create_personal_desktop(desktop_value)
            # 随机桌面时，需要记录所有可以使用该桌面组的分组
            if constants.RANDOM_DESKTOP == data['desktop_type']:
                if links:
                    db_api.insert_with_many(models.YzyRandomDesktop, links)
            db_api.insert_with_many(models.YzyInstances, instances)
            db_api.insert_with_many(models.YzyInstanceDeviceInfo, disks)
            logger.info("create personal desktop %s success", data['name'])
        except Exception as e:
            logger.info("insert personal desktop info to db failed:%s", e)
            return get_error_result("DesktopCreateFail", name=data['name'])
        return get_error_result("Success", desktop_value)

    def start_personl_desktop(self, desktop_uuid):
        """
        个人桌面组开机操作，根据桌面组进行所有桌面的开机。对于系统盘还原的情况，就是创建虚拟机
        """
        desktop = db_api.get_personal_desktop_with_first({'uuid': desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")

        subnet = db_api.get_subnet_by_uuid(desktop.subnet_uuid)
        return self._start_desktop(desktop, subnet)

    def stop_personal_desktop(self, desktop_uuid, hard=False):
        """
        关机操作，根据桌面组进行所有桌面的关机。对于系统盘还原的情况，就是删除虚拟机（只删除系统盘）
        """
        desktop = db_api.get_personal_desktop_with_first({'uuid': desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        return self._stop_desktop(desktop, True, hard)

    def stop_personal_desktop_for_node(self, desktop_uuid, node_uuid):
        """
        关机操作，根据桌面组进行所有桌面的关机。对于系统盘还原的情况，就是删除虚拟机（只删除系统盘）
        """
        desktop = db_api.get_personal_desktop_with_first({'uuid': desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            logger.error("node %s not exist", node_uuid)
            return get_error_result("NodeNotExist", name="")
        return self._stop_desktop_for_node(desktop, node, True)

    def reboot_personal_desktop(self, desktop_uuid):
        """
        重启操作，根据盘的还原属性进行还原，即相当于关机再开机
        """
        desktop = db_api.get_personal_desktop_with_first({'uuid': desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        subnet = db_api.get_subnet_by_uuid(desktop.subnet_uuid)
        return self._reboot_desktop(desktop, subnet)

    def delete_personal_desktop(self, desktop_uuid):
        """
        删除桌面组，不管什么类型桌面，全部删除
        """
        desktop = db_api.get_personal_desktop_with_first({'uuid': desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        template = db_api.get_instance_template(desktop.template_uuid)
        if not template:
            return get_error_result("TemplateNotExist")

        logger.info("get intances in desktop:%s", desktop.name)
        instances = db_api.get_instance_by_desktop(desktop.uuid)
        all_task = list()
        failed_num = 0
        success_num = 0
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for instance in instances:
                logger.info("delete instance %s thread", instance.uuid)
                sys_base, data_base = self._get_storage_path_with_uuid(instance.sys_storage, instance.data_storage)
                future = executor.submit(self.delete_instance, instance, sys_base, data_base)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if not result:
                    failed_num += 1
                else:
                    success_num += 1

        db.session.flush()
        # if failed_num > 0:
        #     return get_error_result("DesktopDeleteFail", name=desktop.name,
        #                         data={"failed_num": failed_num, "success_num": success_num})
        # else:
        if constants.RANDOM_DESKTOP == desktop.desktop_type:
            randoms = db_api.get_random_desktop_with_all({"desktop_uuid": desktop.uuid})
            for item in randoms:
                item.soft_delete()
        desktop.soft_delete()
        logger.info("delete desktop %s success, success:%s, failed:%s", desktop.name, success_num, failed_num)
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def update_personal_desktop(self, data):
        """
        :param data:
        {
            "uuid": "",
            "value": {
                "name": ""
            }
        }
        :return:
        """
        desktop_uuid = data.get('uuid', '')
        desktop = db_api.get_personal_desktop_with_first({'uuid': desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        try:
            desktop.update(data['value'])
            desktop.soft_update()
        except Exception as e:
            logger.error("update desktop %s failed:%s", desktop_uuid, e)
            return get_error_result("DesktopUpdateFail", name=desktop.name)
        logger.info("update desktop %s success", desktop_uuid)
        return get_error_result("Success")

    def enter_maintenance(self, desktop_uuid):
        desktop = db_api.get_personal_desktop_with_first({'uuid': desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        try:
            desktop.maintenance = True
            desktop.soft_update()
        except Exception as e:
            logger.error("desktop enter maintenance %s failed:%s", desktop_uuid, e)
            return get_error_result("DesktopUpdateFail", name=desktop.name)
        logger.info("desktop enter maintenance %s success", desktop_uuid)
        return get_error_result("Success")

    def exit_maintenance(self, desktop_uuid):
        desktop = db_api.get_personal_desktop_with_first({'uuid': desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        try:
            desktop.maintenance = False
            desktop.soft_update()
        except Exception as e:
            logger.error("desktop exit maintenance %s failed:%s", desktop_uuid, e)
            return get_error_result("DesktopUpdateFail", name=desktop.name)
        logger.info("desktop exit maintenance %s success", desktop_uuid)
        return get_error_result("Success")


class InstanceController(BaseController):

    def start_instances(self, data):
        """
        桌面的批量开机, 如果是一个桌面，失败则提示原因。如果是多个，则统计失败和成功个数
        :param data:
            {
                "desktop_uuid": "4c41b1dc-35d6-11ea-bc23-000c295dd728",
                "desktop_type": 1,
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
            }
        :return:
        """
        # desktop_type = data.get('desktop_type', constants.EDUCATION_DESKTOP)
        # if constants.EDUCATION_DESKTOP == desktop_type:
        #     desktop = db_api.get_desktop_by_uuid(data['desktop_uuid'])
        # else:
        #     desktop = db_api.get_personal_desktop_with_first({'uuid': data['desktop_uuid']})
        desktop = db_api.get_desktop_by_uuid(data['desktop_uuid'])
        # 添加任务信息数据记录
        uuid = create_uuid()
        task_data = {
            "uuid": uuid,
            "task_uuid": data['desktop_uuid'],
            "name": constants.NAME_TYPE_MAP[3],
            "status": constants.TASK_RUNNING,
            "type": 3
        }
        db_api.create_task_info(task_data)
        task_obj = db_api.get_task_info_first({"uuid": uuid})
        try:
            if not desktop:
                desktop = db_api.get_personal_desktop_with_first({'uuid': data['desktop_uuid']})
                if not desktop:
                    logger.error("desktop %s not exist", data['desktop_uuid'])
                    task_obj.update({"status": constants.TASK_ERROR})
                    task_obj.soft_update()
                    return get_error_result("DesktopNotExist", name="")
            subnet = None
            if desktop.subnet_uuid:
                subnet = db_api.get_subnet_by_uuid(desktop.subnet_uuid)
                if not subnet:
                    logger.error("subnet: %s not exist", desktop.subnet_uuid)
                    task_obj.update({"status": constants.TASK_ERROR})
                    task_obj.soft_update()
                    return get_error_result("SubnetNotExist")
            template = db_api.get_instance_template(desktop.template_uuid)
            if not template:
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return get_error_result("TemplateNotExist")
            sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
            if not (sys_base and data_base):
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return get_error_result("InstancePathNotExist")

            logger.info("get intances in desktop:%s", desktop.name)
            instances = list()
            failed_num = 0
            success_num = 0
            result = db_api.get_instance_by_desktop(data['desktop_uuid'])
            for ins in data['instances']:
                for item in result:
                    if item.uuid == ins['uuid']:
                        instances.append(item)
                        break
                else:
                    logger.error("the instance %s not exists", ins['uuid'])
                    failed_num += 1
            # 并发启动
            all_task = list()
            with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
                for instance in instances:
                    logger.info("start instance %s thread", instance.uuid)
                    future = executor.submit(self.create_instance, desktop, subnet, instance, sys_base, data_base)
                    all_task.append(future)
                for future in as_completed(all_task):
                    result = future.result()
                    if result.get('code') != 0:
                        failed_num += 1
                    else:
                        success_num += 1
                time.sleep(1)

            db.session.flush()
            logger.info("start instances end, success:%s, failed:%s", success_num, failed_num)
            if 1 == len(data['instances']) and 1 == failed_num:
                # ret = get_error_result("InstanceStartFail", name="")
                # ret['msg'] = result['data'] if result.get('data') else result.get('msg')
                if result.get("data"):
                    if "Cannot allocate memory" in result['data']:
                        result['msg'] += "，内存不足"
                    else:
                        result['msg'] += "，%s" % result["data"]
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return result
        except Exception as e:
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            logger.error("instance start fail: %s", e)
            return get_error_result("OtherError")
        task_obj.update({"status": constants.TASK_COMPLETE})
        task_obj.soft_update()
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def stop_instances(self, data, hard=False, timeout=None):
        """
        桌面的批量关机,如果是一个桌面，失败则提示原因。如果是多个，则统计失败和成功个数
        :param data:
            {
                "desktop_uuid": "4c41b1dc-35d6-11ea-bc23-000c295dd728",
                "desktop_type": 2,
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
            }
        :return:
        """
        # desktop_type = data.get('desktop_type', constants.EDUCATION_DESKTOP)
        # if constants.EDUCATION_DESKTOP == desktop_type:
        #     desktop = db_api.get_desktop_by_uuid(data['desktop_uuid'])
        # else:
        #     desktop = db_api.get_personal_desktop_with_first({'uuid': data['desktop_uuid']})
        # 添加任务信息数据记录
        uuid = create_uuid()
        task_data = {
            "uuid": uuid,
            "task_uuid": data['desktop_uuid'],
            "name": constants.NAME_TYPE_MAP[4],
            "status": constants.TASK_RUNNING,
            "type": 4
        }
        db_api.create_task_info(task_data)
        task_obj = db_api.get_task_info_first({"uuid": uuid})
        try:
            personal = False
            desktop = db_api.get_desktop_by_uuid(data['desktop_uuid'])
            if not desktop:
                desktop = db_api.get_personal_desktop_with_first({'uuid': data['desktop_uuid']})
                if not desktop:
                    logger.error("desktop %s not exist", data['desktop_uuid'])
                    task_obj.update({"status": constants.TASK_ERROR})
                    task_obj.soft_update()
                    return get_error_result("DesktopNotExist", name="")
                personal = True

            logger.info("get instances in desktop:%s", desktop.name)
            instances = list()
            failed_num = 0
            success_num = 0
            result = db_api.get_instance_by_desktop(data['desktop_uuid'])
            for ins in data['instances']:
                for item in result:
                    if item.uuid == ins['uuid']:
                        instances.append(item)
                        break
                else:
                    logger.error("the instance %s not exists", ins['uuid'])
                    failed_num += 1
            all_task = list()
            with ThreadPoolExecutor(max_workers=2*constants.MAX_THREADS) as executor:
                for instance in instances:
                    logger.info("stop instance %s thread", instance.uuid)
                    future = executor.submit(self.stop_instance, instance, desktop, personal, hard, timeout)
                    all_task.append(future)
                for future in as_completed(all_task):
                    result = future.result()
                    if not result:
                        failed_num += 1
                    else:
                        success_num += 1

            db.session.flush()
            logger.info("stop instances end, success:%s, failed:%s", success_num, failed_num)
            if 1 == len(data['instances']) and 1 == failed_num:
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return get_error_result("InstanceStopFail", name="")
        except Exception as e:
            logger.error("instance stop fail :%s", e)
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("OtherError")
        task_obj.update({"status": constants.TASK_COMPLETE})
        task_obj.soft_update()
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def delete_instances(self, data):
        """
        桌面的批量删除，如果是一个桌面，删除失败则提示原因。如果是多个，则统计失败和成功个数
        :param data:
            {
                "desktop_uuid": "4c41b1dc-35d6-11ea-bc23-000c295dd728",
                "desktop_type": 2,
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
            }
        :return:
        """
        # desktop_type = data.get('desktop_type', constants.EDUCATION_DESKTOP)
        # if constants.EDUCATION_DESKTOP == desktop_type:
        #     desktop = db_api.get_desktop_by_uuid(data['desktop_uuid'])
        # else:
        #     desktop = db_api.get_personal_desktop_with_first({'uuid': data['desktop_uuid']})
        personal = False
        desktop = db_api.get_desktop_by_uuid(data['desktop_uuid'])
        if not desktop:
            desktop = db_api.get_personal_desktop_with_first({'uuid': data['desktop_uuid']})
            if not desktop:
                logger.error("desktop %s not exist", data['desktop_uuid'])
                return get_error_result("DesktopNotExist", name="")
            personal = True
        if 1 == len(data['instances']):
            result = db_api.get_instance_with_first({'uuid': data['instances'][0]['uuid']})
            if not result:
                return get_error_result("InstanceNotExist", name="")
            if constants.STATUS_ACTIVE == result.status:
                return get_error_result("PersonalInstanceActive", name=result.name)
        template = db_api.get_instance_template(desktop.template_uuid)
        if not template:
            return get_error_result("TemplateNotExist")

        logger.info("get intances in desktop:%s", desktop.name)
        instances = list()
        failed_num = 0
        success_num = 0
        result = db_api.get_instance_by_desktop(data['desktop_uuid'])
        for ins in data['instances']:
            for item in result:
                if item.uuid == ins['uuid']:
                    instances.append(item)
                    break
            else:
                logger.error("the instance %s not exists", ins['uuid'])
                failed_num += 1

        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for instance in instances:
                if personal and constants.STATUS_ACTIVE == instance.status:
                    logger.error("the instance is active, can not delete, name:%s, uuid:%s", instance.name, instance.uuid)
                    failed_num += 1
                    continue
                logger.info("delete instance %s thread", instance.uuid)
                sys_base, data_base = self._get_storage_path_with_uuid(instance.sys_storage, instance.data_storage)
                future = executor.submit(self.delete_instance, instance, sys_base, data_base)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if not result:
                    failed_num += 1
                else:
                    desktop.instance_num -= 1
                    success_num += 1
        db.session.flush()
        desktop.soft_update()
        logger.info("delete instances success, success:%s, failed:%s", success_num, failed_num)
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def reboot_instances(self, data):
        # desktop_type = data.get('desktop_type', constants.EDUCATION_DESKTOP)
        # if constants.EDUCATION_DESKTOP == desktop_type:
        #     desktop = db_api.get_desktop_by_uuid(data['desktop_uuid'])
        # else:
        #     desktop = db_api.get_personal_desktop_with_first({'uuid': data['desktop_uuid']})
        # 添加任务信息数据记录
        uuid = create_uuid()
        task_data = {
            "uuid": uuid,
            "task_uuid": data['desktop_uuid'],
            "name": constants.NAME_TYPE_MAP[5],
            "status": constants.TASK_RUNNING,
            "type": 5
        }
        db_api.create_task_info(task_data)
        task_obj = db_api.get_task_info_first({"uuid": uuid})
        try:
            desktop = db_api.get_desktop_by_uuid(data['desktop_uuid'])
            if not desktop:
                desktop = db_api.get_personal_desktop_with_first({'uuid': data['desktop_uuid']})
                if not desktop:
                    logger.error("desktop %s not exist", data['desktop_uuid'])
                    task_obj.update({"status": constants.TASK_ERROR})
                    task_obj.soft_update()
                    return get_error_result("DesktopNotExist", name="")
            subnet = None
            if desktop.subnet_uuid:
                subnet = db_api.get_subnet_by_uuid(desktop.subnet_uuid)
                if not subnet:
                    logger.error("subnet: %s not exist", desktop.subnet_uuid)
                    task_obj.update({"status": constants.TASK_ERROR})
                    task_obj.soft_update()
                    return get_error_result("SubnetNotExist")

            template = db_api.get_instance_template(desktop.template_uuid)
            if not template:
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return get_error_result("TemplateNotExist")
            sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
            if not (sys_base and data_base):
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return get_error_result("InstancePathNotExist")

            logger.info("get intances in desktop:%s", desktop.name)
            instances = list()
            failed_num = 0
            success_num = 0
            result = db_api.get_instance_by_desktop(data['desktop_uuid'])
            for ins in data['instances']:
                for item in result:
                    if item.uuid == ins['uuid']:
                        instances.append(item)
                        break
                else:
                    logger.error("the instance %s not exists", ins['uuid'])
                    failed_num += 1
            all_task = list()
            with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
                for instance in instances:
                    logger.info("reboot instance %s thread", instance.uuid)
                    future = executor.submit(self.reboot_instance, desktop, subnet, instance, sys_base, data_base)
                    all_task.append(future)
                for future in as_completed(all_task):
                    result = future.result()
                    if result.get('code') != 0:
                        failed_num += 1
                    else:
                        success_num += 1
            db.session.flush()
            logger.info("reboot instances end, success:%s, failed:%s", success_num, failed_num)
            if 1 == len(data['instances']) and 1 == failed_num:
                ret = get_error_result("InstanceRebootFail", name="")
                ret['msg'] = result['data'] if result.get('data') else result.get('msg')
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return ret
        except Exception as e:
            logger.error("instance reboot fail:%s", e)
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("OtherError")
        task_obj.update({"status": constants.TASK_COMPLETE})
        task_obj.soft_update()
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def check_education_available_ips(self, subnet, instance_num, origin_num):
        unused_ips = list()
        # 检测可用IP是否充足
        if not subnet.enable_dhcp:
            self.education_used_ips = self.get_education_used_ipaddr(subnet.uuid)
            all_ips = find_ips(subnet.start_ip, subnet.end_ip)
            for ip in all_ips:
                if ip not in self.education_used_ips:
                    unused_ips.append(ip)
            logger.info("get unused ips")
            if len(unused_ips) >= (instance_num + origin_num):
                return unused_ips

    def check_available_ips(self, subnet, start_ip, instance_num):
        unused_ips = list()
        # 检测可用IP是否充足
        if not subnet.enable_dhcp:
            used_ips = self.get_personal_used_ipaddr(subnet.uuid)
            all_ips = find_ips(start_ip, subnet.end_ip)
            for ip in all_ips:
                if ip not in used_ips:
                    unused_ips.append(ip)
            logger.info("get unused ips")
            if len(unused_ips) >= instance_num:
                return unused_ips

    def add_education_instances(self, data):
        """
        向桌面组添加桌面
        """
        desktop = db_api.get_desktop_by_uuid(data['desktop_uuid'])
        if not desktop:
            logger.error("desktop %s not exist", data['desktop_uuid'])
            return get_error_result("DesktopNotExist", name="")
        subnet = db_api.get_subnet_by_uuid(desktop.subnet_uuid)
        if not subnet:
            logger.error("subnet: %s not exist", desktop.subnet_uuid)
            return get_error_result("SubnetNotExist")
        unused_ips = self.check_education_available_ips(subnet, data['instance_num'], desktop.instance_num)
        if not unused_ips:
            return get_error_result("IPNotEnough")
        sys_base, data_base = self._get_instance_storage_path()
        if not (sys_base and sys_base):
            return get_error_result("InstancePathNotExist")
        # add instance
        template = db_api.get_instance_template(desktop.template_uuid)
        self.used_macs = self.get_used_macs()
        # 取所有的包括删除的，是为了找到删除掉的桌面对应的终端号
        origin_instances = db_api.get_instance_all({'desktop_uuid': desktop.uuid})
        for instance in origin_instances:
            if not instance.deleted:
                # 如果添加数量大于删除掉的，新分配的IP要去除目前桌面已占用的
                if instance.ipaddr in unused_ips:
                    unused_ips.remove(instance.ipaddr)

        deleted_count = 0
        recovers = list()
        recoverd = list()
        for ins in origin_instances:
            if ins.deleted:
                # deleted_instance.host_uuid = node.uuid
                recovers.append(ins)
                deleted_count += 1
                if deleted_count == data['instance_num']:
                    # 添加的数量小于等于曾经删除的数量情况，取要添加的个数桌面进行恢复
                    for ipaddr, num in data['create_info'].items():
                        node = db_api.get_node_with_first({'ip': ipaddr})
                        for j in range(num):
                            for item in recovers:
                                if item not in recoverd:
                                    item.deleted = False
                                    item.mac = generate_mac(self.used_macs)
                                    item.host_uuid = node.uuid
                                    item.sys_storage = sys_base['uuid']
                                    item.data_storage = data_base['uuid']
                                    item.status = constants.STATUS_INACTIVE
                                    # devices = db_api.get_devices_by_instance(template.uuid)
                                    devices = db_api.get_devices_with_all({"instance_uuid": template.uuid})
                                    disks = list()
                                    for disk in devices:
                                        info = {
                                            "uuid": create_uuid(),
                                            "type": disk.type,
                                            "device_name": disk.device_name,
                                            "image_id": disk['uuid'],
                                            "instance_uuid": item.uuid,
                                            "boot_index": disk.boot_index,
                                            "size": disk.size
                                        }
                                        disks.append(info)
                                    item.soft_update()
                                    db_api.insert_with_many(models.YzyInstanceDeviceInfo, disks)
                                    logger.info("recover instance, uuid:%s, name:%s, ipaddr:%s", item.uuid, item.name, ipaddr)
                                    recoverd.append(item)
                                    break
                    logger.info("get the deleted instance is larger than add num")
                    desktop.instance_num += data['instance_num']
                    desktop.soft_update()
                    return get_error_result("Success", data)
        else:
            instances = list()
            insert_instances = list()
            insert_disks = list()
            # devices = db_api.get_devices_by_instance(template.uuid)
            devices = db_api.get_devices_with_all({"instance_uuid": template.uuid})
            postfix = int(desktop.postfix)
            postfix_start = len(origin_instances) + desktop.postfix_start
            last_terminal = 0
            if recovers:
                last_terminal = recovers[-1].terminal_id
            if int(data['instance_num'] - deleted_count) > 0:
                terminal_id = db_api.get_instance_max_terminal_id({'desktop_uuid': desktop.uuid})
                # 添加的数量大于曾经删除的桌面，要额外新加桌面，而终端IP需要连续往上加
                if terminal_id > last_terminal:
                    last_terminal = terminal_id
                # 未使用IP的控制决定了新加桌面的分配
                for item in recovers:
                    if item.ipaddr in unused_ips:
                        unused_ips.remove(item.ipaddr)
            last_terminal += 1
            for i in range(data['instance_num'] - deleted_count):
                # 添加的数量大于曾经删除的桌面，要额外新加桌面
                if len(str(postfix_start)) < postfix:
                    post = '0' * (postfix - len(str(postfix_start))) + str(postfix_start)
                else:
                    post = str(postfix_start)
                instance_name = desktop.prefix + post
                instance_uuid = create_uuid()
                mac = generate_mac(self.used_macs)
                instance_value = {
                    "uuid": instance_uuid,
                    "name": instance_name,
                    "classify": 1,
                    "desktop_uuid": desktop.uuid,
                    "sys_storage": sys_base['uuid'],
                    "data_storage": data_base['uuid'],
                    "terminal_id": last_terminal,
                    "status": constants.STATUS_INACTIVE,
                    "ipaddr": generate_ips(unused_ips, self.education_used_ips) if desktop.subnet_uuid else '',
                    "mac": mac,
                    "port_uuid": create_uuid()
                }
                instances.append(instance_value)
                last_terminal += 1
                postfix_start += 1
                for disk in devices:
                    info = {
                        "uuid": create_uuid(),
                        "type": disk.type,
                        "device_name": disk.device_name,
                        "image_id": disk['uuid'],
                        "instance_uuid": instance_uuid,
                        "boot_index": disk.boot_index,
                        "size": disk.size
                    }
                    insert_disks.append(info)
            # devices = db_api.get_devices_by_instance(template.uuid)
            devices = db_api.get_devices_with_all({"instance_uuid": template.uuid})
            # 上面计算好要恢复的桌面和要新加的桌面，这里进行统一添加
            for ipaddr, num in data['create_info'].items():
                node = db_api.get_node_with_first({'ip': ipaddr})
                for j in range(num):
                    if recovers:
                        item = recovers.pop()
                        item.deleted = False
                        item.mac = generate_mac(self.used_macs)
                        item.host_uuid = node.uuid
                        item.sys_storage = sys_base['uuid']
                        item.data_storage = data_base['uuid']
                        item.status = constants.STATUS_INACTIVE
                        disks = list()
                        for disk in devices:
                            info = {
                                "uuid": create_uuid(),
                                "type": disk.type,
                                "device_name": disk.device_name,
                                "image_id": disk['uuid'],
                                "instance_uuid": item.uuid,
                                "boot_index": disk.boot_index,
                                "size": disk.size
                            }
                            disks.append(info)
                        item.soft_update()
                        db_api.insert_with_many(models.YzyInstanceDeviceInfo, disks)
                        logger.info("recover instance, uuid:%s, name:%s", item.uuid, item.name)
                    else:
                        if instances:
                            item = instances.pop()
                            item['host_uuid'] = node.uuid
                            insert_instances.append(item)
                            logger.info("add instance, name:%s, terminal_id:%s", item['name'], item['terminal_id'])
            try:
                if insert_instances:
                    insert_instances.reverse()
                    db_api.insert_with_many(models.YzyInstances, insert_instances)
                    db_api.insert_with_many(models.YzyInstanceDeviceInfo, insert_disks)
                desktop.instance_num += data['instance_num']
                desktop.soft_update()
                logger.info("create instance success")
            except Exception as e:
                logging.info("insert instance info to db failed:%s", e)
                return get_error_result("InstanceCreateFail", desktop=desktop.name)
        return get_error_result("Success", data)

    def add_instances(self, data):
        """
        向桌面组添加桌面，个人桌面组中添加桌面时，和分组或者用户的对应关系是额外的操作
        """
        desktop_uuid = data.get('desktop_uuid', '')
        if not desktop_uuid:
            return get_error_result("ParamError")

        desktop_type = data.get('desktop_type', constants.EDUCATION_DESKTOP)
        if constants.EDUCATION_DESKTOP == desktop_type:
            return self.add_education_instances(data)
        else:
            return self.add_personal_instances(data)

    def add_personal_instances(self, data):
        desktop = db_api.get_personal_desktop_with_first({'uuid': data['desktop_uuid']})
        if not desktop:
            logger.error("desktop %s not exist", data['desktop_uuid'])
            return get_error_result("DesktopNotExist", name="")
        # 个人桌面组只有使用了子网时才需要检测可用IP数量
        if desktop.subnet_uuid:
            subnet = db_api.get_subnet_by_uuid(desktop.subnet_uuid)
            if not subnet:
                logger.error("subnet: %s not exist", desktop.subnet_uuid)
                return get_error_result("SubnetNotExist")
            if constants.ALLOCATE_SYS_TYPE == desktop.allocate_type:
                start_ip = subnet.start_ip
            else:
                start_ip = desktop.allocate_start
            unused_ips = self.check_available_ips(subnet, start_ip, data['instance_num'])
            if not unused_ips:
                return get_error_result("IPNotEnough")
        sys_base, data_base = self._get_instance_storage_path()
        if not (sys_base and sys_base):
            return get_error_result("InstancePathNotExist")

        # add instance
        template = db_api.get_instance_template(desktop.template_uuid)
        self.used_macs = self.get_used_macs()
        instances = list()
        disks = list()
        # devices = db_api.get_devices_by_instance(template.uuid)
        devices = db_api.get_devices_with_all({"instance_uuid": template.uuid})
        all_ins = db_api.get_instance_with_all({'desktop_uuid': desktop.uuid})
        if not all_ins:
            postfix_start = 1
        else:
            postfix_start = int(all_ins[-1].name.split(desktop.prefix)[-1]) + 1
        postfix = int(desktop.postfix)
        prefix = data['prefix'] if data.get("prefix", None) else desktop.prefix
        for ipaddr, num in data['create_info'].items():
            node = db_api.get_node_with_first({'ip': ipaddr})
            for i in range(num):
                # 桌面名称是前缀加几位数字
                if len(str(postfix_start)) < postfix:
                    post = '0' * (postfix - len(str(postfix_start))) + str(postfix_start)
                else:
                    post = str(postfix_start)
                instance_name = prefix + post
                instance_uuid = create_uuid()
                mac = generate_mac(self.used_macs)
                instance_value = {
                    "uuid": instance_uuid,
                    "name": instance_name,
                    "host_uuid": node.uuid,
                    "classify": 2,
                    "desktop_uuid": desktop.uuid,
                    "sys_storage": sys_base['uuid'],
                    "data_storage": data_base['uuid'],
                    "status": constants.STATUS_INACTIVE,
                    "ipaddr": generate_ips(unused_ips, self.used_ips) if desktop.subnet_uuid else '',
                    "mac": mac,
                    "port_uuid": create_uuid()
                }
                instances.append(instance_value)
                postfix_start += 1
                for disk in devices:
                    info = {
                        "uuid": create_uuid(),
                        "type": disk.type,
                        "device_name": disk.device_name,
                        "image_id": disk['uuid'],
                        "instance_uuid": instance_uuid,
                        "boot_index": disk.boot_index,
                        "size": disk.size
                    }
                    disks.append(info)
        try:
            db_api.insert_with_many(models.YzyInstances, instances)
            db_api.insert_with_many(models.YzyInstanceDeviceInfo, disks)
            desktop.instance_num += len(instances)
            desktop.soft_update()
            logger.info("create instance success")
        except Exception as e:
            logging.info("insert instance info to db failed:%s", e)
            return get_error_result("InstanceCreateFail", desktop=desktop.name)
        return get_error_result("Success", data)

    def add_group(self, data):
        desktop_uuid = data.get('desktop_uuid', '')
        if not desktop_uuid:
            return get_error_result("ParamError")

        desktop = db_api.get_personal_desktop_with_first({'uuid': data['desktop_uuid']})
        if not desktop:
            logger.error("desktop %s not exist", data['desktop_uuid'])
            return get_error_result("DesktopNotExist", name="")
        success_num = 0
        failed_num = 0
        links = list()
        for group in data.get('groups', []):
            if not db_api.get_group_with_first({'uuid': group['group_uuid']}):
                logger.error("the group not exists, name:%s, uuid:%s", group['group_name'], group['group_uuid'])
                failed_num += 1
                continue
            if db_api.get_random_desktop_with_first({'desktop_uuid': desktop.uuid, 'group_uuid': group['group_uuid']}):
                logger.error("the group already bind with this desktop, desktop_uuid:%s, group_uuid:%s",
                             desktop.uuid, group['group_uuid'])
                failed_num += 1
                continue
            info = {
                "uuid": create_uuid(),
                'desktop_uuid': desktop_uuid,
                'group_uuid': group['group_uuid']
            }
            links.append(info)
            success_num += 1
        if links:
            db_api.insert_with_many(models.YzyRandomDesktop, links)
            logger.info("add group to random desktop")
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def delete_group(self, data):
        success_num = 0
        failed_num = 0
        for group in data['groups']:
            bind = db_api.get_random_desktop_with_first({'uuid': group['uuid']})
            if bind:
                bind.soft_delete()
                success_num += 1
            else:
                logger.error("the group bind not exist, uuid:%s", group['uuid'])
                failed_num += 1
        logger.info("delete group bind success")
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def change_bind(self, data):
        instance_uuid = data.get('instance_uuid', '')
        instance = db_api.get_instance_with_first({'uuid': instance_uuid})
        if not instance:
            return get_error_result("InstanceNotExist", name='')
        user_uuid = data.get('user_uuid', '')
        instance.user_uuid = user_uuid
        instance.soft_update()
        logger.info("change instance %s bind to user %s success", instance.uuid, data.get('user_uuid', ''))
        return get_error_result("Success")

    def change_group(self, data):
        desktop_uuid = data.get('desktop_uuid', '')
        desktop = db_api.get_personal_desktop_with_first({'uuid': data['desktop_uuid']})
        if not desktop:
            logger.error("desktop %s not exist", data['desktop_uuid'])
            return get_error_result("DesktopNotExist", name="")

        group_uuid = data.get('group_uuid', '')
        group = db_api.get_group_with_first({"uuid": group_uuid})
        if not group:
            return get_error_result("GroupNotExists", name='')

        users = db_api.get_group_user_with_all({'group_uuid': group_uuid})
        instances = db_api.get_instance_with_all({"desktop_uuid": desktop_uuid})
        used = list()
        for instance in instances:
            for user in users:
                if not user.enabled:
                    continue
                if user.uuid in used:
                    continue
                instance.user_uuid = user.uuid
                instance.soft_update()
                used.append(user.uuid)
                break
            else:
                instance.user_uuid = ''
                instance.soft_update()
        desktop.group_uuid = group.uuid
        desktop.soft_update()
        logger.info("desktop %s change group %s success", desktop.name, group.name)
        return get_error_result("Success")

    def start_instance_with_uuid(self, uuid):
        instance = db_api.get_instance_with_first({"uuid": uuid})
        if not instance:
            logger.error("instance: %s not exist", uuid)
            return get_error_result("InstanceNotExist", name='')
        if constants.EDUCATION_DESKTOP == instance.classify:
            desktop = db_api.get_desktop_by_uuid(instance.desktop_uuid)
        elif constants.PERSONAL_DEKSTOP == instance.classify:
            desktop = db_api.get_personal_desktop_with_first({"uuid": instance.desktop_uuid})
        else:
            return get_error_result("ParamError")
        subnet = None
        if desktop.subnet_uuid:
            subnet = db_api.get_subnet_by_uuid(desktop.subnet_uuid)
            if not subnet:
                logger.error("subnet: %s not exist", desktop.subnet_uuid)
                return get_error_result("SubnetNotExist")
        template = db_api.get_instance_template(desktop.template_uuid)
        sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
        if not (sys_base and sys_base):
            return get_error_result("InstancePathNotExist")

        return self.create_instance(desktop, subnet, instance, sys_base, data_base)

    def get_console(self, data):
        uuid = data.get("uuid", '')
        instance = db_api.get_instance_with_first({"uuid": uuid})
        if not instance:
            instance = db_api.get_instance_template(uuid)
            if not instance:
                logger.error("instance: %s not exist", uuid)
                return get_error_result("InstanceNotExist", name='')

        host = db_api.get_node_with_first({"uuid": instance.host_uuid})
        info = {
            "uuid": instance.uuid,
            "name": instance.name
        }
        rep_json = self._get_instance_status(host.ip, info)
        if rep_json.get('code') != 0:
            return get_error_result("InstancePowerOff", name=instance.name)
        if rep_json['data'].get('state') != constants.DOMAIN_STATE['running']:
            return get_error_result("InstancePowerOff", name=instance.name)
        node = db_api.get_controller_node()
        websockify_url = "ws://%s:%s/websockify/?token=%s" % (node.ip, constants.WEBSOCKIFY_PORT, instance.uuid)
        logger.debug("get console success, websockify_url: %s", websockify_url)
        return get_error_result("Success", {'websockify_url': websockify_url})
