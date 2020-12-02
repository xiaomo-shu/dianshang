import logging
from web_manage.yzy_resource_mgr.models import *
from web_manage.common.http import server_post
from web_manage.common.log import operation_record
from web_manage.common.utils import get_error_result, JSONResponse, is_ip_addr

logger = logging.getLogger(__name__)


class VirtualSwitchManager(object):

    def get_object_by_uuid(self, model, uuid):
        try:
            obj = model.objects.filter(deleted=False).get(uuid=uuid)
            return obj
        except Exception as e:
            return None

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
        return func(self, data)
        # return ret

    @operation_record("创建虚拟交换机 {data[name]}")
    def create_virtual_switch(self, data):
        uplinks = data.get("uplinks")
        if not uplinks:
            logger.error("create virtual switch error: not uplinks parameter %s"% data)
            return get_error_result("ParamError")

        # 已启用HA的网卡不能绑定Flat类型的分布式虚拟交换机
        ha_nic_uuids = list()
        if data.get("type", "") == "Flat":
            ha_info_objs = YzyHaInfo.objects.filter(deleted=False).all()
            if ha_info_objs:
                for ha_info_obj in ha_info_objs:
                    ha_nic_uuids.append(ha_info_obj.master_nic_uuid)
                    ha_nic_uuids.append(ha_info_obj.backup_nic_uuid)

        for uplink in uplinks:
            # 判断每个链接的正确性
            node_uuid = uplink.get("node_uuid")
            node_name = uplink.get("node_name")
            nic_uuid = uplink.get("nic_uuid")
            nic_name = uplink.get("nic_name")

            if ha_nic_uuids and nic_uuid in ha_nic_uuids:
                return get_error_result("FlatVSUplinkNicHaError")

            node_network = self.get_object_by_uuid(YzyNodeNetworkInfo, nic_uuid)
            if node_network:
                if node_network.node.uuid != node_uuid:
                    logger.error("create virtual switch error: uplink[%s] not nic"% uplink)
                    ret = get_error_result("NetworkInterfaceNotExist", node=node_name, interface=nic_name)
                    return ret
            else:
                logger.error("create virtual switch error: node[%s] not exist"% (node_name))
                return get_error_result("NodeNotExistMsg", hostname=node_name)
        #
        ret = server_post("/vswitch/create", data)
        logger.info("create virtual switch: server api return [%s]"% ret)
        return ret

    @operation_record("修改分布式虚拟交换机 {uuids}")
    def delete_virtual_switch(self, uuids):
        ret = get_error_result("Success")
        for uuid in uuids:
            obj = self.get_object_by_uuid(YzyVirtualSwitchs, uuid)
            if obj:
                ret = server_post("/vswitch/delete", {'uuid': uuid})
                if ret.get("code", -1) != 0:
                    logger.error("delete virtual switch [%s] error: %s" % (uuid, ret))
                    break
            else:
                logger.error("delete virtual switch [%s] info not exist!" % uuid)
                ret = get_error_result("VSwitchNotExist")
        return ret

    @operation_record("修改分布式虚拟交换机 {data[name]}")
    def update_virtual_switch(self, data):
        ret = server_post("/vswitch/update", data)
        logger.info("update virtual switch: server api return [%s]" % ret)
        return ret

    def node_map_update(self, data):
        ret = server_post("/vswitch/update_map", data)
        logger.info("update virtual switch: server api return [%s]" % ret)
        return ret

    def service_node(self, data):
        pass

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
        ip = data.get("ip")
        root_pwd = data.get("root_pwd")
        if not ip or not is_ip_addr(ip):
            logging.error("check node parameter ip error: %s" % ip)
            return get_error_result("IPAddrError", ipaddr=ip)
            # ret['msg'] = ret['msg'].format({"ipaddr": ip})
            # return ret
        if not root_pwd:
            logging.error("check node parameter root_pwd not exist!")
            return get_error_result("ParamError")

        ret = server_post("/api/v1/node/check", data)
        if ret.get('code') != 0:
            logger.info("check node KVM failed:%s", ret['msg'])
            return ret
        logger.info("check node KVM success, ip: %s", ip)
        return ret

    @operation_record("添加计算节点 名称:{data[hostname]}, IP:{data[ip]}")
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
        resource_pool =  self.get_object_by_uuid(YzyResourcePools, pool_uuid)
        if not resource_pool:
            logger.error("add node KVM, pool_name: %s, pool_uuid: %s"% (pool_name, pool_uuid))
            return get_error_result("ResourcePoolNameExistErr", name = pool_name)
        switch_uuid = data.get("switch_uuid")
        virtual_switch  = self.get_object_by_uuid(YzyVirtualSwitchs, switch_uuid)
        if not virtual_switch:
            logger.error("add node KVM, switch_name, switch_uuid: %s"% switch_uuid)
            return get_error_result("VSwitchNotExist")
        ret = server_post("/api/v1/node/check", data)
        if ret.get('code') != 0:
            logger.info("add node KVM failed:%s", ret['msg'])
            return ret
        logger.info("add node KVM success, data: %s", data)
        return ret


    def delete_node(self):
        pass

    def operate_node(self):
        pass


virtual_switch_mgr = VirtualSwitchManager()
