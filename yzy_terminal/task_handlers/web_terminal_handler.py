import os
import logging
import time
import datetime as dt
import json
import traceback
from functools import wraps
from flask import current_app
import common.errcode as errcode
from yzy_terminal.task_handlers.base_handler import BaseHandler, BaseProcess
from yzy_terminal.thrift_protocols.terminal.ttypes import *
from yzy_terminal.database import api as db_api
from common.utils import is_ip_addr, is_netmask
from common.config import SERVER_CONF


def timefn(fn):
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        logging.debug("@timefn:" + fn.__name__ + " took " + str(t2 - t1) + " seconds")
        return result
    return measure_time


class WebTerminalHandler(BaseHandler):
    def __init__(self):
        super(WebTerminalHandler, self).__init__()
        self.type = "WebTerminalHandler"

    def deal(self, task):
        p = WebTerminalHandlerProcess(task)
        r = p.process()
        return r


class WebTerminalHandlerProcess(BaseProcess):
    def __init__(self, task):
        super(WebTerminalHandlerProcess, self).__init__(task)
        self.name = os.path.basename(__file__).split('.')[0]

    # shutdown terminal
    @timefn
    def shutdown(self):
        try:
            resp = errcode.get_error_result()
            cmd_msg = CommandMsg()
            cmd_msg.cmdstr = 'shutdown'
            cmd_msg.BodyType = CommandBodyType.TEXT
            cmd_msg.Body = "Command:%s" % cmd_msg.cmdstr
            mac_list = self.task.get("data").get("mac_list")
            for mac in mac_list.split(','):
                self.send_thrift_cmd(mac, cmd_msg)
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def restart(self):
        try:
            resp = errcode.get_error_result()
            cmd_msg = CommandMsg()
            cmd_msg.cmdstr = 'restart'
            cmd_msg.BodyType = CommandBodyType.TEXT
            cmd_msg.Body = "Command:%s" % cmd_msg.cmdstr
            mac_list = self.task.get("data").get("mac_list")
            count = 0
            for mac in mac_list.split(','):
                self.send_thrift_cmd(mac, cmd_msg)
                count += 1
                if count >= 10:
                    time.sleep(1)
                    count = 0
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def delete(self):
        """
        just delete database tables records just for not online terminal
        :return:
        """
        try:
            resp = errcode.get_error_result()
            mac_list = self.task.get("data").get("mac_list").split(',')
            logging.debug('Will exec delete macs tables records {}'.format(mac_list))
            table_api = db_api.YzyTerminalTableCtrl(current_app.db)
            for mac in mac_list:
                table_api.delete_terminal_by_mac(mac)
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def modify_terminal_name(self):
        try:
            resp = errcode.get_error_result()
            cmd_msg = CommandMsg()
            cmd_msg.cmdstr = 'update_config'
            cmd_msg.BodyType = CommandBodyType.TEXT
            cmd_msg.Body = "Command:%s" % cmd_msg.cmdstr
            data = self.task.get("data")
            logging.debug(data)
            # yzy_terminal update
            for mac in data.keys():
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry_terminal = table_api.select_terminal_by_mac(mac)
                if qry_terminal:
                    terminal_values = {
                        'mac': mac,
                        'conf_version': str(int(qry_terminal.conf_version) + 1),
                        'name': data[mac]
                    }
                    table_api.update_terminal_by_mac(**terminal_values)
                    if qry_terminal.status == '1':
                        self.send_thrift_cmd(mac, cmd_msg)
                else:
                    logging.warning('mac not found in yzy_terminal {}'.format(mac))
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def terminal_order(self):
        logging.debug('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            resp = errcode.get_error_result()
            group_uuid = self.task.get("data").get("group_uuid")
            start_id = self.task.get("data").get("start_num")
            cmd_msg = CommandMsg()
            cmd_msg.cmdstr = 'order'
            cmd_msg.BodyType = CommandBodyType.TEXT
            cmd_msg.Body = "Command:%s" % cmd_msg.cmdstr
            cmd_msg.ArgsDic = {'terminal_id': str(start_id)}
            # select all records from yzy_terminal use group_uuid
            table_api = db_api.YzyTerminalTableCtrl(current_app.db)
            qrys = table_api.select_terminal_by_group_uuid(group_uuid)
            mac_list = [qry.mac for qry in qrys]
            if not len(mac_list):
                logging.error("param error, group_uuid {}".format(group_uuid))
                return errcode.get_error_result("RequestParamError")

            insert_data = {
                'order_macs': ','.join(mac_list),
                'start_id': start_id,
                'current_id': start_id,
                'confirm_macs': "",
                'confirm_ids': "",
                'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # session insert redis
            if self.rds.ping_server():
                # delele all group_uuid order seesions
                match_key = 'command:order:{}:*'.format(group_uuid)
                key_names = self.rds.keys(match_key)
                for key_name in key_names:
                    logging.debug("delete old key: {}".format(key_name))
                    self.rds.delete(key_name)
                cmd_msg.batch_num = self.rds.incr("cmd_batch_num")
                order_key = 'command:order:{}:{}'.format(group_uuid, cmd_msg.batch_num)
                self.rds.set(order_key, json.dumps(insert_data))
                self.rds.expire(order_key, self.rds.live_seconds)
            else:
                logging.error('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
                resp['data'] = {}
                resp['data']['batch_num'] = cmd_msg.batch_num
                return resp

            for mac in mac_list:
                # redis add a record to save order session for order_confirm
                self.send_thrift_cmd(mac, cmd_msg)

            resp['data'] = {}
            resp['data']['batch_num'] = cmd_msg.batch_num
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            resp['data'] = {}
            resp['data']['batch_num'] = cmd_msg.batch_num
            return resp

    @timefn
    def cancel_terminal_order(self):
        try:
            resp = errcode.get_error_result()
            cmd_msg = CommandMsg()
            cmd_msg.cmdstr = 'order'
            cmd_msg.BodyType = CommandBodyType.TEXT
            cmd_msg.Body = "Command:%s" % cmd_msg.cmdstr
            cmd_msg.ArgsDic = {'terminal_id': "-1"}
            logging.debug("task data: {}".format(self.task.get("data")))
            group_uuid = self.task.get("data").get("group_uuid")
            batch_num = self.task.get("data").get("batch_num")
            cmd_msg.batch_num = int(batch_num)
            # delete redis record
            mac_list = []
            if self.rds.ping_server():
                order_key = 'command:order:{}:{}'.format(group_uuid, batch_num)
                if self.rds.exists(order_key):
                    json_data = self.rds.get(order_key)
                    if json_data:
                        data_dict = json.loads(json_data)
                        mac_list = data_dict['order_macs'].split(',')
                    self.rds.delete(order_key)
                    logging.debug("delete old key: {}".format(order_key))
                    for mac in mac_list:
                        self.send_thrift_cmd(mac, cmd_msg)
                # delele all group_uuid order seesions
                match_key = 'command:order:{}:*'.format(group_uuid)
                key_names = self.rds.keys(match_key)
                for key_name in key_names:
                    logging.debug("delete old key: {}".format(key_name))
                    self.rds.delete(key_name)
            else:
                logging.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def modify_ip(self):
        try:
            resp = errcode.get_error_result()
            cmd_msg = CommandMsg()
            cmd_msg.cmdstr = 'update_ip'
            cmd_msg.BodyType = CommandBodyType.TEXT
            mac_list = self.task.get("data").get("mac_list").split(',')
            ip_list = self.task.get("data").get("to_ip_list").split(',')
            gateway = self.task.get("data").get("gateway")
            mask = self.task.get("data").get("mask")
            dns1 = self.task.get("data").get("dns1", "")
            dns2 = self.task.get("data").get("dns2", "")

            if not (is_ip_addr(gateway) and is_netmask(mask)[0] and len(mac_list) == len(ip_list)):
                logging.error("param error, gateway {}, mask {}, dns1 {}, dns2 {}".format(gateway, mask, dns1, dns2))
                return errcode.get_error_result("RequestParamError")

            ip_info = {
                "IsDhcp": 0,
                "Ip": "",
                "Subnet": mask,
                "Gateway": gateway,
                "Mac": "",
                "DNS1": dns1,
                "DNS2": dns2,
            }
            for mac in mac_list:
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry_terminal = table_api.select_terminal_by_mac(mac)
                ip = ip_list[mac_list.index(mac)]
                ip_info["Ip"] = ip
                ip_info["Mac"] = mac
                body = str(json.dumps(ip_info).encode('utf-8'), encoding='utf-8')
                cmd_msg.Body = "Command:{}|{}".format(cmd_msg.cmdstr, body)
                logging.debug(cmd_msg)
                if qry_terminal:
                    terminal_values = {
                        'mac': mac,
                        'conf_version': str(int(qry_terminal.conf_version) + 1),
                        'ip': ip,
                        'mask': ip_info['Subnet'],
                        'gateway': ip_info['Gateway'],
                        'is_dhcp': int(ip_info['IsDhcp']),
                        'dns1': ip_info['DNS1'],
                        'dns2': ip_info['DNS2']
                    }
                    table_api.update_terminal_by_mac(**terminal_values)
                    if qry_terminal.status == '1':
                        self.send_thrift_cmd(mac, cmd_msg)
                else:
                    logging.warning('mac not found in yzy_terminal {}'.format(mac))
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def set_terminal(self):
        try:
            resp = errcode.get_error_result()
            cmd_msg = CommandMsg()
            cmd_msg.cmdstr = 'update_config'
            cmd_msg.BodyType = CommandBodyType.TEXT
            cmd_msg.Body = "Command:%s" % cmd_msg.cmdstr
            logging.debug('get data {}'.format(self.task.get("data")))
            mac_list = self.task.get("data").get("mac_list").split(',')
            show_desktop_type = self.task.get("data").get("mode").get("show_desktop_type")
            auto_desktop = self.task.get("data").get("mode").get("auto_desktop")
            open_strategy = self.task.get("data").get("mode").get("open_strategy")
            close_desktop_strategy = self.task.get("data").get("mode").get("close_desktop_strategy")
            close_terminal_strategy = self.task.get("data").get("mode").get("close_terminal_strategy")
            current_screen_info = self.task.get("data").get("program").get("current_screen_info")
            server_ip = self.task.get("data").get("program").get("server_ip")
            show_modify_user_passwd = self.task.get("data").get("program").get("show_modify_user_passwd")
            terminal_setup_passwd = self.task.get("data").get("program").get("terminal_setup_passwd")
            window_mode = self.task.get("data").get("windows").get("window_mode")
            goto_local_desktop = self.task.get("data").get("windows").get("disconnect_setup").get("goto_local_desktop")
            goto_local_auth = self.task.get("data").get("windows").get("disconnect_setup").get("goto_local_auth")
            show_local_button = self.task.get("data").get("windows").get("show").get("show_local_button")
            goto_local_passwd = self.task.get("data").get("windows").get("show").get("goto_local_passwd")

            set_mode_info = {
                'show_desktop_type': show_desktop_type,
                'auto_desktop': auto_desktop,
                'open_strategy': open_strategy,
                'close_desktop_strategy': close_desktop_strategy,
                'close_terminal_strategy': close_terminal_strategy
            }
            set_windows_info = {
                'window_mode': window_mode,
                'disconnect_setup': {
                    'goto_local_desktop': goto_local_desktop,
                    'goto_local_auth': goto_local_auth
                },
                'show': {
                    'show_local_button': show_local_button,
                    'goto_local_passwd': goto_local_passwd
                }
            }
            # yzy_terminal update setup_conf
            for mac in mac_list:
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry_terminal = table_api.select_terminal_by_mac(mac)
                if qry_terminal:
                    setup_info = json.loads(qry_terminal.setup_info)
                    logging.debug(setup_info)
                    setup_info['mode'] = set_mode_info
                    set_program_info = {
                        'server_ip': server_ip,
                        'server_port': 9999,
                        'show_modify_user_passwd': show_modify_user_passwd,
                        'terminal_setup_passwd': terminal_setup_passwd,
                        'current_screen_info': {
                            'width': int(current_screen_info.split('*')[0]),
                            'height': int(current_screen_info.split('*')[1])
                        },
                        'screen_info_list': setup_info['program']['screen_info_list']
                    }
                    setup_info['program'] = set_program_info
                    setup_info['windows'] = set_windows_info
                    terminal_values = {
                        'mac': qry_terminal.mac,
                        'conf_version': str(int(qry_terminal.conf_version) + 1),
                        'setup_info': json.dumps(setup_info)
                    }
                    table_api.update_terminal_by_mac(**terminal_values)
                    if qry_terminal.status == '1':
                        self.send_thrift_cmd(mac, cmd_msg)
                else:
                    logging.error('mac not found in yzy_terminal {}'.format(mac))
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    # 获取请求后，就可以确定最终获取到的文件名称 "mac+开始日期.zip"
    # 发送给命令给终端成功后，就在redis里面建立一条记录，key：文件名 value: false表示传输没完成
    @timefn
    def get_log_file(self):
        try:
            resp = errcode.get_error_result()
            cmd_msg = CommandMsg()
            cmd_msg.cmdstr = 'upload_log'
            cmd_msg.BodyType = CommandBodyType.TEXT
            cmd_msg.Body = "Command:%s" % cmd_msg.cmdstr
            cmd_msg.ArgsDic = {
                'start_time': self.task.get("data").get("start_date"),
                "end_time": self.task.get("data").get("end_date")
            }
            mac_list = self.task.get("data").get("mac_list")
            # if directory not exists, then create it
            if not os.path.exists(SERVER_CONF.terminal.log_dir):
                os.makedirs(SERVER_CONF.terminal.log_dir)
            for mac in mac_list.split(','):
                # delete log file and ok file if exists
                os.system("rm -f {}/{}*.zip".format(SERVER_CONF.terminal.log_dir, mac))
                os.system("rm -f {}/{}*.ok".format(SERVER_CONF.terminal.log_dir, mac))
                self.send_thrift_cmd(mac, cmd_msg)
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def update_program(self):
        try:
            resp = errcode.get_error_result()
            file_name = self.task.get("data").get("program_file_name")
            cmd_msg = CommandMsg()
            cmd_msg.cmdstr = 'update_soft'
            cmd_msg.BodyType = CommandBodyType.TEXT
            cmd_msg.Body = "Command:{}|{}".format(cmd_msg.cmdstr, file_name)
            cmd_msg.ArgsDic = {'file_name': file_name}
            mac_list = self.task.get("data").get("mac_list")
            for mac in mac_list.split(','):
                self.send_thrift_cmd(mac, cmd_msg)
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def desktop_close_notice(self):
        try:
            resp = errcode.get_error_result()
            cmd_msg = CommandMsg()
            cmd_msg.cmdstr = 'vm_shutdown'
            cmd_msg.BodyType = CommandBodyType.TEXT
            data = self.task.get("data")
            data['desktop_name'] = data["instance_name"]
            data['dsk_uuid'] = data["instance_uuid"]
            data.pop("instance_name")
            data.pop("instance_uuid")
            data['dsk_type'] = "kvm"
            data['status'] = 0
            terminal_mac = data['terminal_mac']
            data.pop("terminal_mac")
            body = str(json.dumps(data).encode('utf-8'), encoding='utf-8')
            cmd_msg.Body = "Command:{}|{}".format(cmd_msg.cmdstr, body)
            if terminal_mac:
                table_terminal_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry_terminal = table_terminal_api.select_terminal_by_mac(terminal_mac)
                if qry_terminal and qry_terminal.status == '1':
                    self.send_thrift_cmd(terminal_mac, cmd_msg)
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def change_group(self):
        try:
            resp = errcode.get_error_result()
            mac_list = self.task.get("data").get("mac_list").split(',')
            to_group_uuid = self.task.get("data").get("to_group_uuid")
            # yzy_terminal update
            for mac in mac_list:
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                qry_terminal = table_api.select_terminal_by_mac(mac)
                if qry_terminal:
                    terminal_values = {
                        'mac': mac,
                        'group_uuid': to_group_uuid
                    }
                    table_api.update_terminal_by_mac(**terminal_values)
                else:
                    logging.debug('mac not found in yzy_terminal {}'.format(mac))
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def delete_group(self):
        try:
            resp = errcode.get_error_result()
            group_uuid = self.task.get("data").get("group_uuid")
            # yzy_terminal update
            table_api = db_api.YzyTerminalTableCtrl(current_app.db)
            table_api.reset_group_uuid(group_uuid)
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def user_logout(self):
        try:
            resp = errcode.get_error_result()
            cmd_msg = CommandMsg()
            cmd_msg.cmdstr = 'user_logout'
            cmd_msg.BodyType = CommandBodyType.TEXT
            cmd_msg.Body = "Command:%s" % cmd_msg.cmdstr
            mac_list = self.task.get("data").get("mac_list")
            for mac in mac_list.split(','):
                self.send_thrift_cmd(mac, cmd_msg)
            return resp
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp
