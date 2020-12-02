# -*- coding:utf-8 -*-
import logging
import netaddr
import ipaddress
import os
import subprocess
import json
import time
from flask import jsonify, Response
from common import constants, cmdutils
from common.utils import check_node_status, build_result, compute_post, is_ip_addr, create_uuid, monitor_post, \
            is_netmask, check_vlan_id, get_error_name, icmp_ping, get_error_result
from common.config import SERVER_CONF
from yzy_server.database import apis as db_api
from yzy_server.database import models
from yzy_server.monitor.node_monitor import update_node_status
from .template_ctl import TemplateController
from .desktop_ctl import InstanceController
from yzy_server.apis.v1.controllers.desktop_ctl import BaseController
from yzy_server.monitor.node_monitor import update_service_status
from yzy_server.extensions import db
from yzy_server.utils import get_template_images, get_voi_ha_domain_info, ha_sync_file


logger = logging.getLogger(__name__)


class NodeController(object):

    def _check_params(self, data):
        if not data:
            return False
        ip = data.get("ip", "")
        network_name = data.get("network_name", "")
        switch_name = data.get("switch_name", "")
        switch_type = data.get("switch_type", "")
        # subnet = data.get("subnet_info", "")
        if not (ip and network_name and switch_name and switch_type):
            return False
        return True

    def check_subnet_params(self, data):
        for i in (data['start_ip'], data['end_ip'], data['gateway']):
            if not is_ip_addr(i):
                _ip = i
                raise Exception("%s is not ip address" % _ip)
        if data.get('dns1') and not is_ip_addr(data['dns1']):
            raise Exception("%s is not ip address" % data['dns1'])

        if data.get('dns2') and not is_ip_addr(data['dns2']):
            raise Exception("%s is not ip address" % data['dns1'])

        _is_netmask, netmask_bits = is_netmask(data['netmask'])
        if not _is_netmask:
            raise Exception("%s netmask error" % data['netmask'])

    def _generate_subnet_info(self, data):
        """
        返回子网信息
        :param data:
            {
                "network_uuid": "570a316e-27b5-11ea-9eac-562668d3ccea",
                "name": "subnet1",
                "start_ip": "172.16.1.10",
                "end_ip": "172.16.1.20",
                "netmask": "255.255.0.0",
                "gateway": "172.16.1.254",
                "dns1": "8.8.8.8",
                "dns2": ""
            }
        :return:
        """
        _is_netmask, netmask_bits = is_netmask(data['netmask'])
        subnet_value = {
            "uuid": create_uuid(),
            "name": data['name'],
            "network_uuid": data['network_uuid'],
            "netmask": data['netmask'],
            "gateway": data['gateway'],
            "cidr": "%s/%s" % (data['start_ip'], netmask_bits),
            "start_ip": data['start_ip'],
            "end_ip": data['end_ip'],
            "enable_dhcp": 0,
            "dns1": data['dns1'] if data.get('dns1', '') else None,
            "dns2": data['dns2'] if data.get('dns2', '') else None
        }
        return subnet_value

    def init_default_pool(self):
        pool_value = None
        pools = db_api.get_resource_pool_list()
        for pool in pools:
            if 1 == pool.default:
                pool_uuid = pool.uuid
                break
        else:
            pool_uuid = create_uuid()
            pool_value = {
                "uuid": pool_uuid,
                "name": "default",
                "default": 1
            }
        return pool_uuid, pool_value

    def init_controller_node(self, data):
        """
        初始化控制节点
        :param data:
        :return:
        """
        if not self._check_params(data):
            return build_result("ParamError")

        node = db_api.get_controller_node()
        if node:
            return build_result("ControllerExists", node=node.ip)

        if not is_ip_addr(data['ip']):
            return build_result("IPAddrError", ipaddr=data['ip'])

        if constants.VLAN_NETWORK_TYPE == data['switch_type']:
            vlan_id = data.get('vlan_id', '')
            if not check_vlan_id(str(vlan_id)):
                return build_result("VlanIDError", vid=vlan_id)
        else:
            vlan_id = 0

        # try:
        #     self.check_subnet_params(data['subnet_info'])
        # except Exception as e:
        #     return build_result("SubnetInfoError", name=data['subnet_info']['name'])

        node_uuid = create_uuid()
        # 节点网卡和存储信息获取
        data_nic_uuid = None
        master_netmask = '255.255.255.0'
        try:
            logger.info("get node network info")
            #网卡列表
            nic_list = list()
            #网卡IP列表
            nic_ip_list = list()
            #存储信息列表
            part_list = list()
            #核对节点ip、密码
            ret = self.check_node_virtual(data['ip'], data['password'])
            if ret["code"] != 0:
                return build_result("NodeCheckFail", ret, node=data['ip'])
            data['hostname'] = ret["data"]["hostname"]
            nics = self.get_node_network_interface(data['ip'])
            parts = self.get_node_storage(data['ip'])
            for nic_info in nics:
                nic_uuid = create_uuid()
                if nic_info['interface'] == data['data_interface']:
                    data_nic_uuid = nic_uuid
                info = {
                    'uuid': nic_uuid,
                    'nic': nic_info['interface'],
                    'mac': nic_info['mac'],
                    'node_uuid': node_uuid,
                    'speed': nic_info['speed'],
                    'type': 0,
                    'status': 2 if nic_info['stat'] else 1
                }
                if nic_info.get('ip') and nic_info.get('mask'):
                    if nic_info['ip'] == data['ip']:
                        master_netmask = nic_info['mask']
                    nic_ip = {
                        'uuid': create_uuid(),
                        'nic_uuid': nic_uuid,
                        'name': nic_info['interface'],
                        'ip': nic_info['ip'],
                        'netmask': nic_info['mask'],
                        'gateway': nic_info['gateway'],
                        'dns1': nic_info['dns1'],
                        'dns2': nic_info['dns2'],
                        'is_image': 1 if nic_info['interface'] == data['image_interface'] else 0,
                        'is_manage': 1 if nic_info['interface'] == data['manage_interface'] else 0
                    }
                    nic_ip_list.append(nic_ip)
                nic_list.append(info)
            for part in parts:
                for key, value in data['storages'].items():
                    if key == part['path']:
                        role = value
                        break
                else:
                    role = ''
                part_uuid = create_uuid()
                info = {
                    'uuid': part_uuid,
                    'node_uuid': node_uuid,
                    'path': part['path'],
                    'role': role,
                    'type': part['type'],
                    'total': part['total'],
                    'free': part['free'],
                    'used': part['used']
                }
                part_list.append(info)
            if not data_nic_uuid:
                raise Exception('vswitch nic not exists')
            logger.info("get nics and storages")
        except:
            logger.error("node init fail!", exc_info=True)
            return build_result("NodeInfoGetFail", node=data['ip'])

        # add default switch
        vs_uuid = create_uuid()
        switch_value = {
            "uuid": vs_uuid,
            "name": data['switch_name'],
            "type": data['switch_type'],
            "default": 1
        }
        uplink_value = {
            "uuid": create_uuid(),
            "vs_uuid": vs_uuid,
            "node_uuid": node_uuid,
            "nic_uuid": data_nic_uuid
        }
        logger.info("get vswitch info")
        # add default network
        network_uuid = create_uuid()
        network_value = {
            "uuid": network_uuid,
            "name": data['network_name'],
            "switch_name": data['switch_name'],
            "switch_uuid": vs_uuid,
            "switch_type": data['switch_type'],
            "vlan_id": vlan_id,
            "default": 1
        }
        # 底层建立网桥
        _data = {
            "command": "create",
            "handler": "NetworkHandler",
            "data": {
                "network_id": network_uuid,
                "network_type": data['switch_type'],
                "physical_interface": data['data_interface'],
                "vlan_id": vlan_id
            }
        }
        rep_json = compute_post(data['ip'], _data)
        ret_code = rep_json.get("code", -1)
        if ret_code != 0:
            logger.error("create network failed:%s", rep_json['msg'])
            return build_result("NetworkCreateFail", name=data['network_name'])
        logger.info("create network success")
        # add subnet
        # data['subnet_info']['network_uuid'] = network_uuid
        # subnet_value = self._generate_subnet_info(data['subnet_info'])
        try:
            pool_uuid, pool_value = self.init_default_pool()
            if pool_value:
                db_api.add_resource_pool(pool_value)
            url = "/api/v1/monitor/hardware"
            rep_json = monitor_post(data['ip'], url, None)
            if rep_json["code"] != 0:
                logger.error("get node:%s hardware info fail" % data['ip'])
                return build_result("GetHardwareInfoFailure")

            hardware_data = rep_json.get("data", {})
            logger.info('get node:%s hardware info' % str(hardware_data))

            gpu_info = list((str(value)+" * "+key) for key, value in hardware_data["gfxcard"].items())[0]
            cpu_info_list = list((str(value)+" * "+key) for key, value in hardware_data["cpu"].items())
            cpu_info = ','.join(cpu_info_list)
            mem_info_list = list((str(value['count']) + " * " + key + ' ' + str(value['size']))
                                 for key, value in hardware_data["memory"].items())
            mem_info = ','.join(mem_info_list)

            server_version_info = hardware_data["server_version"]

            node_value = {
                "uuid": node_uuid,
                "ip": data['ip'],
                "name": data["hostname"],
                "hostname": data['hostname'],
                "resource_pool_uuid": pool_uuid if data['is_compute'] else '',
                "status": "active",
                "gpu_info": gpu_info,
                "cpu_info":  cpu_info,
                "mem_info":  mem_info,
                "server_version_info":  server_version_info,
                "type": constants.ROLE_MASTER_AND_COMPUTE if data['is_compute'] else constants.ROLE_MASTER
            }
            db_api.add_server_node(node_value)
            db_api.add_virtual_swtich(switch_value)
            if uplink_value:
                db_api.add_virtual_switch_uplink(uplink_value)
            if network_value:
                db_api.add_network(network_value)
            # db_api.add_subnet(subnet_value)
            if nic_list:
                db_api.insert_with_many(models.YzyNodeNetworkInfo, nic_list)
            if nic_ip_list:
                db_api.insert_with_many(models.YzyInterfaceIp, nic_ip_list)
            db_api.insert_with_many(models.YzyNodeStorages, part_list)

            ntp_server_command = {
                "command": "config_ntp_server",
                "handler": "NodeHandler",
                "data": {
                    "ipaddr": data['ip'],
                    "netmask": master_netmask
                }
            }
            ret = compute_post(data['ip'], ntp_server_command)
            logger.info("config ntp server:%s", ret)
        except Exception as e:
            logger.error("init controller failed:%s", e, exc_info=True)
            _data = {
                "command": "delete",
                "handler": "NetworkHandler",
                "data": {
                    "network_id": network_uuid,
                    "vlan_id": vlan_id
                }
            }
            rep_json = compute_post(data['ip'], _data)
            ret_code = rep_json.get("code", -1)
            if ret_code != 0:
                logger.error("delete network failed:%s", rep_json['msg'])
            logger.info("delete network success")
            return build_result("ControllerNodeInitFail", node=data['ip'])
        return build_result("Success")

    def init_controller_to_compute(self, data):
        try:
            pools = db_api.get_resource_pool_list()
            for pool in pools:
                if 1 == pool.default:
                    pool_uuid = pool.uuid
                    break
            else:
                pool_uuid = create_uuid()
                pool_value = {
                    "uuid": pool_uuid,
                    "name": "default",
                    "default": 1
                }
            node_value = {
                "uuid": create_uuid(),
                "ip": data['ip'],
                "name": data['hostname'],
                "hostname": data['hostname'],
                "resource_pool_uuid": pool_uuid,
                "status": "active",
                "type": 1       # 主控和计算一体
            }
            if not pools:
                db_api.add_resource_pool(pool_value)
            db_api.add_server_node(node_value)
        except Exception as e:
            logger.info("init compute failed:%s", e)
            return build_result("CreateNodeFail", name=data['ip'])

    def get_controller_list(self):
        controllers = list()
        controller_list = db_api.get_controller_node()

        for cnt in controller_list:
            controllers.append(cnt.to_json())

        ret = {
            "controller_list": controllers
        }
        return build_result("Success", ret)

    def _check_param(self, data):
        if not data:
            return False

        ip = data.get("ip", "")
        m_ip = data.get("m_ip", "")
        pool_uuid = data.get("pool_uuid", "")
        network = data.get("network", "")
        manage_interface = data.get("manage_interface", "")
        image_interface = data.get("image_interface", "")
        if not (ip and m_ip and pool_uuid and network and manage_interface and image_interface):
            return False
        logger.info("check params ok")
        return True

    def add_node(self, data):
        if not self._check_param(data):
            return build_result("ParamError")

        if not is_ip_addr(data['ip']):
            return build_result("IPAddrError", ipaddr=data['ip'])
        node = db_api.get_node_by_ip(data['ip'])
        if node and node.type not in (constants.ROLE_MASTER_AND_COMPUTE, constants.ROLE_MASTER):
            return build_result("NodeAlreadyExist", host_name=data['ip'])

        if node and node.type == constants.ROLE_MASTER_AND_COMPUTE:
            # if node.resource_pool_uuid:
            #     return build_result("NodeAlreadyExist", host_name=data['ip'])
            node.resource_pool_uuid = data['pool_uuid']
            node.soft_update()
            return build_result("Success")

        # 添加网络和存储信息
        node_uuid = create_uuid()
        vswitch_nic = None
        try:
            logger.info("get node network info")
            nic_list = list()
            nic_ip_list = list()
            part_list = list()
            vswitch_uplink_list = list()
            ret = self.check_node_virtual(data['ip'], data['password'])
            if ret["code"] != 0:
                return build_result("NodeCheckFail", ret, node=data['ip'])
            data['hostname'] = ret["data"]["hostname"]
            controller = db_api.get_controller_node()
            storages = db_api.get_node_storage_all({'node_uuid': controller.uuid})
            parts = self.get_node_storage(data['ip'])
            # 判断主控用作存储的挂载点，在添加的节点上是否存在
            for storage in storages:
                if storage['role']:
                    for part in parts:
                        if part['path'] == storage['path']:
                            break
                    else:
                        logger.error("the node storages is less of %s", storage['path'])
                        return build_result("NodeStorageError", node=data['ip'], path=storage['path'])

            nic_map = {}
            vswitch_map = {}
            nics = self.get_node_network_interface(data['ip'])
            for nic_info in nics:
                nic_uuid = create_uuid()
                nic_map[nic_info['interface']] = nic_uuid
                info = {
                    'uuid': nic_uuid,
                    'nic': nic_info['interface'],
                    'mac': nic_info['mac'],
                    'node_uuid': node_uuid,
                    'speed': nic_info['speed'],
                    'type': 0,
                    'status': 2 if nic_info['stat'] else 1
                }
                if nic_info.get('ip') and nic_info.get('mask'):
                    nic_ip = {
                        'uuid': create_uuid(),
                        'nic_uuid': nic_uuid,
                        'name': nic_info['interface'],
                        'ip': nic_info['ip'],
                        'netmask': nic_info['mask'],
                        'gateway': nic_info['gateway'],
                        'dns1': nic_info['dns1'],
                        'dns2': nic_info['dns2'],
                        'is_image': 1 if nic_info['interface'] == data['image_interface'] else 0,
                        'is_manage': 1 if nic_info['interface'] == data['manage_interface'] else 0
                    }
                    nic_ip_list.append(nic_ip)
                nic_list.append(info)
            for part in parts:
                for storage in storages:
                    if storage['path'] == part['path']:
                        role = storage['role']
                        break
                else:
                    role = ''
                part_uuid = create_uuid()
                info = {
                    'uuid': part_uuid,
                    'node_uuid': node_uuid,
                    'path': part['path'],
                    'role': role,
                    'type': part['type'],
                    'free': part['free'],
                    'total': part['total'],
                    'used': part['used']
                }
                part_list.append(info)
            switch_uuid = None
            for network in data['network']:
                vswitch_uuid = create_uuid()
                vswitch_uplink = {
                    "uuid": vswitch_uuid,
                    "vs_uuid": network['switch_uuid'],
                    "node_uuid": node_uuid,
                    "nic_uuid": nic_map[network['interface']]
                }
                vswitch_map[network['switch_uuid']] = network['interface']
                switch_uuid = network['switch_uuid']
                vswitch_uplink_list.append(vswitch_uplink)
        except Exception as e:
            logger.error("get nic and storages failed:%s", e, exc_info=True)
            return build_result("NodeInfoGetFail", node=data['ip'])

        try:
            url = "/api/v1/monitor/hardware"
            rep_json = monitor_post(data['ip'], url, None)
            if rep_json["code"] != 0:
                logger.error("get node:%s hardware info fail" % data['ip'])
                return build_result("GetHardwareInfoFailure")

            hardware_data = rep_json.get("data", {})
            logger.info('get node:%s hardware info' % str(hardware_data))

            gpu_info = list((str(value)+" * "+key) for key, value in hardware_data["gfxcard"].items())[0]
            cpu_info_list = list((str(value)+" * "+key) for key, value in hardware_data["cpu"].items())
            cpu_info = ','.join(cpu_info_list)
            mem_info_list = list((str(value['count']) + " * " + key + ' ' + str(value['size']))
                                 for key, value in hardware_data["memory"].items())
            mem_info = ','.join(mem_info_list)

            server_version_info = hardware_data["server_version"]
            node_value = {
                "uuid": node_uuid,
                "ip": data['ip'],
                "name": data['hostname'],
                "hostname": data['hostname'],
                "resource_pool_uuid": data['pool_uuid'],
                "status": "active",
                "gpu_info": gpu_info,
                "cpu_info":  cpu_info,
                "mem_info":  mem_info,
                "server_version_info":  server_version_info,
                "type": constants.ROLE_COMPUTE
            }
            db_api.add_server_node(node_value)
            if vswitch_uplink_list:
                db_api.insert_with_many(models.YzyVswitchUplink, vswitch_uplink_list)
            if nic_list:
                db_api.insert_with_many(models.YzyNodeNetworkInfo, nic_list)
            if nic_ip_list:
                db_api.insert_with_many(models.YzyInterfaceIp, nic_ip_list)
            if part_list:
                db_api.insert_with_many(models.YzyNodeStorages, part_list)

            networks = db_api.get_networks()
            for network in networks:
                if switch_uuid != network['switch_uuid']:
                    continue
                vlan_id = network['vlan_id']
                _data = {
                    "command": "create",
                    "handler": "NetworkHandler",
                    "data": {
                        "network_id": network['uuid'],
                        "network_type": network['switch_type'],
                        "physical_interface": vswitch_map[network['switch_uuid']],
                        "vlan_id": int(vlan_id) if vlan_id else ""
                    }
                }
                rep_json = compute_post(data['ip'], _data)
                ret_code = rep_json.get("code", -1)
                if ret_code != 0:
                    logger.error("create network failed:%s", rep_json['msg'])
                    raise Exception("create network failed")
                logger.info("create network success")
            ntp_command = {
                "command": "set_ntp_sync",
                "handler": "NodeHandler",
                "data": {
                    "controller_ip": controller.ip
                }
            }
            compute_post(data['ip'], ntp_command)
            TemplateController().node_sync_image(data['pool_uuid'], data['ip'], node_uuid)
            services = constants.NETWORK_SERVICE.append('yzy-deployment')
            self.disable_service(node_uuid, services)
        except Exception as e:
            logger.error("init node: %s fail:%s", data['ip'], str(e), exc_info=True)
            self.rollback_add_node(node_uuid)
            return build_result("CreateNodeFail", node=data['ip'])
        return build_result("Success")

    def _delete_network_interface(self, ipaddr, network_uuid, vlan_id=None):
        _data = {
            "command": "delete",
            "handler": "NetworkHandler",
            "data": {
                "network_id": network_uuid,
                "vlan_id": int(vlan_id) if vlan_id else ""
            }
        }
        rep_json = compute_post(ipaddr, _data)
        ret_code = rep_json.get("code", -1)
        if ret_code != 0:
            logger.error("delete network failed:%s", rep_json['msg'])
        logger.info("delete network:%s in %s success", network_uuid, ipaddr)

    # def disable_control_node_deployment(self, ip, service_name='yzy-deployment'):
    #     url = "/api/v1/monitor/task"
    #     data = {
    #         "handler": "ServiceHandler",
    #         "command": "disable",
    #         "data": {
    #             "service": service_name
    #         }
    #     }
    #     logger.info("disable %s in %s", service_name, ip)
    #     rep_json = monitor_post(ip, url, data)
    #     return rep_json

    def enable_control_node_deployment(self, ip, service_name='yzy-deployment'):
        """开启开机自启初始化服务"""
        url = "/api/v1/monitor/task"
        data = {
            "handler": "ServiceHandler",
            "command": "enable",
            "data": {
                "service": service_name
            }
        }
        logger.info("enable %s in %s", service_name, ip)
        rep_json = monitor_post(ip, url, data)
        return rep_json

    def check_template_instance(self, node, status):
        """校验是否存在系统桌面或者不还原盘"""
        logger.info("check template and desktop")
        templates = db_api.get_template_with_all({"host_uuid": node.uuid})
        sys_desktop = []
        desktop_name = {}
        for template in templates:
            # 系统桌面
            if template.classify == 3:
                sys_desktop.append(template.name)
        instances = db_api.get_instance_with_all({'host_uuid': node.uuid})
        for instance in instances:
            if instance.classify == 1:
                desktop = db_api.get_desktop_with_first({"uuid": instance.desktop_uuid})
            else:
                desktop = db_api.get_personal_desktop_with_first({"uuid": instance.desktop_uuid})
            if desktop.sys_restore == 0 or desktop.data_restore == 0:
                if desktop.name not in desktop_name.keys():
                    desktop_name[desktop.name] = [instance.name]
                else:
                    desktop_name[desktop.name].append(instance.name)
        if sys_desktop or desktop_name:
            return sys_desktop, desktop_name
        for instance in instances:
            if instance.classify == 1:
                desktop = db_api.get_desktop_with_first({"uuid": instance.desktop_uuid})
            else:
                desktop = db_api.get_personal_desktop_with_first({"uuid": instance.desktop_uuid})
            if status != constants.STATUS_SHUTDOWN:
                info = {
                    "uuid": instance.uuid,
                    "name": instance.name,
                    "sys_base": "",
                    "data_base": ""
                }
                BaseController()._delete_instance(node.ip, info)
                instance.soft_delete()
                desktop.instance_num -= 1
                desktop.soft_update()
        return sys_desktop, desktop_name

    def return_params(self, desktop_name):
        """组织返回给前端的参数格式"""
        instance_list = []
        for k, v in desktop_name.items():
            name_dict = {}
            name_dict["desktop"] = k
            name_dict["instance"] = v
            instance_list.append(name_dict)
        return instance_list

    def get_storage_list(self, node_uuid):
        """获取磁盘分区信息列表"""
        storage_list = list()
        template_data = db_api.get_template_data_storage(node_uuid)
        storage_list.append(template_data)
        template_sys = db_api.get_template_sys_storage(node_uuid)
        storage_list.append(template_sys)
        instance_data = db_api.get_instance_data_storage()
        storage_list.append(instance_data)
        instance_sys = db_api.get_instance_sys_storage()
        storage_list.append(instance_sys)
        return storage_list

    def delete_node(self, node_uuid):
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            return build_result("NodeNotExist")
        # 记录节点初始状态
        status = node.status
        self.update_node(node.uuid, status=constants.STATUS_DELETING)
        if node.type in [1, 3]:
            return build_result("ControllerCannotDelete", node=node.ip)
        sys_desktop, desktop_name = self.check_template_instance(node, status)
        if sys_desktop or desktop_name:
            # 如果删除失败，节点状态恢复初始状态
            self.update_node(node.uuid, status=status)
            instance_list = self.return_params(desktop_name)
            return build_result("SystemNotRestoreError",
                                data={"sys_names": sys_desktop, "names": instance_list})
        # 界面存在模板或者桌面时，不允许删除
        # template = db_api.get_template_with_all({'host_uuid': node_uuid})
        # if template:
        #     return build_result("InstanceExist", node=node.ip)
        # template = db_api.get_item_with_first(models.YzyVoiTemplate, {'host_uuid': node_uuid})
        # if template:
        #     return build_result("InstanceExist", node=node.ip)
        # 也需要删除节点上建立的网桥等网络设备，还有存储信息
        uplinks = db_api.get_uplinks_all({'node_uuid': node_uuid})
        for uplink in uplinks:
            networks = db_api.get_network_all({'switch_uuid': uplink.vs_uuid})
            for network in networks:
                vlan_id = network.vlan_id
                self._delete_network_interface(node.ip, network.uuid, vlan_id)
            uplink.soft_delete()

        # 清除bond_nics表，请求compute服务解绑bond
        bond_nics = db_api.get_bond_nics_all({'node_uuid': node_uuid})
        master_name_dict = dict()
        for bond in bond_nics:
            if bond.master_name not in master_name_dict.keys():
                master_name_dict[bond.master_name] = list()
                ip_infos = db_api.get_item_with_all(models.YzyInterfaceIp, {'nic_uuid': bond.master_uuid})
                info = {
                    "slaves": list(),
                    "ip_list": list(),
                }
                if ip_infos:
                    info["ip_list"] = [{
                        "ip": obj.ip,
                        "netmask": obj.netmask,
                        "gateway": obj.gateway,
                        "dns1": obj.dns1,
                        "dns2": obj.dns2,
                        "is_manage": obj.is_manage,
                        "is_image": obj.is_image
                    } for obj in ip_infos]
                    info["ip_list"].sort(key=lambda x: (-x["is_manage"], -x["is_image"]))
                master_name_dict[bond.master_name] = info
            master_name_dict[bond.master_name]["slaves"].append({
                "nic": bond.slave_name,
                "ip_list": list()
            })
            bond.soft_delete()

        for master_name, info in master_name_dict.items():
            info["slaves"][0]["ip_list"] = info.pop("ip_list", [])
            _data = {
                "command": "unbond",
                "handler": "NetworkHandler",
                "data": {
                    "slaves": info["slaves"],
                    "bond_name": master_name
                }
            }
            rep_json = compute_post(node.ip, _data)

        nics = db_api.get_nics_all({'node_uuid': node_uuid})
        for nic in nics:
            nic_infos = db_api.get_item_with_all(models.YzyInterfaceIp, {'nic_uuid': nic.uuid})
            for info in nic_infos:
                info.soft_delete()
            nic.soft_delete()
        paths = db_api.get_node_storage_all({'node_uuid': node_uuid})
        for path in paths:
            path.soft_delete()
        node.soft_delete()
        # 服务信息
        services = db_api.get_item_with_all(models.YzyNodeServices, {'node_uuid': node_uuid})
        for service in services:
            service.soft_delete()
        # 数据库备份信息
        backs = db_api.get_item_with_all(models.YzyDatabaseBack, {'node_uuid': node_uuid})
        for back in backs:
            back.soft_delete()
        if status != constants.STATUS_SHUTDOWN:
            storage_list = self.get_storage_list(node_uuid)
            for storage in set(storage_list):
                # 清理磁盘分区数据
                url = "/api/v1/monitor/task"
                data = {
                    "handler": "FileHandler",
                    "command": "delete_file",
                    "data": {
                        "file_name": storage.path
                    }
                }
                monitor_post(node.ip, url, data)
            # 开启节点初始化服务
            self.enable_control_node_deployment(node.ip)
            self.enable_control_node_deployment(node.ip, 'ukey')
            # 关闭节点
            result = self.node_task(node.ip, "shutdown")
            if result.get("code", -1) != 0:
                return build_result("NodeShutdownFailed", node=node.ip)
        node.soft_delete()
        logger.info("delete node:%s success", node_uuid)
        return build_result("Success")

    def rollback_add_node(self, node_uuid):
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            return build_result("NodeNotExist")
        uplinks = db_api.get_uplinks_all({'node_uuid': node_uuid})
        for uplink in uplinks:
            networks = db_api.get_network_all({'switch_uuid': uplink.vs_uuid})
            for network in networks:
                vlan_id = network.vlan_id
                self._delete_network_interface(node.ip, network.uuid, vlan_id)
            uplink.soft_delete()
        nics = db_api.get_nics_all({'node_uuid': node_uuid})
        for nic in nics:
            nic_infos = db_api.get_item_with_all(models.YzyInterfaceIp, {'nic_uuid': nic.uuid})
            for info in nic_infos:
                info.soft_delete()
            nic.soft_delete()
        paths = db_api.get_node_storage_all({'node_uuid': node_uuid})
        for path in paths:
            path.soft_delete()
        node.soft_delete()
        # 服务信息
        services = db_api.get_item_with_all(models.YzyNodeServices, {'node_uuid': node_uuid})
        for service in services:
            service.soft_delete()

        storage_list = self.get_storage_list(node_uuid)
        for storage in set(storage_list):
            # 清理磁盘分区数据
            url = "/api/v1/monitor/task"
            data = {
                "handler": "FileHandler",
                "command": "delete_file",
                "data": {
                    "file_name": storage.path
                }
            }
            monitor_post(node.ip, url, data)
        # 开启节点初始化服务
        self.enable_control_node_deployment(node.ip)
        self.enable_control_node_deployment(node.ip, 'ukey')
        node.soft_delete()
        logger.info("rollback node:%s success", node_uuid)
        return build_result("Success")

    def node_task(self, ip, command):
        # 检测节点是否支持虚拟化
        url = "/api/v1/monitor/task"
        data = {
            "handler": "OsHandler",
            "command": command
        }
        rep_json = monitor_post(ip, url, data)
        return rep_json

    def shutdown_node(self, node_uuid, timeout=None):
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            return build_result("NodeNotExist")
        self.update_node(node_uuid, status=constants.STATUS_SHUTDOWNING)
        # 关闭所有桌面
        instances = db_api.get_instance_with_all({"host_uuid": node.uuid})
        active_instances = dict()
        for instance in instances:
            if instance.status == constants.STATUS_ACTIVE:
                _desktop_uuid = instance.desktop_uuid
                if _desktop_uuid not in active_instances:
                    active_instances[_desktop_uuid] = list()
                active_instances[_desktop_uuid].append(
                    {"uuid": instance.uuid, "name": instance.name}
                )
        desktop_instances = list()
        for k, v in active_instances.items():
            _d = {"desktop_uuid": k, "instances": v}
            desktop_instances.append(_d)

        # 起多个线程同时处理桌面关机操作
        instance_contrallor = InstanceController()
        for item in desktop_instances:
            instance_contrallor.stop_instances(item, timeout=timeout)

        rep_json = self.node_task(node['ip'], 'shutdown')
        ret_code = rep_json.get("code", -1)
        if ret_code != 0:
            logger.error("shutdown node failed:%s", rep_json['msg'])
            return build_result("NodeShutdownFailed", node=node.ip)
        # self.update_node(node_uuid, status=constants.STATUS_SHUTDOWN)
        logger.info("shutdown node %s success", node_uuid)
        return build_result('Success')

    def reboot_node(self, node_uuid):
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            return build_result("NodeNotExist")
        rep_json = self.node_task(node['ip'], 'reboot')
        ret_code = rep_json.get("code", -1)
        if ret_code != 0:
            logger.error("reboot node failed:%s", rep_json['msg'])
            return build_result("NodeRebootFailed", node=node.ip)
        logger.info("reboot node %s success", node_uuid)
        return build_result('Success')

    def check_node_virtual(self, ip, root_pwd):
        # 检测节点是否支持虚拟化
        url = "/api/v1/monitor/cpuvt"
        data = {
            "user": "root",
            "password": root_pwd
        }
        rep_json = monitor_post(ip, url, data)
        return rep_json

    def get_default_network_info(self):
        """
        获取默认的数据网络及虚拟交换机的信息
        :return:
        """
        default_network_info = {}
        default_network = db_api.get_default_network()
        if default_network:
            default_network_info["network_info"] = default_network.to_json()

        default_virtual_switch = db_api.get_default_virtual_switch()
        if default_virtual_switch:
            default_network_info["virtual_switch"] = default_virtual_switch.to_json()

        return default_network_info

    def _get_node_nics(self, ip):
        url = "/api/v1/monitor/network"
        rep_json = monitor_post(ip, url, None)
        return rep_json

    def add_ip_node(self, data):
        """
        节点网卡添加IP
        :param data:
        :return:
        """
        logger.info("add ip info")
        node_uuid = data.get("node_uuid")
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            logger.error("node add ip, node[%s] not exist", node_uuid)
            return build_result("NodeNotExist")
        nic_uuid = data.get("nic_uuid")
        nic = db_api.get_nics_first({'uuid': nic_uuid})
        if not nic:
            logger.error("node add ip, network interface[%s] not exist", nic_uuid)
            return build_result("NodeNICNotExist")
        # 目前一个网卡限制为添加两个IP
        ip_infos = nic.ip_infos
        ips = [i for i in ip_infos if not i.deleted]
        if len(ips) >= 2:
            logger.error("node add ip, network interface[%s] too many ip", nic_uuid)
            return build_result("NodeNICIpTooManyError")

        # 如果是flat网络，需要将IP配置到网桥上
        net_info = dict()
        switchs = db_api.get_virtual_switch_list({"type": constants.FLAT_NETWORK_TYPE})
        for switch in switchs:
            vs_uplink = db_api.get_uplinks_first({'nic_uuid': nic_uuid, 'vs_uuid': switch.uuid})
            if vs_uplink:
                nets = db_api.get_network_all({'switch_uuid': switch.uuid})
                if nets:
                    net_info = {
                        "network_id": nets[0].uuid,
                        "physical_interface": nic.nic
                    }
                    break

        # 将已有的和新加的IP信息一起传到底层
        all_info = list()
        gate_info = dict()
        for info in ips:
            all_info.append({
                "ip": info.ip,
                "netmask": info.netmask
            })
            if info.gateway:
                gate_info['gateway'] = info.gateway
                data['gateway'] = info.gateway
            if info.dns1:
                gate_info['dns1'] = info.dns1
                data['dns1'] = info.dns1
            if info.dns2:
                gate_info['dns2'] = info.dns2
                data['dns2'] = info.dns2
        all_info.append({
            "ip": data['ip'],
            "netmask": data['netmask']
        })
        if not gate_info and data.get('gateway'):
            gate_info['gateway'] = data.get('gateway', '')
            gate_info['dns1'] = data.get('dns1', '')
            gate_info['dns2'] = data.get('dns2', '')
        cmd = {
            "command": "set_ip",
            "handler": "NetworkHandler",
            "data": {
                "name": nic.nic,
                "ip_infos": all_info,
                "gate_info": gate_info,
                "net_info": net_info
            }
        }
        logger.info("add ip %s in nic %s of node %s", data['ip'], nic.nic, node.ip)
        ret_json = compute_post(node.ip, cmd)
        if ret_json.get("code", -1) != 0:
            logger.error("node add ip fail: %s", ret_json.get("msg"))
            code = ret_json.get("code", -1)
            errcode = get_error_name(code)
            return build_result(errcode)
        # 记录数据库
        uuid = create_uuid()
        data['is_manage'] = 0
        data['is_image'] = 0
        data.update({"name": nic.nic, "uuid": uuid})
        try:
            db_api.add_nic_ip(data)
        except Exception as e:
            logger.error("node add ip fail, database commit error: %s", e, exc_info=True)
            # 删除子IP
            ret = monitor_post(node.ip, "/api/v1/monitor/delete_ip", data)
            logger.info("node add ip fail, delete ip monitor result: %s", ret)
            return build_result("NodeNICIpAddError")
        logger.info("node add ip success!")
        return build_result("Success", data=data)

    def delete_ip_node(self, data):
        try:
            nic = db_api.get_nics_first({'uuid': data['nic_uuid']})
            if not nic:
                logger.error("node delete ip, network interface[%s] not exist", data['nic_uuid'])
                return build_result("NodeNICNotExist")
            delete_ip = db_api.get_nic_ip_by_uuid(data["uuid"])
            if delete_ip.is_manage or delete_ip.is_image:
                logger.exception("can not delete manage or image network")
                return build_result("ManageNetCanNotUpdate")
            # 如果是flat网络，需要将IP配置到网桥上
            net_info = dict()
            switchs = db_api.get_virtual_switch_list({"type": constants.FLAT_NETWORK_TYPE})
            for switch in switchs:
                vs_uplink = db_api.get_uplinks_first({'nic_uuid': data['nic_uuid'], 'vs_uuid': switch.uuid})
                if vs_uplink:
                    nets = db_api.get_network_all({'switch_uuid': switch.uuid})
                    if nets:
                        net_info = {
                            "network_id": nets[0].uuid,
                            "physical_interface": nic.nic
                        }
                        break
            # 组合删除之后的IP信息
            ip_infos = nic.ip_infos
            ips = [i for i in ip_infos if not i.deleted]
            all_info = list()
            gate_info = dict()
            for info in ips:
                if info.uuid == delete_ip.uuid:
                    continue
                all_info.append({
                    "ip": info.ip,
                    "netmask": info.netmask
                })
                gate_info = {
                    "gateway": info.gateway,
                    "dns1": info.dns1,
                    "dns2": info.dns2
                }
            cmd = {
                "command": "set_ip",
                "handler": "NetworkHandler",
                "data": {
                    "name": nic.nic,
                    "ip_infos": all_info,
                    "gate_info": gate_info,
                    "net_info": net_info
                }
            }
            logger.info("delete ip %s in nic %s of node %s", delete_ip.ip, delete_ip.name, data['node_ip'])
            ret_json = compute_post(data['node_ip'], cmd)
            if ret_json.get("code", -1) != 0:
                logger.error("node delete ip fail: %s", ret_json.get("msg"))
                code = ret_json.get("code", -1)
                errcode = get_error_name(code)
                return build_result(errcode)
            delete_ip.soft_delete()
        except Exception as e:
            logger.error("node delete ip fail: %s", e, exc_info=True)
            return build_result("NodeNICIpAddError")
        
        logger.info("node delete ip success!")
        return build_result("Success")

    def check_image_ip(self, ip, master_image_nic, master_image_ip):
        try:
            result = subprocess.call(["ping", "-I", master_image_ip, ip, "-w", "2"])
            if result == 0:
                return build_result("Success")
            else:
                return build_result("ImageNetworkConnectFail")
        except Exception as e:
            return build_result("ImageNetworkConnectFail")

    def ping_node(self, ip):
        try:
            ret = check_node_status(ip)
            if ret.get('code') == 0:
                return build_result("Success")
            else:
                return build_result("NodeIPConnetFail", ip=ip)
        except Exception as e:
            return build_result("NodeIPConnetFail", ip=ip)

    def ping_ip(self, ip):
        if not icmp_ping(ip, count=3):
            return build_result("QuorumIPConnectError")
        return build_result("Success")


    def update_node(self, uuid, type=None, status=None, name=None, pool_uuid=None):
        try:
            node = db_api.get_node_by_uuid(uuid)
            if type:
                node.type = type
            if name:
                node.name = name
            if status:
                node.status = status
            # if pool_uuid:
                # node.resource_pool_uuid = pool_uuid
            node.soft_update()
        except Exception as e:
            return build_result("ModifyNodeFail")
        return build_result("Success")

    def update_ip_node(self, data):
        return jsonify(self._update_ip_node(data))

    def _update_ip_node(self, data):
        try:
            ha_flag = data.get("ha_flag", False)
            update_ip = db_api.get_nic_ip_by_uuid(data["uuid"])
            if not ha_flag:
                if update_ip.is_manage or update_ip.is_image:
                    logger.error("node update ip fail, network interface[%s] not exist", data['nic_uuid'])
                    return get_error_result("ManageNetCanNotUpdate")
            nic = db_api.get_nics_first({'uuid': data['nic_uuid']})
            if not nic:
                logger.error("node add ip, network interface[%s] not exist", data['nic_uuid'])
                return get_error_result("NodeNICNotExist")
            # 如果是flat网络，需要将IP配置到网桥上
            net_info = dict()
            switchs = db_api.get_virtual_switch_list({"type": constants.FLAT_NETWORK_TYPE})
            for switch in switchs:
                vs_uplink = db_api.get_uplinks_first({'nic_uuid': data['nic_uuid'], 'vs_uuid': switch.uuid})
                if vs_uplink:
                    nets = db_api.get_network_all({'switch_uuid': switch.uuid})
                    if nets:
                        net_info = {
                            "network_id": nets[0].uuid,
                            "physical_interface": nic.nic
                        }
                        break
            ips = [i for i in nic.ip_infos if not i.deleted]
            gate_info = dict()
            all_info = list()
            for info in ips:
                if info.uuid == update_ip.uuid:
                    all_info.append({
                        "ip": data['ip'],
                        "netmask": data['netmask']
                    })
                else:
                    all_info.append({
                        "ip": info.ip,
                        "netmask": info.netmask
                    })
                gate_info = {
                    "gateway": info.gateway,
                    "dns1": info.dns1,
                    "dns2": info.dns2
                }
            cmd = {
                "command": "set_ip",
                "handler": "NetworkHandler",
                "data": {
                    "name": nic.nic,
                    "ip_infos": all_info,
                    "gate_info": gate_info,
                    "net_info": net_info
                }
            }
            logger.info("update ip %s in nic %s of node %s", update_ip.ip, update_ip.name, data['node_ip'])
            ret_json = compute_post(data['node_ip'], cmd)
            if ret_json.get("code", -1) != 0:
                logger.error("node update ip fail: %s", ret_json.get("msg"))
                code = ret_json.get("code", -1)
                errcode = get_error_name(code)
                return get_error_result(errcode)

            logger.info("before update_ip in db: %s", update_ip.ip)
            update_ip.ip = data['ip']
            update_ip.netmask = data['netmask']
            update_ip.soft_update()
            logger.info("after update_ip in db: %s", update_ip.ip)

            if ha_flag:
                master_obj = db_api.get_controller_node()
                logger.info("before node_ip in db: %s", master_obj.ip)
                master_obj.ip = data['ip']
                master_obj.soft_update()
                logger.info("after node_ip in db: %s", master_obj.ip)
        except Exception as e:
            logger.error("node update ip fail, database commit error: %s", e, exc_info=True)
            return get_error_result("NodeNICIpAddError")
        
        logger.info("node update ip success!")
        return get_error_result("Success", data=data)

    def update_gate_info(self, data):
        try:
            nic = db_api.get_nics_first({'uuid': data['nic_uuid']})
            if not nic:
                logger.error("node add ip, network interface[%s] not exist", data['nic_uuid'])
                return build_result("NodeNICNotExist")
            ips = [i for i in nic.ip_infos if not i.deleted]

            net_info = dict()
            switchs = db_api.get_virtual_switch_list({"type": constants.FLAT_NETWORK_TYPE})
            for switch in switchs:
                vs_uplink = db_api.get_uplinks_first({'nic_uuid': data['nic_uuid'], 'vs_uuid': switch.uuid})
                if vs_uplink:
                    nets = db_api.get_network_all({'switch_uuid': switch.uuid})
                    if nets:
                        net_info = {
                            "network_id": nets[0].uuid,
                            "physical_interface": nic.nic
                        }
                        break
            all_info = list()
            count = 0
            if data.get('gateway'):
                # 网关必须和其中一个iP在同一个网络
                gate_ip = None
                for info in ips:
                    netmask_bits = netaddr.IPAddress(info.netmask).netmask_bits()
                    network_num = ipaddress.ip_interface(info.ip + "/" + str(netmask_bits)).network
                    if ipaddress.IPv4Address(data['gateway']) not in network_num:
                        count += 1
                    else:
                        gate_ip = info
                if count > 0 and count == len(ips):
                    return build_result("GatewayAndIpError")
                # 网关所在网络的那个IP必须放在第一个，否则网关设置不成功
                for info in ips:
                    if info.uuid == gate_ip.uuid:
                        all_info.append({
                            "ip": info.ip,
                            "netmask": info.netmask
                        })
                for info in ips:
                    if info.uuid != gate_ip.uuid:
                        all_info.append({
                            "ip": info.ip,
                            "netmask": info.netmask
                        })
            else:
                for info in ips:
                    all_info.append({
                        "ip": info.ip,
                        "netmask": info.netmask
                    })
            gate_info = {
                "gateway": data.get('gateway', ''),
                "dns1": data.get('dns1', ''),
                "dns2": data.get('dns2', '')
            }
            cmd = {
                "command": "set_ip",
                "handler": "NetworkHandler",
                "data": {
                    "name": nic.nic,
                    "ip_infos": all_info,
                    "gate_info": gate_info,
                    "net_info": net_info
                }
            }
            logger.info("update gate info %s in nic %s of node %s", data['gateway'], nic.nic, data['node_ip'])
            ret_json = compute_post(data['node_ip'], cmd)
            if ret_json.get("code", -1) != 0:
                logger.error("node update ip fail: %s", ret_json.get("msg"))
                code = ret_json.get("code", -1)
                errcode = get_error_name(code)
                return build_result(errcode)

            for info in ips:
                info.gateway = data.get('gateway', '')
                info.dns1 = data.get('dns1', '')
                info.dns2 = data.get('dns2', '')
                info.soft_update()
        except Exception as e:
            logger.error("node update gate info fail, database commit error: %s", e, exc_info=True)
            return build_result("NodeNICIpAddError")

        logger.info("node update gate info success!")
        return build_result("Success", data=data)

    def mn_map_update_node(self, uplinks):
        try:
            # 已做HA的主备控节点，不允许修改管理IP
            ha_nic_uuids = list()
            ha_info_objs = db_api.get_ha_info_all()
            if ha_info_objs:
                for ha_info_obj in ha_info_objs:
                    ha_nic_uuids.append(ha_info_obj.master_nic_uuid)
                    ha_nic_uuids.append(ha_info_obj.backup_nic_uuid)

            for uplink in uplinks:
                old_nic_ip = db_api.get_nic_ip_by_uuid(uplink['old_ip_uuid'])
                new_nic_ip = db_api.get_nic_ip_by_uuid(uplink['new_ip_uuid'])

                if old_nic_ip.nic_uuid in ha_nic_uuids or new_nic_ip.nic_uuid in ha_nic_uuids:
                    return build_result("HaNodeChangeManagementIPError")

                old_nic_ip.is_manage = 0
                new_nic_ip.is_manage = 1
                old_nic_ip.soft_update()
                new_nic_ip.soft_update()
                nic_info = db_api.get_nics_first({'uuid': new_nic_ip.nic_uuid})
                node = db_api.get_node_with_first({'uuid': nic_info.node_uuid})
                if node:
                    logger.info("set node %s ip to %s", node.name, new_nic_ip.ip)
                    node.ip = new_nic_ip.ip
                    node.soft_update()
        except Exception as e:
            logger.error("node update ip fail:%s", e, exc_info=True)
            return build_result("NodeNICIpAddError")
        
        logger.info("node mn ip success!")
        return build_result("Success")
    
    def in_map_update_node(self, uplinks):
        try:
            new_nics = []
            old_nics = []
            master_nic = None
            master_ip = None
            for uplink in uplinks:
                old_nic_ip = db_api.get_nic_ip_by_uuid(uplink['old_ip_uuid'])
                new_nic_ip = db_api.get_nic_ip_by_uuid(uplink['new_ip_uuid'])

                old_nic_ip.is_image = 0
                new_nic_ip.is_image = 1
                old_nics.append(old_nic_ip)
                new_nics.append(new_nic_ip)
                node_uuid = new_nic_ip.nic.node_uuid
                node = db_api.get_node_by_uuid(node_uuid)
                if node.type in [1, 3]:
                    master_nic = new_nic_ip.nic.nic
                    master_ip = new_nic_ip.ip
            
            logger.debug("master_nic is %s", master_nic)
            for nic in new_nics:
                try:
                    if master_ip != nic.ip:
                        result = subprocess.call(["ping", "-I", master_nic, nic.ip, "-w", "2"])
                        if result != 0:
                            return build_result("ImageNetworkConnectFail")
                except Exception as e:
                    return build_result("ImageNetworkConnectFail")

            for old_nic in old_nics:
                logger.info('old_nic is ' + str(old_nic.is_image) + ' ' + old_nic.name)
                old_nic.soft_update()
            for new_nic in new_nics:
                logger.info('new_nic is ' + str(new_nic.is_image) + ' ' + new_nic.name)
                new_nic.soft_update()
        except Exception as e:
            logger.error("node update ip fail:%s", e, exc_info=True)
            return build_result("NodeNICIpAddError")
        
        logger.info("node in ip success!")
        return build_result("Success")

    def get_node_network_interface(self, ip):
        """
        查询节点的网卡信息
        :param ip:
        :return:
        """
        interface_list = []
        rep_json = self._get_node_nics(ip)
        if rep_json["code"] != 0:
            logger.error("get node:%s network info fail" % ip)
            raise Exception("node network info fail: %s" % rep_json.get("msg", ""))
        data = rep_json.get("data", {})
        for k, v in data.items():
            if isinstance(v, dict):
                v.update({"interface": k})
                interface_list.append(v)
        return interface_list

    def get_node_storage(self, ip):
        """
        查询节点的存储信息
        :param ip:
        :return:
        """
        path_list = []
        url = "/api/v1/monitor/disk"
        rep_json = monitor_post(ip, url, None)
        if rep_json["code"] != 0:
            logger.error("get node:%s storage info fail" % ip)
            raise Exception("node storage info fail: %s" % rep_json.get("msg", ""))
        data = rep_json.get("data", {})
        for k, v in data.items():
            if isinstance(v, dict) and k not in ['/', '/home', '/boot', '/boot/efi']:
                v.update({"path": k})
                path_list.append(v)

        return path_list

    def check_password(self, data):
        if not data:
            return build_result("ParamError")
        ip = data.get("ip", "")
        root_pwd = data.get("root_pwd", "")
        url = "/api/v1/monitor/verify_password"
        req = {
            "user": "root",
            "password": root_pwd
        }
        rep_json = monitor_post(ip, url, req)
        return rep_json

    def check_node(self, ip, root_pwd, check=True, is_controller=True):
        """
        检测节点的虚拟化开启情况
        """
        if not is_ip_addr(ip):
            return build_result("IPAddrError", ipaddr=ip)
        ret = self.check_node_virtual(ip, root_pwd)
        if ret["code"] != 0:
            return build_result("NodeCheckFail", ret, node=ip)
        vt_status = ret["data"]["cpuvt"]
        # hostname = ret["data"]["hostname"]
        if check and not vt_status:
            logger.error("ip: %s not support virtualization" % ip)
            return build_result("NodeNotSupportvirtual", node=ip)

        result = {}
        result["interface_list"] = []
        result["storage_list"] = []
        try:
            result["interface_list"] = self.get_node_network_interface(ip)
            result["storage_list"] = self.get_node_storage(ip)
            if not is_controller:

                default_virtual_switchs = db_api.get_virtual_switch_list({})
                virtual_switch_list = list()
                if default_virtual_switchs:
                    for default_virtual_switch in default_virtual_switchs:
                        virtual_switch_list.append(default_virtual_switch.to_json())
                    result["virtual_switch_list"] = virtual_switch_list
                if len(result.get('interface_list')) < len(default_virtual_switchs):
                    logger.error("network card less than virtual switch")
                    return build_result("NetworkCardVirtualSwitchError")
                if len(result.get('interface_list')):
                    ip_list = [interface['ip'] for interface in result.get('interface_list') if interface['ip']]
                    if not ip_list:
                        return build_result("NodeCheckFail", ret, node=ip)
        except Exception as e:
            logger.exception("node check fail", exc_info=True)
            return build_result("NodeCheckFail", node=ip)
        ret = build_result("Success", result)
        return ret

    def check_support(self, data):
        """
        :param data:
            {
                "ip": "172.16.1.49",
                "root_pwd": "123",
                "check": False,
                "is_controller": False
            }
        :return:
        """
        if not data:
            return build_result("ParamError")
        ip = data.get("ip", "")
        root_pwd = data.get("root_pwd", "")
        check = data.get("check", True)
        is_controller = data.get("is_controller", True)
        if not (ip and root_pwd):
            return build_result("ParamError")
        try:
            ret = self.check_node(ip, root_pwd, check, is_controller)
        except Exception as e:
            return build_result("NodeCheckFail", node=data['ip'])
        return ret

    def restart_service(self, node_uuid, service):
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            return build_result("NodeNotExist")
        url = "/api/v1/monitor/task"
        data = {
            "handler": "ServiceHandler",
            "command": "restart",
            "data": {
                "service": service
            }
        }
        rep_json = monitor_post(node['ip'], url, data)
        return rep_json

    def start_service(self, node_uuid, service):
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            return build_result("NodeNotExist")
        url = "/api/v1/monitor/task"
        data = {
            "handler": "ServiceHandler",
            "command": "start",
            "data": {
                "service": service
            }
        }
        rep_json = monitor_post(node['ip'], url, data)
        return rep_json

    def stop_service(self, node_uuid, service):
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            return build_result("NodeNotExist")
        url = "/api/v1/monitor/task"
        data = {
            "handler": "ServiceHandler",
            "command": "stop",
            "data": {
                "service": service
            }
        }
        rep_json = monitor_post(node['ip'], url, data)
        return rep_json

    def disable_service(self, node_uuid, service):
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            return build_result("NodeNotExist")
        url = "/api/v1/monitor/task"
        data = {
            "handler": "ServiceHandler",
            "command": "disable",
            "data": {
                "service": service
            }
        }
        rep_json = monitor_post(node['ip'], url, data)
        return rep_json

    def update_info(self, data):
        if not data:
            return build_result("ParamError")
        type = data.get("type", "")
        node_uuid = data.get("node_uuid", "")
        node_status = ""
        if not (type and node_uuid):
            return build_result("ParamError")
        try:
            if type == 'service':
                services = data.get("data", "")
                if not services:
                    return build_result("ParamError")
                service_names = services.keys()
                node_services = db_api.get_service_by_node_uuid(node_uuid)
                node_service_names = list(map(lambda node_service: node_service.name, node_services))
                exist_service_names = list(filter(lambda service_name: service_name in node_service_names, service_names))
                not_exist_service_names = list(filter(lambda service_name: service_name not in node_service_names, service_names))

                nodes = {}
                if not_exist_service_names and len(not_exist_service_names) > 0:
                    service_list = list()
                    for not_exist_service_name in not_exist_service_names:
                        service_uuid = create_uuid()
                        service = {
                            'uuid': service_uuid,
                            'node_uuid': node_uuid,
                            'name': not_exist_service_name,
                            'status': services[not_exist_service_name]
                        }
                        service_list.append(service)
                    db_api.insert_with_many(models.YzyNodeServices, service_list)
                if exist_service_names and len(exist_service_names) > 0:
                    for exist_service_name in exist_service_names:
                        service = db_api.get_service_by_name(exist_service_name)
                        service.name = exist_service_name
                        service.status = services[exist_service_name]
                        service.soft_update()
            elif type == 'resource':
                pass

        except Exception as e:
            return build_result("NodeCheckFail", node_uuid)

        return build_result("Success")

    def update_node_monitor(self, data):
        """更新服务节点的监控信息"""
        try:
            update_node_status()
        except Exception as e:
            logger.error("", exc_info=True)
        return build_result("Success")

    def add_bond(self, data):
        """
        添加网卡bond
        {
            "ipaddr": "172.16.1.88",
            "node_uuid": "f819e839-e193-4356-b6b4-acc35652ce27",
            "slaves": [
                {
                    "nic_uuid": "d206a470-5252-4d88-96d3-afb125aef1aa",
                    "nic_name": "eth1",
                },
                {
                    "nic_uuid": "c6c29155-9994-4e2c-a2f6-deba1397297b",
                    "nic_name": "eth2"
                }
            ],
            "ip_list":[
                {
                    "ip": "192.168.1.88",
                    "netmask": "255.255.255.0",
                    "is_manage": 0,
                    "is_image": 0
                },
                {
                    "ip": "192.168.1.89",
                    "netmask": "255.255.255.0",
                    "is_manage": 0,
                    "is_image": 0
                }
            ],
            "gate_info": {
                    "gateway": "192.168.1.254",
                    "dns1": "8.8.8.8",
                    "dns2": "",
            },
            "bond_info": {
                "dev": "bond0",
                "mode": 0,
                "slaves": ["eth1", "eth2"]
            }
        }
        """
        try:
            logger.info("data: %s" % data)
            # networks = list()
            # # 获取slave网卡上的数据网络，提供给compute服务做替换
            # for slave_nic in data["slaves"]:
            #     net_list = db_api.get_network_by_nic(nic_uuid=slave_nic["nic_uuid"], node_uuid=data["node_uuid"])
            #     for net in net_list:
            #         networks.append({
            #             "network_id": net.uuid,
            #             "network_type": net.switch_type,
            #             "vlan_id": net.vlan_id
            #         })
            # logger.info("networks: %s" % networks)

            # 校验：网关必须和其中一个IP在同一个网络
            # 重排：网关所在网络的那个IP必须放在第一个，否则网关设置不成功
            try:
                ip_list = self._reorder_ip_list(data["ip_list"], data["gate_info"])
            except Exception as e:
                return build_result("GatewayAndIpError")

            _data = {
                "command": "bond",
                "handler": "NetworkHandler",
                "data": {
                    "ip_list": ip_list,
                    "gate_info": data["gate_info"],
                    "bond_info": data["bond_info"]
                }
            }

            # 请求compute服务变更网卡配置文件
            rep_json = compute_post(data["ipaddr"], _data)
            ret_code = rep_json.get("code", -1)
            if ret_code != 0:
                logger.error("add bond failed in compute_node: %s" % rep_json['msg'])
                return jsonify(rep_json)
            logger.info("add bond: %s in compute_node %s success" %  (data["bond_info"]["dev"], data["ipaddr"]))

            # 需要处理3个库表：interface_ip、bond_nics、node_network_info
            # 在yzy_node_network_info中新增bond网卡，slave网卡的原有数据不变，只是在展示网卡的时候过滤掉
            bond_nic_info = rep_json["data"]["bond_nic_info"]
            bond_nic_info["uuid"] = create_uuid()
            bond_nic_info["node_uuid"] = data["node_uuid"]
            bond_nic_info["type"] = 1
            db_api.add_nic(bond_nic_info)
            logger.info("bond: %s in table: yzy_node_network_info, data: %s" %
                        (data["bond_info"]["dev"], bond_nic_info))
            logger.info("bond: %s in table: yzy_node_network_info success" % data["bond_info"]["dev"])

            # 在yzy_bond_nics中新增bond与slave的绑定关系
            for slave_nic in data["slaves"]:
                info = {
                    "uuid": create_uuid(),
                    "mode": data["bond_info"]["mode"],
                    "master_uuid": bond_nic_info["uuid"],
                    "master_name": bond_nic_info["nic"],
                    "slave_uuid": slave_nic["nic_uuid"],
                    "slave_name": slave_nic["nic_name"],
                    # "vs_uplink_uuid": slave_nic["vs_uplink_uuid"],
                    "node_uuid": data["node_uuid"]
                }
                db_api.add_bond_nics(info)
                logger.info("bond: %s insert into table: yzy_bond_nics, data: %s" %  (data["bond_info"]["dev"], info))
            logger.info("bond: %s in table: yzy_bond_nics success" % data["bond_info"]["dev"])

            # 在yzy_interface_ip中新增bond网卡的ip
            for ip_info in data["ip_list"]:
                ip_info["uuid"] = create_uuid()
                ip_info["name"] = data["bond_info"]["dev"]
                ip_info["nic_uuid"] = bond_nic_info["uuid"]
                ip_info["gateway"] = data["gate_info"]["gateway"]
                ip_info["dns1"] = data["gate_info"]["dns1"]
                ip_info["dns2"] = data["gate_info"]["dns2"]
                db_api.add_nic_ip(ip_info)
                logger.info("bond: %s insert into table: yzy_interface_ip, data: %s" % (data["bond_info"]["dev"], ip_info))
            logger.info("bond: %s in table: yzy_interface_ip success" % data["bond_info"]["dev"])

            # # 在yzy_interface_ip中新增bond网卡的ip
            # # server层给compute层的ip_list中包含了两个多余字段：is_manage、is_image
            # # compute层会把ip_list再加一个字段name，作为bond_interface_ip返回
            # # 因此，在bond_interface_ip上再增加两个字段uuid、nic_uuid，就能直接入库了
            # for ip_info in rep_json["data"]["bond_interface_ip"]:
            #     ip_info["uuid"] = create_uuid()
            #     ip_info["nic_uuid"] = bond_nic_info["uuid"]
            #     db_api.add_nic_ip(ip_info)
            #     logger.info("bond: %s insert into table: yzy_interface_ip, data: %s" % (data["bond_info"]["dev"], ip_info))
            # logger.info("bond: %s in table: yzy_interface_ip success" % data["bond_info"]["dev"])

            # 删除slave网卡上的interface_ip
            for slave_nic in data["slaves"]:
                interface_ips = db_api.get_nic_ips_all({"nic_uuid": slave_nic["nic_uuid"]})
                for ip in interface_ips:
                    ip.soft_delete()
                    logger.info("delete yzy_interface_ip: nic_uuid: %s, name: %s, ip: %s" % (slave_nic["nic_uuid"], slave_nic["nic_name"], ip.ip))
            logger.info("delete slaves of bond: %s in table: yzy_interface_ip success" % data["bond_info"]["dev"])

            #     # 更新slave网卡上的交换机
            #     # 前提：slave网卡上最多只有1个交换机，且最多只有1个slave网卡绑定了交换机（web层已做校验）
            #     vs_uplink = db_api.get_uplinks_first({"nic_uuid": slave_nic["nic_uuid"], "node_uuid": data["node_uuid"]})
            #     # 如果slave网卡上有交换机，则把vswitch_uplink的nic_uuid替换为bond网卡
            #     if vs_uplink:
            #         # uplink_info = {
            #         #     "uuid": create_uuid(),
            #         #     "vs_uuid": uplink.vs_uuid,
            #         #     "nic_uuid": bond_nic_info["uuid"],
            #         #     "node_uuid": data["node_uuid"]
            #         # }
            #         # db_api.add_virtual_switch_uplink(uplink_info)
            #         # uplink.soft_delete()
            #         vs_uplink.nic_uuid = bond_nic_info["uuid"]
            #         logger.info("update yzy_vswitch_uplink: uplink.uuid: %s, data: nic_uuid: %s" % (vs_uplink.uuid, vs_uplink.nic_uuid))
            # logger.info("bond: %s in table: yzy_virtual_switch_uplink success" % data["bond_info"]["dev"])

        except Exception as e:
            logger.exception("add_bond Exception: %s" % str(e), exc_info=True)
            return build_result("BondAddError", node=data["ipaddr"], data=str(e))

        return build_result("Success")

    def edit_bond(self, data):
        """
        编辑网卡bond
        {
            "ipaddr": "172.16.1.88",
            "bond_uuid": "",
            "slaves": [
                {
                    "nic_uuid": "d206a470-5252-4d88-96d3-afb125aef1aa",
                    "nic_name": "eth1",
                },
                {
                    "nic_uuid": "c6c29155-9994-4e2c-a2f6-deba1397297b",
                    "nic_name": "eth2"
                }
            ],
            "ip_list":[
                {
                    "ip": "192.168.1.88",
                    "netmask": "255.255.255.0",
                    "is_manage": 0,
                    "is_image": 0
                },
                {
                    "ip": "192.168.1.89",
                    "netmask": "255.255.255.0",
                    "is_manage": 0,
                    "is_image": 0
                }
            ],
            "gate_info": {
                    "gateway": "192.168.1.254",
                    "dns1": "8.8.8.8",
                    "dns2": "",
            },
            "bond_info": {
                "dev": "bond0",
                "mode": 0,
                "slaves": ["eth1", "eth2"]
            }
        }
        """
        try:
            logger.info("data: %s" % data)
            # 找出减少了哪些slave，新增了哪些slave
            bond_nics = db_api.get_bond_nics_all({"master_uuid": data["bond_uuid"]})
            old_slaves = [bond_nic.slave_name for bond_nic in bond_nics]
            remove_slaves = [old for old in old_slaves if old not in data["bond_info"]["slaves"]]
            new_slaves = [new for new in data["bond_info"]["slaves"] if new not in old_slaves]

            # 校验：网关必须和其中一个IP在同一个网络
            # 重排：网关所在网络的那个IP必须放在第一个，否则网关设置不成功
            try:
                ip_list = self._reorder_ip_list(data["ip_list"], data["gate_info"])
            except Exception as e:
                return build_result("GatewayAndIpError")

            _data = {
                "command": "edit_bond",
                "handler": "NetworkHandler",
                "data": {
                    "ip_list": ip_list,
                    "gate_info": data["gate_info"],
                    "bond_info": data["bond_info"],
                    "remove_slaves": remove_slaves
                }
            }

            # 请求compute服务变更网卡配置文件
            rep_json = compute_post(data["ipaddr"], _data)
            ret_code = rep_json.get("code", -1)
            if ret_code != 0:
                logger.error("edit bond failed in compute_node: %s" % rep_json['msg'])
                return jsonify(rep_json)
            logger.info("edit bond: %s in compute_node %s success" %  (data["bond_info"]["dev"], data["ipaddr"]))

            # 需要处理3个库表：interface_ip、bond_nics、node_network_info
            # 在yzy_node_network_info中更新bond网卡的mac、speed、status，只有这三个字段有可能变化
            bond_nic_info = rep_json["data"]["bond_nic_info"]
            bond_nic_obj = db_api.get_nics_first({"uuid": data["bond_uuid"]})
            bond_nic_obj.mac = bond_nic_info["mac"]
            bond_nic_obj.speed = bond_nic_info["speed"]
            bond_nic_obj.status = bond_nic_info["status"]
            bond_nic_obj.soft_update()
            logger.info("bond: %s update table: yzy_node_network_info, data: %s" %
                        (data["bond_info"]["dev"], bond_nic_info))
            logger.info("bond: %s update table: yzy_node_network_info success" % data["bond_info"]["dev"])

            for bond_nic in bond_nics:
                # 在yzy_bond_nics中删除减少的slave与bond的绑定关系
                if bond_nic.slave_name in remove_slaves:
                    logger.info("delete yzy_bond_nics: master_name: %s, slave_name: %s" %
                                (bond_nic.master_name, bond_nic.slave_name))
                    bond_nic.soft_delete()
                # 在yzy_bond_nics中更新mode
                else:
                    if bond_nic.mode != data["bond_info"]["mode"]:
                        bond_nic.mode = data["bond_info"]["mode"]
                        bond_nic.soft_update()
                        logger.info("update yzy_bond_nics: master_name: %s, slave_name: %s, mode: %s" %
                                (bond_nic.master_name, bond_nic.slave_name, bond_nic.mode))

            # 在yzy_bond_nics中添加新slave与bond的绑定关系
            for slave_nic in data["slaves"]:
                if slave_nic["nic_name"] in new_slaves:
                    info = {
                        "uuid": create_uuid(),
                        "mode": data["bond_info"]["mode"],
                        "master_uuid": bond_nic_obj.uuid,
                        "master_name": bond_nic_obj.nic,
                        "slave_uuid": slave_nic["nic_uuid"],
                        "slave_name": slave_nic["nic_name"],
                        # "vs_uplink_uuid": slave_nic["vs_uplink_uuid"],
                        "node_uuid": bond_nic_obj.node_uuid
                    }
                    db_api.add_bond_nics(info)
                    logger.info("bond: %s insert into table: yzy_bond_nics, data: %s" %  (data["bond_info"]["dev"], info))
            logger.info("bond: %s update table: yzy_bond_nics success" % data["bond_info"]["dev"])

            manage_or_image_ips = list()
            # 在yzy_interface_ip中删除bond网卡上的无角色ip，对有角色IP更新网关
            # 由于网关：管理 > 镜像 > 传参，新slave可能有管理\镜像IP，将导致bond上原有IP的网关要更新
            interface_ips = db_api.get_nic_ips_all({"nic_uuid": data["bond_uuid"]})
            for ip_obj in interface_ips:
                # 删除bond网卡上的无角色ip
                if ip_obj.is_manage != 1 and ip_obj.is_image != 1:
                    ip_obj.soft_delete()
                    logger.info("delete yzy_interface_ip: nic_uuid: %s, name: %s, ip: %s" %
                                (ip_obj.nic_uuid, ip_obj.name, ip_obj.ip))
                # 对有角色IP更新网关
                else:
                    manage_or_image_ips.append(ip_obj.ip)
                    ip_obj.gateway = data["gate_info"]["gateway"]
                    ip_obj.dns1 = data["gate_info"]["dns1"]
                    ip_obj.dns2 = data["gate_info"]["dns2"]
                    ip_obj.soft_update()

            # 删除slave网卡上的interface_ip，主要是为了删除新slave上的IP
            for slave_nic in data["slaves"]:
                interface_ips = db_api.get_nic_ips_all({"nic_uuid": slave_nic["nic_uuid"]})
                for ip in interface_ips:
                    ip.soft_delete()
                    logger.info("delete yzy_interface_ip: nic_uuid: %s, name: %s, ip: %s" % (slave_nic["nic_uuid"], slave_nic["nic_name"], ip.ip))

            # 在yzy_interface_ip中新增bond网卡的无角色ip，以及新slave上的管理或镜像IP
            for ip_info in data["ip_list"]:
                if ip_info["ip"] not in manage_or_image_ips:
                    ip_info["uuid"] = create_uuid()
                    ip_info["name"] = data["bond_info"]["dev"]
                    ip_info["nic_uuid"] = bond_nic_obj.uuid
                    ip_info["gateway"] = data["gate_info"]["gateway"]
                    ip_info["dns1"] = data["gate_info"]["dns1"]
                    ip_info["dns2"] = data["gate_info"]["dns2"]
                    db_api.add_nic_ip(ip_info)
                    logger.info("bond: %s insert into table: yzy_interface_ip, data: %s" % (data["bond_info"]["dev"], ip_info))
            logger.info("bond: %s update table: yzy_interface_ip success" % data["bond_info"]["dev"])

        except Exception as e:
            logger.exception("edit_bond Exception: %s" % str(e), exc_info=True)
            return build_result("BondEditError", node=data["ipaddr"], data=str(e))

        return build_result("Success")

    def unbond(self, data):
        """
        "ipaddr": "",
        "slaves": [
            {
                "nic_name": "eth0",
                "nic_uuid": "",
                "ip_list": [
                    {
                        "ip": "",
                        "netmask": "",
                        "gateway": "192.168.1.254",
                        "dns1": "8.8.8.8",
                        "dns2": "",
                        "is_manage": 0,
                        "is_image": 0
                    },
                ...
                ]
            },
            ...
        ],
        "bond_name": "bond0",
        "bond_uuid": ""
        """
        try:
            logger.info("data: %s" % data)
            # # 如果bond网卡上有数据网络，则不能解绑bond
            # net_list = db_api.get_network_by_nic(nic_uuid=data["bond_uuid"], node_uuid=data["node_uuid"])
            # if net_list:
            #     return build_result("BondDeleteError", node=data["ipaddr"])

            _data = {
                "command": "unbond",
                "handler": "NetworkHandler",
                "data": {
                    "slaves": list(),
                    "bond_name": data["bond_name"]
                }
            }

            for slave_nic in data.get("slaves", []):
                info =  {
                    "nic": slave_nic["nic_name"],
                    "ip_list": list(),
                }
                if slave_nic["ip_list"]:
                    # 重排slave的ip_list：管理、镜像IP放在第一位
                    # 不用校验这些ip是否与网关在同一网络，因为所有ip的网关都是同一个（继承于bond网关），很可能不在同一网络
                    slave_nic["ip_list"].sort(key=lambda x: (-x["is_manage"], -x["is_image"]))
                    info["ip_list"] = [{
                        "ip": _d["ip"],
                        "netmask": _d["netmask"],
                        "gateway": _d["gateway"],
                        "dns1": _d["dns1"],
                        "dns2": _d["dns2"],
                    } for _d in slave_nic["ip_list"]]

                _data["data"]["slaves"].append(info)

            # 请求compute服务变更网卡配置文件
            rep_json = compute_post(data["ipaddr"], _data)
            ret_code = rep_json.get("code", -1)
            if ret_code != 0:
                logger.error("unbond failed in compute_node: %s" % rep_json['msg'])
                return jsonify(rep_json)
            logger.info("unbond: delete %s in compute_node %s success" % (data["bond_name"], data["ipaddr"]))

            # 需要处理3个库表：interface_ip、bond_nics、node_network_info
            # 删除bond网卡上的interface_ip
            interface_ips = db_api.get_nic_ips_all({"nic_uuid": data["bond_uuid"]})
            for ip_obj in interface_ips:
                ip_obj.soft_delete()
                logger.info("delete yzy_interface_ip: nic_uuid: %s, name: %s, ip: %s" %
                            (ip_obj.nic_uuid, ip_obj.name, ip_obj.ip))

            # 允许用户选择将bond网卡上的IP分配给哪个网卡
            # 对于继承了ip的slave网卡，新增interface_ip
            for slave_nic in data["slaves"]:
                for ip_dict in slave_nic.get("ip_list", []):
                    ip_info = {
                        "uuid": create_uuid(),
                        "name": slave_nic["nic_name"],
                        "nic_uuid": slave_nic["nic_uuid"],
                        "ip": ip_dict["ip"],
                        "netmask": ip_dict["netmask"],
                        "gateway": ip_dict["gateway"],
                        "dns1": ip_dict["dns1"],
                        "dns2": ip_dict["dns2"],
                        "is_manage": ip_dict["is_manage"],
                        "is_image": ip_dict["is_image"]
                    }
                    db_api.add_nic_ip(ip_info)
                    logger.info(
                        "nic: %s insert into table: yzy_interface_ip, data: %s" % (slave_nic["nic_name"], ip_info)
                    )
            logger.info("unbond: delete %s in table: yzy_interface_ip success" % data["bond_name"])

            # # 更新bond网卡上的交换机
            # # 前提：bond网卡上最多只有1个交换机，且最多只有1个slave网卡曾经绑定过交换机
            # vs_uplink = db_api.get_uplinks_first({"nic_uuid": data["bond_uuid"], "node_uuid": data["node_uuid"]})
            # if vs_uplink:
            #     slave_is_uplink = db_api.get_bond_nics_first({"master_uuid": data["bond_uuid"], "vs_uplink_uuid": vs_uplink.uuid})
            #     # 如果有slave网卡曾经绑定过该交换机，说明bond网卡的交换机是从该slave中继承过来的，则还原回去
            #     # 把vswitch_uplink的nic_uuid更新为曾经绑定了该交换机的原slave网卡
            #     if slave_is_uplink:
            #         vs_uplink.nic_uuid = slave_is_uplink.slave_uuid
            #         logger.info("update yzy_vswitch_uplink: uplink.uuid: %s, nic_uuid: %s" %
            #                     (vs_uplink.uuid, vs_uplink.nic_uuid))
            #     # 如果没有slave网卡曾经绑定过该交换机，说明bond网卡的交换机是后来新增的或改变来的，则删除bond网卡与该交换机的uplink
            #     else:
            #         vs_uplink.soft_delete()
            #         logger.info("delete yzy_vswitch_uplink: uplink.uuid: %s, nic_uuid: %s" %
            #                     (vs_uplink.uuid, vs_uplink.nic_uuid))
            # logger.info("unbond: %s in table: yzy_vswitch_uplink success" % data["bond_name"])

            # 删除bond_nics中的bond与slave绑定关系
            bond_nics = db_api.get_bond_nics_all({"master_uuid": data["bond_uuid"]})
            for bond_nic in bond_nics:
                logger.info("delete yzy_bond_nics: master_name: %s, slave_name: %s" %
                            (bond_nic.master_name, bond_nic.slave_name))
                bond_nic.soft_delete()
            logger.info("unbond: delete %s in table: yzy_bond_nics success" % data["bond_name"])

            # 删除node_network_info中的bond网卡
            bond_nic_info = db_api.get_nics_first({"uuid": data["bond_uuid"]})
            bond_nic_info.soft_delete()
            logger.info("delete yzy_node_network_info: uuid: %s, nic: %s" %
                        (data["bond_uuid"], data["bond_name"]))
            logger.info("unbond: delete %s in table: yzy_node_network_info success" % data["bond_name"])

        except Exception as e:
            logger.exception("unbond Exception: %s" % str(e), exc_info=True)
            return build_result("BondDeleteError", node=data["ipaddr"], data=str(e))

        return build_result("Success")

    def _reorder_ip_list(self, ips, gate_info):
        gate_ip = None
        count = 0
        # all_info = list()
        # 网关必须和其中一个IP在同一个网络
        if gate_info.get("gateway", ""):
            for info in ips[::-1]:
                netmask_bits = netaddr.IPAddress(info["netmask"]).netmask_bits()
                network_num = ipaddress.ip_interface(info["ip"] + "/" + str(netmask_bits)).network
                if ipaddress.IPv4Address(gate_info["gateway"]) not in network_num:
                    count += 1
                else:
                    gate_ip = info
            if count > 0 and count == len(ips):
                raise Exception("GatewayAndIpError")

        # 网关所在网络的那个IP必须放在第一个，否则网关设置不成功
        # 如果有管理、镜像IP，则网关一定是管理、镜像IP的，将其放在第一位
        # 如果都是无角色IP，则网关所在网络的那个IP放在第一位
        ips.sort(key=lambda x: (-x["is_manage"], -x["is_image"]))
        first_ip = ips[0]
        if not first_ip["is_manage"] and not first_ip["is_image"] and gate_ip:
            first_ip = gate_ip

        if first_ip is not ips[0]:
            ips.remove(first_ip)
            ips.insert(0, first_ip)

        return [{"ip": _d["ip"], "netmask": _d["netmask"]} for _d in ips]

    def change_master(self, data):
        master_ip = data.get('master_ip', '')
        node = db_api.get_node_with_first({"ip": master_ip})
        if not node:
            return build_result("NodeNotExist")

        # 主备切换后，更新yzy_ha_info表，master与backup角色对换
        ha_info_objs = db_api.get_ha_info_all()
        for ha_info_obj in ha_info_objs:
            if ha_info_obj.backup_ip == master_ip:
                ha_info_obj.master_ip, ha_info_obj.backup_ip = ha_info_obj.backup_ip, ha_info_obj.master_ip
                ha_info_obj.master_nic, ha_info_obj.backup_nic = ha_info_obj.backup_nic, ha_info_obj.master_nic
                ha_info_obj.master_nic_uuid, ha_info_obj.backup_nic_uuid = ha_info_obj.backup_nic_uuid, ha_info_obj.master_nic_uuid
                ha_info_obj.master_uuid, ha_info_obj.backup_uuid = ha_info_obj.backup_uuid, ha_info_obj.master_uuid
                ha_info_obj.soft_update()
                logger.info("update ha_info[%s] master ip/nic/nic_uuid/node_uuid from %s to %s",
                            (ha_info_obj.uuid, ha_info_obj.backup_ip, ha_info_obj.master_ip))

        if node.type in [constants.ROLE_MASTER, constants.ROLE_MASTER_AND_COMPUTE]:
            logger.info("node role is master, return")
            return build_result("Success")

        # 主备切换后，更新yzy_nodes表的节点type
        origin = db_api.get_controller_node()
        origin_type = origin.type
        if constants.ROLE_MASTER_AND_COMPUTE == origin_type:
            origin.type = constants.ROLE_SLAVE_AND_COMPUTE
        else:
            origin.type = constants.ROLE_SLAVE
        logger.info("update node %s role from %s to %s", origin.ip, origin_type, origin.type)
        origin.soft_update()
        node_type = node.type
        if node_type in [constants.ROLE_SLAVE_AND_COMPUTE, constants.ROLE_SLAVE]:
            node.type = constants.ROLE_MASTER_AND_COMPUTE
        else:
            node.type = constants.ROLE_MASTER
        logger.info("update node %s role from %s to %s", node.ip, node_type, node.type)
        node.soft_update()

        # 主备切换后，更新yzy_template、yzy_voi_template表的模板宿主机uuid
        templates = db_api.get_template_with_all({})
        for template in templates:
            if constants.SYSTEM_DESKTOP == template.classify:
                continue
            logger.info("update template %s host_uuid to %s", template.name, node.uuid)
            template.host_uuid = node.uuid
            template.soft_update()
        voi_templates = db_api.get_voi_template_with_all({})
        for template in voi_templates:
            if constants.SYSTEM_DESKTOP == template.classify:
                continue
            logger.info("update template %s host_uuid to %s", template.name, node.uuid)
            template.host_uuid = node.uuid
            template.soft_update()

        # 主备切换后，更新yzy_node_services表
        # 特别是当备控第一次切换成主控时，其服务列表应从计算服务更新为主控服务
        ret = monitor_post(node.ip, 'api/v1/monitor/service', {})
        if ret.get('code') == 0:
            services = ret['data']
            logging.info("update service status")
            update_service_status(node, services, constants.MASTER_SERVICE)
        return build_result("Success")

    def ha_sync(self, path):

        def send_file():
            store_path = path
            with open(store_path, 'rb') as targetfile:
                while True:
                    data = targetfile.read(constants.CHUNKSIZE)
                    if not data:
                        break
                    yield data

        if not os.path.exists(path):
            return build_result("Success")
        else:
            file_name = os.path.split('/')[-1]
            logger.debug("begin to send file %s", path)
            response = Response(send_file(), content_type='application/octet-stream')
            response.headers["Content-disposition"] = 'attachment; filename=%s' % file_name
            logger.debug("finish to send file %s", path)
            return response

    def enable_ha(self, data):
        update_ip_data = data.get("update_ip_data", None)
        enable_ha_data = data.get("enable_ha_data", None)
        if not update_ip_data or not enable_ha_data:
            logger.error("enable_ha ParamError update_ip_data: %s, enable_ha_data: %s" % (update_ip_data, enable_ha_data))
            return build_result("ParamError", data={"update_ip_data": update_ip_data, "enable_ha_data": enable_ha_data})
        else:
            update_ip_ret = self._update_ip_node(update_ip_data)
            enable_ha_ret = self._enable_ha(enable_ha_data)
            return build_result("Success", data={"update_ip_ret": update_ip_ret, "enable_ha_ret": enable_ha_ret})

    def _enable_ha(self, data):
        try:
            logger.info("data: %s" % data)
            # if not icmp_ping(data["quorum_ip"], count=3):
            #     return build_result("QuorumIPConnectError")

            # 找出需要同步的ISO库、数据库备份文件，VOI模板的base盘、差异盘、种子文件、XML
            paths = list()
            voi_xlms = list()
            voi_template_list = list()
            voi_ha_domain_info = list()
            for iso in db_api.get_item_with_all(models.YzyIso, {}):
                paths.append(iso.path)
            for bak in db_api.get_item_with_all(models.YzyDatabaseBack, {}):
                paths.append(bak.path)
            for template in db_api.get_voi_template_with_all({}):
                voi_template_list.extend(
                    get_template_images(template.uuid, template.host_uuid, download_base_disk=True, download_torrent=True)
                )
                voi_ha_domain_info.append(get_voi_ha_domain_info(template, data["backup_uuid"]))
                voi_xlms.append("/etc/libvirt/qemu/" + constants.VOI_BASE_NAME % template.id + ".xml")

            info = {
                "vip": data["vip"],
                "netmask": data["netmask"],
                "sensitivity": data["sensitivity"],
                "quorum_ip": data["quorum_ip"],
                "master_ip": data["master_ip"],
                "backup_ip": data["backup_ip"],
                "master_nic": data["master_nic"],
                "backup_nic": data["backup_nic"],
                "paths": paths,
                "voi_template_list": voi_template_list,
                "voi_xlms": voi_xlms,
                "voi_ha_domain_info": voi_ha_domain_info,
                "post_data": data["post_data"]
            }

            # 请求本地compute服务配置HA
            _data = {
                "command": "enable_ha",
                "handler": "HaHandler",
                "data": info
            }
            rep_json = compute_post('127.0.0.1', _data, timeout=1800)
            ret_code = rep_json.get("code", -1)
            if ret_code != 0:
                logger.error("enable_ha failed in compute_node: %s" % rep_json['msg'])
                return rep_json
            logger.info("enable_ha in compute_node %s and %s success" % (data["master_ip"], data["backup_ip"]))

            # 在yzy_ha_info表新增记录
            info["uuid"] = create_uuid()
            info["master_uuid"] = data["master_uuid"]
            info["backup_uuid"] = data["backup_uuid"]
            info["master_nic_uuid"] = data["master_nic_uuid"]
            info["backup_nic_uuid"] = data["backup_nic_uuid"]

            db_api.add_ha_info(info)
            logger.info("insert in table: yzy_ha_info, data: %s" % info)

            # 将备控节点在yzy_node表中的type更新为2（计算和备控一体）
            node_obj = db_api.get_node_by_uuid(data["backup_uuid"])
            node_obj.type = constants.ROLE_SLAVE_AND_COMPUTE
            node_obj.soft_update()
            logger.info("update table: yzy_node: node_uuid %s, type %s" % (data["backup_uuid"], node_obj.type))
        except Exception as e:
            logger.exception("enable_ha Exception: %s" % str(e), exc_info=True)
            return get_error_result("EnableHAError", data=str(e))
        return get_error_result("Success")

    def disable_ha(self, data):
        try:
            logger.info("data: %s" % data)

            ha_info_obj = db_api.get_ha_info_by_uuid(data.get("ha_info_uuid", ""))
            if not ha_info_obj:
                return build_result("ParamError")

            new_master_ip = ha_info_obj.vip
            vip_host_ip, peer_host_ip, peer_uuid = self.get_host_and_peer_ip(ha_info_obj)

            # 校验HA运行状态
            if not self._check_ha_running_status(peer_host_ip):
                return build_result("HaNotRunningError")

            # 找出需要删除的ISO库、数据库备份文件，VOI模板的base盘、差异盘、种子文件、XML
            paths = list()
            voi_xlms = list()
            voi_template_list = list()
            for iso in db_api.get_item_with_all(models.YzyIso, {}):
                paths.append(iso.path)
            for bak in db_api.get_item_with_all(models.YzyDatabaseBack, {}):
                paths.append(bak.path)
            for template in db_api.get_voi_template_with_all({}):
                voi_template_list.extend(
                    get_template_images(template.uuid, template.host_uuid, download_base_disk=True, download_torrent=True)
                )
                voi_xlms.append("/etc/libvirt/qemu/" + constants.VOI_BASE_NAME % template.id + ".xml")

            # 获取变更主控IP所需信息
            master_ip_obj = db_api.get_nic_ip_by_ip(vip_host_ip)
            post_data = {
                "uuid": master_ip_obj.uuid,
                "nic_uuid": master_ip_obj.nic_uuid,
                "nic_name": master_ip_obj.name,
                "node_ip": "127.0.0.1",
                "ip": ha_info_obj.vip,
                "netmask": master_ip_obj.netmask,
                "ha_flag": True
            }
            logger.info("post_data: %s", post_data)

            # 在yzy_ha_info表删除记录
            ha_info_obj.soft_delete()
            logger.info("delete in table: yzy_ha_info, ha_info_uuid: %s" % data["ha_info_uuid"])

            # 将peer节点在yzy_node表中的type更新为5（计算）
            node_obj = db_api.get_node_by_uuid(peer_uuid)
            node_obj.type = constants.ROLE_COMPUTE
            node_obj.soft_update()
            logger.info("update table: yzy_node: node_uuid %s, type %s" % (peer_uuid, node_obj.type))

            # 请求本地compute服务清除HA配置，不等待直接返回
            logger.info("disable_ha in compute_node %s and %s" % (vip_host_ip, peer_host_ip))
            _data = {
                "command": "disable_ha",
                "handler": "HaHandler",
                "data": {
                    "vip_host_ip": vip_host_ip,
                    "peer_host_ip": peer_host_ip,
                    "paths": paths,
                    "voi_template_list": voi_template_list,
                    "voi_xlms": voi_xlms,
                    "post_data": post_data
                }
            }
            self._subprocess_compute_post(_data)
            return build_result("Success", data=new_master_ip)
        except Exception as e:
            logger.exception("disable_ha Exception: %s" % str(e), exc_info=True)
            return build_result("DisableHAError", data=str(e))

    def switch_ha_master(self, data):
        try:
            logger.info("data: %s" % data)

            new_vip_host_ip = data.get("new_vip_host_ip", None)
            vip = data.get("vip", None)
            if not new_vip_host_ip or not vip:
                return build_result("ParamError")

            # 如果new_vip_host就是本节点，则无需切换
            # code, out = cmdutils.run_cmd("ip addr |grep {ip}".format(ip=new_vip_host_ip), ignore_log=True)
            # if code == 0 and new_vip_host_ip in out:
            #     logging.info("new_vip_host_ip %s already master, no need to switch" % new_vip_host_ip)
            #     return build_result("Success")

            code, out = cmdutils.run_cmd("""ip -br a |grep ' UP ' |grep -o '[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*'""",
                                         ignore_log=True)
            if code != 0:
                logger.error(out)
            else:
                ip_list = [ip for ip in out.strip('\n').split('\n')]
                for ip in ip_list:
                    if ip == new_vip_host_ip:
                        logging.info("new_vip_host_ip %s already master, no need to switch" % new_vip_host_ip)
                        return build_result("Success")

            # # 校验HA运行状态
            # if not self._check_ha_running_status(new_vip_host_ip):
            #     return build_result("HaNotRunningError")

            # 校验HA运行状态、数据同步状态
            rep_json = self._ha_status({})
            data = rep_json.get("data", {})
            for key in ["ha_enable_status", "ha_running_status", "master_net_status", "backup_net_status"]:
                if data.get(key, constants.HA_STATUS_UNKNOWN) != constants.HA_STATUS_NORMAL:
                    return build_result("HaNotRunningError", data=data)
            if data.get("data_sync_status", constants.HA_STATUS_UNKNOWN) != constants.HA_STATUS_NORMAL:
                return build_result("HaNotSyncingError", data=data)

            # notify.sh脚本中会发请求更新yzy_node表两个节点的type以及yzy_template表的宿主机uuid，因此本接口不做表处理
            # 请求本地compute服务切换主备，不等待直接返回
            logger.info("switch_ha_master at compute node: %s" % new_vip_host_ip)
            _data = {
                "command": "switch_ha_master",
                "handler": "HaHandler",
                "data": {
                    "new_vip_host_ip": new_vip_host_ip,
                    "vip": vip
                }
            }
            self._subprocess_compute_post(_data)
            return build_result("Success")
        except Exception as e:
            logger.exception("switch_ha_master Exception: %s" % str(e), exc_info=True)
            return build_result("SwitchHaMasterError", data=str(e))

    def ha_status(self, data):
        return jsonify(self._ha_status(data))

    def _ha_status(self, data):
        try:
            if data.get("ha_info_uuid", ""):
                ha_info_obj = db_api.get_ha_info_by_uuid(data.get("ha_info_uuid", ""))
            else:
                ha_info_obj = db_api.get_ha_info_first()

            if not ha_info_obj:
                return get_error_result("Success")
                # return get_error_result("ParamError")

            vip_host_ip, peer_host_ip, peer_uuid = self.get_host_and_peer_ip(ha_info_obj)
            ha_enable_status = constants.HA_STATUS_NORMAL
            ha_running_status = constants.HA_STATUS_NORMAL
            master_net_status = constants.HA_STATUS_NORMAL
            backup_net_status = constants.HA_STATUS_NORMAL

            # 数据同步状态包括3部分：
            # 1、主控节点上mysql slave 线程是否正常；
            master_mysql_slave_status = constants.HA_STATUS_UNKNOWN
            # 2、备控节点上mysql slave 线程是否正常；
            backup_mysql_slave_status = constants.HA_STATUS_UNKNOWN
            # 3、后台定时任务同步ISO库和数据库备份文件是否完成；
            file_sync_status = constants.HA_STATUS_UNKNOWN

            # 本节点ping不通网关（以敏感度为限）：视为主控网络连接状态断开
            if not icmp_ping(ha_info_obj.quorum_ip, timeout=1, count=ha_info_obj.sensitivity):
                master_net_status = constants.HA_STATUS_FAULT
                logger.error("vip_host[%s] ping quorum_ip[%s] failed" % (vip_host_ip, ha_info_obj.quorum_ip))

            # 主控节点上mysql slave 线程报错，视为数据同步状态：未同步
            query_ret = db.session.execute("show slave status;").first()
            if query_ret:
                query_ret = [i for i in query_ret if isinstance(i, str) and i.startswith("Error ")]
                if query_ret:
                    logger.error("master node mysql slave status error: %s", query_ret)
                    master_mysql_slave_status = constants.HA_STATUS_FAULT
                else:
                    master_mysql_slave_status = constants.HA_STATUS_NORMAL

            # 本节点ping不通备控：视为HA运行状态故障、备控网络连接状态未知
            if not icmp_ping(peer_host_ip, timeout=1, count=3):
                ha_running_status = constants.HA_STATUS_FAULT
                backup_net_status = constants.HA_STATUS_UNKNOWN
                logger.error("vip_host[%s] ping peer_host_ip[%s] failed" % (vip_host_ip, peer_host_ip))
            else:
                # 本节点keepalived未正常运行：视为HA运行状态故障
                code, out = cmdutils.run_cmd("systemctl status keepalived", ignore_log=True)
                if code != 0 or "active (running)" not in out:
                    ha_running_status = constants.HA_STATUS_FAULT
                    logger.error("vip_host[%s] keepalived not running" % vip_host_ip)
                # 备控节点keepalived未正常运行：视为HA运行状态故障
                # 备控节点ping不通网关（以敏感度为限）：视为备控网络连接状态断开
                else:
                    paths = list()
                    for iso in db_api.get_item_with_all(models.YzyIso, {}):
                        paths.append(iso.path)
                    for bak in db_api.get_item_with_all(models.YzyDatabaseBack, {}):
                        paths.append(bak.path)
                    _data = {
                        "command": "check_backup_ha_status",
                        "handler": "HaHandler",
                        "data": {
                            "quorum_ip": ha_info_obj.quorum_ip,
                            "sensitivity": ha_info_obj.sensitivity,
                            "paths": paths
                        }
                    }
                    rep_json = compute_post(peer_host_ip, _data)
                    ret_code = rep_json.get("code", -1)
                    ret_data = rep_json.get("data", [])
                    if ret_code != 0 or not ret_data or len(ret_data) != 4:
                        ha_running_status = constants.HA_STATUS_FAULT
                        backup_net_status = constants.HA_STATUS_UNKNOWN
                        logger.error("peer_host[%s] check_backup_ha_status rep_json: %s" % (peer_host_ip, rep_json))
                    else:
                        keepalived_status = ret_data[0]
                        quorum_ip_status = ret_data[1]
                        backup_mysql_slave_status = ret_data[2]
                        file_sync_status = ret_data[3]
                        if keepalived_status != constants.HA_STATUS_NORMAL:
                            ha_running_status = constants.HA_STATUS_FAULT
                            logger.error("peer_host[%s] keepalived not running" % peer_host_ip)
                        if quorum_ip_status != constants.HA_STATUS_NORMAL:
                            backup_net_status = constants.HA_STATUS_FAULT
                            logger.error("peer_host[%s] ping quorum_ip[%s] failed" % (peer_host_ip, ha_info_obj.quorum_ip))
                        # 备控节点上mysql slave 线程报错，视为数据同步状态：未同步
                        if backup_mysql_slave_status != constants.HA_STATUS_NORMAL:
                            logger.error("backup node mysql slave status error: %s", backup_mysql_slave_status)
                        # 后台定时任务同步ISO库和数据库备份文件未完成，视为数据同步状态：未同步
                        if file_sync_status != constants.HA_STATUS_NORMAL:
                            logger.error("file sync status error: %s", file_sync_status)

                # isos = db_api.get_item_with_all(models.YzyIso, {})
                # paths = list()
                # for iso in isos:
                #     paths.append(iso.path)
                # _data = {
                #     "command": "data_sync_status",
                #     "handler": "NodeHandler",
                #     "data": {
                #         "paths": paths
                #     }
                # }
                # rep_json = compute_post(peer_host_ip, _data)
                # if rep_json.get('data'):
                #     data_sync_status = constants.HA_STATUS_NORMAL
                # else:
                #     data_sync_status = constants.HA_STATUS_FAULT

            # 3个数据状态都正常，视为HA数据已同步
            if file_sync_status == constants.HA_STATUS_NORMAL and \
                    master_mysql_slave_status == constants.HA_STATUS_NORMAL and\
                    backup_mysql_slave_status == constants.HA_STATUS_NORMAL:
                data_sync_status = constants.HA_STATUS_NORMAL
            else:
                data_sync_status = constants.HA_STATUS_FAULT

            return get_error_result("Success", data={
                "ha_enable_status": ha_enable_status,
                "ha_running_status": ha_running_status,
                "master_net_status": master_net_status,
                "backup_net_status": backup_net_status,
                "data_sync_status": data_sync_status,
                "file_sync_status": file_sync_status,
                "master_mysql_slave_status": master_mysql_slave_status,
                "backup_mysql_slave_status": backup_mysql_slave_status
            })
        except Exception as e:
            logger.exception("ha_status Exception: %s" % str(e), exc_info=True)
            return get_error_result("OtherError", data=str(e))

    def check_ha_done(self):
        for i in range(5):
            try:
                nodes = db_api.get_node_with_all({'deleted': False})
                return build_result("Success", data={"version": "5.0.0.2"})
            except Exception as e:
                time.sleep(1)
                continue
        else:
            return build_result("OtherError")

    def ha_sync_web_post(self, data):
        """
        专门给web层调用的接口，如果启用了HA，把指定文件（例如：ISO库文件，数据库备份文件）同步给备控，未启用则不同步。
        """
        paths = data.get("paths", None)
        if paths:
            ha_sync_file([{"path": p} for p in paths])
        return build_result("Success")

    def _check_ha_running_status(self, peer_host_ip):
        # 本节点ping不通备控：视为HA运行状态故障
        if not icmp_ping(peer_host_ip, count=3):
            return False

        # 本节点keepalived未正常运行：视为HA运行状态故障
        code, out = cmdutils.run_cmd("systemctl status keepalived", ignore_log=True)
        if code != 0 or "active (running)" not in out:
            return False

        # 备控节点keepalived未正常运行：视为HA运行状态故障
        _data = {
            "command": "check_backup_ha_status",
            "handler": "HaHandler",
            "data": {}
        }
        rep_json = compute_post(peer_host_ip, _data)
        ret_code = rep_json.get("code", -1)
        ret_data = rep_json.get("data", [])
        if ret_code != 0 or not ret_data or len(ret_data) != 4:
            return False

        if ret_data[0] != constants.HA_STATUS_NORMAL:
            return False
        return True

    # def change_ha_status(self, data):
    #     node_ip = data.get('node_ip', '')
    #     ha_info_obj = db_api.get_ha_info_by_node_ip(node_ip)
    #     if not ha_info_obj:
    #         return build_result("ParamError")
    #
    #     ha_running_status = data.get('ha_running_status', None)
    #     if ha_running_status:
    #         if ha_running_status not in [constants.HA_STATUS_NORMAL, constants.HA_STATUS_FAULT]:
    #             return build_result("ParamError")
    #         ha_info_obj.ha_running_status = ha_running_status
    #
    #     net_status = data.get('net_status', None)
    #     if net_status:
    #         if net_status not in [constants.HA_STATUS_NORMAL, constants.HA_STATUS_FAULT, constants.HA_STATUS_UNKNOWN]:
    #             return build_result("ParamError")
    #         if ha_info_obj.master_ip == node_ip:
    #             ha_info_obj.master_net_status = net_status
    #         elif ha_info_obj.backup_ip == node_ip:
    #             ha_info_obj.backup_net_status = net_status
    #
    #     ha_info_obj.soft_update()
    #     return build_result("Success")

    def _subprocess_compute_post(self, data):
        bind = SERVER_CONF.addresses.get_by_default('compute_bind', '')
        if bind:
            port = bind.split(':')[-1]
        else:
            port = constants.COMPUTE_DEFAULT_PORT

        exec_str = """curl -i -X POST -H Content-type:application/json -d"""
        exec_cmd = exec_str.split(" ")
        exec_cmd.append(json.dumps(data))
        exec_cmd.append('http://127.0.0.1:%s/api/v1/' % str(port))
        subprocess.Popen(exec_cmd)

    def get_host_and_peer_ip(self, ha_info_obj):
        ips = (ha_info_obj.master_ip, ha_info_obj.backup_ip)

        # 确定peer（无VIP节点）的ip和node_uuid
        # 由于前端调VIP的yzy-web，而yzy-web只会调本地的yzy-server，则本节点一定是vip_host
        code, out = cmdutils.run_cmd("ip addr |grep {ip}".format(ip=ips[0]), ignore_log=True)
        if code == 0 and ips[0] in out:
            vip_host_ip = ips[0]
            peer_host_ip = ips[1]
            peer_uuid = ha_info_obj.backup_uuid
        else:
            vip_host_ip = ips[1]
            peer_host_ip = ips[0]
            peer_uuid = ha_info_obj.master_uuid
        logging.info("vip_host_ip: %s, peer_host_ip: %s" % (vip_host_ip, peer_host_ip))
        return vip_host_ip, peer_host_ip, peer_uuid

    def get_disk_parts(self, data):
        node_uuid = data.get("node_uuid")
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            logger.error("get disk parts error, node[%s] not exist", node_uuid)
            return get_error_result("NodeNotExist")
        cmd = {
                "command": "get_incre_parts",
                "handler": "DiskHandler",
                "data": {
                }
            }
        ret = compute_post(node.ip, cmd)
        return ret

    def extend_vg(self, data):
        node_uuid = data.get("node_uuid")
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            logger.error("node[%s] not exist", node_uuid)
            return get_error_result("NodeNotExist")
        cmd = {
                "command": "extend_vg",
                "handler": "DiskHandler",
                "data": data
            }
        ret = compute_post(node.ip, cmd)
        return ret

    def vg_detail(self, data):
        node_uuid = data.get("node_uuid")
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            logger.error("node[%s] not exist", node_uuid)
            return get_error_result("NodeNotExist")
        cmd = {
                "command": "vg_detail",
                "handler": "DiskHandler",
                "data": {}
            }
        ret = compute_post(node.ip, cmd)
        return ret

    def extend_lv(self, data):
        node_uuid = data.get("node_uuid")
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            logger.error("node[%s] not exist", node_uuid)
            return get_error_result("NodeNotExist")
        cmd = {
                "command": "extend_lv",
                "handler": "DiskHandler",
                "data": data
            }
        ret = compute_post(node.ip, cmd)
        logger.info("extend lv %s:%s", data['mount_point'], ret)
        return ret

    def create_lv(self, data):
        node_uuid = data.get("node_uuid")
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            logger.error("node[%s] not exist", node_uuid)
            return get_error_result("NodeNotExist")
        controller = db_api.get_controller_node()
        if node_uuid != controller.uuid:
            storages = db_api.get_node_storage_all({"node_uuid": controller.uuid})
            mount_point = os.path.join(constants.LV_PATH_PREFIX, data['lv_name'])
            for storage in storages:
                if mount_point == storage.path:
                    break
                else:
                    return get_error_result("NodeStorageException", name=data['lv_name'])
        cmd = {
                "command": "create_lv",
                "handler": "DiskHandler",
                "data": data
            }
        ret = compute_post(node.ip, cmd)
        if ret.get('code') == 0:
            logger.info("add lv %s in %s success", data['lv_name'], data['vg_name'])
            mount_point = ret['data'].get('mount_point')
            parts = self.get_node_storage(node.ip)
            part_list = list()
            for part in parts:
                if part['path'] == mount_point:
                    part_list.append({
                        "uuid": create_uuid(),
                        "node_uuid": node_uuid,
                        "path": mount_point,
                        "role": '',
                        'type': part['type'],
                        'free': part['free'],
                        'total': part['total'],
                        'used': part['used']
                    })
                    break
            else:
                return get_error_result("MountPointNotExist")
            db_api.insert_with_many(models.YzyNodeStorages, part_list)
        return ret

    def get_system_run_time(self, data):
        node_uuid = data.get("node_uuid", "")
        node = db_api.get_node_by_uuid(node_uuid)
        if not node:
            logger.error("node[%s] not exist", node_uuid)
            return get_error_result("NodeNotExist")
        url = "/api/v1/monitor/get_time"
        data = {}
        ret = monitor_post(node.ip, url, data)
        return ret

