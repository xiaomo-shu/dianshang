import time
import os
import functools
from datetime import datetime, timedelta
import logging
import json
import ipaddress
import netaddr
import collections
import hashlib
from threading import Thread
from flask import jsonify
from .desktop_ctl import BaseController
from yzy_server.database import apis as db_api
from common.utils import build_result, create_uuid, find_ips, is_ip_addr, single_lock, compute_post, voi_terminal_post
from common import constants
from yzy_server.database import models


logger = logging.getLogger(__name__)


class VoiTerminalController(object):
    def _get_template_storage_path(self):
        template_sys = db_api.get_template_sys_storage()
        template_data = db_api.get_template_data_storage()
        if not template_sys:
            sys_base = constants.DEFAULT_SYS_PATH
        else:
            sys_base = template_sys.path
        sys_path = os.path.join(sys_base, 'instances')
        if not template_data:
            data_base = constants.DEFAULT_DATA_PATH
        else:
            data_base = template_data.path
        data_path = os.path.join(data_base, 'datas')
        return sys_path, data_path

    def education_group(self, data):
        logger.info("get data: {}".format(data))
        terminal_ip = data.get("terminal_ip", "")
        if not is_ip_addr(terminal_ip):
            return build_result("ParamError")
        _group = None
        edu_groups = db_api.get_item_with_all(models.YzyVoiGroup, {"group_type": constants.EDUCATION_DESKTOP})
        for group in edu_groups:
            start_ip = group.start_ip
            end_ip = group.end_ip
            if terminal_ip in find_ips(start_ip, end_ip):
                _group = group
                break
        if not _group:
            return build_result("Success")
        ret = {
            "name": _group.name,
            "uuid": _group.uuid,
        }
        logger.info("return data: {}".format(ret))
        return build_result("Success", ret)

    def education_groups(self):
        edu_groups = db_api.get_item_with_all(models.YzyVoiGroup, {"group_type": constants.EDUCATION_DESKTOP})
        ret = {
            "groups": [x.uuid for x in edu_groups]
        }
        return build_result("Success", ret)

    def terminal_desktop_bind(self, data):
        logger.info("terminal desktop bind data: {}".format(data))
        try:
            terminal_uuid = data.get("terminal_uuid", "")
            desktop_uuid = data.get("desktop_uuid", "")
            desktop = db_api.get_item_with_first(models.YzyVoiDesktop, {"uuid": desktop_uuid})
            if not desktop:
                logger.error("terminal desktop bind desktop not exist: %s", desktop_uuid)
                return build_result("VOIDesktopGroupNotExist")
            bind_info = {
                "uuid": create_uuid(),
                "terminal_uuid": terminal_uuid,
                "desktop_uuid": desktop_uuid
            }
            db_api.create_voi_terminal_desktop_bind(bind_info)
            logger.info("terminal desktop bind data: {} success".format(bind_info))
            return build_result("Success")
        except Exception as e:
            logger.error("", exc_info=True)
            return build_result("OtherError")

    @single_lock
    def create_terminal_desktop_bind(self, data):
        """
            'group_uuid','terminal_uuid','terminal_id','mac',
            'ip','mask','gateway','dns1','dns2','is_dhcp',
        """
        logger.info("create terminal desktop bind data: {}".format(data))
        try:
            terminal_uuid = data.get("terminal_uuid", "")
            terminal_id = data.get("terminal_id", "")
            group_uuid = data.get("group_uuid", "")
            terminal_mac = data.get("mac", "")
            bind_info = {}
            # group_uuid != input group_uuid, then delete all old data
            db_api.delete_voi_terminal_desktops(group_uuid, terminal_uuid)
            # get all desktop groups
            qry_desktop_groups = db_api.get_item_with_all(models.YzyVoiDesktop, {"group_uuid": group_uuid})
            for qry in qry_desktop_groups:
                desktop_group_uuid = qry.uuid
                # one (desktop_group_uuid, terminal_id) only one row
                qry_exists = db_api.get_item_with_first(models.YzyVoiTerminalToDesktops,
                                                        {"desktop_group_uuid": desktop_group_uuid,
                                                         "terminal_uuid": terminal_uuid})
                if qry_exists:
                    logger.info('continue: {}'.format(terminal_mac))
                    continue
                logger.info('desktop_group_uuid: {}, qry.ip_detail: {}'.format(desktop_group_uuid, qry.ip_detail))
                desktop_is_dhcp = 0
                if qry.ip_detail:
                    ip_detail = json.loads(qry.ip_detail)
                    desktop_is_dhcp = int(ip_detail.get("auto", True))
                    desktop_start_ip = ip_detail.get("start_ip", "")
                    desktop_mask = ip_detail.get("netmask", "")
                    desktop_gateway = ip_detail.get("gateway", "")
                    desktop_dns1 = ip_detail.get("dns_master", "")
                    desktop_dns2 = ip_detail.get("dns_slave", "")
                desktop_ip_info = {}
                if bool(qry.use_bottom_ip):
                    logger.info('desktop_group_uuid: {}, qry.use_bottom_ip: {}'.format(desktop_group_uuid,
                                                                                       qry.use_bottom_ip))
                    desktop_ip_info = {
                        "desktop_is_dhcp": data.get("is_dhcp", ""),
                        "desktop_ip": data.get("ip", ""),
                        "desktop_mask": data.get("mask", ""),
                        "desktop_gateway": data.get("gateway", ""),
                        "desktop_dns1": data.get("dns1", ""),
                        "desktop_dns2": data.get("dns2", ""),
                    }
                elif desktop_is_dhcp:
                    logger.info('desktop_group_uuid: {}, desktop_is_dhcp: {}'.format(desktop_group_uuid,
                                                                                       desktop_is_dhcp))
                    desktop_ip_info = {
                        "desktop_is_dhcp": 1,
                        "desktop_ip": "",
                        "desktop_mask": "",
                        "desktop_gateway": "",
                        "desktop_dns1": "",
                        "desktop_dns2": "",
                    }
                else:
                    logger.info('desktop_group_uuid: {}, static ip'.format(desktop_group_uuid))
                    # get ip pool use start_ip and netmask, filter yzy_voi_terminal_desktops ips, get least ip
                    netmask_bits = netaddr.IPAddress(desktop_mask).netmask_bits()
                    network = ipaddress.ip_interface(desktop_start_ip + '/' + str(netmask_bits)).network
                    original_ip_pool = [x for x in network.hosts() if x >= ipaddress.IPv4Address(desktop_start_ip)]
                    # get used ip in this desktop_group_uuid
                    qry_ips = db_api.get_item_with_all(models.YzyVoiTerminalToDesktops,
                                                       {"desktop_group_uuid": desktop_group_uuid})
                    used_ip_pool = [ipaddress.IPv4Address(qry.desktop_ip) for qry in qry_ips]
                    available_ip_pool = [ip for ip in original_ip_pool if ip not in used_ip_pool]
                    if available_ip_pool:
                        desktop_ip = min(available_ip_pool).compressed
                        desktop_ip_info = {
                            "desktop_is_dhcp": 0,
                            "desktop_ip": desktop_ip,
                            "desktop_mask": desktop_mask,
                            "desktop_gateway": desktop_gateway,
                            "desktop_dns1": desktop_dns1,
                            "desktop_dns2": desktop_dns2,
                        }
                    else:  # use use_bottom_ip
                        logger.info('desktop_group_uuid: {}, no availabel_ip'.format(desktop_group_uuid))
                        desktop_ip_info = {
                            "desktop_is_dhcp": data.get("is_dhcp", ""),
                            "desktop_ip": data.get("ip", ""),
                            "desktop_mask": data.get("mask", ""),
                            "desktop_gateway": data.get("gateway", ""),
                            "desktop_dns1": data.get("dns1", ""),
                            "desktop_dns2": data.get("dns2", ""),
                        }
                bind_info = {
                    "uuid": create_uuid(),
                    "group_uuid": group_uuid,
                    "terminal_uuid": terminal_uuid,
                    "desktop_group_uuid": desktop_group_uuid,
                    "terminal_mac": terminal_mac,
                }
                bind_info.update(desktop_ip_info)
                db_api.create_voi_terminal_desktop_bind(bind_info)
            logger.info("terminal desktop bind data: {} success".format(bind_info))
            return build_result("Success")
        except Exception as e:
            logger.error("", exc_info=True)
            return build_result("OtherError")

    def update_terminal_desktop_bind(self, data):
        """
            'new_group_uuid','terminal_mac'
        """
        logger.info("update desktop_status data: {}".format(data))
        try:
            desktop_group_uuid = data.get('desktop_group_uuid', None)
            terminal_mac = data.get('mac', None)
            cmd = data.get("cmd", None)
            desktop_ip_info = {
                "desktop_is_dhcp": data.get("is_dhcp", 0),
                "desktop_ip": data.get("ip", ""),
                "desktop_mask": data.get("netmask", ""),
                "desktop_gateway": data.get("gateway", ""),
                "desktop_dns1": data.get("dns1", ""),
                "desktop_dns2": data.get("dns2", "")
            }
            if cmd == "login" and desktop_group_uuid:
                update_data = {
                    "desktop_group_uuid": desktop_group_uuid,
                    "terminal_mac": terminal_mac,
                    "desktop_status": 1
                }
                # get desktop_group ip_detail, if is dhcp, then update ip info
                desktop_group = db_api.get_item_with_first(models.YzyVoiDesktop, {'uuid': desktop_group_uuid})
                if desktop_group and not desktop_group.use_bottom_ip and desktop_group.ip_detail:
                    ip_detail = json.loads(desktop_group.ip_detail)
                    is_dhcp = ip_detail.get('auto', False)
                    if is_dhcp:
                        update_data.update(desktop_ip_info)
                logger.info('update table data: {}'.format(update_data))
                db_api.update_voi_terminal_desktop_info(update_data)
            elif cmd == "logout" and not desktop_group_uuid:
                update_data = {
                    "terminal_mac": terminal_mac,
                    "desktop_status": 0
                }
                logger.info('update table data: {}'.format(update_data))
                db_api.update_voi_terminal_desktop_info(update_data)
            else:
                logger.error("request message error: {}".format(data))
                return build_result("MessageError")
            return build_result("Success")
        except Exception as e:
            logger.error("", exc_info=True)
            return build_result("OtherError")

    def delete_terminal_desktop_bind(self, data):
        """
            'new_group_uuid','terminal_mac'
        """
        logger.info("delete terminal desktop bind data: {}".format(data))
        try:
            terminal_mac = data.get("terminal_mac", "")
            new_group_uuid = data.get("new_group_uuid", "")
            # group_uuid != input group_uuid, then delete all old data
            db_api.delete_voi_terminal_desktops(new_group_uuid, terminal_mac)
            return build_result("Success")
        except Exception as e:
            logger.error("", exc_info=True)
            return build_result("OtherError")

    def order_terminal_desktop_ip(self, data):
        """
            "terminal_id_list": terminal_id_list,
            "group_uuid": group_uuid,
            "terminal_mac_list": terminal_mac_list
        """
        logger.info("order terminal desktop ip data: {}".format(data))
        try:
            group_uuid = data.get("group_uuid", "")
            terminal_mac_list = data.get("terminal_mac_list", "")
            terminal_id_list = data.get("terminal_id_list", "")
            if terminal_mac_list:
                terminals_list = list(zip(terminal_id_list, terminal_mac_list))
                terminals_list = sorted(terminals_list, key=lambda x: x[0])
            else:
                logger.warning('request terminal_mac_list is null, please check!!1')
                return build_result("Success")
            # group_uuid get all desktop groups
            qry_desktop_groups = db_api.get_item_with_all(models.YzyVoiDesktop, {'group_uuid': group_uuid})
            for desktop_group in qry_desktop_groups:
                if not desktop_group.use_bottom_ip and desktop_group.ip_detail:
                    ip_detail = json.loads(desktop_group.ip_detail)
                    desktop_is_dhcp = ip_detail.get("auto", True)
                    if not desktop_is_dhcp:
                        desktop_start_ip = ip_detail.get("start_ip", "")
                        desktop_mask = ip_detail.get("netmask", "")
                        desktop_gateway = ip_detail.get("gateway", "")
                        desktop_dns1 = ip_detail.get("dns_master", "")
                        desktop_dns2 = ip_detail.get("dns_slave", "")
                        netmask_bits = netaddr.IPAddress(desktop_mask).netmask_bits()
                        network = ipaddress.ip_interface(desktop_start_ip + '/' + str(netmask_bits)).network
                        desktop_ip_pool = [x for x in network.hosts() if x >= ipaddress.IPv4Address(desktop_start_ip)]
                        if desktop_ip_pool:
                            for terminal_id, terminal_mac in terminals_list:
                                set_ip_detail = {}
                                if desktop_ip_pool:
                                    desktop_ip = min(desktop_ip_pool)
                                    set_ip_detail = {
                                        "desktop_is_dhcp": 0,
                                        "desktop_ip": desktop_ip.compressed,
                                        "desktop_mask": desktop_mask,
                                        "desktop_gateway": desktop_gateway,
                                        "desktop_dns1": desktop_dns1,
                                        "desktop_dns2": desktop_dns2,
                                    }
                                    desktop_ip_pool.remove(desktop_ip)
                                    logger.debug('terminal_id: {}, terminal_mac: {}, ip: {}'.format(
                                        terminal_id, terminal_mac, desktop_ip))
                                else:
                                    # no more available ip, set desktop ip use bottom ip
                                    requst_data = {
                                        "handler": "WebTerminalHandler",
                                        "command": "get_terminal_ip",
                                        "data": {
                                            'mac': terminal_mac
                                        }
                                    }
                                    ret = voi_terminal_post("/api/v1/voi/terminal/command/", requst_data)
                                    if ret.get("code", -1) != 0:
                                        logger.error("voi_terminal_post request: {}, ret: {}".format(requst_data, ret))
                                        return ret
                                    bottom_ip = ret.get("data", None)
                                    set_ip_detail = {
                                        "desktop_is_dhcp": 0,
                                        "desktop_ip": bottom_ip['ip'],
                                        "desktop_mask": bottom_ip['mask'],
                                        "desktop_gateway": bottom_ip['gateway'],
                                        "desktop_dns1": bottom_ip['dns1'],
                                        "desktop_dns2": bottom_ip['dns2'],
                                    }
                                # update database table  set_ip_detail
                                db_api.update_voi_terminal_desktop_bind(desktop_group.uuid,
                                                                        terminal_mac,
                                                                        set_ip_detail)
                        else:
                            logger.warning('desktop group ip setup error, no available ip')

            return build_result("Success")
        except Exception as e:
            logger.error("", exc_info=True)
            return build_result("OtherError")

    def create_share_disk_torrent(self, disk_info, version):
        disks = list()
        disk_uuid = disk_info["uuid"]
        base_path = disk_info["base_path"]
        backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
        for i in range(version + 1):
            file_path = os.path.join(backing_dir, constants.VOI_SHARE_BASE_PREFIX % str(i) + disk_uuid)
            if os.path.exists(file_path):
                torrent_path = file_path + ".torrent"
                disks.append({"file_path": file_path, "torrent_path": torrent_path})
        data = {
            "command": "create_torrent",
            "data": {
                "torrents": disks
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", data)
        if ret.get("code", -1) != 0:
            logger.error("threading voi share disk create disk fail torrent :%s", ret)
            return ret
        logger.info("threading voi share disk create disk torrent success!!!")
        return ret

    def create_share_disk(self, data):
        """
        创建共享数据盘
        {
            "group_uuid": "xxxxxx"
            "disk_size": 5,  # 共享盘大小
            "enable" : 0,    # 是否启用
            "restore": 0     # 还原与不还原
        }
        :param data:
        :return:
        """
        """
         {
            "command": "create_share",
            "handler": "VoiHandler",
            "data": {
                "disk_info": {
                    'uuid': '2f110de8-78d8-11ea-ad5d-000c29e84b9c',
                    'base_path': '/opt/slow/instances'
                }
                "version": 0
            }
        }
        """
        logger.info("terminal share disk create data: {}".format(data))
        try:
            # disk_uuid = create_uuid()
            version = 0
            node = db_api.get_controller_node()
            sys_base, data_base = self._get_template_storage_path()
            disk_info = dict()
            disk_info["uuid"] = create_uuid()
            disk_info["base_path"] = sys_base
            disk_info["size"] = data["disk_size"]
            command_data = {
                "command": "create_share",
                "handler": "VoiHandler",
                "data": {
                    "disk_info": disk_info,
                    "version": version
                }
            }
            logger.info("create share disk %s", disk_info)
            rep_json = compute_post(node.ip, command_data, timeout=600)
            if rep_json.get("code", -1) != 0:
                logger.error("create voi share disk:%s failed, error:%s", disk_info, rep_json.get('data'))
                # message = rep_json['data'] if rep_json.get('data', None) else rep_json['msg']
                return jsonify(rep_json)
            # 记录数据库
            share_disk = {
                "group_uuid": data["group_uuid"],
                "uuid": disk_info["uuid"],
                "disk_size": data["disk_size"],
                "enable": data["enable"],
                "restore": data["restore"]
            }
            db_api.create_voi_terminal_share(share_disk)
            # todo 生成bt种子
            # 生成种子文件
            task = Thread(target=self.create_share_disk_torrent, args=(disk_info,version))
            task.start()
            logger.info("create terminal voi share disk data: {} success".format(share_disk))
            return build_result("Success", {"disk": share_disk})
        except Exception as e:
            logger.error("", exc_info=True)
            return build_result("OtherError")

    def update_share_disk(self, data):
        """
        更新共享数据盘
        {
                "uuid": "xxxxxxxxxx",
                "enable": 0,
                "disk_size": 8,
                "restore": 1,
                "share_desktop": [
                    {"uuid": "xxxxxxx", "name": "xxxxx", "choice": 0},
                    {"uuid": "xxxxxxx", "name": "xxxxx", "choice": 0}
                ]
            }
        :param data:
        :return:
        """
        """
         {
            "command": "create_share",
            "handler": "VoiHandler",
            "data": {
                "disk_info": {
                    'uuid': '2f110de8-78d8-11ea-ad5d-000c29e84b9c',
                    'base_path': '/opt/slow/instances'
                }
                "version": 0
            }
        }
        """
        logger.info("terminal share disk update data: {}".format(data))
        try:
            # disk_uuid = create_uuid()
            version = 0
            disk_uuid = data["uuid"]
            sys_base, data_base = self._get_template_storage_path()
            share_disk = db_api.get_item_with_first(models.YzyVoiTerminalShareDisk, {"uuid": disk_uuid})
            disk_info = dict()
            disk_info["uuid"] = share_disk.uuid
            disk_info["base_path"] = sys_base
            disk_info["size"] = data["disk_size"]
            # 判断是否大小有更新
            if data["disk_size"] != share_disk.disk_size:
                # 需要重新删除创建
                # pass
                node = db_api.get_controller_node()
                delete_command = {
                    "command": "delete_share",
                    "handler": "VoiHandler",
                    "data": {
                        "disk_info": {
                            "uuid": share_disk.uuid,
                            "base_path": sys_base,
                        },
                        "version": version
                    }
                }
                ret = compute_post(node.ip, delete_command)
                if ret.get("code", -1) != 0:
                    logger.error("terminal share disk update fail, delete old fail")
                    return build_result("ShareDiskUpdateFail")
                # 创建新的容量盘
                command_data = {
                    "command": "create_share",
                    "handler": "VoiHandler",
                    "data": {
                        "disk_info": disk_info,
                        "version": version
                    }
                }
                ret_json = compute_post(node.ip, command_data)
                if ret_json.get("code", -1) != 0:
                    logger.error("terminal share disk update fail, create new fail")
                    return build_result("ShareDiskUpdateFail")
                share_disk.disk_size = data["disk_size"]
            # todo 维护桌面组的绑定关系
            # import pdb; pdb.set_trace()
            desktops = db_api.get_item_with_all(models.YzyVoiDesktop, {"group_uuid": share_disk.group_uuid})
            desktop_binds = db_api.get_item_with_all(models.YzyVoiShareToDesktops, {"disk_uuid": disk_uuid})
            share_desktops = data["share_desktop"]
            copy_share_desktops = share_desktops[:]
            for desktop in share_desktops:
                # is_exist = False
                for bind in desktop_binds:
                    if desktop["uuid"] == bind.desktop_uuid:
                        # is_exist = True
                        if not desktop["choice"]:
                            bind.soft_delete()
                        copy_share_desktops.remove(desktop)
            insert_binds = list()
            if copy_share_desktops:
                for desktop in copy_share_desktops:
                    if desktop["choice"]:
                        for _d in desktops:
                            if desktop["uuid"] == _d.uuid:
                                insert_binds.append({
                                    "uuid": create_uuid(),
                                    "group_uuid": share_disk.group_uuid,
                                    "disk_uuid": disk_uuid,
                                    "desktop_uuid": desktop["uuid"],
                                    "desktop_name": desktop["name"]
                                })
            # 更新数据库绑定记录
            if insert_binds:
                db_api.insert_with_many(models.YzyVoiShareToDesktops, insert_binds)
            # 更新数据库记录
            share_disk.restore = data["restore"]
            share_disk.enable = data["enable"]
            share_disk.soft_update()
            # todo 生成bt种子
            # 生成种子文件
            task = Thread(target=self.create_share_disk_torrent, args=(disk_info, version))
            task.start()
            logger.info("update terminal voi share disk data: {} success".format(share_disk))
            return build_result("Success")
        except Exception as e:
            logger.error("", exc_info=True)
            return build_result("OtherError")
