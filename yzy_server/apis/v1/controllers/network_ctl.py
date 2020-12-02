# -*- coding:utf-8 -*-
import logging
from common import constants
from yzy_server.database import apis as db_api
from yzy_server.database import models
from common.utils import build_result, is_netmask, is_ip_addr, \
create_uuid, check_vlan_id, compute_post

logger = logging.getLogger(__name__)


class NetworkController(object):

    def _check_params(self, data):
        if not data:
            return False
        name = data.get("network_name", "")
        switch_name = data.get("switch_name", "")
        switch_type = data.get("switch_type", "")
        subnet = data.get("subnet_info", "")
        if not (name and switch_name and switch_type and subnet):
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

    def init_network(self, data):
        """
        :param data:
            {
                "ip": "172.16.1.49",
                "network_name": "default",
                "switch_name": "default",
                "switch_type": "vlan",
                "vlan_id": 10,
                "subnet_info": {
                    "name": "default",
                    "start_ip": "172.16.1.10",
                    "end_ip": "172.16.1.20",
                    "netmask": "255.255.0.0",
                    "gateway": "172.16.1.254",
                    "dns1": "8.8.8.8",
                    "dns2": ""
                }
                "uplink": {
                    "node_uuid": "",
                    "nic_uuid": "",
                    "interface": "ens224"
                }
            }
        :return:
        """
        logger.info("check params")
        if not self._check_params(data):
            return build_result("ParamError")

        vs = db_api.get_virtual_switch_by_name(data['switch_name'])
        if vs:
            return build_result("VSwitchExistError", name=data['switch_name'])
        network = db_api.get_network_by_name(data['network_name'])
        if network:
            return build_result("NetworkNameRepeatError", name=data['network_name'])

        if constants.VLAN_NETWORK_TYPE == data['switch_type']:
            vlan_id = data.get('vlan_id', '')
            if not check_vlan_id(str(vlan_id)):
                return build_result("VlanIDError", vid=vlan_id)
        else:
            vlan_id = None

        subnet = db_api.get_subnet_by_name(data['subnet_info']['name'])
        if subnet:
            return build_result("SubnetNameRepeatError", name=data['subnet_info']['name'])
        try:
            self.check_subnet_params(data['subnet_info'])
        except Exception as e:
            return build_result("SubnetInfoError", e.__str__(), name=data['name'])

        # add default switch
        vs_uuid = create_uuid()
        switch_value = {
            "uuid": vs_uuid,
            "name": data['switch_name'],
            "type": data['switch_type'],
            "default": 1
        }
        uplink_value = {
            "vs_uuid": vs_uuid,
            "node_uuid": data['uplink']['node_uuid'],
            "nic_uuid": data['uplink']['nic_uuid']
        }
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
        _data = {
            "command": "create",
            "handler": "NetworkHandler",
            "data": {
                "network_id": network_uuid,
                "network_type": data['switch_type'],
                "physical_interface": data['uplink']['interface'],
                "vlan_id": vlan_id
            }
        }
        rep_json = compute_post(data['ip'], _data)
        ret_code = rep_json.get("code", -1)
        if ret_code != 0:
            logger.error("create network failed:%s", rep_json['data'])
            return build_result("NetworkCreateFail")
        logger.info("create network success")
        # add subnet
        data['subnet_info']['network_uuid'] = network_uuid
        subnet_value = self._generate_subnet_info(data['subnet_info'])
        try:
            db_api.add_virtual_swtich(switch_value)
            db_api.add_virtual_switch_uplink(uplink_value)
            db_api.add_network(network_value)
            db_api.add_subnet(subnet_value)
            logger.info("init network success")
        except Exception as e:
            logger.error("init network failed:%s", e, exc_info=True)
            return build_result("NetworkInitFail")
        return build_result("Success")

    def _create_network(self, ipaddr, network_uuid, network_type, interface, vlan_id):
        command_data = {
            "command": "create",
            "handler": "NetworkHandler",
            "data": {
                "network_id": network_uuid,
                "network_type": network_type,
                "physical_interface": interface,
                "vlan_id": int(vlan_id) if vlan_id else ''
            }
        }
        logger.info("create network %s in node %s on interface %s", network_uuid, ipaddr, interface)
        rep_json = compute_post(ipaddr, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("create network failed, node:%s, error:%s", ipaddr, rep_json['data'])
            raise Exception("create network failed")

    def _delete_network(self, ipaddr, network_uuid, vlan_id):
        command_data = {
            "command": "delete",
            "handler": "NetworkHandler",
            "data": {
                "network_id": network_uuid,
                "vlan_id": int(vlan_id) if vlan_id else ''
            }
        }
        logger.info("delete network %s in node %s", network_uuid, ipaddr)
        rep_json = compute_post(ipaddr, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("delete network failed, node:%s, error:%s", ipaddr, rep_json['data'])
            raise Exception("delete network failed")

    def create_network(self, data):
        """
        创建数据网络
        :param data:
            {
                "name": "network1",
                "switch_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea",
                "vlan_id": 10,
                "subnet_info": {
                    "subnet_name": "default",
                    "start_ip": "172.16.1.10",
                    "end_ip": "172.16.1.20",
                    "netmask": "255.255.0.0",
                    "gateway": "172.16.1.254",
                    "dns1": "8.8.8.8",
                    "dns2": ""
                }
            }
        :return:
        """
        if not data:
            return build_result("ParamError")

        network_info = db_api.get_network_by_name(data['name'])
        if network_info:
            logger.error("network name : %s repeat", data['name'])
            return build_result("NetworkNameRepeatError", name=data['name'])

        virtual_switch = db_api.get_virtual_switch(data['switch_uuid'])
        if not virtual_switch:
            logger.error("not virtual switch : %s", data['switch_uuid'])
            return build_result("VSwitchNotExist")
        network_type = virtual_switch.type
        if constants.VLAN_NETWORK_TYPE == network_type:
            vlan_id = data.get('vlan_id', 1)
            if not check_vlan_id(str(vlan_id)):
                return build_result("VlanIDError", vid=vlan_id)
        else:
            vlan_id = None
            net = db_api.get_network_all({'switch_uuid': virtual_switch.uuid})
            if net:
                return build_result("VSwitchFlatInUse")

        network_uuid = create_uuid()
        for uplink in virtual_switch.uplinks:
            if not uplink.deleted:
                node = db_api.get_node_by_uuid(uplink.node_uuid)
                nic = db_api.get_nics_first({"uuid": uplink.nic_uuid})
                try:
                    self._create_network(node.ip, network_uuid, virtual_switch.type, nic.nic, vlan_id)
                except Exception as e:
                    logger.error("NetworkCreateFail: %s"%e, exc_info=True)
                    # 虚拟机启动会检测网桥并且进行添加，所以这里创建失败无所谓
                    # return build_result("NetworkCreateFail", name=data['name'])

        network_value = {
            "uuid": network_uuid,
            "name": data['name'],
            "switch_name": virtual_switch.name,
            "switch_uuid": virtual_switch.uuid,
            "switch_type": virtual_switch.type,
            "vlan_id": vlan_id
        }
        logger.info("add network info in db")
        db_api.add_network(network_value)
        if data.get('subnet_info'):
            data['subnet_info']['network_uuid'] = network_uuid
            subnet_info = self._generate_subnet_info(data['subnet_info'])
            db_api.add_subnet(subnet_info)
        return build_result("Success")

    def delete_network(self, network_uuid):
        network = db_api.get_network_by_uuid(network_uuid)
        if not network:
            logger.error("network [%s] info not exist", network_uuid)
            return build_result("NetworkInfoNotExist")

        virtual_switch = network.virtual_switch_of_network
        if not virtual_switch or virtual_switch.deleted:
            logger.error("network [%s] not virtual switch" % network_uuid)
            return build_result("NetworkNotVSError")

        template = db_api.get_template_with_all({'network_uuid': network_uuid})
        if template:
            logger.error("network is in use, can not deleted")
            return build_result("NetworkInUse", name=network.name)

        network_type = virtual_switch.type
        if constants.VLAN_NETWORK_TYPE == network_type:
            vlan_id = network.vlan_id
        else:
            vlan_id = None

        for uplink in virtual_switch.uplinks:
            if not uplink.deleted:
                node = db_api.get_node_by_uuid(uplink.node_uuid)
                try:
                    self._delete_network(node.ip, network_uuid, vlan_id)
                except Exception as e:
                    logger.error("delete network in node %s failed:%s", node.ip, e, exc_info=True)
                    # return build_result("NetworkCreateFail")

        subnets = db_api.get_subnet_by_network(network.uuid)
        for subnet in subnets:
            subnet.soft_delete()
        network.soft_delete()
        return build_result("Success")

    def update_network(self, data):
        """
        修改网络的名称
        :param data:
            {
                "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea",
                "value": {
                    "name": "network1"
                }
            }
        :return:
        """
        network_uuid = data.get('uuid', '')
        network = db_api.get_network_by_uuid(network_uuid)
        if not network:
            logger.error("network: %s not exist" % network_uuid)
            return build_result("NetworkInfoNotExist")
        try:
            network.update(data)
            network.soft_update()
        except Exception as e:
            logger.error("update network:%s failed:%s", network_uuid, e, exc_info=True)
            return build_result("NetworkUpdateError", name=network.name)
        logger.info("update network:%s success", network_uuid)
        return build_result("Success")

    def get_network_list(self):
        """
        获取网络列表信息
        :return:
        """
        network_list = []
        networks = db_api.get_networks()
        for nw in networks:
            _d = nw.to_json()
            subnets = nw.subnet_of_network
            _d.update({"subnet_num": len(subnets)})
            network_list.append(_d)

        ret = {
            "network_list": network_list,
            "total": len(network_list)
        }

        return build_result("Success", ret)

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

    def create_subnet(self, data):
        """
        创建子网
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
        subnet = db_api.get_subnet_by_name(data['name'], data['network_uuid'])
        if subnet:
            return build_result("SubnetNameRepeatError", name=data['name'])
        try:
            self.check_subnet_params(data)
        except Exception as e:
            return build_result("SubnetInfoError", e.__str__(), name=data['name'])
        try:
            subnet_info = self._generate_subnet_info(data)
            db_api.add_subnet(subnet_info)
        except Exception as e:
            logger.info("create subnet failed:%s", e)
            return build_result("SubnetCreateError", name=data['name'])
        return build_result("Success", subnet_info)

    def delete_subnet(self, subnet_uuids):
        """
        删除子网, 批量操作
        :param subnet_uuids:
        :return:
        """
        prompt_info = []
        try:
            for subnet_uuid in subnet_uuids:
                ### 判断子网是否已被占用
                subnet = db_api.get_subnet_by_uuid(subnet_uuid)
                if not subnet:
                    logger.error("subnet: %s not exist", subnet_uuid)
                    return build_result("SubnetNotExist")
                templates = db_api.get_template_with_all({'deleted': False, 'subnet_uuid': subnet_uuid})
                template_names = list(map(lambda template: template.name, templates))
                if len(template_names) > 0:
                    prompt_info.append("子网 %s 被模板 %s 所引用" % (subnet.name, ','.join(template_names)))
                    continue
                groups = db_api.get_group_with_all({'deleted': False, 'subnet_uuid': subnet_uuid})
                groups_names = list(map(lambda group: group.name, groups))
                if len(groups_names) > 0:
                    prompt_info.append("子网 %s 被分组 %s 所引用" % (subnet.name, ','.join(groups_names)))
                    continue
                desktops = db_api.get_desktop_with_all({'deleted': False, 'subnet_uuid': subnet_uuid})
                desktop_names = list(map(lambda desktop: desktop.name, desktops))
                if len(desktop_names) > 0:
                    prompt_info.append("子网 %s 被桌面 %s 所引用" % (subnet.name, ','.join(desktop_names)))
                    continue
                personal_desktops = db_api.get_personal_desktop_with_all({'deleted': False, 'subnet_uuid': subnet_uuid})
                personal_desktops_names = list(map(lambda personal_desktop: personal_desktop.name, personal_desktops))
                if len(personal_desktops_names) > 0:
                    prompt_info.append("子网 %s 被桌面 %s 所引用" % (subnet.name, ','.join(personal_desktops_names)))
                    continue
                # 判断子网是否被VOI使用
                voi_templates = db_api.get_voi_template_with_all({'deleted': False, 'subnet_uuid': subnet_uuid})
                voi_template_names = list(map(lambda template: template.name, voi_templates))
                if len(voi_template_names) > 0:
                    prompt_info.append("子网 %s 被VOI模板 %s 所引用" % (subnet.name, ','.join(voi_template_names)))
                    continue
                subnet.soft_delete()
            if len(prompt_info) > 0:
                return build_result("SubnetDeleteInfo")
        except Exception as e:
            return build_result("SubnetDeleteFail")
        return build_result("Success")

    def update_subnet(self, data):
        subnet_uuid = data.get("uuid", "")
        subnet = db_api.get_subnet_by_uuid(subnet_uuid)
        if not subnet:
            logger.error("subnet: %s not exist", subnet_uuid)
            return build_result("SubnetNotExist")
        subnet.name = data['name']
        subnet.start_ip = data['start_ip']
        subnet.end_ip = data['end_ip']
        subnet.netmask = data['netmask']
        subnet.gateway = data['gateway']
        subnet.dns1 = data['dns1']
        subnet.dns2 = data['dns2']
        subnet.soft_update()
        logger.info("update subnet:%s success", subnet_uuid)
        return build_result("Success", data=subnet)

    def get_subnets_of_network(self, network_uuid):
        """
        查询子网列表
        :param network_uuid:
        :return:
        """
        subnets = db_api.get_subnet_by_network(network_uuid)
        subnet_list = list()
        for subnet in subnets:
            subnet_list.append(subnet.to_json())
        ret = {
            "subnet_list": subnet_list
        }
        return build_result("Success", ret)


class VirtualSwitchController(NetworkController):

    def create_virtual_switch(self, data):
        """
        创建虚拟交换机
        :param data:
            {
                "name": "switch1",
                "type": "vlan",
                "desc": "this is switch1",
                "uplinks": [
                    {
                        "node_uuid": "",
                        "nic_uuid": ""
                    },
                    ...
                ]
            }
        :return:
        """
        if not data:
            return build_result("ParamError")
        vs_uuid = create_uuid()
        switch_value = {
            "uuid": vs_uuid,
            "name": data['name'],
            "type": data['type'],
            "desc": data.get("desc", '')
        }
        uplinks = list()
        for nic in data.get('uplinks', []):
            uplink_value = {
                "uuid": create_uuid(),
                "vs_uuid": vs_uuid,
                "node_uuid": nic['node_uuid'],
                "nic_uuid": nic['nic_uuid']
            }
            uplinks.append(uplink_value)
        try:
            db_api.add_virtual_swtich(switch_value)
            if uplinks:
                db_api.insert_with_many(models.YzyVswitchUplink, uplinks)
            logger.info("add virtual switch:%s success", data['name'])
        except Exception as e:
            logger.error("add virtual switch failed:%s", e, exc_info=True)
            return build_result("VSwitchCreateError", name=data['name'])
        return build_result("Success", switch_value)

    def delete_virtual_switch(self, vswitch_uuid):
        virtual_switch = db_api.get_virtual_switch(vswitch_uuid)
        if not virtual_switch:
            logger.error("virtual switch: %s not exist", vswitch_uuid)
            return build_result("VSwitchNotExist")
        yzy_virtual_switch = db_api.get_network_all({'switch_uuid':vswitch_uuid})
        if yzy_virtual_switch:
            logger.error('distributed virtual switch associated with data network cannot be deleted')
            return build_result('VSwitchDeletedError', name=virtual_switch.name)
        for uplink in virtual_switch.uplinks:
            if not uplink.deleted:
                uplink.soft_delete()
        virtual_switch.soft_delete()
        logger.info("delete virtual switch:%s success", vswitch_uuid)
        return build_result("Success")

    def update_virtual_switchs(self, data):
        """
        更新虚拟交换机信息
        限制条件比较多
        1、有模板或者桌面使用基于该虚拟机交换机的网络时，不能修改节点的接口对应关系
        2、修改节点的接口对应关系时，需要删除原先创建的设备，然后重新创建新的网络设备
        :param data:
            {
                "uuid": "caa5d57e-3731-11ea-801e-000c295dd728",
                "name": "switch1",
                "type": "vlan",
                "desc": "this is switch1",
                "uplinks": [
                    {
                        "node_uuid": "",
                        "nic_uuid": ""
                    },
                    ...
                ]
            }
        :return:
        """
        vswitch_uuid = data.get('uuid', '')
        logger.info("update vswitch %s", vswitch_uuid)
        vswitch = db_api.get_virtual_switch(vswitch_uuid)
        if not vswitch:
            return build_result("VSwitchNotExist")
        # 虚拟交换机有被使用，无法修改
        networks = db_api.get_network_all({"switch_uuid": vswitch.uuid})
        for network in networks:
            templates = db_api.get_template_with_all({"network_uuid": network.uuid})
            if templates:
                return build_result("VSwitchUsedError", name=vswitch.name)
            desktops = db_api.get_desktop_with_all({"network_uuid": network.uuid})
            if desktops:
                return build_result("VSwitchUsedError", name=vswitch.name)

        # 如果没有数据网络使用该虚拟交换机,则只需要修改对应关系
        for item in data['uplinks']:
            for uplink in vswitch.uplinks:
                if not uplink.deleted:
                    if item['node_uuid'] == uplink.node_uuid:
                        if item['nic_uuid'] != uplink.nic_uuid:
                            logger.info("update nic from %s to %s", uplink.nic_uuid, item['nic_uuid'])
                            node = db_api.get_node_by_uuid(item['node_uuid'])
                            nic = db_api.get_nics_first({'uuid': item['nic_uuid']})
                            for network in networks:
                                self._delete_network(node.ip, network.uuid, network.vlan_id)
                                self._create_network(node.ip, network.uuid, network.switch_type, nic.nic, network.vlan_id)
                            uplink.nic_uuid = item['nic_uuid']
                            uplink.soft_update()
                            break
        vswitch.name = data['name']
        vswitch.desc = data['desc']
        vswitch.type = data['type']
        vswitch.soft_update()
        return build_result("Success")

    def update_virtual_switch(self, data):
        """
        更新虚拟交换机信息
        限制条件比较多
        1、有模板或者桌面使用基于该虚拟机交换机的网络时，不能修改节点的接口对应关系
        2、修改节点的接口对应关系时，需要删除原先创建的设备，然后重新创建新的网络设备
        :param data:
            {
                "uuid": "caa5d57e-3731-11ea-801e-000c295dd728",
                "node_uuid": "",
                "nic_uuid": ""
            }
        :return:
        """
        vswitch_uuid = data.get('uuid', '')
        logger.info("update vswitch %s", vswitch_uuid)
        vswitch = db_api.get_virtual_switch(vswitch_uuid)
        if not vswitch:
            return build_result("VSwitchNotExist")
        # 虚拟交换机有被使用，无法修改
        networks = db_api.get_network_all({"switch_uuid": vswitch.uuid})
        for network in networks:
            templates = db_api.get_template_with_all({"network_uuid": network.uuid})
            if templates:
                return build_result("VSwitchUsedError", name=vswitch.name)
            desktops = db_api.get_desktop_with_all({"network_uuid": network.uuid})
            if desktops:
                return build_result("VSwitchUsedError", name=vswitch.name)

        # 如果没有数据网络使用该虚拟交换机,则只需要修改对应关系
        try:
            for uplink in vswitch.uplinks:
                if not uplink.deleted:
                    if data['node_uuid'] == uplink.node_uuid:
                        if data['nic_uuid'] != uplink.nic_uuid:
                            logger.info("update nic from %s to %s", uplink.nic_uuid, data['nic_uuid'])
                            node = db_api.get_node_by_uuid(data['node_uuid'])
                            nic = db_api.get_nics_first({'uuid': data['nic_uuid']})
                            for network in networks:
                                self._delete_network(node.ip, network.uuid, network.vlan_id)
                                self._create_network(node.ip, network.uuid, network.switch_type, nic.nic, network.vlan_id)
                            uplink.nic_uuid = data['nic_uuid']
                            uplink.soft_update()
                            break
        except Exception as e:
            return build_result("OtherError")
        return build_result("Success")

    def virtual_switch_info(self, vswitch_uuid):
        """
        虚拟交换机的信息
        :param vswitch_uuid:
        :return:
        """
        virtual_switch = db_api.get_virtual_switch(vswitch_uuid)
        if not virtual_switch:
            logger.error("virtual switch: %s not exist", vswitch_uuid)
            return build_result("VSwitchNotExist")

        info = {
            "name": virtual_switch.name,
            "type": virtual_switch.type,
            "default": virtual_switch.default,
            "desc": virtual_switch.desc or '',
            "uplinks": list()
        }
        for uplink in virtual_switch.uplinks:
            if not uplink.deleted:
                node = db_api.get_node_by_uuid(uplink.node_uuid)
                if node:
                    uplink_info = {
                        "hostname": node.hostname,
                        "interface": uplink.interface
                    }
                    info['uplinks'].append(uplink_info)
        return build_result("Success", info)

    def get_vswitch_list(self):
        vswitch_list = list()
        vswitchs = db_api.get_virtual_switch_list({})
        for virtual_switch in vswitchs:
            info = {
                "name": virtual_switch.name,
                "type": virtual_switch.type,
                "default": virtual_switch.default,
                "desc": virtual_switch.desc or '',
                "uplinks": list()
            }
            for uplink in virtual_switch.uplinks:
                if not uplink.deleted:
                    node = db_api.get_node_by_uuid(uplink.node_uuid)
                    uplink_info = {
                        "hostname": node.hostname,
                        "interface": uplink.interface
                    }
                    info['uplinks'].append(uplink_info)
            vswitch_list.append(info)
        ret = {
            "vswitch_list": vswitch_list
        }
        return build_result("Success", ret)
