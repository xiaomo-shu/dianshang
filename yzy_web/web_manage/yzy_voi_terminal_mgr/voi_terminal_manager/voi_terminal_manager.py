import os
import logging
import time
import json
import datetime
import traceback
import ipaddress

from web_manage.yzy_voi_edu_desktop_mgr.models import *
from web_manage.yzy_resource_mgr.models import YzyNodes, YzyNodeStorages
from web_manage.yzy_voi_terminal_mgr.models import *
from web_manage.common.http import server_post, terminal_post, voi_terminal_post
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common import constants
# from web_manage.common.utils import JSONResponse, YzyWebPagination, create_uuid
from web_manage.common.utils import get_error_result, JSONResponse, YzyWebPagination, is_ip_addr, is_netmask, find_ips,\
                                    size_to_G, gi_to_section, bytes_to_section

logger = logging.getLogger(__name__)

count = 0


class VoiTerminalManager(object):

    system_type_dict = {
            "windows_7_x64": 1,
            "windows_7": 2,
            "windows_10": 3,
            "windows_10_x64": 4,
            "other": 0
        }

    def get_object_by_uuid(self, model, uuid):
        try:
            obj = model.objects.filter(deleted=False).get(uuid=uuid)
            return obj
        except Exception as e:
            return None

    def get_all_object(self, model, _filter=None, all=True):
        try:
            query = model.objects.filter(deleted=False)
            if _filter:
                filter_dict = dict()
                for k, v in _filter.items():
                    if isinstance(v, (str,int)):
                        filter_dict[k] = v
                    if isinstance(v, list):
                        filter_dict["%s__in"% k] = v
                query = query.filter(**filter_dict)
            # import pdb; pdb.set_trace()
            if all:
                return query.all()
            return query.first()

        except Exception as e:
            return []

    def get_node_storage(self):
        sys_storage = self.get_all_object(YzyNodeStorages, {"role__contains": str(constants.INSTANCE_SYS)}, False)
        data_storage = self.get_all_object(YzyNodeStorages, {"role__contains": str(constants.INSTANCE_DATA)}, False)
        sys_dir = constants.DEFAULT_SYS_PATH
        if sys_storage:
            sys_dir = os.path.join(sys_storage.path, "instances")
        data_dir = constants.DEFAULT_DATA_PATH
        if data_storage:
            data_dir = os.path.join(data_storage.path, "datas")
        sys_base, data_base = os.path.join(sys_dir, "_base"), os.path.join(data_dir, "_base")
        return sys_base, data_base


    def get_terminal_mac_name_list(self, data):
        terminals = data.get("terminals", [])
        mac_list = list()
        name_list = list()
        for terminal in terminals:
            name = terminal["name"]
            mac = str(terminal["mac"])
            if mac not in mac_list:
                mac_list.append(mac)
            if name not in name_list:
                name_list.append(name)
        if not mac_list:
            raise Exception("terminals not exist")
        return mac_list, name_list

    def get_group_info(self, uuid):
        return self.get_object_by_uuid(YzyVoiGroup, uuid)

    def dict_to(self):
        pass

    def get_all_group_name(self, group_type=None):
        groups = list()
        if not group_type:
            all_groups = self.get_all_object(YzyVoiGroup)
        else:
            all_groups = self.get_all_object(YzyVoiGroup, {"group_type": group_type})
        for group in all_groups:
            groups.append({"uuid": group.uuid, "name": group.name})
        groups.append({"uuid":"", "name": "未分组"})
        return get_error_result("Success", groups)

    def get_edu_group_name(self):
        groups = list()
        all_groups = self.get_all_object(YzyVoiGroup, {"group_type": constants.EDUCATION_TYPE})
        for group in all_groups:
            groups.append({"uuid": group.uuid, "name": group.name})
        # groups.append({"uuid": "", "name": "未分组"})
        return get_error_result("Success", groups)

    def get_all_group(self, group_type=None):
        if not group_type:
            groups = self.get_all_object(YzyVoiGroup)
        else:
            groups = self.get_all_object(YzyVoiGroup, {"group_type": group_type})

        terminals = self.get_all_object(YzyVoiTerminal)
        data = list()
        sum = len(terminals)
        count = 0
        for group in groups:
            _d = {"name": group.name, "uuid": group.uuid, "type": group.group_type, "count": 0}
            for terminal in terminals:
                if terminal.group_uuid  == group.uuid:
                    _d["count"] += 1
                    count += 1
            data.append(_d)
        data.sort(key=lambda x:x["type"])
        if not group_type or str(group_type) == "0":
            data.append({"name": "未分组", "uuid": "", "type": 0, "count": sum - count})
        ret = get_error_result("Success")
        ret["data"] = data
        return ret

    def check_setup_info(self, setup_info):
        """
        {
            "mode":{
                "show_desktop_type":1,
                "auto_desktop":0
            },
            "program": {
                "server_ip": "172.16.1.33"
            }
        }
        :param setup_info:
        :return:
        """
        if not setup_info:
            return False

        mode = setup_info.get("mode")
        program = setup_info.get("program")
        # windows = setup_info.get("windows")
        if not (mode and program):
            return False
        try:
            assert mode["show_desktop_type"] in (0, 1, 2), "show desktop type"
            assert mode["auto_desktop"] >= 0 , "auto desktop"
            assert is_ip_addr(program["server_ip"]), "server ip"
        except Exception as e:
            logger.error("%s"% str(e), exc_info=True)
            return False
        return True

    def terminal_operate(self, request):
        """
        节点服务的相关操作
        :param request:
        :return:
        """
        _data = request.data
        cmd = _data.get("cmd")
        data = _data.get("data")
        try:
            func = getattr(self, cmd + '_terminal')
        except:
            ret = get_error_result("ParamError")
            return JSONResponse(ret, status=400,
                                json_dumps_params={'ensure_ascii': False})
        return func(data)
        # return ret

    def start_terminal(self, data):
        """ start 终端 """
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
        except Exception as e:
            logger.error("", exc_info=True)
            logger.error(''.join(traceback.format_exc()))
            return get_error_result("ParamError")

        mac_list_str = ",".join(mac_list)
        # 提交终端服务接口
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "start",
            "data": {
                "mac_list": mac_list_str,
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "唤醒终端 %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal start fail: %s"% mac_list_str)
            return ret

        logger.info("terminal start success!!! %s"% mac_list_str)
        return get_error_result("Success")

    def shutdown_terminal(self, data):
        """ 关闭终端 """
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
        except Exception as e:
            logger.error("", exc_info=True)
            logger.error(''.join(traceback.format_exc()))
            return get_error_result("ParamError")

        mac_list_str = ",".join(mac_list)
        # 提交终端服务接口
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "shutdown",
            "data": {
                "mac_list": mac_list_str,
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "关闭终端 %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal close fail: %s"% mac_list_str)
            return ret

        logger.info("terminal close success!!! %s"% mac_list_str)
        return get_error_result("Success")

    def reboot_terminal(self, data):
        """ 重启终端 """
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
        except Exception as e:
            logger.error("", exc_info=True)
            return get_error_result("ParamError")

        mac_list_str = ",".join(mac_list)
        # 提交终端服务接口
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "restart",
            "data": {
                "mac_list": mac_list_str,
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "重启终端 %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal restart fail: %s" % mac_list_str)
            return get_error_result("TerminalCloseOperateError")

        logger.info("terminal restart success!!! %s" % mac_list_str)
        return get_error_result("Success")

    def delete_terminal(self, data):
        """ 删除终端 """
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
        except Exception as e:
            logger.error("", exc_info=True)
            return get_error_result("ParamError")

        mac_list_str = ",".join(mac_list)
        # 提交终端服务接口
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "delete",
            "data": {
                "mac_list": mac_list_str,
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "删除终端 %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal delete fail: %s"% mac_list_str)
            return get_error_result("TerminalDeleteOperateError")

        logger.info("terminal delete success!!! %s"% mac_list_str)
        return get_error_result("Success")

    def get_setup_terminal(self, data):
        """ 设置终端配置接口 """
        logger.info("get_setup_terminal: {}".format(data))
        terminals = data.get("terminals", [])
        if not terminals:
            logger.error("terminal setup get error: not terminal param")
            return get_error_result("ParamError")

        if len(terminals) == 1:
            terminal = terminals[0]
            terminal_mac = terminal["mac"]
            terminal_obj = self.get_all_object(YzyVoiTerminal, {"mac": terminal_mac}, False)
            if not terminal_obj:
                logger.error("terminal setup get error: %s terminal not exist"% terminal_mac)
                return get_error_result("TerminalNotExistError")
            try:
                setup_info = json.loads(terminal_obj.setup_info)
            except:
                logger.error("terminal setup get error: setup_info  %s error"% terminal_obj.setup_info)
                return get_error_result("TerminalSetupInfoError")

            if "server_port" in setup_info["program"]:
                setup_info["program"].pop("server_port")
            return get_error_result("Success", setup_info)
        else:
            mac_list = list()
            for terminal in terminals:
                mac = terminal["mac"]
                if mac not in mac_list:
                    mac_list.append(mac)
            terminal_objs = self.get_all_object(YzyVoiTerminal, {"mac": mac_list})
            try:
                for terminal in terminal_objs:
                    setup_info = json.loads(terminal.setup_info)
                    server_ip = setup_info["program"]["server_ip"]
            except Exception as e:
                logger.error("", exc_info=True)
                return get_error_result("TerminalSetupInfoError")
            data = {
                "program": {
                    "server_ip": server_ip,
                }
            }
            ret = get_error_result("Success", data)
            return ret

    def update_setup_terminal(self, data):
        """更新终端配置
        {
            "handler": "WebTerminalHandler",
            "command": "set_terminal",
            "data": {
                "mac_list": "00-50-56-C0-00-08,00-50-56-C0-00-07,00-50-56-C0-00-06",
                "mode": {
                    "show_desktop_type": 0,
                    "auto_desktop": 1
                },
                "program": {
                    "server_ip": "172.16.1.33"
                }
            }
        }
        """
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
        except Exception as e:
            logger.error("", exc_info=True)
            return get_error_result("ParamError")

        setup_info = data.get("setup_info", {})
        if not self.check_setup_info(setup_info):
            return get_error_result("TerminalSetupInfoParamError")
        data = {"mac_list": ",".join(mac_list)}
        data.update(setup_info)
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "set_terminal",
            "data": data
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "更新终端配置 %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal update setup info fail")
            return ret

        logger.info("terminal update setup info success!!!")
        return get_error_result("Success")

    def update_name_terminal(self, data):
        """ 修改终端名称 """
        terminals = data.get("terminals", [])
        perfix = data.get("prefix", "")
        postfix = data.get("postfix", "")
        postfix_start = data.get("postfix_start", "")
        use_terminal_id = data.get("use_terminal_id", False)
        if not (terminals and perfix and postfix):
            logger.error("update terminals name param error")
            return get_error_result("ParamError")

        name_list = list()
        _data = dict()
        if use_terminal_id:
            for terminal in terminals:
                mac = terminal["mac"]
                name = terminal["name"]
                terminal_id = terminal["terminal_id"]
                _s = "%" + "0%sd" % postfix
                _n = perfix.upper() + "-" + _s % int(terminal_id)
                _data[mac] = _n
                if name not in name_list:
                    name_list.append(name)
        else:
            for terminal in terminals:
                mac = terminal["mac"]
                name = terminal["name"]
                _s = "%" + "0%sd" % postfix
                _n = perfix.upper() + "-" + _s % postfix_start
                _data[mac] = _n
                postfix_start += 1
                if name not in name_list:
                    name_list.append(name)

        req_data = {
            "handler": "WebTerminalHandler",
            "command": "modify_terminal_name",
            "data": _data
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "修改终端名称 %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal update name fail")
            return ret

        logger.info("terminal update name success!!!")
        return get_error_result("Success")

    def start_sort_terminal(self, data):
        group_uuid = data.get("group_uuid", "")
        start_num = data.get("index_start")

        if not (group_uuid and start_num) or not isinstance(start_num, int):
            logger.error("terminal sort number error: param error")
            return get_error_result("ParamError")

        # 判断组的存在
        group = self.get_object_by_uuid(YzyVoiGroup, group_uuid)
        if not group:
            logger.error("terminal sort number error: %s group not exist"% group_uuid)
            return get_error_result("TerminalWebGroupNotExist")

        req_data = {
            "handler": "WebTerminalHandler",
            "command": "terminal_order",
            "data": {
                "group_uuid": group_uuid,
                "start_num": start_num
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "分组 %s 终端排序" % group.name
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal update name fail")
            return ret

        logger.info("terminal sort number success!!! %s" % group.name)
        return ret

    def end_sort_terminal(self, data):
        """ 终止排序 """
        batch_num = data.get("batch_num", None)
        group_uuid = data.get("group_uuid", None)
        if not batch_num or not group_uuid:
            return get_error_result("ParamError")

        req_data = {
            "handler": "WebTerminalHandler",
            "command": "cancel_terminal_order",
            "data": {
                "group_uuid": group_uuid,
                "batch_num": batch_num
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "停止终端排序: %s" % batch_num
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal update name fail")
            return ret

        logger.info("terminal stop sort number success!!! %s" % batch_num)
        return ret

    def modify_ip_terminal(self, data):
        """ 按序重排ip
        """
        terminals = data.get("terminals", [])
        group_uuid = data.get("group_uuid", "")
        start_ip = data.get("start_ip")
        netmask = data.get("netmask")
        gateway = data.get("gateway")
        dns1 = data.get("dns1")
        dns2 = data.get("dns2")
        yzy_group = self.get_object_by_uuid(YzyVoiGroup, uuid=group_uuid)
        if not yzy_group:
            return get_error_result("ParameterError")
        if not is_ip_addr(start_ip):
            return get_error_result("IpAddressError")
        if not is_netmask(netmask)[0]:
            return get_error_result("SubnetMaskError")
        if not is_ip_addr(gateway):
            return get_error_result("GatewayError")
        if not is_ip_addr(dns1):
            return get_error_result("DnsAddressError")
        netmask_bits = is_netmask(netmask)[1]
        network_num = ipaddress.ip_interface(start_ip + '/' + str(netmask_bits)).network
        flag_a = ipaddress.ip_network(start_ip).compare_networks(ipaddress.ip_network(yzy_group.start_ip))
        flag_b = ipaddress.ip_network(start_ip).compare_networks(ipaddress.ip_network(yzy_group.end_ip))
        if flag_a == -1 or flag_b == 1:
            logger.error("terminal repeat modify ip param error: ip not in address segment")
            return get_error_result("IpAddressSegmentError")
        if ipaddress.IPv4Address(gateway) not in network_num:
            logger.error("terminal repeat modify ip param error: ip address and gateway not in same network segment")
            return get_error_result("GatewayAndIpError")
        terminal_count = len(self.get_all_object(YzyVoiTerminal, {"group_uuid": group_uuid}))
        if terminal_count == 0:
            logger.error("terminal repeat modify ip param error: no terminal this group")
            return get_error_result("TerminalGroupError")
        group_end_ip = ipaddress.IPv4Address(yzy_group.end_ip)
        ip_resources = [x for x in network_num.hosts() if ipaddress.IPv4Address(start_ip) <= x <= group_end_ip]
        if len(ip_resources) < terminal_count:
            logger.error("terminal repeat modify ip param error: IpResourcesError")
            return get_error_result("IpResourcesError")
        terminals = self.get_all_object(YzyVoiTerminal, {"group_uuid": group_uuid}).order_by("terminal_id")
        name_list = list()
        mac_list = list()
        for terminal in terminals:
            mac = terminal.mac
            name = terminal.name
            if mac not in mac_list:
                mac_list.append(mac)
            if name not in name_list:
                name_list.append(name)

        start_num = int(start_ip.split(".")[-1])
        end_num = start_num + len(terminals) - 1
        if end_num > 254:
            logger.error("terminal modify sort ip error")
            return get_error_result("TerminalSortIpError")
        _ip = start_ip.split(".")
        _ip[-1] = str(end_num)
        end_ip = ".".join(_ip)
        ips = find_ips(start_ip, end_ip)
        ips_str = ",".join(ips)
        mac_list_str = ",".join(mac_list)
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "modify_ip",
            "data": {
                "group_uuid": group_uuid,
                "mac_list": mac_list_str,
                "to_ip_list": ips_str,
                "mask": netmask,
                "gateway": gateway,
                "dns1": dns1,
                "dns2": dns2 if is_ip_addr(dns2) else ""
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command", req_data)
        msg = "终端重排IP: %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal repeat sort ip fail")
            return ret

        logger.info("terminal repeat sort ip success!!! %s" % ("/".join(name_list)))
        return ret

    def move_terminal(self, data):
        """ 移动终端
        "data": {
              "terminals": [
                  {"id":  1, "name":  "yzy-01"},
                  {"id":  2, "name":  "yzy-02"},
                  {"id":  3, "name":  "yzy-03"}
              ],
              "group_name": "503办公室",
              "group_uuid": "xxxx-xxx-xxx"
           }
        """
        # terminals = data.get("terminals", "")
        group_uuid = data.get("group_uuid", "")
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
        except Exception as e:
            logger.error("", exc_info=True)
            return get_error_result("ParamError")

        group = self.get_object_by_uuid(YzyVoiGroup, group_uuid)

        terminal_objs = self.get_all_object(YzyVoiTerminal, {"mac": mac_list})
        for terminal in terminal_objs:
            terminal.group_uuid = group_uuid
            terminal.save()
            request_data = {
                "new_group_uuid": group_uuid,
                "terminal_mac": terminal.mac
            }
            ret = server_post("/api/v1/voi/terminal/education/delete_desktop_bind", request_data)
            if ret.get('code') != 0:
                logger.info("delete old voi desktop bind records failed:%s", ret['msg'])
            else:
                logger.info("delete old voi desktop bind records success, mac:%s", request_data['terminal_mac'])
        ret = get_error_result("Success")
        msg = "移动终端: %s 到 %s 分组" % ("/".join(name_list), group.name if group else "未分组")
        insert_operation_log(msg, ret["msg"])
        logger.info("terminal move success !!!!" )
        return ret

    def enter_maintenance_mode_terminal(self, data):
        """ enter_maintenance_mode 终端 """
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
        except Exception as e:
            logger.error("", exc_info=True)
            logger.error(''.join(traceback.format_exc()))
            return get_error_result("ParamError")

        mac_list_str = ",".join(mac_list)
        # 提交终端服务接口
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "enter_maintenance_mode",
            "data": {
                "mac_list": mac_list_str,
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "enter_maintenance_mode 终端 %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal enter_maintenance_mode fail: %s"% mac_list_str)
            return ret

        logger.info("terminal enter_maintenance_mode success!!! %s"% mac_list_str)
        return get_error_result("Success")

    def clear_all_desktop_terminal(self, data):
        """ clear_all_desktop 终端 """
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
        except Exception as e:
            logger.error("", exc_info=True)
            logger.error(''.join(traceback.format_exc()))
            return get_error_result("ParamError")

        mac_list_str = ",".join(mac_list)
        # 提交终端服务接口
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "clear_all_desktop",
            "data": {
                "mac_list": mac_list_str,
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "clear_all_desktop 终端 %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal clear_all_desktop fail: %s"% mac_list_str)
            return ret

        logger.info("terminal clear_all_desktop success!!! %s"% mac_list_str)
        return get_error_result("Success")

    # def download_desktop_terminal(self, data):
    #     """ download_desktop 终端 """
    #     try:
    #         mac_list, name_list = self.get_terminal_mac_name_list(data)
    #     except Exception as e:
    #         logger.error("", exc_info=True)
    #         logger.error(''.join(traceback.format_exc()))
    #         return get_error_result("ParamError")
    #
    #     mac_list_str = ",".join(mac_list)
    #     # 提交终端服务接口
    #     req_data = {
    #         "handler": "WebTerminalHandler",
    #         "command": "download_desktop",
    #         "data": {
    #             "mac_list": mac_list_str,
    #         }
    #     }
    #     ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
    #     msg = "download_desktop 终端 %s" % "/".join(name_list)
    #     insert_operation_log(msg, ret["msg"])
    #     if ret.get("code", -1) != 0:
    #         logger.error("terminal download_desktop fail: %s"% mac_list_str)
    #         return ret
    #
    #     logger.info("terminal download_desktop success!!! %s"% mac_list_str)
    #     return get_error_result("Success")
    #
    # def cancel_download_desktop_terminal(self, data):
    #     """ cancel_download_desktop 终端 """
    #     try:
    #         mac_list, name_list = self.get_terminal_mac_name_list(data)
    #     except Exception as e:
    #         logger.error("", exc_info=True)
    #         logger.error(''.join(traceback.format_exc()))
    #         return get_error_result("ParamError")
    #
    #     mac_list_str = ",".join(mac_list)
    #     # 提交终端服务接口
    #     req_data = {
    #         "handler": "WebTerminalHandler",
    #         "command": "cancel_download_desktop",
    #         "data": {
    #             "mac_list": mac_list_str,
    #         }
    #     }
    #     ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
    #     msg = "cancel_download_desktop 终端 %s" % "/".join(name_list)
    #     insert_operation_log(msg, ret["msg"])
    #     if ret.get("code", -1) != 0:
    #         logger.error("terminal cancel_download_desktop fail: %s"% mac_list_str)
    #         return ret
    #
    #     logger.info("terminal cancel_download_desktop success!!! %s"% mac_list_str)
    #     return get_error_result("Success")

    def get_data_disk_setup_terminal(self, data):
        """ get_data_disk_setup 终端 """
        try:
            setup_info = data.get("setup_info", "")
            group_uuid = data.get("group_uuid", "")
            terminals = self.get_all_object(YzyVoiTerminal, {"group_uuid": group_uuid})
            name_list = list()
            mac_list = list()
            for terminal in terminals:
                mac = terminal.mac
                name = terminal.name
                if mac not in mac_list:
                    mac_list.append(mac)
                if name not in name_list:
                    name_list.append(name)
        except Exception as e:
            logger.error("", exc_info=True)
            logger.error(''.join(traceback.format_exc()))
            return get_error_result("ParamError")

        mac_list_str = ",".join(mac_list)
        # 提交终端服务接口
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "get_data_disk_setup",
            "data": {
                "mac_list": mac_list_str,
                "setup_info": setup_info,
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "get_data_disk_setup  %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal get_data_disk_setup fail: %s"% mac_list_str)
            return ret

        logger.info("terminal get_data_disk_setup success!!! %s"% mac_list_str)
        return get_error_result("Success")

    def update_data_disk_setup_terminal(self, data):
        """ update_data_disk_setup 终端 """
        try:
            setup_info = data.get("setup_info", "")
            group_uuid = data.get("group_uuid", "")
            terminals = self.get_all_object(YzyVoiTerminal, {"group_uuid": group_uuid})
            name_list = list()
            mac_list = list()
            for terminal in terminals:
                mac = terminal.mac
                name = terminal.name
                if mac not in mac_list:
                    mac_list.append(mac)
                if name not in name_list:
                    name_list.append(name)
        except Exception as e:
            logger.error("", exc_info=True)
            logger.error(''.join(traceback.format_exc()))
            return get_error_result("ParamError")

        mac_list_str = ",".join(mac_list)
        # 提交终端服务接口
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "update_data_disk_setup",
            "data": {
                "mac_list": mac_list_str,
                "setup_info": setup_info,
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "update_data_disk_setup 终端 %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal update_data_disk_setup fail: %s"% mac_list_str)
            return ret

        logger.info("terminal update_data_disk_setup success!!! %s"% mac_list_str)
        return get_error_result("Success")

    def send_desktop_terminal(self, data):
        """ 下发桌面
            {
                "cmd": "send_desktop",
                "data": {
                    "terminals": [
                        {"mac": "xxxxxx", "name": "xxxxxx"}
                    ],
                    "desktop_uuid": "xxxxxxxxx",
                    "desktop_name": "name"
                }
            }
        """

        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
        except Exception as e:
            logger.error("", exc_info=True)
            logger.error(''.join(traceback.format_exc()))
            return get_error_result("ParamError")

        mac_list_str = ",".join(mac_list)
        desktop_uuid = data.get("desktop_uuid", "")
        desktop_name = data.get("desktop_name", "")
        sys_reserve_size = data.get("sys_reserve_size", 20)
        data_reserve_size = data.get("sys_reserve_size", 20)

        desktop = self.get_object_by_uuid(YzyVoiDesktop, desktop_uuid)
        sys_base, data_base = self.get_node_storage()
        template = desktop.template
        devices = self.get_all_object(YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
        operates = self.get_all_object(YzyVoiTemplateOperate, {"template": template.uuid, "exist": 1})
        disks = list()
        for dev in devices:
            if dev.type == constants.IMAGE_TYPE_SYSTEM:
                _t = 0
                base_dir = sys_base
                restore_flag = desktop.sys_restore
                reserve_size_input = sys_reserve_size
            else:
                _t = 1
                restore_flag = desktop.data_restore
                base_dir = data_base
                reserve_size_input = data_reserve_size
            base_name = "voi_0_%s"% dev.uuid
            base_file = os.path.join(base_dir, base_name)
            real_size = str(dev.section) if dev.section else str(gi_to_section(dev.size))
            # reserve_size = str(bytes_to_section(os.path.getsize(base_file)))
            reserve_size = str(gi_to_section(100))
            disks.append({
                "uuid" : dev.uuid, "type": _t, "prefix": "voi", "dif_level": 0,
                "real_size":  real_size, "reserve_size": reserve_size,
                "torrent_file": base_file + ".torrent", "restore_flag": restore_flag, "max_dif": template.version
            })
            for oper in operates:
                disk_name = "voi_%s_%s"% (oper.version, dev.uuid)
                disk_path = os.path.join(base_dir, disk_name)
                # section = str(dev.section) if dev.section else str(dev.size * 1024 * 1024 * 2)
                # reserve_size = str(bytes_to_section(os.path.getsize(disk_path)) + gi_to_section(100)) # 加5G
                reserve_size = str(gi_to_section(100)) # 加5G
                disks.append({
                    "uuid": dev.uuid, "type": _t, "prefix": "voi", "dif_level": oper.version,
                    "real_size": real_size, "reserve_size": reserve_size,
                    "torrent_file": disk_path + ".torrent", "restore_flag": restore_flag, "max_dif": template.version
                })
        # 是否有数据盘
        share_disk_bind = self.get_all_object(YzyVoiShareToDesktops, {"desktop_uuid" : desktop_uuid}, False)
        if share_disk_bind:
            share_disk = self.get_object_by_uuid(YzyVoiTerminalShareDisk, share_disk_bind.disk_uuid)
            if share_disk and share_disk.enable:
                # back_dir =
                base_name = (constants.VOI_SHARE_BASE_PREFIX % share_disk.version) + share_disk.uuid
                base_file =  os.path.join(sys_base, base_name)
                reserve_size = str(bytes_to_section(os.path.getsize(base_file)))
                disks.append({
                    "uuid": share_disk.uuid, "type": 2, "prefix": "voi", "dif_level": 0,
                    "reserve_size": reserve_size, "real_size": str(gi_to_section(share_disk.disk_size)),
                    "torrent_file": base_file + ".torrent", "restore_flag" : share_disk.restore,
                    "max_dif": share_disk.version
                })

        # use_bottom_ip = desktop.use_bottom_ip
        # desktop_is_dhcp = 1
        # desktop_ip = ""
        # desktop_mask = ""
        # desktop_gateway = ""
        # desktop_dns1 = ""
        # desktop_dns2 = ""
        # if not use_bottom_ip:
        #     qry_temminal_desktops = self.get_all_object(YzyVoiTerminalToDesktops, {
        #         "desktop_group_uuid": desktop.uuid,
        #         "terminal_uuid": terminal_uuid
        #     })
        #     if qry_temminal_desktops:
        #         desktop_is_dhcp = qry_temminal_desktops.desktop_is_dhcp
        #         if not desktop_is_dhcp:
        #             desktop_ip = qry_temminal_desktops.desktop_ip
        #             desktop_mask = qry_temminal_desktops.desktop_mask
        #             desktop_gateway = qry_temminal_desktops.desktop_gateway
        #             desktop_dns1 = qry_temminal_desktops.desktop_dns1
        #             desktop_dns2 = qry_temminal_desktops.desktop_dns2

        _desktop = dict()
        _desktop.update({
            "desktop_group_name": desktop.name, "desktop_group_uuid": desktop.uuid,
            "desktop_group_status": int(desktop.active),
            "default_desktop_group": True if desktop.default else False,
            "os_sys_type": self.system_type_dict[desktop.os_type.lower()],
            "desktop_name": "%s-"% desktop.prefix,
            "template_uuid": template.uuid,
            "sys_restore": desktop.sys_restore,
            "data_restore": desktop.data_restore,
            "desktop_group_desc": template.desc,
            "desktop_is_dhcp": desktop.use_bottom_ip,
            "desktop_ip": "",
            "desktop_mask": "",
            "desktop_gateway": "",
            "desktop_dns1": "",
            "desktop_dns2": "",
        })
        _desktop["disks"] = disks
        # 提交终端服务接口
        fail_num = 0
        success_num = 0
        # for mac in mac_list:
        req_data = {
            "command": "send_desktop",
            "data": {
                "mac_list": mac_list_str,
                "desktop": _desktop
            }
        }

        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "下发桌面%s 终端 %s" %(desktop_name, "/".join(name_list))
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("send_desktop_terminal fail: %s, ret: %s" % (mac_list, ret))
            return ret

        logger.info("send_desktop_terminal success!!! %s, success: %s, fail: %s" % (mac_list_str, success_num, fail_num))
        return get_error_result("Success")

    def cancel_send_desktop_terminal(self, data):
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
        except Exception as e:
            logger.error("", exc_info=True)
            logger.error(''.join(traceback.format_exc()))
            return get_error_result("ParamError")

        mac_list_str = ",".join(mac_list)
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "cancel_send_desktop",
            "data": {
                "mac_list": mac_list_str,
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        msg = "cancel_send_desktop %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal close fail: %s"% mac_list_str)
            return ret

        logger.info("terminal close success!!! %s"% mac_list_str)
        return get_error_result("Success")

    def get_share_disk_terminal(self, data):
        """ 获取终端共享盘 """
        group_uuid = data.get("group_uuid", "")
        group = self.get_object_by_uuid(YzyVoiGroup, group_uuid)
        if not group:
            logger.error("get terminal share disk group %s not exist"% group_uuid)
            return get_error_result("TerminalWebGroupNotExist")
        desktops = self.get_all_object(YzyVoiDesktop, {"group": group_uuid})
        share_disk = self.get_all_object(YzyVoiTerminalShareDisk, {"group_uuid": group_uuid}, False)
        if not share_disk:
            # 如果共享盘不存在
            # 创建共享盘
            data = {
                "group_uuid": group_uuid,
                "disk_size": constants.VOI_SHARE_DISK_MIN,  # 共享盘大小
                "enable" : 0,    # 是否启用
                "restore": 0     # 还原与不还原
            }
            ret_json = server_post("/api/v1/voi/terminal/share_disk/create", data)
            if ret_json.get("code", -1) != 0:
                logger.error("get terminal share disk create fail group %s"% group_uuid)
                return ret_json
            data["uuid"] = ret_json["data"]["uuid"]
            share_desktop = list()
            for desktop in desktops:
                share_desktop.append({"name": desktop.name, "uuid": desktop.uuid, "choice": 0})
            data["share_desktop"] = share_desktop
            logger.info("get terminal share disk : {}  not exist" % data)
            # return get_error_result("Success", data=data)
        else:
            # 共享盘存在
            # 查找桌面绑定关系
            share_binds = self.get_all_object(YzyVoiShareToDesktops, {"disk_uuid": share_disk.uuid})
            share_desktop = list()
            for desktop in desktops:
                _d = {"name": desktop.name, "uuid": desktop.uuid, "choice": 0}
                for bind in share_binds:
                    if desktop.uuid == bind.desktop_uuid:
                        _d["choice"] = 1
                share_desktop.append(_d)
            data = {
                "uuid": share_disk.uuid,
                "group_uuid": group_uuid,
                "disk_size": share_disk.disk_size,
                "enable": share_disk.enable,
                "restore": share_disk.restore,
                "share_desktop": share_desktop
            }
            logger.info("get terminal share disk : {} exist" % data)
        return get_error_result("Success", data=data)

    def update_share_disk_terminal(self, data):
        """ 更新终端共享数据盘
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
        """
        disk_uuid = data.get("uuid", "")
        group_uuid = data.get("group_uuid", "")
        group = self.get_object_by_uuid(YzyVoiGroup, group_uuid)
        if not group:
            logger.error("get terminal share disk group %s not exist"% group_uuid)
            return get_error_result("TerminalWebGroupNotExist")
        desktops = self.get_all_object(YzyVoiDesktop, {"group": group_uuid})
        share_disk = self.get_all_object(YzyVoiTerminalShareDisk, {"group_uuid": group_uuid, "uuid": disk_uuid}, False)
        if not share_disk:
            logger.info("update terminal share disk : {}  not exist" % data)
            return get_error_result("VoiShareDiskNotExist")

        ret_json = server_post("/api/v1/voi/terminal/share_disk/update", data)
        if ret_json.get("code", -1) != 0:
            logger.error("update terminal share disk fail group %s" % data)
            return ret_json

        logger.info("update terminal share disk : {}" % data)
        return get_error_result("Success", data=data)


voi_terminal_mgr = VoiTerminalManager()
