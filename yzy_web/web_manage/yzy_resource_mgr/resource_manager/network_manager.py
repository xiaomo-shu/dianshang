import logging
import ipaddress

from web_manage.yzy_edu_desktop_mgr.models import *
from web_manage.yzy_user_desktop_mgr.models import *
from web_manage.yzy_resource_mgr.models import *
from web_manage.yzy_user_desktop_mgr import models as personal_model
from web_manage.common.http import server_post
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.utils import get_error_result, JSONResponse, is_ip_addr, is_netmask

logger = logging.getLogger(__name__)


class NetworkManager(object):

    def get_object_by_uuid(self, model, uuid):
        try:
            obj = model.objects.filter(deleted=False).get(uuid=uuid)
            return obj
        except Exception as e:
            return None

    def get_object_by_name_and_not_uuid(self, model, name, uuid):
        try:
            obj = model.objects.filter(deleted=False).exclude(uuid=uuid).get(name=name)
            return obj
        except Exception as e:
            return None

    def check_subnet_params(self, data, subnets=None):
        start_ip = data.get('start_ip')
        end_ip = data.get('end_ip')
        gateway = data.get('gateway')
        netmask = data.get('netmask')
        dns1 = data.get('dns1')
        dns2 = data.get('dns2')
        if not start_ip or not end_ip or not gateway or not netmask or not dns1:
            return get_error_result("ParameterError"), False

        for i in [start_ip, end_ip, gateway, dns1, netmask]:
            if not is_ip_addr(i):
                return get_error_result("IpAddressGatewayDnsAddressError"), False
        if dns2 and dns2 != '' and not is_ip_addr(dns2):
            return get_error_result("DnsAddressError"), False

        _is_netmask, netmask_bits = is_netmask(netmask)
        if _is_netmask:
            network_num = ipaddress.ip_interface(start_ip + '/' + str(netmask_bits)).network
            if ipaddress.ip_address(end_ip) not in network_num or ipaddress.ip_address(gateway) not in network_num:
                return get_error_result("GatewayAndIpError"), False
        else:
            return get_error_result("SubnetMaskError"), False

        if ipaddress.ip_network(start_ip).compare_networks(ipaddress.ip_network(end_ip)) >= 0:
            return get_error_result("EndIPLessThanStartIP"), False

        if subnets is not None:
            exit_subnets = []
            for subnet in subnets:
                flag_a = ipaddress.ip_network(data['start_ip']).compare_networks(ipaddress.ip_network(subnet.start_ip))
                flag_b = ipaddress.ip_network(subnet.end_ip).compare_networks(ipaddress.ip_network(data['start_ip']))
                flag_c = ipaddress.ip_network(data['end_ip']).compare_networks(ipaddress.ip_network(subnet.start_ip))
                flag_d = ipaddress.ip_network(subnet.end_ip).compare_networks(ipaddress.ip_network(data['end_ip']))
                flag_e = ipaddress.ip_network(subnet.start_ip).compare_networks(ipaddress.ip_network(data['start_ip']))
                flag_f = ipaddress.ip_network(data['end_ip']).compare_networks(ipaddress.ip_network(subnet.end_ip))
                if (flag_a >= 0 and flag_b >= 0) or (flag_c >= 0 and flag_d >= 0) or (flag_e >= 0 and flag_f >= 0):
                    exit_subnets.append(subnet)
            if len(exit_subnets) > 0:
                return get_error_result("IpAddressConflictError"), False

        return '', True


    @operation_record("创建数据网络 {data[name]}")
    def create_network(self, data):
        """
        {
            "name": "test_network2",
            "switch_uuid" : "9c7050ba-5213-11ea-9d93-000c295dd728",
            "vlan_id" : 12,
            "subnet_info": {
                    "name": "subnet1",
                    "start_ip": "192.168.1.10",
                    "end_ip": "192.168.1.20",
                    "netmask": "255.255.255.0",
                    "gateway": "192.168.1.0",
                    "dns1": "8.8.8.8"
                }
        }
        :param data:
        :return:
        """
        virtual_switch_uuid = data.get("switch_uuid")
        virtual_switch = self.get_object_by_uuid(YzyVirtualSwitchs, virtual_switch_uuid)
        if not virtual_switch:
            logger.error("create data-network error: virtual switch [%s] not exist!"% virtual_switch_uuid)
            ret = get_error_result("VSwitchNotExist")
            return ret
        if data.get('subnet_info'):
            ret, status = self.check_subnet_params(data.get('subnet_info'))
            if not status:
                logger.error("create data-network error: check subnet params fail")
                return ret
            # virtual_start_ip = data.get('subnet_info').get('start_ip')
            # virtual_end_ip = data.get('subnet_info').get('end_ip')
            # gateway = data.get('subnet_info').get('gateway')
            # netmask = data.get('subnet_info').get('netmask')
            # dns1 = data.get('subnet_info').get('dns1')
            # if not virtual_end_ip or not virtual_start_ip or not gateway or not netmask or not dns1:
            #     logger.error("ParameterError")
            #     return get_error_result("ParameterError")
            # _is_netmask, netmask_bits = is_netmask(netmask)
            # if _is_netmask:
            #     network_num = ipaddress.ip_interface(virtual_start_ip + '/' + str(netmask_bits)).network
            #     if ipaddress.ip_address(virtual_end_ip) not in network_num or ipaddress.ip_address(gateway) not in network_num:
            #         logger.error("create data-network error: incorrect gateway")
            #         ret = get_error_result("GatewayAndIpError")
            #         return ret
            #     if ipaddress.ip_network(virtual_start_ip).compare_networks(ipaddress.ip_network(virtual_end_ip)) >= 0:
            #         logger.error("create data-network error: virtual start_ip:%s less than virtual! end_ip:%s or input ip in different network segments"% (virtual_end_ip, virtual_start_ip))
            #         ret = get_error_result("EndIPLessThanStartIP")
            #         return ret
            # else:
            #     logger.error("subnet mask error: %s"% netmask)
            #     ret = get_error_result("SubnetMaskError")
            #     return ret
        ret = server_post("/network/create", data)
        logger.info("create data-network server api return: %s"% ret)
        return ret

    def update_network(self, data, uuid):
        """
        编辑网络
        :param data:
        :return:
        """
        new_name = data.get("name", "")
        network = self.get_object_by_name_and_not_uuid(YzyNetworks, new_name, uuid)
        if network:
            logger.error("update data-network error, the name[%s][%s] not change"%(network.name, new_name))
            return get_error_result("UpdateNoChangeError", param=new_name)
        data['uuid'] = uuid
        ret = server_post("/network/update", data)
        return ret

    def delete_network(self, uuids):
        """
        :param data:
        :return:
        """
        ret = get_error_result("Success")
        success_num = 0
        failed_num = 0
        try:
            for uuid in uuids:
                obj = self.get_object_by_uuid(YzyNetworks, uuid)
                if obj:
                    templates = education_model.YzyInstanceTemplate.objects.filter(deleted=False, network=obj).count()
                    if templates > 0:
                        failed_num += 1
                        continue
                    groups = education_model.YzyGroup.objects.filter(deleted=False, network=obj).count()
                    if groups > 0:
                        failed_num += 1
                        continue
                    desktops = education_model.YzyDesktop.objects.filter(deleted=False, network=obj).count()
                    if desktops > 0:
                        failed_num += 1
                        continue
                    personal_desktops = personal_model.YzyPersonalDesktop.objects.filter(deleted=False, network=obj).count()
                    if personal_desktops > 0:
                        failed_num += 1
                        continue
                    ret = server_post("/network/delete", {'uuid': uuid})
                    if ret.get("code", -1) != 0:
                        failed_num += 1
                    else:
                        success_num += 1
                else:
                    failed_num += 1
        except Exception as e:
            logger.error("delete network failed:%s", e, exc_info=True)
            return get_error_result("DataNetworkDeleteFail")
        
        msg = "删除数据网络 %s" % ('/'.join(uuids))
        insert_operation_log(msg, ret["msg"])
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    @operation_record("添加计算节点 名称:{data[name]}, IP:{data[ip]}")
    def add_node(self, data):
        """
        data: {
                "hostname": "controller",
                "ip": "172.16.1.11",
                "pool_name": "default",
                "pool_uuid": "ec92a530-4885-11ea-8e15-000c295dd728",
                "network_uuid": "ec796fde-4885-11ea-8e15-000c295dd728",
                "switch_uuid": "ec796624-4885-11ea-8e15-000c295dd728",
                "interface": "ens224",
                "manage_interface": "ens192",
                "image_interface": "ens192"
        }
        :param data:
        :return:
        """
        logger.info("add node KVM: %s" % data)
        pool_name = data.get("pool_name")
        pool_uuid = data.get("pool_uuid")
        resource_pool = self.get_object_by_uuid(YzyResourcePools, pool_uuid)
        if not resource_pool:
            logger.error("add node KVM, pool_name: %s, pool_uuid: %s"% (pool_name, pool_uuid))
            return get_error_result("ResourcePoolNameExistErr", name = pool_name)
        switch_uuid = data.get("switch_uuid")
        virtual_switch = self.get_object_by_uuid(YzyVirtualSwitchs, switch_uuid)
        if not virtual_switch:
            logger.error("add node KVM, switch_name, switch_uuid: %s"% switch_uuid)
            return get_error_result("VSwitchNotExist")
        ret = server_post("/api/v1/node/check", data)
        if ret.get('code') != 0:
            logger.info("add node KVM failed:%s", ret['msg'])
            return ret
        logger.info("add node KVM success, data: %s", data)
        return ret

    @operation_record("编辑计算节点 名称:{data[hostname]}, IP:{data[ip]}, name: {data[name]}")
    def update_node(self, data):
        """
        data {
            "uuid": "xxxxxxxxxxxxxxxx-xxxxxxxxxx",
            "hostname": "xxxxxx",
            "ip": "xxxxxxxx",
            "name": "xxxxxx"
        }
        :param data:
        :return:
        """
        # pass
        uuid = data.get("uuid")
        hostname = data.get("hostname")
        node = self.get_object_by_uuid(YzyNodes, uuid)
        if not node:
            logger.error("update node info error, node: %s[%s] not exist"%(hostname, uuid))
            return get_error_result("NodeNotExist")

        name = data.get("name")
        node.name = name
        node.save()
        return get_error_result("Success")

    def delete_node(self, data):
        """
        data : [
            {"uuid": "xxxxxxx", "hostname": "xxxxxx"},
            {"uuid": "xxxxxxx", "hostname": "xxxxxx"},
            {"uuid": "xxxxxxx", "hostname": "xxxxxx"}
        ]
        删除节点
        :return:
        """
        names = []
        ret = get_error_result("Success")
        for node in data:
            uuid = node.get("uuid")
            hostname = node.get("hostname")
            names.append(hostname)
            obj = self.get_object_by_uuid(YzyNodes, uuid)
            if obj:
                ret = server_post("/node/delete", node)
                if ret.get("code", -1) != 0:
                    logger.error("delete node[%s] error: %s"% (hostname, ret))
                    break
            else:
                logger.error("delete node[%s] info not exist!"% hostname)
                ret = get_error_result("NodeNotExistMsg", hostname=hostname)
        msg = "删除节点 %s" % ('/'.join(names))
        insert_operation_log(msg, ret["msg"])
        return ret

    def reboot_node(self, data):
        """
        data : [
            {"uuid": "xxxxxxx", "hostname": "xxxxxx"},
            {"uuid": "xxxxxxx", "hostname": "xxxxxx"},
            {"uuid": "xxxxxxx", "hostname": "xxxxxx"}
        ]
        :param data:
        :return:
        """
        names = []
        ret = get_error_result("Success")
        for node in data:
            uuid = node.get("uuid")
            hostname = node.get("hostname")
            names.append(hostname)
            obj = self.get_object_by_uuid(YzyNodes, uuid)
            if obj:
                ret = server_post("/node/reboot", node)
                if ret.get("code", -1) != 0:
                    logger.error("reboot node[%s] error: %s" % (hostname, ret))
                    break
            else:
                logger.error("reboot node[%s] info not exist!" % hostname)
                ret = get_error_result("NodeNotExistMsg", hostname=hostname)
        msg = "重启节点 %s" % ('/'.join(names))
        insert_operation_log(msg, ret["msg"])
        return ret

    def shutdown_node(self, data):
        """
        data : [
            {"uuid": "xxxxxxx", "hostname": "xxxxxx"},
            {"uuid": "xxxxxxx", "hostname": "xxxxxx"},
            {"uuid": "xxxxxxx", "hostname": "xxxxxx"}
        ]
        :param data:
        :return:
        """
        names = []
        ret = get_error_result("Success")
        for node in data:
            uuid = node.get("uuid")
            hostname = node.get("hostname")
            names.append(hostname)
            obj = self.get_object_by_uuid(YzyNodes, uuid)
            if obj:
                ret = server_post("/node/shutdown", node)
                if ret.get("code", -1) != 0:
                    logger.error("shutdown node[%s] error: %s" % (hostname, ret))
                    break
            else:
                logger.error("shutdown node[%s] info not exist!" % hostname)
                ret = get_error_result("NodeNotExistMsg", hostname=hostname)
        msg = "关机节点 %s" % ('/'.join(names))
        insert_operation_log(msg, ret["msg"])
        return ret

    def operate_node(self):
        pass


