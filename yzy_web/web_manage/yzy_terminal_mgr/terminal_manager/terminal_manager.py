import os
import logging
import time
import json
import datetime
import tarfile
import ipaddress
import copy

from web_manage.yzy_edu_desktop_mgr.models import *
from web_manage.yzy_resource_mgr.models import YzyNodes
from web_manage.yzy_terminal_mgr.models import *
from web_manage.common.http import server_post, terminal_post
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common import constants
# from web_manage.common.utils import JSONResponse, YzyWebPagination, create_uuid
from web_manage.common.utils import get_error_result, JSONResponse, YzyWebPagination, is_ip_addr, is_netmask, find_ips,\
                                    size_to_M

logger = logging.getLogger(__name__)

count = 0

class TerminalManager(object):

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
            if all:
                return query.all()
            return query.first()

        except Exception as e:
            return []

    def get_terminal_mac_name_list(self, data):
        terminals = data.get("terminals", [])
        mac_list = list()
        name_list = list()
        for terminal in terminals:
            name = terminal["name"]
            mac = str(terminal["mac"])
            # status = terminal['status']
            if mac not in mac_list:
                mac_list.append(mac)
            if name not in name_list:
                name_list.append(name)
        if not mac_list:
            raise Exception("terminals not exist")
        return mac_list, name_list


    def get_group_info(self, uuid):
        return self.get_object_by_uuid(YzyGroup, uuid)

    def dict_to(self):
        pass

    def get_not_edu_group(self):
        groups = list()
        personal_groups = self.get_all_object(YzyGroup, {"group_type": constants.PERSONAL_TYPE})
        for group in personal_groups:
            groups.append({"uuid": group.uuid, "name": group.name})
        groups.append({"uuid":"", "name": "未分组"})
        return get_error_result("Success", groups)

    def get_all_group(self, group_type=None):
        if not group_type:
            groups = self.get_all_object(YzyGroup)
        else:
            groups = self.get_all_object(YzyGroup, {"group_type": group_type})

        terminals = self.get_all_object(YzyTerminal)
        data = list()
        sum = len(terminals)
        count = 0
        for group in groups:
            _d = {"name": group.name, "uuid": group.uuid, "type": group.group_type, "count": 0}
            for terminal in terminals:
                if terminal.group_uuid == group.uuid:
                    _d["count"] += 1
                    count += 1
            data.append(_d)
        data.sort(key=lambda x: x["type"])
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
                "auto_desktop":0,
                "close_desktop_strategy":true,
                "close_terminal_strategy" : true,
                "open_strategy":true
            },
            "program": {
                "screen_resolution": "1024*768",
                "server_ip": "172.16.1.33",
                "show_modify_user_passwd": true,
                "terminal_setup_passwd": "111111"
            },
            "windows":{
                "window_mode":2,
                "disconnect_setup":{
                    "goto_local_desktop":5
                },
                "show":{
                    "show_local_button":true,
                    "goto_local_passwd":"123456"
                }
            }
        }
        :param setup_info:
        :return:
        """
        if not setup_info:
            return False

        mode = setup_info.get("mode")
        program = setup_info.get("program")
        windows = setup_info.get("windows")
        if not (mode and program and windows):
            return False
        try:
            assert mode["show_desktop_type"] in (0, 1, 2), "show desktop type"
            assert mode["auto_desktop"] >= 0 , "auto desktop"
            assert isinstance(mode["close_desktop_strategy"], bool), "close desktop strategy"
            assert isinstance(mode["close_terminal_strategy"], bool), "close terminal strategy"
            assert isinstance(mode["open_strategy"], bool), "open strategy"
            assert is_ip_addr(program["server_ip"]), "server ip"
            assert isinstance(program["show_modify_user_passwd"], bool), "show modify user passwd"
            assert windows["window_mode"] in (1,2,3), "window mode"
            assert windows["disconnect_setup"]["goto_local_desktop"] >= -1, "goto local desktop"
            assert isinstance(windows["disconnect_setup"]["goto_local_auth"], bool), "goto local auth"
            # assert isinstance(windows["goto_local_auth"], bool), "goto local auth"
            assert isinstance(windows["show"]["show_local_button"], bool), "show local button"
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

    def shutdown_terminal(self, data):
        """ 关闭终端 """
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
        except Exception as e:
            logger.error("", exc_info=True)
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
        ret = terminal_post("/api/v1/terminal/task", req_data)
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
        ret = terminal_post("/api/v1/terminal/task", req_data)
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
        ret = terminal_post("/api/v1/terminal/task", req_data)
        msg = "删除终端 %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal close fail: %s"% mac_list_str)
            return get_error_result("TerminalCloseOperateError")

        logger.info("terminal delete success!!! %s"% mac_list_str)
        return get_error_result("Success")

    def get_setup_terminal(self, data):
        """ 设置终端配置接口 """
        terminals = data.get("terminals", [])
        if not terminals:
            logger.error("terminal setup get error: not terminal param")
            return get_error_result("ParamError")

        if len(terminals) == 1:
            terminal = terminals[0]
            terminal_mac = terminal["mac"]
            terminal_obj = self.get_all_object(YzyTerminal, {"mac": terminal_mac}, False)
            if not terminal_obj:
                logger.error("terminal setup get error: %s terminal not exist"% terminal_mac)
                return get_error_result("TerminalNotExistError")
            try:
                setup_info = json.loads(terminal_obj.setup_info)
            except:
                logger.error("terminal setup get error: setup_info  %s error"% terminal_obj.setup_info)
                return get_error_result("TerminalSetupInfoError")
            setup_info["program"]["screen_info_list"] = setup_info["program"]["screen_info_list"].split(",")
            current_screen_info = "%s*%s"% (setup_info["program"]["current_screen_info"]["width"],
                                            setup_info["program"]["current_screen_info"]["height"])
            setup_info["program"]["current_screen_info"] = current_screen_info
            setup_info["program"].pop("server_port")
            return get_error_result("Success", setup_info)
        else:
            mac_list = list()
            for terminal in terminals:
                mac = terminal["mac"]
                if mac not in mac_list:
                    mac_list.append(mac)
            terminal_objs = self.get_all_object(YzyTerminal, {"mac": mac_list}).order_by("-terminal_id")
            screen_info_list = list()
            current_screen_list = []
            server_ip = ""
            top_level_service_ip = None
            teacher_service_ip = None
            classroom_num = None
            multicast_ip = None
            multicast_port = None
            hide_tools = None
            try:
                for terminal in terminal_objs:
                    setup_info = json.loads(terminal.setup_info)
                    if setup_info.get('program') and hide_tools is None:
                        hide_tools = setup_info['program']['hide_tools']
                    if setup_info.get('teaching'):
                        if setup_info.get('teaching').get('top_level_service_ip') and top_level_service_ip is None:
                            top_level_service_ip = setup_info['teaching']['top_level_service_ip']
                        if setup_info.get('teaching').get('teacher_service_ip') and teacher_service_ip is None:
                            teacher_service_ip = setup_info['teaching']['teacher_service_ip']
                        if setup_info.get('teaching').get('classroom_num') and classroom_num is None:
                            classroom_num = setup_info['teaching']['classroom_num']
                        if setup_info.get('teaching').get('multicast_ip') and multicast_ip is None:
                            multicast_ip = setup_info['teaching']['multicast_ip']
                        if setup_info.get('teaching').get('multicast_port') and multicast_port is None:
                            multicast_port = setup_info['teaching']['multicast_port']
                    current_screen_list.append(setup_info['program']['current_screen_info'])
                    sceen_info = setup_info["program"]["screen_info_list"]
                    server_ip = setup_info["program"]["server_ip"]
                    for i in sceen_info.split(","):
                        if i not in screen_info_list:
                            screen_info_list.append(i)
            except Exception as e:
                logger.error("", exc_info=True)
                return get_error_result("TerminalSetupInfoError")

            current_screen_dict = {current_screen_list.count(current_screen): current_screen
                                   for current_screen in current_screen_list}
            current_screen_info = current_screen_dict[max(current_screen_dict.keys())]
            current_screen_info = "%s*%s" %(current_screen_info['width'], current_screen_info['height'])
            data = {
                "program": {
                    "current_screen_info": current_screen_info,
                    "screen_info_list": screen_info_list,
                    "server_ip": server_ip,
                    "hide_tools": hide_tools,
                },
                "teaching": {
                    "top_level_service_ip": top_level_service_ip,
                    "teacher_service_ip": teacher_service_ip,
                    "classroom_num": classroom_num,
                    "multicast_ip": multicast_ip,
                    "multicast_port": multicast_port
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
                    "auto_desktop": 1,
                    "open_strategy": true,
                    "close_desktop_strategy": false,
                    "close_terminal_strategy": true
                },
                "program": {
                    "screen_resolution": "1024*768",
                    "server_ip": "172.16.1.33",
                    "show_modify_user_passwd": true,
                    "terminal_setup_passwd": "111111"
                },
                "windows": {
                    "window_mode": 2,
                    "goto_local_desktop": 5,
                    "goto_local_auth": true,
                    "show_local_button": false,
                    "goto_local_passwd": "123456"
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
        ret = terminal_post("/api/v1/terminal/task", req_data)
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
        if not (terminals and perfix and postfix and postfix_start):
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
        ret = terminal_post("/api/v1/terminal/task", req_data)
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
        group = self.get_object_by_uuid(YzyGroup, group_uuid)
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
        ret = terminal_post("/api/v1/terminal/task", req_data)
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
        ret = terminal_post("/api/v1/terminal/task", req_data)
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
        terminals = data.get("terminals",[])

        modify_ip_method = data.get("modify_ip_method")
        group_uuid = data.get("group_uuid", "")
        if modify_ip_method == "dhcp":
            req_data = {
                "handler": "WebTerminalHandler",
                "command": "modify_ip",
                "data": {
                    "group_uuid": group_uuid,
                    "modify_ip_method": modify_ip_method,
                }
            }
            logger.debug("Use dhcp to modify group's %s terminals" % group_uuid)
            ret = terminal_post("/api/v1/terminal/task", req_data)
            return ret

        start_ip = data.get("start_ip")
        netmask = data.get("netmask")
        gateway = data.get("gateway")
        dns1 = data.get("dns1")
        dns2 = data.get("dns2")
        yzy_group = self.get_object_by_uuid(YzyGroup, uuid=group_uuid)
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
        terminal_count = len(self.get_all_object(YzyTerminal, {"group_uuid": group_uuid}))
        if terminal_count == 0:
            logger.error("terminal repeat modify ip param error: no terminal this group")
            return get_error_result("TerminalGroupError")
        group_end_ip = ipaddress.IPv4Address(yzy_group.end_ip)
        ip_resources = [x for x in network_num.hosts() if ipaddress.IPv4Address(start_ip) <= x <= group_end_ip]
        if len(ip_resources) < terminal_count:
            logger.error("terminal repeat modify ip param error: IpResourcesError")
            return get_error_result("IpResourcesError")
        terminals = self.get_all_object(YzyTerminal, {"group_uuid": group_uuid}).order_by("terminal_id")
        name_list = list()
        mac_list = list()
        ips = list()
        for terminal in terminals:
            mac = terminal.mac
            name = terminal.name
            if mac not in mac_list:
                mac_list.append(mac)
            if name not in name_list:
                name_list.append(name)
            ips.append(ip_resources[terminal.terminal_id - 1].exploded)

        # start_num = int(start_ip.split(".")[-1])
        # end_num = start_num + max(max_num) - 1
        # if end_num > 254:
        #     logger.error("terminal modify sort ip error")
        #     return get_error_result("TerminalSortIpError")
        # _ip = start_ip.split(".")
        # _ip[-1] = str(end_num)
        # end_ip = ".".join(_ip)
        # ips = find_ips(start_ip, end_ip)
        ips_str = ",".join(ips)
        mac_list_str = ",".join(mac_list)
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "modify_ip",
            "data": {
                "mac_list": mac_list_str,
                "to_ip_list": ips_str,
                "mask": netmask,
                "gateway": gateway,
                "dns1": dns1,
                "dns2": dns2 if is_ip_addr(dns2) else ""
            }
        }
        ret = terminal_post("/api/v1/terminal/task", req_data)
        msg = "终端重排IP: %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0:
            logger.error("terminal repeat sort ip fail")
            return ret

        logger.info("terminal repeat sort ip success!!! %s" % ("/".join(name_list) ))
        return ret

    def export_log_terminal(self, data):
        """ 终端日志导出 """
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
            if not mac_list:
                raise Exception("terminals not exist")
        except Exception as e:
            logger.error("", exc_info=True)
            return get_error_result("ParamError")

        if len(mac_list) > 5:
            logger.error("terminal log export error: %s too much!"% (len(mac_list)))
            return get_error_result("TerminalLogFiveLimitError")
        success_num = 0
        fail_num = 0
        today_date = datetime.datetime.now()
        start_date = (today_date + datetime.timedelta(days=-7)).strftime("%Y-%m-%d")
        c_mac_list = copy.deepcopy(mac_list)
        for i in mac_list:
            terminal = YzyTerminal.objects.filter(deleted=False, mac=i).first()
            if terminal.status == '0':
                c_mac_list.remove(i)
                fail_num += 1
                continue
            file_name = "%s_%s.ok"% (i, start_date)
            file_path = os.path.join(constants.TERMINAL_LOG_PATH, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
        targe_file = os.path.join(constants.TERMINAL_LOG_PATH, "%s.tar.gz"% today_date.strftime("%Y-%m-%d"))
        if os.path.exists(targe_file):
            os.remove(targe_file)
        if len(c_mac_list) == 0:
            success_num += len(c_mac_list)
            ret = get_error_result("Success")
            ret['msg'] = '批量导出日志' + ret['msg'] + ': {}, 失败: {}'.format(success_num, fail_num)
            return ret
        req_data = {
            "handler": "WebTerminalHandler",
            "command": "get_log_file",
            "data": {
                "mac_list": ",".join(c_mac_list),
                "start_date": start_date,
                "end_date": today_date.strftime("%Y-%m-%d")
            }
        }
        ret = terminal_post("/api/v1/terminal/task", req_data)
        msg = "导出终端日志: %s" % "/".join(name_list)
        insert_operation_log(msg, ret["msg"])
        if ret.get("code", -1) != 0 :
            logger.error("terminal log export error: %s"% ret["msg"])
            return ret

        logger.info("terminal export log success!!! %s" % ("/".join(name_list)))
        success_num += len(c_mac_list)
        ret = get_error_result("Success")
        ret['msg'] = '批量导出日志' + ret['msg'] + ': {}, 失败: {}'.format(success_num, fail_num)
        return ret

    def poll_log_terminal(self, data):
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
            if not mac_list:
                raise Exception("terminals not exist")
        except Exception as e:
            logger.error("", exc_info=True)
            return get_error_result("ParamError")
        start_date = datetime.datetime.now().strftime("%Y-%m-%d")
        log_dir = constants.TERMINAL_LOG_PATH
        for mac in mac_list:
            terminal = YzyTerminal.objects.filter(deleted=False, mac=mac).first()
            if terminal.status == '0':
                continue
            ok_file = os.path.join(log_dir, "%s_%s.ok"% (mac,start_date))
            if not os.path.exists(ok_file):
                return get_error_result("TerminalLogNotExist")
        # 打包日志
        tar_file = "%s.tar.gz"% start_date
        tar_file_path = os.path.join(constants.TERMINAL_LOG_PATH, tar_file)
        tar = tarfile.open(tar_file_path, "w:gz")
        for mac in mac_list:
            log_file = os.path.join(log_dir, "%s_%s.zip"% (mac, start_date))
            if os.path.exists(log_file):
                tar.add(log_file)
        tar.close()
        # 查找主控节点
        host = self.get_all_object(YzyNodes, {"type": [1,3]}, False)

        down_url = "http://%s:%s/api/v1.0/terminal_mgr/terminal_log/?file=%s"%(host.ip, constants.WEB_DEFAULT_PORT, tar_file)
        return get_error_result("Success", {"down_url": down_url})

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
        if not group_uuid:
            group_uuid = None
        try:
            mac_list, name_list = self.get_terminal_mac_name_list(data)
        except Exception as e:
            logger.error("", exc_info=True)
            return get_error_result("ParamError")

        group = self.get_object_by_uuid(YzyGroup, group_uuid)
        # if not group:
        #     logger.error("terminal move error : %s group not exist"% group_uuid)
        #     return get_error_result("TerminalWebGroupNotExist")
        if group and group.group_type != constants.PERSONAL_TYPE:
            logger.error("terminal move error : %s group not peronal group"% group_uuid)
            return get_error_result("TerminalNotPersonalGroupError")

        terminal_objs = self.get_all_object(YzyTerminal, {"mac": mac_list})
        for terminal in terminal_objs:
            terminal.group_uuid = group_uuid
            terminal.save()
        ret = get_error_result("Success")
        msg = "移动终端: %s 到 %s 分组" % ("/".join(name_list), group.name if group else "未分组")
        insert_operation_log(msg, ret["msg"])
        logger.error("terminal move success !!!!" )
        return ret

    # def terminal_log_download(self, request):
    #     _file = request.GET.get("file", "")
    #     if not os.path.exists(_file):
    #         return get_error_result("OtherError")

    def upgrade_terminal(self, data):
        """ 终端升级 """
        all = data.get("all")
        group_uuid = data.get("group_uuid")
        upgrade_uuid = data.get("upgrade_uuid")
        upgrade = self.get_object_by_uuid(YzyTerminalUpgrade, upgrade_uuid)
        if all:
            terminals = self.get_all_object(YzyTerminal, {"group_uuid": group_uuid})
            mac_list = list()
            name_list = list()
            for terminal in terminals:
                mac = terminal.mac
                if upgrade.platform == terminal.platform:
                    if mac not in mac_list:
                        mac_list.append(mac)
                    name_list.append(terminal.name)
        else:
            try:
                mac_list, name_list = self.get_terminal_mac_name_list(data)
            except Exception as e:
                logger.error("", exc_info=True)
                return get_error_result("ParamError")
            terminals = self.get_all_object(YzyTerminal, {"mac": mac_list})
            for terminal in terminals:
                if terminal.platform.lower() != upgrade.platform.lower():
                    mac_list.remove(terminal.mac)
        if not mac_list:
            logger.error("NO need upgrade terminals")
            return get_error_result("TerminalUpgradeNotNeedError")

        upgrade_pig = upgrade.path
        if not os.path.exists(upgrade_pig):
            return get_error_result("TerminalUpgradeFileError")

        req_data = {
            "handler": "WebTerminalHandler",
            "command": "update_program",
            "data": {
                "mac_list": ",".join(mac_list),
                "program_file_name": os.path.basename(upgrade_pig)
            }
        }
        ret = terminal_post("/api/v1/terminal/task", req_data)
        # msg = "移动终端: %s 到 %s 分组" % ("/".join(name_list), group.name)
        # insert_operation_log(msg, ret["msg"])

        if ret.get("code", -1) != 0 :
            logger.error("terminal upgrade error: %s"% ret["msg"])
            return ret

        logger.info("terminal upgrade success!!! %s" % ("/".join(name_list)))
        return get_error_result("Success")

    def upload_upgrade(self, upgrade_uuid, file_obj):
        upgrade = self.get_object_by_uuid(YzyTerminalUpgrade, upgrade_uuid)
        if not upgrade:
            logger.error("upload upgrade error: %s not exist"% upgrade_uuid)
            return get_error_result("ParamError")

        file_name = file_obj.name
        # 判断文件名称
        try:
            platform, os_name, version = os.path.splitext(file_name)[0].split("_")
            if platform.lower() not in ("arm", "x86") or platform.lower() != str(upgrade.platform).lower():
                raise Exception("platform not in arm or x86")
            if os_name.lower() not in ("windows", "linux") or os_name.lower() != str(upgrade.os).lower():
                raise Exception("os error : %s"% os_name)

        except Exception as e:
            logger.error("", exc_info=True)
            return get_error_result("TerminalUpgradeNameError")

        if upgrade.path and os.path.exists(upgrade.path):
            os.remove(upgrade.path)
        upgrade_dir = constants.TERMINAL_UPGRADE_PATH
        if not os.path.exists(upgrade_dir):
            try:
                os.makedirs(upgrade_dir)
            except Exception as e:
                logger.error("", exc_info=True)
                return get_error_result("OtherError")
        file_path = os.path.join(constants.TERMINAL_UPGRADE_PATH, file_name)
        # else:
        #     file_path = upgrade.path
        size = 0
        with open(file_path, "wb+") as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
                size += len(chunk)
            f.close()
        # 更新数据库
        upgrade.version = version
        upgrade.path = file_path
        upgrade.size = size_to_M(size)
        upgrade.upload_at = datetime.datetime.now()
        upgrade.save()
        # upgrade.os = os_name
        return get_error_result("Success")

    def check_start_ip_terminal(self, data):
        start_ip = data.get('start_ip')
        if not is_ip_addr(start_ip):
            return get_error_result("IpAddressError")
        group_uuid = data.get("group_uuid", "")
        yzy_group = self.get_object_by_uuid(YzyGroup, uuid=group_uuid)
        if not yzy_group:
            return get_error_result("ParameterError")
        flag_a = ipaddress.ip_network(start_ip).compare_networks(ipaddress.ip_network(yzy_group.start_ip))
        flag_b = ipaddress.ip_network(start_ip).compare_networks(ipaddress.ip_network(yzy_group.end_ip))
        if flag_a == -1 or flag_b == 1:
            logger.error("terminal repeat modify ip param error: ip not in address segment")
            return get_error_result("IpAddressSegmentError")
        return get_error_result("Success")


terminal_mgr = TerminalManager()
