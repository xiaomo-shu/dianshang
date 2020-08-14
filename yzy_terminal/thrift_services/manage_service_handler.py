import sys
import time
import json
import traceback
import logging
import datetime as dt
from functools import wraps
from flask import current_app
import common.errcode as errcode
from yzy_terminal.thrift_protocols.terminal import ManageService
from yzy_terminal.thrift_protocols.terminal.ttypes import *
from yzy_terminal.database import api as db_api
from yzy_terminal.redis_client import RedisClient
from yzy_terminal.thrift_protocols.terminal import ConnectService
import random
from yzy_terminal.http_client import HttpClient
from common.utils import is_ip_addr


def timefn(fn):
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        logging.debug("@timefn:" + fn.__name__ + " took " + str(t2 - t1) + " seconds")
        return result
    return measure_time


class ManageServiceHandler:
    def __init__(self, app):
        self.mac_token = app.mac_token
        self.token_status = app.token_status
        self.order_lock = app.order_lock
        self.app = app
        self.rds = RedisClient()
        self.http_client = HttpClient()

    def mac_to_oprot(self, mac):
        with self.app.app_context():
            if mac not in current_app.mac_token.keys():
                logging.debug("mac not in cache {}".format(current_app.mac_token.keys()))
                return False
            token_id = current_app.mac_token[mac]
            if token_id not in current_app.token_client.keys():
                logging.debug("token_id not in cache {}".format(current_app.token_client.keys()))
                return False
            if token_id not in current_app.token_status.keys():
                logging.debug("token_id is not in {}".format(current_app.token_status.keys()))
                return False
            return current_app.token_client[token_id]

    def send_thrift_cmd(self, mac, cmd):
        try:
            oprot = self.mac_to_oprot(mac)
            if not oprot:
                return False
            conn_client = ConnectService.Client(oprot)
            conn_client.Command(cmd)
            return True
        except Exception as err:
            logging.error("exception {}".format(err))
            return False

    def combine_terminal_conf(self, table_data):
        try:
            terminal_conf = TerminalConf()
            terminal_conf.terminal_id = table_data['terminal_id']
            terminal_conf.mac = table_data['mac']
            terminal_conf.ip_info = IPInfo()
            terminal_conf.ip_info.Mac = table_data['mac']
            terminal_conf.ip_info.Ip = table_data['ip']
            terminal_conf.ip_info.Subnet = table_data['mask']
            terminal_conf.ip_info.Gateway = table_data['gateway']
            terminal_conf.ip_info.DNS1 = table_data['dns1']
            terminal_conf.ip_info.DNS2 = table_data['dns2']
            terminal_conf.ip_info.IsDhcp = int(table_data['is_dhcp'])
            terminal_conf.terminal_name = table_data['name']
            terminal_conf.platform = table_data['platform']
            terminal_conf.soft_version = table_data['soft_version']
            terminal_conf.conf_version = int(table_data['conf_version'])
            setup_info = json.loads(table_data['setup_info'])

            mode = setup_info['mode']
            terminal_conf.show_desktop_type = mode['show_desktop_type']
            terminal_conf.auto_desktop = mode['auto_desktop']
            terminal_conf.close_desktop_strategy = mode['close_desktop_strategy']
            terminal_conf.close_terminal_strategy = mode['close_terminal_strategy']
            terminal_conf.open_strategy = mode['open_strategy']

            program = setup_info['program']
            terminal_conf.server_info = ServiceInfo()
            terminal_conf.server_info.Ip = program['server_ip']
            terminal_conf.server_info.Port = program['server_port']
            terminal_conf.screen_info_list = []
            terminal_conf.screen_info_list = [ScreenInfo(int(element.split('*')[0]), int(element.split('*')[1]))
                for element in program['screen_info_list'].split(',')]
            terminal_conf.current_screen_info = ScreenInfo()
            terminal_conf.current_screen_info.Width = program['current_screen_info']['width']
            terminal_conf.current_screen_info.Height = program['current_screen_info']['height']
            terminal_conf.show_modify_user_passwd = program['show_modify_user_passwd']
            terminal_conf.terminal_setup_passwd = program['terminal_setup_passwd']

            windows = setup_info['windows']
            terminal_conf.window_mode = windows['window_mode']
            terminal_conf.disconnect_setup = DisconnectSetup()
            terminal_conf.disconnect_setup.goto_local_desktop = windows['disconnect_setup']['goto_local_desktop']
            terminal_conf.disconnect_setup.goto_local_auth = windows['disconnect_setup']['goto_local_auth']
            terminal_conf.show = DisplaySetup()
            terminal_conf.show.show_local_button = windows['show']['show_local_button']
            terminal_conf.show.goto_local_passwd = windows['show']['goto_local_passwd']
        except Exception as err:
            logging.error('err {}'.format(err))
            logging.error(''.join(traceback.format_exc()))
            return None
        return terminal_conf

    def set_default_terminal_info(self, mac):
        setup_info = {
            'mode': {
                'show_desktop_type': 0,
                'auto_desktop': 0,
                'close_desktop_strategy': False,
                'close_terminal_strategy': False,
                'open_strategy': False 
            },
            'program': {
                'server_ip': "",
                'server_port': 9999,
                'screen_info_list': [],
                'current_screen_info': {
                    'width': 0,
                    'height': 0
                 },
                'show_modify_user_passwd': False,
                'terminal_setup_passwd': "" 
            },
            'windows': {
                'window_mode': 1,
                'disconnect_setup': {
                    'goto_local_desktop': 0,
                    'goto_local_auth':False 
                },
                'show': {
                    'show_local_button': False,
                    'goto_local_passwd': "" 
                }
            }
        }
        terminal_values = {
            'terminal_id': 1,
            'mac': mac,
            'ip': "",
            'mask': "",
            'gateway': "",
            'dns1': "",
            'dns2': "",
            'is_dhcp': 0,
            'name': "",
            'platform': "",
            'soft_version': "",
            'status': '1',
            'register_time': dt.datetime.now(),
            'conf_version': "-1",
            'setup_info': json.dumps(setup_info),
        }
        return terminal_values
 

    @timefn
    def ClientLogin(self, token_id, hard_info):
        logging.debug('Terminal request: token_id {},hard_info {} '.format(token_id, hard_info))
        if not bool(len(token_id)) or not bool(len(hard_info.MacAddress)):
            logging.error("request parameter error")
            return False
        try:
            self.mac_token[hard_info.MacAddress] = token_id
            self.token_status[token_id] = True
            # set terminal status to offline
            with self.app.app_context():
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry = table_api.select_terminal_by_mac(hard_info.MacAddress)
                if qry:
                    table_api.update_terminal_by_mac(**{'mac': hard_info.MacAddress, 'status': '1'})
                    logging.debug('mac: {} set online'.format(hard_info.MacAddress))
                else:
                    terminal_values = self.set_default_terminal_info(hard_info.MacAddress)
                    table_api.add_terminal(terminal_values)
                    logging.debug('mac: {} add new default yzy_terminal record'.format(hard_info.MacAddress))
            logging.debug("Return terminal: True")
            return True
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            logging.debug("Return terminal: False")
            return False

    @timefn
    def user_login(self, user, mac):
        logging.debug('Terminal request: user {},mac {} '.format(user, mac))
        try:
            request_data = {
                "user_name": user.user_name,
                "password": user.user_passwd,
                "mac": mac
            }
            request_url = "/api/v1/terminal/personal/login"
            logging.debug("request yzy_server {}, {}".format(request_url, request_data))
            server_ret = self.http_client.post(request_url, request_data)
            logging.debug("get yzy_server {}, {},".format(request_url, server_ret))
            if server_ret.get("code", -1) == 0:
                description = {
                    'session_id': server_ret["data"]["session_id"],
                    'phone': server_ret["data"]["phone"],
                    'email': server_ret["data"]["email"],
                    'name': server_ret["data"]["user_name"],
                }
                # single mac login, send old mac logout notice
                old_mac = server_ret["data"].get("old_mac", None)
                if old_mac:
                    cmd_msg = CommandMsg()
                    cmd_msg.cmdstr = 'user_logout'
                    cmd_msg.BodyType = CommandBodyType.TEXT
                    cmd_msg.Body = "Command:%s" % cmd_msg.cmdstr
                    ret = self.send_thrift_cmd(old_mac, cmd_msg)
                    if ret:
                        logging.debug("send user_logout cmd {},".format(old_mac))
                        pass
                ret = ResultInfo(str(server_ret["code"]), server_ret["msg"],
                                 str(json.dumps(description).encode('utf-8'), encoding='utf-8'))
                logging.debug("Return terminal: ret = {}".format(ret))
                return ret
            else:
                logging.error("return code: {}, message: {}".format(server_ret["code"], server_ret["msg"]))
                ret = ResultInfo(str(server_ret["code"]), server_ret["msg"], "")
                logging.debug("Return terminal: ret = {}".format(ret))
                return ret
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            err_info = errcode.get_error_result("OtherError")
            ret = ResultInfo(str(err_info["code"]), err_info["msg"], "")
            logging.debug("Return terminal: ret = {}".format(ret))
            return ret

    @timefn
    def user_logout(self, user_session_id):
        logging.debug('Terminal request: user_session_id {}'.format(user_session_id))
        try:
            request_data = {'session_id': user_session_id}
            request_url = "/api/v1/terminal/personal/logout"
            logging.debug("request yzy_server {}, {}".format(request_url, request_data))
            server_ret = self.http_client.post(request_url, request_data)
            logging.debug("get yzy_server {}, {}".format(request_url, server_ret))
            if server_ret.get("code", -1) == 0:
                ret = ResultInfo(str(server_ret["code"]), server_ret["msg"], "")
                logging.debug("Return terminal: ret = {}".format(ret))
                return ret
            else:
                logging.error("return code: {}, message: {}".format(server_ret["code"], server_ret["msg"]))
                ret = ResultInfo(str(server_ret["code"]), server_ret["msg"], "")
                logging.debug("Return terminal: ret = {}".format(ret))
                return ret
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            err_info = errcode.get_error_result("OtherError")
            ret = ResultInfo(str(err_info["code"]), err_info["msg"], "")
            logging.debug("Return terminal: ret = {}".format(ret))
            return ret

    @timefn
    def user_modify_passwd(self, old_user, new_user):
        logging.debug("Terminal request: old_user {}, new_user {}".format(old_user, new_user))
        try:
            request_data = {
                "user_name": old_user.user_name,
                "password": old_user.user_passwd,
                "new_password": new_user.user_passwd
            }
            request_url = "/api/v1/terminal/personal/change_pwd"
            logging.debug("request yzy_server {}, {}".format(request_url, request_data))
            server_ret = self.http_client.post(request_url, request_data)
            logging.debug("get yzy_server {}, {},".format(request_url, server_ret))
            if server_ret.get("code", -1) == 0:
                ret = ResultInfo(str(server_ret["code"]), server_ret["msg"], "")
                logging.debug("Return terminal: ret = {}".format(ret))
                return ret
            else:
                logging.error("return code: {}, message: {}".format(server_ret["code"], server_ret["msg"]))
                ret = ResultInfo(str(server_ret["code"]), server_ret["msg"], "")
                logging.debug("Return terminal: ret = {}".format(ret))
                return ret
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            err_info = errcode.get_error_result("OtherError")
            ret = ResultInfo(str(err_info["code"]), err_info["msg"], "")
            logging.debug("Return terminal: ret = {}".format(ret))
            return ret

    @timefn
    def get_dskgrop_info(self, mac, user_session_id):
        logging.debug("Terminal request: mac {}, user_session_id {}".format(mac, user_session_id))
        desktop_group_list = []
        if not (len(mac) or len(user_session_id)):
            logging.error("request parameter error")
            return desktop_group_list
        # verify mac and get id and ip, if not exists return directly
        try:
            with self.app.app_context():
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry = table_api.select_terminal_by_mac(mac)
                if qry:
                    logging.debug("qry.mac {}, qry.ip {}, user_session_id {}".format(qry.mac, qry.ip, user_session_id))
                    server_ret = {}
                    if len(user_session_id) > 0:  # user scene
                        request_data = {
                            "session_id": user_session_id
                        }
                        request_url = "/api/v1/terminal/personal/person_desktops"
                        logging.debug("request yzy_server {}, {}".format(request_url, request_data))
                        server_ret = self.http_client.post(request_url, request_data)
                    else:  # classroom scene
                        request_data = {
                            "terminal_id": qry.terminal_id,
                            "terminal_ip": qry.ip
                        }
                        request_url = "/api/v1/terminal/education/edu_desktops"
                        logging.debug("request yzy_server {}, {}".format(request_url, request_data))
                        server_ret = self.http_client.post(request_url, request_data)
                    logging.debug("get yzy_server {} {},".format(request_url, server_ret))
                    if server_ret.get("code", -1) == 0:
                        ret_data = server_ret['data']
                        for desktop_group in ret_data:
                            desktop_group_list.append(
                                DesktopGroupInfo(desktop_group['name'],
                                                 desktop_group['order_num'],
                                                 desktop_group['desc'],
                                                 desktop_group['uuid'],
                                                 desktop_group['os_type']))
                    else:
                        logging.error("return code: {}, message: {}".format(server_ret["code"], server_ret["msg"]))
                logging.debug("Return terminal: desktop_group_list = {}".format(desktop_group_list))
                return desktop_group_list
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            logging.debug("Return terminal: desktop_group_list = {}".format(desktop_group_list))
            return desktop_group_list

    @timefn
    def get_desktop_info(self):
        logging.debug("Terminal request: get_desktop_info API")
        terminal_info_list = []
        terminal_desktop_list = []
        try:
            # select all terminal info from yzy_terminal
            with self.app.app_context():
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry_list = table_api.select_all_terminal()
                for qry in qry_list:
                    terminal_info_list.append({'terminal_mac': qry.mac, 'terminal_id': qry.terminal_id,
                                               'terminal_ip': qry.ip})
            # request yzy_server get desktop_ip
            if len(terminal_info_list) > 0:
                request_data = terminal_info_list
                request_url = "/api/v1/terminal/instance/list"
                logging.debug("request yzy_server {}, {}".format(request_url, request_data))
                server_ret = self.http_client.post(request_url, request_data)
                logging.debug("get yzy_server {}, {},".format(request_url, server_ret))
                if server_ret.get("code", -1) == 0:
                    ret_data = server_ret['data']
                    for element in ret_data:
                        terminal_desktop_list.append(TerminalDesktopInfo(element['terminal_id'], element['terminal_mac'],
                                                                         element['terminal_ip'], element['desktop_ip']))
                else:
                    logging.error("return code: {}, message: {}".format(server_ret["code"], server_ret["msg"]))
            return terminal_desktop_list
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            logging.debug("Return terminal: terminal_desktop_list = {}".format(terminal_desktop_list))
            return terminal_desktop_list

    @timefn
    def desktop_open(self, desktop_group_info, mac, user_session_id):
        logging.debug("Terminal request: mac = {}, session_id = {}, dsk_group_info = {} "
                     .format(mac, user_session_id, desktop_group_info))
        dsk_info = DesktopInfo()
        dsk_info.group = desktop_group_info
        if not bool(len(mac)) or not bool(len(desktop_group_info.group_uuid)) or \
                not bool(len(desktop_group_info.group_name)):
            err_info = errcode.get_error_result("RequestParamError")
            ret = RespDesktopInfo(code=str(err_info['code']), msg=err_info['msg'], dsk_info=dsk_info)
            logging.debug("Return terminal: ret = {}".format(ret))
            return ret
        # 1. request yzy_server start vm and get DesktopInfo
        # verify mac and get id and ip, if not exists return directly
        try:
            with self.app.app_context():
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry = table_api.select_terminal_by_mac(mac)
                if qry:
                    logging.debug("qry.mac {}, qry.ip {}, user_session_id {}".format(qry.mac, qry.ip, user_session_id))
                    server_ret = {}
                    if len(user_session_id) > 0:  # user scene
                        request_data = {
                            "session_id": user_session_id,
                            "desktop_uuid": desktop_group_info.group_uuid,
                            "desktop_name": desktop_group_info.group_name
                        }
                        request_url = "/api/v1/terminal/personal/instance"
                        logging.debug("request yzy_server {}, {}".format(request_url, request_data))
                        server_ret = self.http_client.post(request_url, request_data)
                    else:  # classroom scene
                        request_data = {
                            "terminal_id": qry.terminal_id,
                            "ip": qry.ip,
                            "mac": mac,
                            "desktop_uuid": desktop_group_info.group_uuid,
                            "desktop_name": desktop_group_info.group_name
                        }
                        request_url = "/api/v1/terminal/education/instance"
                        logging.debug("request yzy_server {}, {}".format(request_url, request_data))
                        server_ret = self.http_client.post(request_url, request_data)
                    # combine dsk_info msg
                    logging.debug("get yzy_server return {}, {}".format(request_url, server_ret))
                    if server_ret.get("code", -1) == 0:
                        ret_data = server_ret['data']
                        dsk_info.dsk_type = "kvm"
                        dsk_info.group = desktop_group_info
                        dsk_info.status = 1  # 1-running 0-closed
                        dsk_info.dsk_user = UserInfo("", "")
                        dsk_info.ip = ret_data['spice_host']
                        dsk_info.port = int(ret_data['spice_port'])
                        dsk_info.token = ret_data['spice_token']
                        dsk_info.desktop_name = ret_data['name']
                        dsk_info.os_type = ret_data['os_type']
                        dsk_info.dsk_uuid = ret_data['uuid']
                    else:
                        logging.error("return code: {}, message: {}".format(server_ret["code"], server_ret["msg"]))
                    ret = RespDesktopInfo(code=str(server_ret['code']), msg=server_ret['msg'], dsk_info=dsk_info)
                    logging.debug("Return terminal: ret = {}".format(ret))
                    return ret
                else:
                    err_info = errcode.get_error_result("TerminalConfigNotFound")
                    ret = RespDesktopInfo(code=str(err_info['code']), msg=err_info['msg'], dsk_info=dsk_info)
                    logging.debug("Return terminal: ret = {}".format(ret))
                    return ret
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            err_info = errcode.get_error_result("OtherError")
            ret = RespDesktopInfo(code=str(err_info['code']), msg=err_info['msg'], dsk_info=dsk_info)
            logging.debug("Return terminal: ret = {}".format(ret))
            return ret

    @timefn
    def desktop_close(self, desktop_info):
        logging.debug("Terminal request: desktop_info = {}".format(desktop_info))
        try:
            if not desktop_info.dsk_uuid:
                err_info = errcode.get_error_result("RequestParamError")
                ret = ResultInfo(code=str(err_info['code']), Message=err_info['msg'], Description="")
                return ret
            # 1. request yzy_server stop vm and get DesktopInfo
            request_data = {"desktop_uuid": desktop_info.dsk_uuid}
            request_url = "/api/v1/terminal/instance/close"
            logging.debug("request yzy_server {}, {}".format(request_url, request_data))
            server_ret = self.http_client.post(request_url, request_data)
            logging.debug("get yzy_server return {}, {}".format(request_url, server_ret))
            err_info = errcode.get_error_result()
            ret = ResultInfo(code=str(err_info['code']), Message=err_info['msg'], Description="")
            logging.debug("Return terminal: ret = {}".format(ret))
            return ret
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            err_info = errcode.get_error_result("OtherError")
            ret = ResultInfo(str(err_info["code"]), err_info["msg"], "")
            logging.debug("Return terminal: ret = {}".format(ret))
            return ret

    @timefn
    def all_desktop_close(self, mac, user_session_id):
        # 1. request yzy_server stop vm and get DesktopInfo
        logging.debug("Terminal request: mac {}, user_session_id {}".format(mac, user_session_id))
        # verify mac and get id and ip, if not exists return directly
        try:
            with self.app.app_context():
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry = table_api.select_terminal_by_mac(mac)
                if qry:
                    logging.debug("qry.mac {}, qry.ip {}, user_session_id {}".format(qry.mac, qry.ip, user_session_id))
                    server_ret = {}
                    if len(user_session_id) > 0:  # user scene
                        request_data = {
                            "session_id": user_session_id,
                            "mac": mac
                        }
                        request_url = "/api/v1/terminal/personal/close_instance"
                        logging.debug("request yzy_server {}, {}".format(request_url, request_data))
                        server_ret = self.http_client.post(request_url, request_data)
                    else:
                        request_data = {
                            "mac": mac
                        }
                        request_url = "/api/v1/terminal/education/close_instance"
                        logging.debug("request yzy_server {}, {}".format(request_url, request_data))
                        server_ret = self.http_client.post(request_url, request_data)
                    logging.debug("get yzy_server return {}, {}".format(request_url, server_ret))
                    ret = ResultInfo(code=str(server_ret['code']), Message=server_ret['msg'], Description="")
                    return ret
                else:
                    err_info = errcode.get_error_result("TerminalConfigNotFound")
                    ret = ResultInfo(code=str(err_info['code']), Message=err_info['msg'], Description="")
                    logging.debug("Return terminal: ret = {}".format(ret))
                    return ret
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            err_info = errcode.get_error_result("OtherError")
            ret = ResultInfo(code=str(err_info['code']), Message=err_info['msg'], Description="")
            logging.debug("Return terminal: ret = {}".format(ret))
            return ret

    @timefn
    def get_config_version(self, mac):
        logging.debug("Terminal request: mac {}".format(mac))
        version = -1
        try:
            with self.app.app_context():
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry = table_api.select_terminal_by_mac(mac)
                if qry:
                    version = int(qry['conf_version'])
                    logging.debug('version {}'.format(version))
        except Exception as err:
            logging.error('err {}'.format(err))
            logging.error(''.join(traceback.format_exc()))
        logging.debug("Return terminal: version = {}".format(version))
        return version

    @timefn
    def get_config(self, mac):
        logging.debug("Terminal request: mac {}".format(mac))
        terminal_conf = TerminalConf()
        try:
            with self.app.app_context():
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry = table_api.select_terminal_by_mac(mac)
                if qry:
                    logging.debug("qry.mac {}, qry.setup_info {}".format(qry.mac, qry.setup_info))
                    terminal_conf = self.combine_terminal_conf(qry)
                    terminal_conf.mac = mac
                    logging.debug('combine_terminal_conf {}'.format(terminal_conf))
        except Exception as err:
            logging.error('err {}'.format(err))
            logging.error(''.join(traceback.format_exc()))
        logging.debug("Return terminal: terminal_conf = {}".format(terminal_conf))
        return terminal_conf

    def check_config(self, client_info):
        try:
            err_info = errcode.get_error_result()
            ret = ResultInfo(code=str(err_info['code']), Message=err_info['msg'], Description="")
            terminal_info = client_info.TerminalConfInfo
            if terminal_info.terminal_id < 0 or \
                    len(terminal_info.mac) == 0 or \
                    not is_ip_addr(terminal_info.ip_info.Ip) or \
                    len(terminal_info.terminal_name) == 0 or \
                    len(terminal_info.platform) == 0 or \
                    len(terminal_info.soft_version) == 0 or \
                    terminal_info.show_desktop_type not in [0, 1, 2] or \
                    terminal_info.auto_desktop < 0 or \
                    not is_ip_addr(terminal_info.server_info.Ip) or \
                    len(terminal_info.screen_info_list) == 0 or \
                    terminal_info.current_screen_info.Height <= 0 or \
                    terminal_info.current_screen_info.Width <= 0 or \
                    terminal_info.conf_version < -2 or \
                    terminal_info.window_mode not in [1, 2, 3] or \
                    terminal_info.disconnect_setup.goto_local_desktop < -2:
                err_info = errcode.get_error_result("RequestParamError")
                ret = ResultInfo(code=str(err_info['code']), Message=err_info['msg'], Description="")
                return ret
        except Exception as err:
            logging.error('err {}'.format(err))
            logging.error(''.join(traceback.format_exc()))
            err_info = errcode.get_error_result("OtherError")
            ret = ResultInfo(code=str(err_info['code']), Message=err_info['msg'], Description="")
        return ret

    @timefn
    def update_config(self, client_info):
        logging.debug("Terminal request: client_info.TerminalConfInfo {}".format(client_info.TerminalConfInfo))
        try:
            ret = self.check_config(client_info)
            if ret.code != '0':
                logging.debug("Return terminal: ret = {}".format(ret))
                return ret
            terminal_info = client_info.TerminalConfInfo
            setup_info = {
                'mode': {
                    'show_desktop_type': terminal_info.show_desktop_type,
                    'auto_desktop': terminal_info.auto_desktop,
                    'close_desktop_strategy': terminal_info.close_desktop_strategy,
                    'close_terminal_strategy': terminal_info.close_terminal_strategy,
                    'open_strategy': terminal_info.open_strategy
                },
                'program': {
                    'server_ip': terminal_info.server_info.Ip,
                    'server_port': terminal_info.server_info.Port,
                    'screen_info_list': ','.join(["{}*{}".format(element.Width, element.Height)
                                                  for element in terminal_info.screen_info_list]),
                    'current_screen_info': {
                        'width': terminal_info.current_screen_info.Width,
                        'height': terminal_info.current_screen_info.Height
                     },
                    'show_modify_user_passwd': terminal_info.show_modify_user_passwd,
                    'terminal_setup_passwd': terminal_info.terminal_setup_passwd
                },
                'windows': {
                    'window_mode': terminal_info.window_mode,
                    'disconnect_setup': {
                        'goto_local_desktop': terminal_info.disconnect_setup.goto_local_desktop,
                        'goto_local_auth': terminal_info.disconnect_setup.goto_local_auth
                    },
                    'show': {
                        'show_local_button': terminal_info.show.show_local_button,
                        'goto_local_passwd': terminal_info.show.goto_local_passwd
                    }
                }
            }
            # get group_uuid
            group_uuid = None
            request_data = {'terminal_ip': terminal_info.ip_info.Ip}
            request_url = "/api/v1/terminal/education/group"
            logging.debug("request yzy_server {}, {}".format(request_url, request_data))
            server_ret = self.http_client.post(request_url, request_data)
            logging.debug("get yzy_server return {}, {}".format(request_url, server_ret))
            if server_ret.get("code", -1) == 0:
                ret_data = server_ret.get('data', None)
                if ret_data:
                    group_uuid = ret_data['uuid']
            else:
                logging.error("return code: {}, message: {}".format(server_ret["code"], server_ret["msg"]))
            terminal_values = {
                'terminal_id': terminal_info.terminal_id,
                'mac': terminal_info.mac,
                'ip': terminal_info.ip_info.Ip,
                'mask': terminal_info.ip_info.Subnet,
                'gateway': terminal_info.ip_info.Gateway,
                'dns1': terminal_info.ip_info.DNS1,
                'dns2': terminal_info.ip_info.DNS2,
                'is_dhcp': terminal_info.ip_info.IsDhcp,
                'name': terminal_info.terminal_name,
                'platform': terminal_info.platform,
                'soft_version': terminal_info.soft_version,
                'status': '1',
                'register_time': dt.datetime.now(),
                'conf_version': terminal_info.conf_version,
                'setup_info': json.dumps(setup_info),
                'group_uuid': group_uuid
            }
            terminal_update_values = terminal_values.copy()
            terminal_update_values.pop('register_time')
            logging.debug(terminal_update_values)
            err_info = errcode.get_error_result()
            ret = ResultInfo(code=str(err_info['code']), Message=err_info['msg'], Description="")
            with self.app.app_context():
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry = table_api.select_terminal_by_mac(terminal_info.mac)
                if qry:
                    if qry.group_uuid and not group_uuid:  # need to check personal group
                        request_data = {}
                        request_url = "/api/v1/terminal/personal/group"
                        logging.debug("request yzy_server {}, {}".format(request_url, request_data))
                        server_ret = self.http_client.post(request_url, request_data)
                        logging.debug("get yzy_server return {}, {}".format(request_url, server_ret))
                        if server_ret.get("code", -1) == 0:
                            ret_data = server_ret.get('data', None)
                            if ret_data and qry.group_uuid in ret_data['groups']:
                                terminal_update_values["group_uuid"] = qry.group_uuid
                    table_api.update_terminal_by_mac(**terminal_update_values)
                else:
                    table_api.add_terminal(terminal_values)
        except Exception as err:
            logging.error('err {}'.format(err))
            logging.error(''.join(traceback.format_exc()))
            err_info = errcode.get_error_result("OtherError")
            ret = ResultInfo(code=str(err_info['code']), Message=err_info['msg'], Description="")
        logging.debug("Return terminal: ret = {}".format(ret))
        return ret

    @timefn
    def GetDateTime(self):
        logging.debug('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
        return dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    #  返回值：-1表示非排序中 >=0 正在排序的号码
    @timefn
    def order_query(self, mac):
        logging.debug("Terminal request: mac {}".format(mac))
        # 1. search redis keys like "command:order:*"
        # 2. search "order_macs"
        # 3. return current_id
        cmd_msg = CommandMsg()
        cmd_msg.cmdstr = 'order'
        cmd_msg.BodyType = CommandBodyType.TEXT
        cmd_msg.Body = "Command:%s" % cmd_msg.cmdstr
        cmd_msg.ArgsDic = {'terminal_id': "-1"}
        try:
            # from mac get group_uuid
            with self.app.app_context():
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry = table_api.select_terminal_by_mac(mac)
                if not qry:
                    logging.debug("Mac not in yzy_terminal, Return terminal: CommandMsg = {}".format(cmd_msg))
                    return cmd_msg
            if self.rds.ping_server():
                order_key = 'command:order:{}:*'.format(qry.group_uuid)
                order_keys = self.rds.keys(order_key)
                batch_num = max([int(key.decode().split(':')[-1]) for key in order_keys]) if order_keys else 0
                key = 'command:order:{}:{}'.format(qry.group_uuid, batch_num)
                if batch_num:
                    json_data = self.rds.get(key)
                    data_dict = json.loads(json_data)
                    logging.debug("order_macs = {}".format(data_dict['order_macs']))
                    if mac in data_dict['order_macs']:
                        confirm_ids = [] if 0 == len(data_dict['confirm_ids']) else data_dict['confirm_ids'].split(',')
                        current_id = data_dict['current_id']
                        logging.debug("batch_num: {} current_id: {}".format(batch_num, current_id))
                        cmd_msg.ArgsDic['terminal_id'] = str(current_id)
                        cmd_msg.batch_num = batch_num
            else:
                logging.error('Redis server error')
                pass
        except Exception as err:
            logging.error('err {}'.format(err))
            logging.error(''.join(traceback.format_exc()))
        logging.debug("Return terminal: CommandMsg = {}".format(cmd_msg))
        return cmd_msg

    @timefn
    def command_confirm(self, cmd, mac):
        logging.debug("Terminal request: mac {}, cmd {}".format(mac, cmd))
        try:
            self.order_lock.acquire()
            # from mac get group_uuid
            with self.app.app_context():
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry = table_api.select_terminal_by_mac(mac)
                if not qry:
                    logging.debug("Mac not in yzy_terminal, Return terminal False")
                    return False
            # 1. search batch_num, mac
            logging.debug("Get mac {} cmd {}".format(mac, cmd))
            if self.rds.ping_server():
                order_key = 'command:order:{}:{}'.format(qry.group_uuid, cmd.batch_num)
                confirm_num = cmd.ArgsDic['terminal_id']
                json_data = self.rds.get(order_key)
                if json_data:
                    data_dict = json.loads(json_data)
                    macs = data_dict['order_macs'].split(',')
                    confirm_macs = [] if 0 == len(data_dict['confirm_macs']) else data_dict['confirm_macs'].split(',')
                    confirm_ids = [] if 0 == len(data_dict['confirm_ids']) else data_dict['confirm_ids'].split(',')
                    if int(confirm_num) < data_dict['start_id']:
                        logging.debug('order confirm_num {} little than start_id'.format(confirm_num, data_dict['start_id']))
                        self.order_lock.release()
                        logging.debug("Return terminal: False")
                        return False
                    elif mac not in macs:
                        logging.debug('mac {} not in order session macs {}'.format(mac, macs))
                        self.order_lock.release()
                        logging.debug("Return terminal: False")
                        return False
                    elif confirm_num in confirm_ids:
                        logging.debug('mac already ordered {}'.format(mac))
                        self.order_lock.release()
                        logging.debug("Return terminal: False")
                        return False
                    else:
                        macs.remove(mac)
                        confirm_macs.append(mac)
                        confirm_ids.append(confirm_num)
                        data_dict['order_macs'] = ','.join(macs)
                        data_dict['confirm_macs'] = ','.join(confirm_macs)
                        data_dict['confirm_ids'] = ','.join(confirm_ids)
                        data_dict['current_id'] = int(confirm_num) + 1
                        self.rds.set(order_key, json.dumps(data_dict))
                        logging.debug("confirm mac = {} , id = {} now redis data = {}".format(mac, confirm_num, data_dict))
                        # send order to other macs
                        cmd_msg = CommandMsg()
                        cmd_msg.cmdstr = 'order'
                        cmd_msg.BodyType = CommandBodyType.TEXT
                        cmd_msg.Body = "Command:%s" % cmd_msg.cmdstr
                        #next_terminal_id = data_dict['start_id']
                        next_terminal_id = data_dict['current_id']
                        while str(next_terminal_id) in confirm_ids:
                            next_terminal_id += 1
                        cmd_msg.batch_num = cmd.batch_num
                        cmd_msg.ArgsDic = {'terminal_id': str(next_terminal_id)}
                        for mac_name in macs:
                            self.send_thrift_cmd(mac_name, cmd_msg)
                else:
                    logging.error('Redis no key {}'.format(order_key))
                    self.order_lock.release()
                    logging.debug("Return terminal: False")
                    return False
            else:
                logging.error('Redis server error')
                self.order_lock.release()
                logging.debug("Return terminal: False")
                return False
            self.order_lock.release()
            logging.debug("Return terminal: True")
            return True
        except Exception as err:
            logging.error('err {}'.format(err))
            logging.error(''.join(traceback.format_exc()))
            logging.debug("Return terminal: False")
            self.order_lock.release()
            return False