network_mgr = NetworkManager()


class SubnetManager(object):
    """
    子网管理
    """

    def get_object_by_uuid(self, model, uuid):
        try:
            obj = model.objects.filter(deleted=False).get(uuid=uuid)
            return obj
        except Exception as e:
            return None

    def get_object_by_name(self, model, name, network_uuid):
        try:
            obj = model.objects.filter(deleted=False, network=network_uuid).get(name=name)
            return obj
        except Exception as e:
            return None

    # def check_subnet_params(self, data):
    #     start_ip = data.get('start_ip')
    #     end_ip = data.get('end_ip')
    #     gateway = data.get('gateway')
    #     netmask = data.get('netmask')
    #     dns1 = data.get('dns1')
    #     dns2 = data.get('dns2')
    #     if not start_ip or not end_ip or not gateway or not netmask or not dns1:
    #         raise Exception("param error")
    #     for i in (data['start_ip'], data['end_ip'], data['gateway']):
    #         if not is_ip_addr(i):
    #             _ip = i
    #             raise Exception("%s is not ip address" % _ip)
    #     if not is_ip_addr(dns1):
    #         raise Exception("%s is not ip address" % dns1)
    #
    #     if dns2 != '' and not is_ip_addr(data['dns2']):
    #         raise Exception("%s is not ip address" % dns2)
    #
    #     _is_netmask, netmask_bits = is_netmask(netmask)
    #     if not _is_netmask:
    #         raise Exception("%s netmask error" % netmask)
    #
    #     network_num = ipaddress.ip_interface(start_ip + '/' + str(netmask_bits)).network
    #     if ipaddress.ip_address(end_ip) not in network_num or ipaddress.ip_address(gateway) not in network_num:
    #         raise Exception("start_ip %s, end_ip %s in the wrong sequence"%(start_ip, end_ip))
    #     # if not (start_ip[0:start_ip.rfind('.')] == start_ip[0:start_ip.rfind('.')] and start_ip[0:start_ip.rfind('.')] == gateway[0:gateway.rfind('.')] ):
    #         # raise Exception("start_ip %s, end_ip %s in the wrong sequence"%(data['start_ip'], data['end_ip']))
    #
    #     if ipaddress.ip_network(data['start_ip']).compare_networks(ipaddress.ip_network(data['end_ip'])) >= 0:
    #         raise Exception("start_ip %s, end_ip %s in the wrong sequence"%(data['start_ip'], data['end_ip']))

    @operation_record("创建网络 {data_network_uuid} 的子网 {data[name]}")
    def create_subnet(self, data, data_network_uuid, request):
        # pass
        data['network_uuid'] = data_network_uuid
        network = self.get_object_by_uuid(YzyNetworks, data_network_uuid)
        if not network:
            logger.error("create subnet error: network[%s] not exist!"%(data_network_uuid))
            return get_error_result("NetworkInfoNotExist")
        name = data.get("name")
        subnet = self.get_object_by_name(YzySubnets, name, data_network_uuid)
        if subnet:
            logger.error("create subnet error: subnet name [%s] is repeat"% name)
            return get_error_result("SubnetNameRepeatError", name=name)

        subnets = YzySubnets.objects.filter(network=network, deleted=False)
        ret, status = network_mgr.check_subnet_params(data, subnets)
        if not status:
            logger.error("create subnet error: check subnet params fail")
            return ret
        #
        # try:
        #     self.check_subnet_params(data, subnets)
        #     exit_subnets = []
        #     for subnet in subnets:
        #         flag_a = ipaddress.ip_network(data['start_ip']).compare_networks(ipaddress.ip_network(subnet.start_ip))
        #         flag_b = ipaddress.ip_network(subnet.end_ip).compare_networks(ipaddress.ip_network(data['start_ip']))
        #         flag_c = ipaddress.ip_network(data['end_ip']).compare_networks(ipaddress.ip_network(subnet.start_ip))
        #         flag_d = ipaddress.ip_network(subnet.end_ip).compare_networks(ipaddress.ip_network(data['end_ip']))
        #         flag_e = ipaddress.ip_network(subnet.start_ip).compare_networks(ipaddress.ip_network(data['start_ip']))
        #         flag_f = ipaddress.ip_network(data['end_ip']).compare_networks(ipaddress.ip_network(subnet.end_ip))
        #         if (flag_a >= 0 and flag_b >= 0) or (flag_c >= 0 and flag_d >= 0) or (flag_e >= 0 and flag_f >= 0):
        #             exit_subnets.append(subnet)
        #     if len(exit_subnets) > 0:
        #         return get_error_result("IpAddressConflictError")
        # except Exception as e:
        #     logger.error("create subnet error: subnet parameters[%s] error"% data, exc_info=True )
        #     return get_error_result("SubnetInfoError", name=name)

        ret = server_post("/subnet/create", data)
        logger.info("create subnet: server api return %s"% ret)
        return ret

    def delete_subnet(self, uuids):
        """
        data [
                {"uuid": "1a870202-3732-11ea-8a2d-000c295dd728","name": "xxxxx"},
                {"uuid": "1a870202-3732-11ea-8a2d-000c295dd728","name": "xxxxx"},
                {"uuid": "1a870202-3732-11ea-8a2d-000c295dd728","name": "xxxxx"}
            ]
        :param data:
        :return:
        """
        ret = get_error_result("Success")
        # for uuid in uuids:
        #     obj = self.get_object_by_uuid(YzySubnets, uuid)
        #     if obj:
        #         # 判断是否被占用
        #         templates = YzyInstanceTemplate.objects.filter(subnet_uuid=uuid, deleted=False).all()
        #         if templates:
        #             logger.error("delete subnet[%s] error, is be used"% uuid)

        ret = server_post("/subnet/delete", {'uuids': uuids})
                # if ret.get("code", -1) != 0:
                #     logger.error("delete subnet[%s] error: %s" % (uuid, ret))
                #     break
            # else:
            #     logger.error("delete subnet[%s] info not exist!" % uuid)
            #     ret = get_error_result("SubnetNotExist")
        msg = "删除子网 %s" % ('/'.join(uuids))
        insert_operation_log(msg, ret["msg"])
        return ret

    @operation_record("修改子网信息 {data[name]}")
    def update_subnet(self, data, data_network_uuid, sub_network_uuid):
        subnets = YzySubnets.objects.filter(network=data_network_uuid, deleted=False).exclude(uuid=sub_network_uuid)
        ret, status = network_mgr.check_subnet_params(data, subnets)
        if not status:
            logger.error("update subnet error: check subnet params fail")
            return ret
        # try:
        #     subnets = YzySubnets.objects.filter(network=data_network_uuid, deleted=False)
        #     self.check_subnet_params(data, subnets)
        #     for subnet in subnets:
        #         if subnet.uuid != sub_network_uuid:
        #             flag_a = ipaddress.ip_network(data['start_ip']).compare_networks(ipaddress.ip_network(subnet.start_ip))
        #             flag_b = ipaddress.ip_network(subnet.end_ip).compare_networks(ipaddress.ip_network(data['start_ip']))
        #             flag_c = ipaddress.ip_network(data['end_ip']).compare_networks(ipaddress.ip_network(subnet.start_ip))
        #             flag_d = ipaddress.ip_network(subnet.end_ip).compare_networks(ipaddress.ip_network(data['end_ip']))
        #             flag_e = ipaddress.ip_network(subnet.start_ip).compare_networks(ipaddress.ip_network(data['start_ip']))
        #             flag_f = ipaddress.ip_network(data['end_ip']).compare_networks(ipaddress.ip_network(subnet.end_ip))
        #             if (flag_a >= 0 and flag_b >= 0) or (flag_c >= 0 and flag_d >= 0) or (flag_e >= 0 and flag_f >= 0):
        #                 return get_error_result("IpAddressConflictError")
        # except Exception as e:
        #     logger.error("update subnet error: subnet parameters[%s] error:%s", data, e, exc_info=True)
        #     return get_error_result("SubnetInfoError", name=data['name'])
        data["uuid"] = sub_network_uuid
        ret = server_post('/subnet/update', data)
        logger.info("update subnet: server api return %s", ret)
        return ret


subnet_mgr = SubnetManager()