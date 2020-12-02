import logging
import ipaddress
import netaddr
import time
import os
import traceback
from simplepam import authenticate
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db.models import Q
from web_manage.yzy_resource_mgr.models import *
from web_manage.yzy_edu_desktop_mgr.models import *
from web_manage.yzy_user_desktop_mgr.models import *
from web_manage.common.http import server_post, monitor_post, subprocess_server_post
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.utils import get_error_result, JSONResponse, is_ip_addr, is_netmask
from web_manage.common import constants

logger = logging.getLogger(__name__)


class NodeManager(object):

    def get_object_by_uuid(self, model, uuid):
        try:
            obj = model.objects.filter(deleted=False).get(uuid=uuid)
            return obj
        except Exception as e:
            return None

    def get_object_by_ip(self, model, ip):
        try:
            obj = model.objects.filter(deleted=False).get(ip=ip)
            return obj
        except Exception as e:
            return None

    def get_object_by_name(self, model, name):
        try:
            obj = model.objects.filter(deleted=False).get(name=name)
            return obj
        except Exception as e:
            return None

    def get_object_by_name_and_not_uuid(self, model, name, uuid):
        try:
            obj = model.objects.filter(deleted=False).exclude(uuid=uuid).get(name=name)
            return obj
        except Exception as e:
            return None

    def get_objects_by_host_all(self, model, host):
        objs = model.objects.filter(deleted=False, host=host, status=constants.STATUS_ACTIVE).all()
        return objs

    def node_operate(self, request):
        """
        节点服务的相关操作
        :param request:
        :return:
        """
        _data = request.data
        cmd = _data.get("cmd")
        data = _data.get("data")
        try:
            func = getattr(self, cmd + '_node')
        except:
            ret = get_error_result("ParamError")
            return JSONResponse(ret, status=400,
                                json_dumps_params={'ensure_ascii': False})
        return func(data)
        # return ret

    def service_node(self, data):
        pass

    def update_node_instance_status(self, instances, uuid):
        # instances = self.get_objects_by_host_all(YzyInstances, obj)
        # if instances:
        desktop_uuids = list()
        for instance in instances:
            if instance.desktop_uuid not in desktop_uuids:
                desktop_uuids.append(instance.desktop_uuid)
                if instance.classify == 1:
                    ret = server_post("/api/v1/desktop/education/stop_for_node", {"uuid": instance.desktop_uuid, "node_uuid": uuid})
                    logger.info("reboot node update node education instance status: success %s, fail %s"
                                %(ret.get('data').get('success_num'), ret.get('data').get("failed_num")))
                elif instance.classify == 2:
                    ret = server_post("/api/v1/desktop/personal/stop_for_node", {"uuid": instance.desktop_uuid, "node_uuid": uuid})
                    logger.info("reboot node update node personal instance status: success %s, fail %s"
                                % (ret.get('data').get('success_num'), ret.get('data').get("failed_num")))
                else:
                    pass

    def check_node_password(self, data):
        ret = get_error_result("Success")
        ret = server_post("/node/check_password", data)
        return ret

    def check_node(self, data):
        """
        data: {
            "ip": "172.16.1.49",
            "root_pwd" : "xxxxxx"
        }
        :param data:
        :return:
        """
        logger.info("check node KVM: %s"% data)
        ret = get_error_result("Success")
        ip = data.get("ip")
        root_pwd = data.get("root_pwd")
        ret = server_post("/node/check_password", data)
        if ret.get('code') != 0:
            logger.info("check node KVM failed:%s", ret['msg'])
            return ret

        data["is_controller"] = False
        if not ip or not is_ip_addr(ip):
            logging.error("check node parameter ip error: %s" % ip)
            return get_error_result("IPAddrError", ipaddr=ip)
            # ret['msg'] = ret['msg'].format({"ipaddr": ip})
            # return ret
        if not root_pwd:
            logging.error("check node parameter root_pwd not exist!")
            return get_error_result("ParamError")

        result = {}
        node = self.get_object_by_ip(YzyNodes, ip)
        if node and node.type == 3:
            interface_ips = YzyInterfaceIp.objects.filter(Q(deleted=False), Q(is_manage=1) | Q(is_image=1))
            for interface_ip in interface_ips:
                network_info = YzyNodeNetworkInfo.objects.get(uuid=interface_ip.interface.uuid)
                if node.uuid == network_info.node.uuid:
                    if interface_ip.is_manage:
                        result['manage_interface_name'] = network_info.nic
                        result['manage_interface_ip'] = interface_ip.ip
                    if interface_ip.is_image:
                        result['image_interface_name'] = network_info.nic
                        result['image_interface_ip'] = interface_ip.ip
            switch_uplinks = YzyVirtualSwitchUplink.objects.filter(node_uuid = node.uuid)
            result_switch_uplinks = []
            for switch_uplink in switch_uplinks:
                result_switch_uplink = {}
                result_switch_uplink['vs_name'] = switch_uplink.virtual_switch.name
                result_switch_uplink['nic_name'] = switch_uplink.network_interface.nic
                result_switch_uplinks.append(result_switch_uplink)
            result['vswitchs'] = result_switch_uplinks
            result['is_controller'] = True
        else:
            ret = server_post("/node/check", data)
            if ret.get('code') != 0:
                logger.info("check node KVM failed:%s", ret['msg'])
                return ret
            logger.info("check node KVM success, ip: %s", ip)
            ret['is_controller'] = False
            return ret
        return result

    @operation_record("添加计算节点，IP:{data[ip]}")
    def add_node(self, resource_pool_uuid, data):
        """
        data:     {
            "password": "123",
            "ip": "172.16.1.11",
            "network": [
                {
                    "switch_uuid": "ec796fde-4885-11ea-8e15-000c295dd728",
                    "interface": "eth0"
                },
                {
                    "switch_uuid": "ec796fde-4885-11ea-8e15-000c295dd728",
                    "interface": "eth0"
                }
            ],
            "manage_interface": "ens192",
            "image_interface": "ens192"
        }
        :param data:
        :return:
        """
        logger.info("add node KVM: %s" % data)
        resource_pool = self.get_object_by_uuid(YzyResourcePools, resource_pool_uuid)
        if not resource_pool:
            logger.error("add node KVM, pool_name: %s, pool_uuid: %s"% (resource_pool.name, resource_pool_uuid))
            return get_error_result("ResourcePoolNameExistErr", name='')
        data['pool_uuid'] = resource_pool_uuid
        node = YzyNodes.objects.filter(deleted=False, type__in=[1, 3]).first()
        data['m_ip'] = node.ip
        node = self.get_object_by_ip(YzyNodes, data['ip'])
        if node and node.type == 3:
            request_data = {
                'uuid': node.uuid,
                'name': node.name,
                'type': 1,
                'pool_uuid': resource_pool_uuid
            }
            ret = server_post("/node/update", request_data)
        else:
            ret = server_post("/node/add", data, timeout=1800)
            if ret.get('code') != 0:
                logger.info("add node KVM failed:%s", ret['msg'])
                return ret
        logger.info("add node KVM success, data: %s", data)
        return ret

    @operation_record("编辑计算节点 uuid:{uuid}")
    def update_node(self, data, uuid):
        try:
            node = self.get_object_by_uuid(YzyNodes, uuid)
            if not node:
                logger.error("update node info error, node: %s not exist"%(uuid))
                return get_error_result("NodeNotExist")

            name = data.get("name")
            yzy_node = self.get_object_by_name(YzyNodes, name)
            if yzy_node:
                logger.error("update node info error , node : %s exist"%(name))
                return get_error_result("NameAlreadyUseError")
            add_compute_function = data.get('add_compute_function', False)
            request_data = {
                'uuid': node.uuid,
                'name': name
            }
            if add_compute_function:
                request_data['type'] = 1
                resource_pool = None
                try:
                    resource_pool = YzyResourcePools.objects.get(default=1)
                except Exception as e:
                    return JSONResponse(get_error_result("ResourcePoolNotExist"))
                request_data['pool_uuid'] = resource_pool.uuid
            ret = server_post("/node/update", request_data)
            return ret
        except Exception as e:
            return get_error_result("ModifyNodeFail", node=uuid)

    @operation_record("删除计算节点 uuids:{uuids}")
    def delete_node(self, uuids):
        """
        删除节点
        :return:
        """
        # 已做HA的主备控节点，在资源池中，不允许删除
        ha_node_uuids = list()
        ha_info_objs = YzyHaInfo.objects.filter(deleted=False).all()
        if ha_info_objs:
            for ha_info_obj in ha_info_objs:
                ha_node_uuids.append(ha_info_obj.master_uuid)
                ha_node_uuids.append(ha_info_obj.backup_uuid)

        for uuid in uuids:
            if uuid in ha_node_uuids:
                return get_error_result("DeleteHaNodeError")

        all_task = list()
        failed_num = 0
        success_num = 0
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for uuid in uuids:
                url = "/node/delete"
                request_data = {
                    "uuid": uuid
                }
                future = executor.submit(server_post, url, request_data)
                all_task.append(future)
            if len(uuids) > 1:
                for future in as_completed(all_task):
                    result = future.result()
                    if result.get("code") == 0:
                        success_num += 1
                    else:
                        failed_num += 1
            else:
                return future.result()
            return get_error_result("Success", data={"success_num": success_num, "failed_num": failed_num})

    def ping_node(self, ip):
        ret = get_error_result("Success")
        ret = server_post("/node/ping", {'ip': ip})
        return ret

    def check_image_ip(self, ip, speed):
        ret = get_error_result("Success")
        node = YzyNodes.objects.filter(deleted=False, type__in=[1,3]).first()
        node_interfaces = node.yzy_node_interfaces.all()
        master_image_nic = None
        master_image_speed = None
        master_image_ip = None
        for node_interface in node_interfaces:
            interface_ips = node_interface.yzy_interface_ips.all()
            for interface_ip in interface_ips:
                if interface_ip.is_image:
                    master_image_nic = node_interface.nic
                    master_image_speed = node_interface.speed
                    master_image_ip = interface_ip.ip
                    break
            if master_image_nic:
                break
        if str(master_image_speed) != str(speed):
            result = get_error_result("ImageNetworSpeedFail")
            msg = result['msg']
        else:
            msg = None
        ret = server_post("/node/check_image_ip", {'ip': ip, 'master_image_nic': master_image_nic,
                                                   'master_image_ip': master_image_ip})
        ret['data'] = {'msg': msg}
        return ret

    def ping_ip(self, ip):
        if not is_ip_addr(ip):
            return get_error_result("IpAddressGatewayDnsAddressError")
        ret = server_post("/node/ping_ip", {'ip': ip})
        return ret

    @operation_record("重启主控节点 name:{node[name]}")
    def reboot_controller_node(self, node):
        uuid = node.get("uuid")
        obj = self.get_object_by_uuid(YzyNodes, uuid)
        if not obj:
            logger.error("controller node reboot fail node not exist:%s", uuid)
            return get_error_result("NodeNotExist")
        request_data = {
            'uuid': obj.uuid,
            'status': constants.STATUS_RESTARTING
        }
        ret = server_post("/node/update", request_data)
        instances = self.get_objects_by_host_all(YzyInstances, uuid)
        self.update_node_instance_status(instances, uuid)
        ret = server_post("/node/reboot", {"uuid": uuid})
        return ret

    def shutdown_controller_node(self, node, compute_node=False):
        uuid = node.get("uuid")
        obj = self.get_object_by_uuid(YzyNodes, uuid)
        if not obj:
            logger.error("controller node shutdown fail node not exist:%s", uuid)
            return get_error_result("NodeNotExist")
        request_data = {
            'timeout': constants.SHUTDOWN_TIMEOUT
        }
        if obj.type in [1, 3] and compute_node:
            nodes = YzyNodes.objects.filter(deleted=False).exclude(status=constants.STATUS_SHUTDOWN).\
                exclude(status=constants.STATUS_SHUTDOWNING).exclude(type__in=[1, 3])
            all_task = dict()
            with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
                for node in nodes:
                    request_data['uuid'] = node.uuid
                    logger.info("shutdown node %s thread", node.uuid)
                    url = "/node/shutdown"
                    future = executor.submit(server_post, url, request_data)
                    all_task[node.name] = future.result()

            names = list()
            for k, v in all_task.items():
                if v['code'] != 0:
                    names.append(k)
            if len(names) > 0:
                name_str = '、'.join(names)
                return get_error_result("ComputeNodeShutdownError", data={"names": name_str})
        request_data['uuid'] = obj.uuid
        ret = server_post("/node/shutdown", request_data)
        if ret.get("code") != 0:
            return get_error_result("ComputeNodeShutdownError", node.name)
        msg = "关闭主控节点 %s" % obj.name
        insert_operation_log(msg, ret['msg'])
        return get_error_result("Success")

    def reboot_node(self, nodes):
        ret = get_error_result("Success")
        node_success_num = 0
        node_failed_num = 0
        names = list()
        for node in nodes:
            uuid = node.get("uuid")
            names.append(node.get('name', ''))
            obj = self.get_object_by_uuid(YzyNodes, uuid)
            if obj:
                if obj.status == constants.STATUS_SHUTDOWN:
                    continue
                request_data = {
                    'uuid': obj.uuid,
                    'status': constants.STATUS_RESTARTING
                }
                ret = server_post("/node/update", request_data)
                if ret.get('code') == 0:
                    node_success_num = node_success_num + 1
                else:
                    node_failed_num = node_failed_num + 1
                    logger.error("reboot node update node status fail")
                instances = self.get_objects_by_host_all(YzyInstances, uuid)
                self.update_node_instance_status(instances, uuid)
                ret = server_post("/node/reboot", {"uuid": uuid})
                if ret.get('code') == 0:
                    # req_data = {
                    #     'uuid': obj.uuid,
                    #     'status': constants.STATUS_ACTIVE
                    # }
                    # server_post("/node/update", req_data)
                    node_success_num += 1
                else:
                    node_failed_num += 1
            else:
                node_failed_num = node_failed_num + 1
        msg = "重启计算节点 %s" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'])
        return ret

    @operation_record("启用HA")
    def enable_ha(self, master_uuid, backup_uuid, new_master_ip, sensitivity, quorum_ip, backup_pwd):
        """
        data: {
            "new_master_ip": "172.16.1.199",
            "sensitivity": 60,
            "quorum_ip": "172.16.1.254",
            "master_ip": "172.16.1.66",
            "backup_ip": "172.16.1.88",
            "master_nic": "eth0",
            "backup_nic": "eth0",
            "master_uuid": "194279f3-31db-4ce0-9e46-39ffbf257f64",
            "backup_uuid": "5507fd59-8d3a-4ea0-b8fe-85cd52c173e9",
            "backup_pwd": "123qwe,."
        }
        """
        master_node_obj = self.get_object_by_uuid(YzyNodes, master_uuid)
        if not master_node_obj:
            logger.error("enable_ha fail node not exist:%s", master_uuid)
            return get_error_result("NodeNotExist")

        backup_node_obj = self.get_object_by_uuid(YzyNodes, backup_uuid)
        if not backup_node_obj:
            logger.error("enable_ha fail node not exist:%s", backup_uuid)
            return get_error_result("NodeNotExist")

        # 主控和备控必须都在线，才能启用HA
        if master_node_obj.status != 'active' or backup_node_obj.status != 'active':
            return get_error_result("NodesNotAllActiveError")

        # 查询master_ip/backup_ip, master_nic/backup_nic, netmask
        # 默认使用管理网络
        vip = master_node_obj.ip
        backup_ip = backup_node_obj.ip
        master_ip_obj = self.get_object_by_ip(YzyInterfaceIp, vip)
        # master_ip_obj = YzyInterfaceIp.objects.filter(master_ip, deleted=False).first()
        if not master_ip_obj:
            return get_error_result("IPNotExist", ip=vip)
        backup_ip_obj = self.get_object_by_ip(YzyInterfaceIp, backup_ip)
        # backup_ip_obj = YzyInterfaceIp.objects.filter(backup_ip, deleted=False).first()
        if not backup_ip_obj:
            return get_error_result("IPNotExist", ip=backup_ip)
        netmask = master_ip_obj.netmask
        master_nic = master_ip_obj.name
        backup_nic = backup_ip_obj.name
        master_nic_uuid = master_ip_obj.interface.uuid
        backup_nic_uuid = backup_ip_obj.interface.uuid

        # 校验网卡上是否有FLAT交换机
        master_nic_uplinks = master_ip_obj.interface.yzy_network_interface_uplinks.all()
        if master_nic_uplinks:
            for uplink in master_nic_uplinks:
                if uplink.virtual_switch.type == 'Flat':
                    return get_error_result("HaNicFlatVSUplinkError")
        backup_nic_uplinks = backup_ip_obj.interface.yzy_network_interface_uplinks.all()
        if backup_nic_uplinks:
            for uplink in backup_nic_uplinks:
                if uplink.virtual_switch.type == 'Flat':
                    return get_error_result("HaNicFlatVSUplinkError")

        # 校验vip格式，与master_ip同网段
        new_master_ip_ret = self._verify_new_master_ip(new_master_ip, vip, netmask)
        if new_master_ip_ret:
            return new_master_ip_ret

        # 校验仲裁IP格式，能否ping通
        # 在server层不进行校验
        # if not is_ip_addr(quorum_ip):
        #     return get_error_result("IpAddressGatewayDnsAddressError")
        ping_ret = self.ping_ip(quorum_ip)
        if ping_ret.get("code", -1) != 0:
            return ping_ret

        if sensitivity < 60:
            return get_error_result("SensitivityLessThan60Error")

        # 校验backup_pwd
        _data = {
            "ip": backup_ip,
            "root_pwd": backup_pwd
        }
        ret = server_post("/node/check_password", _data)
        if ret.get('code') != 0:
            logger.info("check backup_pwd in compute node %s failed: %s", (backup_ip, ret['msg']))
            return get_error_result("HaNodePasswordError")

        # 请求server服务变更主控IP所需信息
        update_ip_data = {
            "uuid": master_ip_obj.uuid,
            "nic_uuid": master_nic_uuid,
            "nic_name": master_nic,
            "node_ip": "127.0.0.1",
            "ip": new_master_ip,
            "netmask": master_ip_obj.netmask,
            "ha_flag": True
        }
        # ret = server_post('/node/update_ip', data)
        # logger.info("ret：%s", ret)

        # 当配置HA失败回滚时，变更主控IP所需信息
        post_data = {
            "uuid": master_ip_obj.uuid,
            "nic_uuid": master_nic_uuid,
            "nic_name": master_nic,
            "node_ip": "127.0.0.1",
            "ip": vip,
            "netmask": master_ip_obj.netmask,
            "ha_flag": True
        }

        # 请求sever服务启用HA所需信息
        enable_ha_data = {
            "vip": vip,
            "netmask": netmask,
            "sensitivity": sensitivity,
            "quorum_ip": quorum_ip,
            "master_ip": new_master_ip,
            "backup_ip": backup_ip,
            "master_nic": master_nic,
            "backup_nic": backup_nic,
            "master_nic_uuid": master_nic_uuid,
            "backup_nic_uuid": backup_nic_uuid,
            "master_uuid": master_uuid,
            "backup_uuid": backup_uuid,
            "post_data": post_data
        }
        # ret = server_post("/controller/enable_ha", request_data)

        url = "/controller/enable_ha"
        request_data = {
            "update_ip_data": update_ip_data,
            "enable_ha_data": enable_ha_data
        }
        logger.info("url: %s, request_data: %s" % (url, request_data))
        # 异步调用server层接口，不等结果，直接返回
        subprocess_server_post(url, request_data)
        return ret

    @operation_record("禁用HA")
    def disable_ha(self, ha_info_uuid):
        """
        {
            "ha_info_uuid": "82d56980-7b6d-4086-a9b9-814a2c045f62"
        }
        """
        ha_info_obj = self.get_object_by_uuid(YzyHaInfo, ha_info_uuid)
        if not ha_info_obj:
            logger.error("disable_ha fail ha_info not exist:%s", ha_info_obj)
            return get_error_result("HAInfoNotExist")

        # 必须两节点都在线，且运行状态正常（server层有校验），才允许禁用HA
        master_node = self.get_object_by_uuid(YzyNodes, ha_info_obj.master_uuid)
        backup_node = self.get_object_by_uuid(YzyNodes, ha_info_obj.backup_uuid)
        if not master_node or not backup_node or master_node.status != 'active' or backup_node.status != 'active':
            return get_error_result("NodesNotReadyError")

        request_data = {
            "ha_info_uuid": ha_info_uuid
        }
        ret = server_post("/controller/disable_ha", request_data)
        return ret

    @operation_record("HA主备控切换 新主控IP：{new_vip_host_ip}")
    def switch_ha_master(self, ha_info_uuid, new_vip_host_ip):
        """
        {
            "ha_info_uuid": "82d56980-7b6d-4086-a9b9-814a2c045f62",
            "new_vip_host_ip": "172.16.1.88",
        }
        """
        ha_info_obj = self.get_object_by_uuid(YzyHaInfo, ha_info_uuid)
        if not ha_info_obj:
            logger.error("switch_ha_master fail ha_info not exist:%s", ha_info_obj)
            return get_error_result("HAInfoNotExist")

        if new_vip_host_ip not in [ha_info_obj.master_ip, ha_info_obj.backup_ip]:
            return get_error_result("NotHAInfoIPError")

        # 必须两节点都在线，且运行状态正常（server层有校验），才允许切换主备
        master_node = self.get_object_by_uuid(YzyNodes, ha_info_obj.master_uuid)
        backup_node = self.get_object_by_uuid(YzyNodes, ha_info_obj.backup_uuid)
        if not master_node or not backup_node or master_node.status != 'active' or backup_node.status != 'active':
            return get_error_result("NodesNotReadyError")

        request_data = {
            "new_vip_host_ip": new_vip_host_ip,
            "vip": ha_info_obj.vip
        }
        ret = server_post("/controller/switch_ha_master", request_data)
        return ret

    def ha_status(self, ha_info_uuid):
        """
        {
            "ha_info_uuid": "82d56980-7b6d-4086-a9b9-814a2c045f62"
        }
        """
        ha_info_obj = self.get_object_by_uuid(YzyHaInfo, ha_info_uuid)
        if not ha_info_obj:
            logger.error("ha_status failed ha_info not exist:%s", ha_info_obj)
            # return get_error_result("HAInfoNotExist")
            return get_error_result()

        request_data = {
            "ha_info_uuid": ha_info_uuid
        }
        ret = server_post("/controller/ha_status", request_data)
        return ret

    def shutdown_node(self, nodes):
        """
        nodes [
            {"uuid": "xxxxx", "name": "xxxxxxx"},
            {"uuid": "xxxxx", "name": "xxxxxxx"},
            {"uuid": "xxxxx", "name": "xxxxxxx"}
        ]
        :param nodes:
        :return:
        """
        ret = get_error_result("Success")
        node_success_num = 0
        node_failed_num = 0
        names = list()
        for node in nodes:
            uuid = node.get("uuid")
            names.append(node.get("name",""))
            obj = self.get_object_by_uuid(YzyNodes, uuid)
            if obj:
                request_data = {
                    'uuid': obj.uuid,
                    'timeout': constants.SHUTDOWN_TIMEOUT
                }
                ret = server_post("/node/shutdown", request_data)
                if ret.get('code') == 0:
                    node_success_num = node_success_num + 1
                else:
                    node_failed_num = node_failed_num + 1
                # else:
                #     node_failed_num = node_failed_num + 1
            else:
                node_failed_num = node_failed_num + 1
        msg = "关闭计算节点 %s" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'])
        return get_error_result("Success")
        # return ret

    def restart_service(self, node_uuid, service_uuid):
        if not (service_uuid and node_uuid):
            return JSONResponse(get_error_result("OtherError"))
        service_obj = self.get_object_by_uuid(YzyNodeServices, uuid=service_uuid)
        # if service_obj:
        #     data = {
        #         "service_uuid": service_uuid,
        #         "node_uuid": node_uuid,
        #         "service_name": service_obj.name
        #     }
        #     ret = server_post("/node/restart_service", data)
        # else:
        #     logger.error("restart service[%s] info not exist!" % service_uuid)
        #     ret = get_error_result("NodeServiceNotExist")
        # return ret

        if not service_obj:
            logger.error("restart service[%s] info not exist!" % service_uuid)
            return get_error_result("NodeServiceNotExist")

        node = self.get_object_by_uuid(YzyNodes, uuid=node_uuid)
        if not node:
            logger.error("node [%s] not exist!" % node_uuid)
            return get_error_result("NodeNotExist")

        url = "/api/v1/monitor/task"
        data = {
            "handler": "ServiceHandler",
            "command": "restart",
            "data": {
                "service": service_obj.name
            }
        }

        # monitor只负责发出重启命令
        monitor_ret = monitor_post(node.ip, url, data)
        if monitor_ret['code'] != 0:
            return monitor_ret

        # web负责轮询服务状态
        # TODO yzy-server服务重启时间较长，暂不知原因
        if service_obj.name == 'yzy-server':
            timeout = 90
        else:
            timeout = 5
        try:
            ret = get_error_result("RebootServiceTimeout", name=service_obj.name)
            start_time = time.time()
            while True:
                time.sleep(1)
                now = time.time()
                if now - start_time > timeout:
                    break
                with os.popen("systemctl status {}".format(service_obj.name)) as f:
                    service_status = f.read()
                    if "active (running)" in service_status:
                        logger.info("service %s is active now, cost time: %s" % (service_obj.name, now - start_time))
                        ret = get_error_result()
                        break
        except Exception as e:
            logger.error("service %s reboot faild, exception: %s" % (service_obj.name, str(e)))
            traceback.print_exc()
            ret = get_error_result("OtherError", data=str(e))

        return ret

    def operate_node(self):
        pass

    @operation_record("添加节点{node_uuid}的网卡{nic_uuid}IP信息{data[ip]}")
    def add_ip_node(self, data, node_uuid, nic_uuid):
        """ 添加ip信息
        {
            "node_uuid": "xxxxxxxxxxx",
            "node_name": "name",
            "nic_uuid": "xxxxxx",
            "nic_name": "eth name1",
            "ip": "xxxx",
            "netmask": "xxxxxx",
            "gateway": "xxxxxx",
            "dns1": "xxxx",
            "dns2": "xxxx"
        }
        """
        try:
            node_obj = self.get_object_by_uuid(YzyNodes, uuid=node_uuid)
            nic_obj = self.get_object_by_uuid(YzyNodeNetworkInfo, uuid=nic_uuid)
        except Exception as e:
            logger.exception(e)
            return get_error_result("OtherError")
        ip = data.get('ip', '')
        netmask = data.get('netmask', '')

        # 已启用HA的网卡不能添加附属IP
        ha_nic_uuids = list()
        ha_info_objs = YzyHaInfo.objects.filter(deleted=False).all()
        if ha_info_objs:
            for ha_info_obj in ha_info_objs:
                ha_nic_uuids.append(ha_info_obj.master_nic_uuid)
                ha_nic_uuids.append(ha_info_obj.backup_nic_uuid)
        if nic_obj.uuid in ha_nic_uuids:
            return get_error_result("HaNicAddIPError")

        # 查看该IP是否已被使用
        yzy_interfaces = YzyInterfaceIp.objects.filter(deleted=False, ip=ip).all()
        if len(yzy_interfaces) >= 1:
            logger.error("add ip node fail: ipaddress exists")
            return get_error_result("IPInUse")
        # 不同网卡上不能存在相同网段的IP
        bits = netaddr.IPAddress(netmask).netmask_bits()
        net = ipaddress.ip_interface(ip + '/' + str(bits)).network
        nics = YzyNodeNetworkInfo.objects.filter(node=node_uuid, deleted=False).all()
        for nic in nics:
            if nic.uuid != nic_uuid:
                ips = YzyInterfaceIp.objects.filter(interface=nic.uuid, deleted=False).all()
                for ipinfo in ips:
                    if ipinfo.ip:
                        if ipaddress.ip_address(ipinfo.ip) in net:
                            logger.error("exist another nic has the ip in same segement")
                            return get_error_result("LocalNetworkIpAddressError")

        data['node_name'] = node_obj.name
        data['node_uuid'] = node_uuid
        data['nic_name'] = nic_obj.nic
        data['nic_uuid'] = nic_uuid
        if not nic_obj or nic_obj.node.uuid != node_uuid:
            logger.error("the network interface info: uuid[%s], node[%s] not exist"%(nic_uuid, node_uuid))
            return get_error_result("NetworkInterfaceNotExist", node=data.get("node_name",""), interface=data.get("nic_name", ""))
        # 超过两条不许添加了
        ip_infos = nic_obj.yzy_interface_ips.all()
        count = 0
        for info in ip_infos:
            if not info.deleted:
                count += 1
            if count >= 2:
                logger.error("add the network interface ip error, more than 2")
                return get_error_result("NetworkIpMuchError")

        # 判断IP地址
        ip = data.get("ip")
        netmask = data.get("netmask")
        gateway = data.get("gateway")
        dns1 = data.get("dns1")
        dns2 = data.get("dns2")
        if not (ip and netmask):
            logger.error("add network interface ip need params error: %s"% data)
            return get_error_result("ParamError")
        if not (is_ip_addr(ip) and is_netmask(netmask)[0]):
            logger.error("add network interface ip error: %s", data)
            return get_error_result("IpAddressGatewayDnsAddressError")
        if gateway and not is_ip_addr(gateway):
            return get_error_result("IpAddressGatewayDnsAddressError")
        if dns1 and dns1 != '' and not is_ip_addr(dns1):
            logger.error("add network interface dns2 error: %s", dns1)
            return get_error_result("DnsAddressError")
        if dns2 and dns2 != '' and not is_ip_addr(dns2):
            logger.error("add network interface dns2 error: %s", dns2)
            return get_error_result("DnsAddressError")
        # 判断IP和网关是否属于同一个网络(网络由IP和子网掩码确定)
        if gateway:
            netmask_bits = netaddr.IPAddress(netmask).netmask_bits()
            network_num = ipaddress.ip_interface(ip + "/" + str(netmask_bits)).network
            if ipaddress.IPv4Address(gateway) not in network_num:
                return get_error_result("GatewayAndIpError")

        # 请求server端,进行IP添加
        ret = server_post('/node/add_ip', data)
        return ret

    @operation_record("删除节点{node_uuid}的网卡{nic_uuid}IP信息{ip_info_uuid}")
    def delete_ip_node(self, node_uuid, nic_uuid, ip_info_uuid):
        # 请求server端,进行IP删除
        data = {}
        ip_info = self.get_object_by_uuid(YzyInterfaceIp, uuid=ip_info_uuid)
        node = self.get_object_by_uuid(YzyNodes, uuid=node_uuid)

        # 已启用HA的网卡不能添加删除IP
        ha_nic_uuids = list()
        ha_info_objs = YzyHaInfo.objects.filter(deleted=False).all()
        if ha_info_objs:
            for ha_info_obj in ha_info_objs:
                ha_nic_uuids.append(ha_info_obj.master_nic_uuid)
                ha_nic_uuids.append(ha_info_obj.backup_nic_uuid)
        if nic_uuid in ha_nic_uuids:
            return get_error_result("HaNicDeleteIPError")

        data["nic_name"] = ip_info.name
        data["uuid"] = ip_info_uuid
        data['nic_uuid'] = nic_uuid
        data["node_ip"] = node.ip
        ret = server_post('/node/delete_ip', data)
        return ret

    @operation_record("更新节点{node_uuid}的网卡{nic_uuid}IP信息{ip_info_uuid}")
    def update_ip_node(self, data, node_uuid, nic_uuid, ip_info_uuid):
        # 请求server端,进行IP更新
        ip_info = self.get_object_by_uuid(YzyInterfaceIp, uuid=ip_info_uuid)
        node = self.get_object_by_uuid(YzyNodes, uuid=node_uuid)

        # 已启用HA的网卡不能编辑IP
        ha_nic_uuids = list()
        ha_info_objs = YzyHaInfo.objects.filter(deleted=False).all()
        if ha_info_objs:
            for ha_info_obj in ha_info_objs:
                ha_nic_uuids.append(ha_info_obj.master_nic_uuid)
                ha_nic_uuids.append(ha_info_obj.backup_nic_uuid)
        if nic_uuid in ha_nic_uuids:
            return get_error_result("HaNicEditIPError")

        data["nic_name"] = ip_info.name
        data["uuid"] = ip_info_uuid
        data['nic_uuid'] = nic_uuid
        data["node_ip"] = node.ip
        ret = server_post('/node/update_ip', data)
        return ret

    @operation_record("更新节点{data[node_ip]}的网卡{data[nic_name]}网关信息")
    def update_gate_info(self, data):
        ret = server_post('/node/update_gate_info', data)
        return ret

    @operation_record("更新管理网络")
    def mn_node_map_update(self, uplinks):
        ret = server_post('/node/mn_map_update', uplinks)
        return ret

    @operation_record("更新镜像网络")
    def in_node_map_update(self, uplinks):
        ret = server_post('/node/in_map_update', uplinks)
        return ret

    @operation_record("添加节点{node_uuid}的网卡bond：{bond_name}")
    def add_bond(self, data, node_uuid, bond_name, mode):
        # 校验节点是否存在
        node = self.get_object_by_uuid(YzyNodes, node_uuid)
        if not node:
            logger.error("node[%s] not exist!" % node_uuid)
            return get_error_result("NodeNotExistMsg", hostname=node_uuid)
        else:
            ipaddr = node.ip
            _data = dict()
            _data["ipaddr"] = ipaddr
            _data["node_uuid"] = node_uuid
            _data["slaves"] = list()
            _data["ip_list"] = list()
            _data["gate_info"] = dict()
            manage_gate_info = None
            image_gate_info = None

            # 校验bond名称是否在该节点上重复
            name_exist = node.yzy_node_interfaces.filter(nic=bond_name, node=node_uuid).first()
            if name_exist:
                logger.error("bond name [%s] exist at Node [%s]!" % (bond_name, node_uuid))
                return get_error_result("BondNameRepeatError")

            # vs_uplinks_count = 0
            # 校验slave网卡数量，至少两张才能做bond
            slaves = data.get("slaves", [])
            if len(slaves) < 2:
                return get_error_result("SlaveLessThanTwoError")

            # HA心跳网卡
            ha_nic_uuids = list()
            ha_info_objs = YzyHaInfo.objects.filter(deleted=False).all()
            if ha_info_objs:
                for ha_info_obj in ha_info_objs:
                    ha_nic_uuids.append(ha_info_obj.master_nic_uuid)
                    ha_nic_uuids.append(ha_info_obj.backup_nic_uuid)

            for slave_nic_uuid in slaves:
                # 校验slave网卡是否存在
                slave = node.yzy_node_interfaces.filter(uuid=slave_nic_uuid).first()
                if not slave:
                    logger.error("slave nic[%s] not exist!" % slave_nic_uuid)
                    return get_error_result("SlaveNICNotExist")

                # 已启用HA的网卡不能作为bond的slave
                if slave_nic_uuid in ha_nic_uuids:
                    return get_error_result("HaNicBondError")

                # 校验slave网卡是否已经做过bond了
                already_slave = YzyBondNics.objects.filter(deleted=False, slave_uuid=slave_nic_uuid).first()
                if already_slave:
                    logger.error("slave nic[%s] already bond to [%s(%s)]!"
                                 % (slave_nic_uuid, already_slave.master_name, already_slave.master_uuid))
                    return get_error_result("AlreadySlaveError")

                info = {
                    "nic_uuid": slave_nic_uuid,
                    "nic_name": slave.nic,
                    # "vs_uplink_uuid": None,
                    }

                # 校验slave网卡上是否有交换机，如果有则不能做bond
                vs_uplink_count = slave.yzy_network_interface_uplinks.count()
                if vs_uplink_count:
                    logger.error("slaves virtual_switch count not 0")
                    return get_error_result("SlaveVSUplinksError", nic=slave.nic)

                # # 所有slave网卡上的交换机数量之和不能超过1个
                # # 前提：每个网卡只能绑1个交换机
                # uplink = slave.yzy_network_interface_uplinks.first()
                # if uplink:
                #     # 记录哪个slave网卡上绑定了交换机，提供给server层，方便解绑时还原回去
                #     info["vs_uplink_uuid"] = uplink.uuid
                #     vs_uplinks_count += 1
                #
                # if vs_uplinks_count > 1:
                #     logger.error("slaves virtual_switch count more than 1")
                #     return get_error_result("VSUplinksLimitError")

                # bond网卡自动继承slave的管理网络ip和镜像网络ip
                queryset = slave.yzy_interface_ips.filter(Q(deleted=False), Q(is_manage=1) | Q(is_image=1))
                for ip_obj in queryset:
                    _data["ip_list"].append(
                        {
                            "ip": ip_obj.ip,
                            "netmask": ip_obj.netmask,
                            "is_manage": ip_obj.is_manage,
                            "is_image": ip_obj.is_image
                        }
                    )
                    if ip_obj.is_manage:
                        manage_gate_info = {
                            "gateway": ip_obj.gateway,
                            "dns1": ip_obj.dns1,
                            "dns2": ip_obj.dns2,
                        }
                    if ip_obj.is_image:
                        image_gate_info = {
                            "gateway": ip_obj.gateway,
                            "dns1": ip_obj.dns1,
                            "dns2": ip_obj.dns2,
                        }

                _data["slaves"].append(info)

            # 网关：管理IP > 镜像IP > 传参
            if manage_gate_info:
                _data["gate_info"] = manage_gate_info
            elif image_gate_info:
                _data["gate_info"] = image_gate_info
            else:
                # 允许网关为空
                gate_info = data.get("gate_info", dict())
                # if not gate_info:
                #     return get_error_result("NoGatewayInfoError")
                # 校验传参的网关、DNS格式是否合法
                if gate_info.get("gateway", ""):
                    verify_ret = self._verify_gate_info(gate_info["gateway"], gate_info.get("dns1", ""),
                                                        gate_info.get("dns2", ""))
                    if verify_ret:
                        return verify_ret
                _data["gate_info"] = gate_info

            # bond网卡上至少要有1个IP
            if len(_data["ip_list"]) + len(data.get("ip_list", [])) < 1:
                return get_error_result("BondIpLessThanOne")

            # bond网卡上所有IP数量不能超过4个
            if len(_data["ip_list"]) + len(data.get("ip_list", [])) > 4:
                return get_error_result("NodeNICIpTooManyError")

            # bond网卡的无角色IP
            for ip_info in data.get("ip_list", []):
                # 校验传参的无角色IP格式是否合法，是否与数据库中已有IP冲突
                verify_ret = self._verify_ip_info(ip_info.get("ip", ""), ip_info.get("netmask", ""),
                                                  data["slaves"], node_uuid,)
                if verify_ret:
                    return verify_ret
                ip_info["is_manage"] = 0
                ip_info["is_image"] = 0
                _data["ip_list"].append(ip_info)

            # 网关必须和其中一个IP在同一个网络
            if _data["gate_info"].get("gateway", ""):
                verify_ret = self._verify_gate_ip_match(_data["ip_list"], _data["gate_info"]["gateway"])
                if verify_ret:
                    return verify_ret

            # 请求server服务变更网卡配置文件，并更新数据库记录
            _data["bond_info"] = {
                    "dev": bond_name,
                    "mode": mode,
                }
            _data["bond_info"]["slaves"] = [slave["nic_name"] for slave in _data["slaves"]]
            ret = server_post("/node/add_bond", _data)
            if ret.get("code", -1) != 0:
                logger.error("add_bond in node[%s], ip[%s] error: %s" % (node_uuid, ipaddr, ret))
                return ret

        return get_error_result()

    @operation_record("编辑节点{node_uuid}的网卡bond：{bond_uuid}")
    def edit_bond(self, data, node_uuid, bond_uuid, mode):
        # 校验节点是否存在
        node = self.get_object_by_uuid(YzyNodes, node_uuid)
        if not node:
            logger.error("node[%s] not exist!" % node_uuid)
            return get_error_result("NodeNotExistMsg", hostname=node_uuid)
        else:
            ipaddr = node.ip
            _data = dict()
            _data["ipaddr"] = ipaddr
            _data["slaves"] = list()
            _data["ip_list"] = list()
            _data["gate_info"] = dict()
            manage_gate_info = None
            image_gate_info = None

            # 校验bond网卡是否存在
            bond_nic = node.yzy_node_interfaces.filter(uuid=bond_uuid).first()
            if not bond_nic:
                logger.error("bond nic[%s] not exist!" % bond_nic)
                return get_error_result("BondNICNotExist")

            # HA心跳网卡
            ha_nic_uuids = list()
            ha_info_objs = YzyHaInfo.objects.filter(deleted=False).all()
            if ha_info_objs:
                for ha_info_obj in ha_info_objs:
                    ha_nic_uuids.append(ha_info_obj.master_nic_uuid)
                    ha_nic_uuids.append(ha_info_obj.backup_nic_uuid)
            # 已作为HA心跳网卡的Bond不能编辑或删除
            if bond_uuid in ha_nic_uuids:
                return get_error_result("HaBondEditDeleteError")

            _data["bond_uuid"] = bond_uuid

            # 校验slave网卡数量，至少两张才能做bond
            slaves = data.get("slaves", [])
            if len(slaves) < 2:
                return get_error_result("SlaveLessThanTwoError")
            inactive_count = 0
            for slave_nic_uuid in slaves:
                # 校验slave网卡是否存在
                slave = node.yzy_node_interfaces.filter(uuid=slave_nic_uuid).first()
                if not slave:
                    logger.error("slave nic[%s] not exist!" % slave_nic_uuid)
                    return get_error_result("SlaveNICNotExist")

                # 已启用HA的网卡不能作为bond的slave
                if slave_nic_uuid in ha_nic_uuids:
                    return get_error_result("HaNicBondError")

                if slave.status != 2:
                    inactive_count += 1

                info = {
                    "nic_uuid": slave_nic_uuid,
                    "nic_name": slave.nic,
                    }

                # 校验slave网卡上是否有交换机，如果有则不能做bond
                vs_uplink_count = slave.yzy_network_interface_uplinks.count()
                if vs_uplink_count:
                    logger.error("slaves virtual_switch count not 0")
                    return get_error_result("SlaveVSUplinksError", nic=slave.nic)

                # bond网卡自动继承新slave的管理网络ip和镜像网络ip
                # 旧slave的管理、镜像IP都已经移动到bond网卡上了，这里只会查到新slave的管理、镜像IP
                queryset = slave.yzy_interface_ips.filter(Q(deleted=False), Q(is_manage=1) | Q(is_image=1))
                for ip_obj in queryset:
                    _data["ip_list"].append(
                        {
                            "ip": ip_obj.ip,
                            "netmask": ip_obj.netmask,
                            "is_manage": ip_obj.is_manage,
                            "is_image": ip_obj.is_image
                        }
                    )
                    if ip_obj.is_manage:
                        manage_gate_info = {
                            "gateway": ip_obj.gateway,
                            "dns1": ip_obj.dns1,
                            "dns2": ip_obj.dns2,
                        }
                    if ip_obj.is_image:
                        image_gate_info = {
                            "gateway": ip_obj.gateway,
                            "dns1": ip_obj.dns1,
                            "dns2": ip_obj.dns2,
                        }

                _data["slaves"].append(info)

            # 不允许在编辑bond时所有网卡都是未启用状态，避免管理IP访问不了的情形
            if inactive_count >= len(slaves):
                return get_error_result("AllSlavesInactiveError")

            # 找出bond网卡上已有的管理网络ip和镜像网络ip，一起提供给底层更新网卡配置文件
            queryset = bond_nic.yzy_interface_ips.filter(Q(deleted=False), Q(is_manage=1) | Q(is_image=1))
            for ip_obj in queryset:
                _data["ip_list"].append(
                    {
                        "ip": ip_obj.ip,
                        "netmask": ip_obj.netmask,
                        "is_manage": ip_obj.is_manage,
                        "is_image": ip_obj.is_image
                    }
                )
                if ip_obj.is_manage:
                    manage_gate_info = {
                        "gateway": ip_obj.gateway,
                        "dns1": ip_obj.dns1,
                        "dns2": ip_obj.dns2,
                    }
                if ip_obj.is_image:
                    image_gate_info = {
                        "gateway": ip_obj.gateway,
                        "dns1": ip_obj.dns1,
                        "dns2": ip_obj.dns2,
                    }

            # 网关：管理IP > 镜像IP > 传参
            if manage_gate_info:
                _data["gate_info"] = manage_gate_info
            elif image_gate_info:
                _data["gate_info"] = image_gate_info
            else:
                # 允许网关为空
                gate_info = data.get("gate_info", dict())
                # if not gate_info:
                #     return get_error_result("NoGatewayInfoError")
                # 校验传参的网关、DNS格式是否合法
                if gate_info.get("gateway", ""):
                    verify_ret = self._verify_gate_info(gate_info["gateway"], gate_info.get("dns1", ""),
                                                        gate_info.get("dns2", ""))
                    if verify_ret:
                        return verify_ret
                _data["gate_info"] = gate_info

            # bond网卡上至少要有1个IP
            if len(_data["ip_list"]) + len(data.get("ip_list", [])) < 1:
                return get_error_result("BondIpLessThanOne")

            # bond网卡上所有IP数量不能超过4个
            if len(_data["ip_list"]) + len(data.get("ip_list", [])) > 4:
                return get_error_result("NodeNICIpTooManyError")

            # bond网卡的无角色IP
            for ip_info in data.get("ip_list", []):
                # 校验传参的无角色IP格式是否合法
                verify_ret = self._verify_ip_info(ip_info.get("ip", ""), ip_info.get("netmask", ""),
                                                  data["slaves"], node_uuid, bond_uuid)
                if verify_ret:
                    return verify_ret
                ip_info["is_manage"] = 0
                ip_info["is_image"] = 0
                _data["ip_list"].append(ip_info)

            # 网关必须和其中一个IP在同一个网络
            if _data["gate_info"].get("gateway", ""):
                verify_ret = self._verify_gate_ip_match(_data["ip_list"], _data["gate_info"]["gateway"])
                if verify_ret:
                    return verify_ret

            # 请求server服务变更网卡配置文件，并更新数据库记录
            _data["bond_info"] = {
                    "dev": bond_nic.nic,
                    "mode": mode,
                }
            _data["bond_info"]["slaves"] = [slave["nic_name"] for slave in _data["slaves"]]
            ret = server_post("/node/edit_bond", _data)
            if ret.get("code", -1) != 0:
                logger.error("edit_bond in node[%s], ip[%s] error: %s" % (node_uuid, ipaddr, ret))
                return ret

        return get_error_result()

    @operation_record("删除节点{node_uuid}的网卡bond：{bond_uuid}")
    def delete_bond(self, data, node_uuid, bond_uuid):
        # 校验节点是否存在
        node = self.get_object_by_uuid(YzyNodes, node_uuid)
        if not node:
            logger.error("node[%s] not exist!" % node_uuid)
            return get_error_result("NodeNotExistMsg", hostname=node_uuid)
        else:
            ipaddr = node.ip
            _data = dict()
            _data["ipaddr"] = ipaddr
            _data["node_uuid"] = node_uuid
            _data["slaves"] = list()

            # 校验bond网卡是否存在
            bond_nic = node.yzy_node_interfaces.filter(uuid=bond_uuid).first()
            if not bond_nic:
                logger.error("bond nic[%s] not exist!" % bond_nic)
                return get_error_result("BondNICNotExist")

            # HA心跳网卡
            ha_nic_uuids = list()
            ha_info_objs = YzyHaInfo.objects.filter(deleted=False).all()
            if ha_info_objs:
                for ha_info_obj in ha_info_objs:
                    ha_nic_uuids.append(ha_info_obj.master_nic_uuid)
                    ha_nic_uuids.append(ha_info_obj.backup_nic_uuid)
            # 已作为HA心跳网卡的Bond不能编辑或删除
            if bond_uuid in ha_nic_uuids:
                return get_error_result("HaBondEditDeleteError")

            _data["bond_name"] = bond_nic.nic
            _data["bond_uuid"] = bond_uuid

            # 校验bond网卡上是否有交换机，如果有则不能解绑
            vs_uplink_count = bond_nic.yzy_network_interface_uplinks.count()
            if vs_uplink_count:
                logger.error("bond virtual_switch count not 0")
                return get_error_result("BondVSUplinksError")

            # # 如果bond网卡上有数据网络，则不能解绑bond
            # bond_uplink = bond_nic.yzy_network_interface_uplinks.first()
            # if bond_uplink:
            #     bond_vswith = bond_uplink.virtual_switch
            #     if bond_vswith:
            #         net_list = bond_vswith.yzy_vs_networks.all()
            #         if net_list:
            #             logger.error("bond nic[%s] have data_network!" % bond_nic)
            #             return get_error_result("BondHaveDataNetwork")

            inherited_ip_slaves = [_d for _d in data.get("inherit_infos", []) if _d.get("nic_uuid", None)]
            if len(set([_d["ip_uuid"] for _d in inherited_ip_slaves])) != len(inherited_ip_slaves):
                return get_error_result("ParameterError")

            tmp = dict()
            for _d in inherited_ip_slaves:
                if not _d.get("nic_uuid", None):
                    return get_error_result("ParameterError")
                if _d["nic_uuid"] not in tmp.keys():
                    tmp[_d["nic_uuid"]] = list()
                tmp[_d["nic_uuid"]].append(_d["ip_uuid"])
            for k, v in tmp.items():
                if len(v) > 2:
                    return get_error_result("SlaveInheritIpMuchError")

            ip_count = 0
            bond_manage_ip = bond_nic.yzy_interface_ips.filter(deleted=False, is_manage=1).first()
            bond_image_ip = bond_nic.yzy_interface_ips.filter(deleted=False, is_image=1).first()

            # 获取slave网卡原始IP信息，提供给server层还原
            slaves = YzyBondNics.objects.filter(deleted=False, master_uuid=bond_uuid)
            for slave_obj in slaves:
                info = {
                    "nic_name": slave_obj.slave_name,
                    "nic_uuid": slave_obj.slave_uuid,
                    "ip_list": list()
                }

                # 未启用网卡不能继承IP，避免管理IP访问不了的情形
                node_network_info = YzyNodeNetworkInfo.objects.filter(deleted=False, uuid=slave_obj.slave_uuid).first()
                slave_status = node_network_info.status if hasattr(node_network_info, "status") else 0

                # # 不允许用户选择将bond网卡上的IP分配给哪个网卡，直接将slave网卡原有的IP还原回去
                # slave_origin_ips = YzyInterfaceIp.objects.filter(deleted=False, interface=slave_obj.slave_uuid)
                # for ip_obj in slave_origin_ips:
                #     info["ip_list"].append({
                #         "ip": ip_obj.ip,
                #         "netmask": ip_obj.netmask,
                #         "gateway": ip_obj.gateway,
                #         "dns1": ip_obj.dns1,
                #         "dns2": ip_obj.dns2,
                #         "is_manage": ip_obj.is_manage,
                #         "is_image": ip_obj.is_image
                #     })

                # 允许用户选择将bond网卡上的IP分配给哪个网卡
                for index, ip_slave in enumerate(inherited_ip_slaves):
                    if ip_slave["nic_uuid"] == slave_obj.slave_uuid:
                        # 校验继承IP是否存在
                        ip_obj = self.get_object_by_uuid(YzyInterfaceIp, uuid=ip_slave["ip_uuid"])
                        if not ip_obj:
                            return get_error_result("InheritIPNotExist")
                        ip_info = {
                            "ip": ip_obj.ip,
                            "netmask": ip_obj.netmask,
                            "gateway": ip_obj.gateway,
                            "dns1": ip_obj.dns1,
                            "dns2": ip_obj.dns2,
                            "is_manage": ip_obj.is_manage,
                            "is_image": ip_obj.is_image
                        }

                        # 记录管理、镜像IP是否已分配给slave网卡
                        if ip_info["is_manage"] == 1 and ip_info["ip"] == bond_manage_ip.ip:
                            bond_manage_ip = None
                        if ip_info["is_image"] == 1 and ip_info["ip"] == bond_image_ip.ip:
                            bond_image_ip = None

                        info["ip_list"].append(ip_info)
                        # 记录已分配给salve网卡的IP数量
                        ip_count += 1

                        # 未启用网卡不能继承IP，避免管理IP访问不了的情形
                        if slave_status != 2:
                            return get_error_result("InactiveSlaveCannotInheritIP", nic=slave_obj.slave_name)

                _data["slaves"].append(info)

            # 如果已分配给slave网卡的IP数量不等于入参inherit_infos的长度，说明入参中指定了非slave网卡继承IP，属于入参错误
            if ip_count != len(inherited_ip_slaves):
                return get_error_result("InheritNicNotSlave")
            # 管理、镜像IP必须分配到slave网卡上
            if bond_manage_ip:
                return get_error_result("ManageNetworkNotInherit")
            if bond_image_ip:
                return get_error_result("ImageNetworkNotInherit")

            # 请求server服务变更网卡配置文件，并更新数据库记录
            ret = server_post("/node/unbond", _data)
            if ret.get("code", -1) != 0:
                logger.error("unbond in node[%s], ip[%s] error: %s" % (node_uuid, ipaddr, ret))
                return ret

        return get_error_result()

    def _verify_ip_info(self, ip, netmask, slave_uuids, node_uuid, bond_uuid=''):
        # 校验新IP是否已存在于数据库，新IP可以与slave网卡的已有IP相同，因为slave网卡的已有IP做bond时会被删除
        # 在编辑bond时，还可以与bond网卡的已有IP相同，因为前端传参不区分IP是bond上已有的，还是新增的
        yzy_interfaces = YzyInterfaceIp.objects.filter(deleted=False, ip=ip).all()
        if len(yzy_interfaces) >= 1:
            for ip_obj in yzy_interfaces:
                if ip_obj.interface.uuid != bond_uuid and ip_obj.interface.uuid not in slave_uuids:
                    logger.error("_verify_ip_info: ipaddress exists")
                    return get_error_result("IPUsedError", ip=ip)

        # 本节点的不同网卡上不能存在相同网段的IP，同一个网卡上可以存在相同网段的IP
        bits = netaddr.IPAddress(netmask).netmask_bits()
        net = ipaddress.ip_interface(ip + '/' + str(bits)).network
        nics = YzyNodeNetworkInfo.objects.filter(node=node_uuid, deleted=False).all()
        for nic in nics:
            # 新IP可以与本bond网卡上已有IP相同网段，也可以与slave网卡的已有IP相同网段，因为slave网卡的已有IP做bond时会被删除
            if nic.uuid != bond_uuid and nic.uuid not in slave_uuids:
                ips = YzyInterfaceIp.objects.filter(interface=nic.uuid, deleted=False).all()
                for ipinfo in ips:
                    if ipinfo.ip:
                        if ipaddress.ip_address(ipinfo.ip) in net:
                            logger.error("exist another nic has the ip in same segement")
                            return get_error_result("LocalNetworkIpAddressError")

        if not (ip and netmask):
            logger.error("_verify_ip_info: interface ip need params error: ip: %s, netmask: %s" % (ip, netmask))
            return get_error_result("ParamError")
        try:
            if not (is_ip_addr(ip) and is_netmask(netmask)[0]):
                logger.error("_verify_ip_info: interface ip error: ip: %s, netmask: %s" % (ip, netmask))
                return get_error_result("IpAddressGatewayDnsAddressError")
        except Exception as e:
            # AddrFormatError
            return get_error_result("IpAddressGatewayDnsAddressError")

        return None

    def _verify_gate_info(self, gateway, dns1, dns2):
        if gateway and not is_ip_addr(gateway):
            return get_error_result("IpAddressGatewayDnsAddressError")
        if dns1 and dns1 != '' and not is_ip_addr(dns1):
            logger.error("_verify_gate_info interface dns2 error: %s", dns1)
            return get_error_result("DnsAddressError")
        if dns2 and dns2 != '' and not is_ip_addr(dns2):
            logger.error("_verify_gate_info interface dns2 error: %s", dns2)
            return get_error_result("DnsAddressError")
        return None

    def _verify_gate_ip_match(self, ip_list, gateway):
        count = 0
        # 判断IP和网关是否属于同一个网络(网络由IP和子网掩码确定)，网关必须和其中一个IP在同一个网络
        for info in ip_list:
            netmask_bits = netaddr.IPAddress(info["netmask"]).netmask_bits()
            network_num = ipaddress.ip_interface(info["ip"] + "/" + str(netmask_bits)).network
            if ipaddress.IPv4Address(gateway) not in network_num:
                count += 1
        if count > 0 and count == len(ip_list):
            return get_error_result("GatewayAndIpError")
        return None

    def _verify_new_master_ip(self, new_master_ip, vip, netmask):
        if new_master_ip and not is_ip_addr(new_master_ip):
            return get_error_result("IpAddressGatewayDnsAddressError")

        # 查看该IP是否已被使用
        yzy_interfaces = YzyInterfaceIp.objects.filter(deleted=False, ip=new_master_ip).all()
        if len(yzy_interfaces) >= 1:
            logger.error("add ip node fail: ipaddress exists")
            return get_error_result("IPInUse")

        # vip必须与master_ip/backup_ip在同一网段
        netmask_bits = netaddr.IPAddress(netmask).netmask_bits()
        network_num = ipaddress.ip_interface(vip + "/" + str(netmask_bits)).network
        if ipaddress.IPv4Address(new_master_ip) not in network_num:
            return get_error_result("VIPAndMasterIpError")
        return None


node_mgr = NodeManager()
