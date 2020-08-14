import os
import sys
import time
import datetime as dt
import json
import traceback
import copy
import logging
from threading import Timer
from functools import wraps
from flask import current_app
import common.errcode as errcode
from yzy_terminal_agent.database import api as db_api
from common.utils import build_result, is_ip_addr, is_netmask, create_uuid
from common.config import SERVER_CONF
from yzy_terminal_agent.ext_libs.redis_pub_sub import RedisMessageCenter
from yzy_terminal_agent.extensions import _redis
from yzy_terminal_agent.redis_client import RedisClient
from yzy_terminal_agent.http_client import HttpClient


logger = logging.getLogger(__name__)


def timefn(fn):
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        logger.debug("@timefn:" + fn.__name__ + " took " + str(t2 - t1) + " seconds")
        return result
    return measure_time


class WebTaskHandler(object):
    def __init__(self):
        self.name = os.path.basename(__file__).split('.')[0]
        self.type = "WebTaskHandler"
        self.msg_center = RedisMessageCenter()
        self.rds = RedisClient()
        self.http_client = HttpClient()

    def deal_process(self, data):
        try:
            cmd = data.get("command", "")
            func = getattr(self, cmd)
            return func(data)
        except Exception as err:
            logger.error("Error: {}".format(err))
            logger.error(''.join(traceback.format_exc()))
            return build_result("OtherError", msg="en")

    def create_batch_no(self):
        key_name = "voi_web_command_batch_no"
        return self.rds.incr(key_name)

    def start(self, data):
        try:
            resp = errcode.get_error_result()
            json_data = data.get("data")
            mac_list = json_data.get("mac_list")
            for mac in mac_list.split(','):
                os.system("wol {}".format(mac))
                logger.debug("send wol {}".format(mac))
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    # shutdown terminal
    @timefn
    def shutdown(self, data):
        try:
            logger.debug(data)
            resp = errcode.get_error_result()
            batch_no = self.create_batch_no()
            json_data = data.get("data")
            mac_list = json_data.get("mac_list")
            for mac in mac_list.split(','):
                send_data = {
                    "cmd": "shutdown",
                    "data": {
                        "mac": mac,
                        "params": {
                            "batch_no": batch_no
                        }
                    }
                }
                msg = json.dumps(send_data)
                self.msg_center.public(msg)
            if self.rds.ping():
                redis_key = 'voi_command:shutdown:{}'.format(batch_no)
                insert_data = {
                    "send_macs": mac_list,
                    "confirm_macs": "",
                    'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
            else:
                logger.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def update_desktop_group_notify(self, data):
        try:
            logger.debug(data)
            resp = errcode.get_error_result()
            batch_no = self.create_batch_no()
            json_data = data.get("data")
            group_uuid = json_data.get("group_uuid")
            table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
            qrys = table_api.select_terminal_by_group_uuid(group_uuid)
            mac_list = [qry.mac for qry in qrys]
            if not len(mac_list):
                logger.error("param error, group_uuid {}".format(group_uuid))
                return errcode.get_error_result("RequestParamError")

            for mac in mac_list:
                send_data = {
                    "cmd": "update_desktop_group_info",
                    "data": {
                        "mac": mac,
                        "params": {
                            "batch_no": batch_no
                        }
                    }
                }
                msg = json.dumps(send_data)
                self.msg_center.public(msg)
            if self.rds.ping():
                redis_key = 'voi_command:update_desktop_group_info:{}'.format(batch_no)
                insert_data = {
                    "send_macs": mac_list,
                    "confirm_macs": "",
                    'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
            else:
                logger.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def pxe_start(self, data):
        try:
            logger.debug(data)
            resp = errcode.get_error_result()
            batch_no = self.create_batch_no()
            json_data = data.get("data")
            mac_list = json_data.get("mac_list")
            for mac in mac_list.split(','):
                send_data = {
                    "cmd": "pxe_start",
                    "data": {
                        "mac": mac,
                        "params": {
                            "batch_no": batch_no
                        }
                    }
                }
                msg = json.dumps(send_data)
                self.msg_center.public(msg)
            if self.rds.ping():
                redis_key = 'voi_command:pxe_start:{}'.format(batch_no)
                insert_data = {
                    "send_macs": mac_list,
                    "confirm_macs": "",
                    'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
            else:
                logger.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def restart(self, data):
        try:
            logger.debug(data)
            resp = errcode.get_error_result()
            batch_no = self.create_batch_no()
            json_data = data.get("data")
            mac_list = json_data.get("mac_list")
            for mac in mac_list.split(','):
                send_data = {
                    "cmd": "restart",
                    "data": {
                        "mac": mac,
                        "params": {
                            "batch_no": batch_no
                        }
                    }
                }
                msg = json.dumps(send_data)
                self.msg_center.public(msg)
            if self.rds.ping():
                redis_key = 'voi_command:restart:{}'.format(batch_no)
                insert_data = {
                    "send_macs": mac_list,
                    "confirm_macs": "",
                    'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
            else:
                logger.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def enter_maintenance_mode(self, data):
        try:
            logger.debug(data)
            resp = errcode.get_error_result()
            batch_no = self.create_batch_no()
            json_data = data.get("data")
            mac_list = json_data.get("mac_list")
            for mac in mac_list.split(','):
                send_data = {
                    "cmd": "enter_maintenance_mode",
                    "data": {
                        "mac": mac,
                        "params": {
                            "batch_no": batch_no
                        }
                    }
                }
                msg = json.dumps(send_data)
                self.msg_center.public(msg)
            if self.rds.ping():
                redis_key = 'voi_command:enter_maintenance_mode:{}'.format(batch_no)
                insert_data = {
                    "send_macs": mac_list,
                    "confirm_macs": "",
                    'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
            else:
                logger.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def clear_all_desktop(self, data):
        try:
            logger.debug(data)
            resp = errcode.get_error_result()
            batch_no = self.create_batch_no()
            json_data = data.get("data")
            mac_list = json_data.get("mac_list")
            for mac in mac_list.split(','):
                send_data = {
                    "cmd": "clear_all_desktop",
                    "data": {
                        "mac": mac,
                        "params": {
                            "batch_no": batch_no
                        }
                    }
                }
                msg = json.dumps(send_data)
                self.msg_center.public(msg)
            if self.rds.ping():
                redis_key = 'voi_command:clear_all_desktop:{}'.format(batch_no)
                insert_data = {
                    "send_macs": mac_list,
                    "confirm_macs": "",
                    'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
            else:
                logger.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def add_data_disk(self, data):
        try:
            logger.debug(data)
            resp = errcode.get_error_result()
            batch_no = self.create_batch_no()
            json_data = data.get("data")
            mac_list = json_data.get("mac_list")
            for mac in mac_list.split(','):
                send_data = {
                    "cmd": "add_data_disk",
                    "data": {
                        "mac": mac,
                        "params": {
                            "batch_no": batch_no,
                            "enable": 1,
                            "restore": 0,
                            "size": 100
                        }
                    }
                }
                msg = json.dumps(send_data)
                self.msg_center.public(msg)
            if self.rds.ping():
                redis_key = 'voi_command:add_data_disk:{}'.format(batch_no)
                insert_data = {
                    "send_macs": mac_list,
                    "confirm_macs": "",
                    'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
            else:
                logger.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def delete(self, data):
        """
        just delete database tables records just for not online terminal
        :return:
        """
        try:
            logger.debug(data)
            resp = errcode.get_error_result()
            batch_no = self.create_batch_no()
            json_data = data.get("data")
            mac_list = json_data.get("mac_list")
            logger.debug('Will exec delete macs tables records {}'.format(mac_list))
            table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
            for mac in mac_list.split(','):
                terminal_uuid = table_api.delete_terminal_by_mac(mac)
                # 清除终端与桌面组的bind关系
                bind_table_api = db_api.YzyVoiTerminalToDesktopsCtrl(current_app.db)
                bind_table_api.delete_all_bind_by_terminal(terminal_uuid)
            logger.info("delete terminal : %s success"% mac_list)
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def modify_terminal_name(self, data):
        try:
            logger.debug(data)
            resp = errcode.get_error_result()
            batch_no = self.create_batch_no()
            json_data = data.get("data")
            # yzy_voi_terminal update
            for mac in json_data.keys():
                table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
                qry_terminal = table_api.select_terminal_by_mac(mac)
                if qry_terminal:
                    terminal_values = {
                        'mac': mac,
                        'conf_version': str(int(qry_terminal.conf_version) + 1),
                        'name': json_data[mac]
                    }
                    table_api.update_terminal_by_mac(**terminal_values)
                    send_data = {
                        "cmd": "update_name",
                        "data": {
                            "mac": mac,
                            "params": {
                                "batch_no": batch_no,
                                "conf_version": int(qry_terminal.conf_version) + 1,
                                "name": json_data[mac]
                            }
                        }
                    }
                    msg = json.dumps(send_data)
                    self.msg_center.public(msg)
                else:
                    logger.warning('mac not found in yzy_voi_terminal {}'.format(mac))
            if self.rds.ping():
                redis_key = 'voi_command:update_name:{}'.format(batch_no)  # terminal just use update_config
                insert_data = {
                    "send_macs": ','.join(json_data.keys()),
                    "confirm_macs": "",
                    'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
            else:
                logger.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def terminal_order(self, data):
        logger.debug('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))

        try:
            resp = errcode.get_error_result()
            json_data = data.get("data")
            group_uuid = json_data.get("group_uuid")
            start_id = json_data.get("start_num")
            batch_no = self.create_batch_no()
            # select all records from yzy_voi_terminal use group_uuid
            table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
            qrys = table_api.select_terminal_by_group_uuid(group_uuid)
            mac_list = [qry.mac for qry in qrys]
            if not len(mac_list):
                logger.error("param error, group_uuid {}".format(group_uuid))
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
                match_key = 'voi_command:order:{}:*'.format(group_uuid)
                key_names = self.rds.keys(match_key)
                for key_name in key_names:
                    logger.debug("delete old key: {}".format(key_name))
                    self.rds.delete(key_name)
                redis_key = 'voi_command:order:{}:{}'.format(group_uuid, batch_no)
                self.rds.set(redis_key, json.dumps(insert_data), self.rds.live_seconds)
            else:
                logger.error('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
                resp['data'] = {}
                resp['data']['batch_num'] = batch_no
                return resp

            for mac in mac_list:
                # redis add a record to save order session for order_confirm
                send_data = {
                    "cmd": "order",
                    "data": {
                        "mac": mac,
                        "params": {
                            "batch_no": batch_no,
                            "terminal_id": start_id
                        }
                    }
                }
                msg = json.dumps(send_data)
                self.msg_center.public(msg)

            resp['data'] = {}
            resp['data']['batch_num'] = batch_no
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            resp['data'] = {}
            resp['data']['batch_num'] = batch_no
            return resp

    @timefn
    def cancel_terminal_order(self, data):
        try:
            resp = errcode.get_error_result()
            json_data = data.get("data")
            group_uuid = json_data.get("group_uuid")
            batch_no = json_data.get("batch_num")
            # delete redis record
            mac_list = []
            if self.rds.ping_server():
                redis_key = 'voi_command:order:{}:{}'.format(group_uuid, batch_no)
                if self.rds.exists(redis_key):
                    json_data = self.rds.get(redis_key)
                    if json_data:
                        data_dict = json.loads(json_data)
                        mac_list = data_dict['order_macs'].split(',')
                    self.rds.delete(redis_key)
                    for mac in mac_list:
                        send_data = {
                            "cmd": "order",
                            "data": {
                                "mac": mac,
                                "params": {
                                    "batch_no": batch_no,
                                    "terminal_id": -1
                                }
                            }
                        }
                        msg = json.dumps(send_data)
                        self.msg_center.public(msg)
                else:
                    logger.error("redis_key: {} not exists".format(redis_key))

                # delele all group_uuid order seesions
                match_key = 'voi_command:order:{}:*'.format(group_uuid)
                key_names = self.rds.keys(match_key)
                for key_name in key_names:
                    logger.debug("delete old key: {}".format(key_name))
                    self.rds.delete(key_name)
            else:
                logger.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def modify_ip(self, data):
        try:
            logger.info('input data: {}'.format(data))
            resp = errcode.get_error_result()
            json_data = data.get("data")
            group_uuid = json_data.get("group_uuid", "")
            mac_list = json_data.get("mac_list").split(',')
            ip_list = json_data.get("to_ip_list").split(',')
            gateway = json_data.get("gateway")
            mask = json_data.get("mask")
            dns1 = json_data.get("dns1", "")
            dns2 = json_data.get("dns2", "")
            batch_no = self.create_batch_no()

            if not (is_ip_addr(gateway) and is_netmask(mask)[0] and len(mac_list) == len(ip_list)):
                logger.error("param error, gateway {}, mask {}, dns1 {}, dns2 {}".format(gateway, mask, dns1, dns2))
                return errcode.get_error_result("RequestParamError")

            # 1. order terminal ip
            for mac in mac_list:
                table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
                qry_terminal = table_api.select_terminal_by_mac(mac)
                ip = ip_list[mac_list.index(mac)]
                if qry_terminal:
                    terminal_values = {
                        'mac': mac,
                        'conf_version': str(int(qry_terminal.conf_version) + 1),
                        'ip': ip,
                        'mask': mask,
                        'gateway': gateway,
                        'is_dhcp': 0,
                        'dns1': dns1,
                        'dns2': dns2
                    }
                    table_api.update_terminal_by_mac(**terminal_values)
                    # send redis message to terminal
                    send_data = {
                        "cmd": "update_ip",
                        "data": {
                            "mac": mac,
                            "params": {
                                "batch_no": batch_no,
                                'conf_version': int(qry_terminal.conf_version) + 1,
                                'ip': ip,
                                'mask': mask,
                                'gateway': gateway,
                                'dns1': dns1,
                                'dns2': dns2
                            }
                        }
                    }
                    msg = json.dumps(send_data)
                    self.msg_center.public(msg)
                else:
                    logger.warning('mac not found in yzy_voi_terminal {}'.format(mac))
                if self.rds.ping():
                    redis_key = 'voi_command:update_ip:{}'.format(batch_no)  # terminal just use update_config
                    insert_data = {
                        "send_macs": ','.join(mac_list),
                        "confirm_macs": "",
                        'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
                else:
                    logger.debug('Redis server error')
                    resp = errcode.get_error_result(error="RedisServerError")

            # 2. order desktops ip
            table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
            qrys = table_api.select_terminal_by_group_uuid(group_uuid)
            terminal_mac_list = [qry.mac for qry in qrys]
            terminal_id_list = [qry.terminal_id for qry in qrys]
            if not len(terminal_mac_list):
                logger.error("param error, group_uuid {}".format(group_uuid))
                return errcode.get_error_result("RequestParamError")
            request_data = {
                "terminal_id_list": terminal_id_list,
                "group_uuid": group_uuid,
                "terminal_mac_list": terminal_mac_list
            }
            request_url = "/api/v1/voi/terminal/education/desktop_ip_order"
            logger.debug("request yzy_server {}, {}".format(request_url, request_data))
            server_ret = self.http_client.post(request_url, request_data)
            logger.debug("get yzy_server {} {},".format(request_url, server_ret))
            ret_code = server_ret.get("code", -1)
            if ret_code != 0:
                resp = errcode.get_error_result(error="TerminalDesktopIpOrderError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def set_terminal(self, data):
        try:
            resp = errcode.get_error_result()
            json_data = data.get("data")
            batch_no = self.create_batch_no()
            logger.debug('get data {}'.format(json_data))
            mac_list = json_data.get("mac_list").split(',')
            show_desktop_type = json_data.get("mode").get("show_desktop_type")
            auto_desktop = json_data.get("mode").get("auto_desktop")
            server_ip = json_data.get("program").get("server_ip")

            set_mode_info = {
                'show_desktop_type': show_desktop_type,
                'auto_desktop': auto_desktop,
            }
            set_program_info = {
                'server_ip': server_ip,
            }
            # yzy_voi_terminal update setup_conf
            for mac in mac_list:
                table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
                qry_terminal = table_api.select_terminal_by_mac(mac)
                if qry_terminal:
                    setup_info = json.loads(qry_terminal.setup_info)
                    logger.debug(setup_info)
                    setup_info['mode'] = set_mode_info
                    setup_info['program'] = set_program_info
                    terminal_values = {
                        'mac': qry_terminal.mac,
                        'conf_version': str(int(qry_terminal.conf_version) + 1),
                        'setup_info': json.dumps(setup_info)
                    }
                    table_api.update_terminal_by_mac(**terminal_values)
                    # send redis message to terminal
                    send_data = {
                        "cmd": "update_config",
                        "data": {
                            "mac": mac,
                            "params": {
                                "batch_no": batch_no,
                                'conf_version': int(qry_terminal.conf_version) + 1,
                                "mode": set_mode_info,
                                "program": set_program_info
                            }
                        }
                    }
                    msg = json.dumps(send_data)
                    self.msg_center.public(msg)
                else:
                    logger.error('mac not found in yzy_voi_terminal {}'.format(mac))
                if self.rds.ping():
                    redis_key = 'voi_command:update_config:{}'.format(batch_no)  # terminal just use update_config
                    insert_data = {
                        "send_macs": ','.join(mac_list),
                        "confirm_macs": "",
                        'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
                else:
                    logger.debug('Redis server error')
                    resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def change_group(self, data):
        try:
            resp = errcode.get_error_result()
            json_data = data.get("data")
            mac_list = json_data.get("mac_list").split(',')
            to_group_uuid = json_data.get("to_group_uuid")
            # yzy_voi_terminal update
            for mac in mac_list:
                table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
                qry_terminal = table_api.select_terminal_by_mac(mac)
                if qry_terminal:
                    terminal_values = {
                        'mac': mac,
                        'group_uuid': to_group_uuid
                    }
                    table_api.update_terminal_by_mac(**terminal_values)
                else:
                    logger.debug('mac not found in yzy_voi_terminal {}'.format(mac))
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def delete_group(self, data):
        try:
            resp = errcode.get_error_result()
            json_data = data.get("data")
            group_uuid = json_data.get("group_uuid")
            # yzy_voi_terminal update
            table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
            table_api.reset_group_uuid(group_uuid)
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def send_down_torrent(self, data):
        try:
            resp = errcode.get_error_result()
            json_data = data.get("data")
            logger.info("send down torrent file %s"% json_data)
            mac_list = json_data.get("mac_list").split(',')
            disk_uuid = json_data.get("disk_uuid", "")
            disk_type = json_data.get("disk_type", "")
            sys_type= json_data.get("sys_type", "")
            dif_level = json_data.get("dif_level", "")
            real_size = json_data.get("real_size","")
            torrent_file = json_data.get("torrent_file", "")
            reserve_size = json_data.get("reserve_size")
            batch_no = self.create_batch_no()
            if not os.path.exists(torrent_file):
                logger.error("send down torrent file error: %s not exist"% torrent_file)
                return errcode.get_error_result(error="TorrentFileNotExist")

            for mac in mac_list:
                table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
                qry_terminal = table_api.select_terminal_by_mac(mac)
                if qry_terminal:
                    terminal_values = {
                        "mac": mac,
                        "torrent_file": torrent_file
                    }
                    # table_api.update_terminal_by_mac(**terminal_values)
                    # send redis message to terminal
                    send_data = {
                        "cmd": "send_torrent",
                        "data": {
                            "mac": mac,
                            "desktop": {
                                "uuid": "xxxxxx",
                                "name": "",
                                "desc": "",
                                "sys_type": sys_type,
                                "disks": [
                                    {
                                        "batch_no": batch_no,
                                        "uuid": disk_uuid,
                                        "type": disk_type,
                                        "sys_type": sys_type,
                                        "dif_level": dif_level,
                                        "real_size": real_size,
                                        "reserve_size": reserve_size,
                                        "torrent_file": torrent_file
                                }
                            ]
                            }
                        }
                    }
                    msg = json.dumps(send_data)
                    self.msg_center.public(msg)
                else:
                    logger.warning('mac not found in yzy_voi_terminal {}'.format(mac))
                # if self.rds.ping():
                #     order_key = 'voi_command:update_config:{}'.format(batch_no)  # terminal just use update_config
                #     insert_data = {
                #         "send_macs": json_data.keys(),
                #         "confirm_macs": "",
                #         'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                #     }
                #     self.rds.set(order_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
                # else:
                #     logger.debug('Redis server error')
                #     resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def sync_client_disk(self, data):
        try:
            resp = errcode.get_error_result()
            json_data = data.get("data")
            logger.info("send upload torrent file %s"% json_data)
            mac = json_data.get("mac")
            desktop = json_data.get("desktop", {})
            upload_disks = json_data.get("upload_disks", "")
            download_disks = json_data.get("download_disks", "")
            # dif_level = json_data.get("dif_level", "")
            # real_size = json_data.get("real_size","")
            # torrent_file = json_data.get("torrent_file", "")
            # reserve_space = json_data.get("reserve_space")
            # batch_no =
            # if not os.path.exists(torrent_file):
            #     logger.error("send down torrent file error: %s not exist"% torrent_file)
            #     return errcode.get_error_result(error="TorrentFileNotExist")

            table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
            qry_terminal = table_api.select_terminal_by_mac(mac)
            if qry_terminal:
                if upload_disks:
                    _desktop = copy.deepcopy(desktop)
                    _desktop.pop("download_disks")
                    send_data = {
                        "cmd": "upload_disk",
                        "data": {
                            "batch_no": self.create_batch_no(),
                            "desktop": _desktop
                        }
                    }

                    msg = json.dumps(send_data)
                    self.msg_center.public(msg)
                    logger.info("sync client %s disk: upload disk, %s"% (mac, desktop))
                # 推送种子下载命令
                for disk in download_disks:
                    # table_api.update_terminal_by_mac(**terminal_values)
                    # send redis message to terminal
                    send_data = {
                        "cmd": "send_torrent",
                        "data": {
                            "mac": mac,
                            "desktop": {
                                "batch_no": self.create_batch_no(),
                                "uuid": disk["uuid"],
                                "type": disk["type"],
                                "sys_type": disk["sys_type"],
                                "dif_level": disk["dif_level"],
                                "real_size": disk["real_size"],
                                "reserve_size": disk["reserve_size"],
                                "torrent_file": disk["torrent_file"]
                            }
                        }
                    }
                    msg = json.dumps(send_data)
                    self.msg_center.public(msg)
            else:
                logger.warning('mac not found in yzy_voi_terminal {}'.format(mac))
                # if self.rds.ping():
                #     order_key = 'voi_command:update_config:{}'.format(batch_no)  # terminal just use update_config
                #     insert_data = {
                #         "send_macs": json_data.keys(),
                #         "confirm_macs": "",
                #         'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                #     }
                #     self.rds.set(order_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
                # else:
                #     logger.debug('Redis server error')
                #     resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def upload_desktop(self, data):
        try:
            resp = errcode.get_error_result()
            json_data = data.get("data")
            logger.info("upload desktop info %s" % json_data)
            mac = json_data.get("mac")
            desktop = json_data.get("desktop", {})
            batch_no = self.create_batch_no()
            table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
            qry_terminal = table_api.select_terminal_by_mac(mac)
            if qry_terminal:
                _desktop = copy.deepcopy(desktop)
                send_data = {
                    "cmd": "upload_desktop",
                    "data": {
                        "mac": mac,
                        "batch_no": batch_no,
                        "desktop": desktop
                    }
                }

                msg = json.dumps(send_data)
                self.msg_center.public(msg)
                logger.info("send client %s upload desktop command, %s" % (mac, desktop))
            else:
                logger.warning('mac not found in yzy_voi_terminal {}'.format(mac))
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def send_desktop(self, data):
        """
        {
            "uuid": "模板的uuid",
            "name": "模板名称",
            "desc": "模板描述",
            "disks" : [
                {
                    "uuid":
                    ....
                }
            ]
        }
        :param data:
        :return:
        """
        try:
            resp = errcode.get_error_result()
            json_data = data.get("data")
            logger.info("send desktop info %s" % json_data)
            mac_list = json_data.get("mac_list").split(",")
            desktop = json_data.get("desktop", {})

            for mac in mac_list:
                table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
                qry_terminal = table_api.select_terminal_by_mac(mac)
                if qry_terminal:
                    desktop["desktop_name"] += str(qry_terminal.terminal_id)
                    # 补齐桌面IP地址
                    desktop_is_dhcp = desktop["desktop_is_dhcp"]
                    if not desktop_is_dhcp:
                        terminal_to_desktop_ctl = db_api.YzyVoiTerminalToDesktopsCtrl(current_app.db)
                        terminal_to_desktop = terminal_to_desktop_ctl.get_terminal_to_desktop(qry_terminal.uuid,
                                                                                            desktop["desktop_group_uuid"])
                        # models.YzyVoiTerminalToDesktops, {
                        #     "desktop_group_uuid": desktop.uuid,
                        #     "terminal_uuid": terminal_uuid
                        # })
                        if terminal_to_desktop:
                            desktop_is_dhcp = terminal_to_desktop.desktop_is_dhcp
                            if not desktop_is_dhcp:
                                desktop["desktop_is_dhcp"] = desktop_is_dhcp
                                desktop["desktop_ip"] = terminal_to_desktop.desktop_ip
                                desktop["desktop_mask"] = terminal_to_desktop.desktop_mask
                                desktop["desktop_gateway"] = terminal_to_desktop.desktop_gateway
                                desktop["desktop_dns1"] = terminal_to_desktop.desktop_dns1
                                desktop["desktop_dns2"] = terminal_to_desktop.desktop_dns2

                    batch_no = self.create_batch_no()
                    params = {
                        "batch_no": batch_no,
                        "desktop": desktop
                    }
                    send_data = {
                        "cmd": "send_desktop",
                        "data": {
                            "mac": mac,
                            "params": params
                        }
                    }

                    msg = json.dumps(send_data)
                    self.msg_center.public(msg)
                    logger.info("send client %s desktop info, %s" % (mac, desktop))
                    # # 推送种子下载命令
                    if self.rds.ping():
                        redis_key = 'voi_command:send_desktop:{}'.format(batch_no)  # terminal just use update_config
                        insert_data = {
                            "send_macs": ','.join(mac_list),
                            "confirm_macs": "",
                            "params": params,
                            'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
                    else:
                        logger.debug('Redis server error')
                        resp = errcode.get_error_result(error="RedisServerError")

                else:
                    logger.warning('mac not found in yzy_voi_terminal {}'.format(mac))

            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def cancel_send_desktop(self, data):
        try:
            logger.debug(data)
            resp = errcode.get_error_result()
            batch_no = self.create_batch_no()
            json_data = data.get("data")
            mac_list = json_data.get("mac_list")
            for mac in mac_list.split(','):
                send_data = {
                    "cmd": "cancel_send_desktop",
                    "data": {
                        "mac": mac,
                        "params": {
                            "batch_no": batch_no
                        }
                    }
                }
                msg = json.dumps(send_data)
                self.msg_center.public(msg)
            if self.rds.ping():
                redis_key = 'voi_command:cancel_send_desktop:{}'.format(batch_no)
                insert_data = {
                    "send_macs": mac_list,
                    "confirm_macs": "",
                    'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
            else:
                logger.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def create_torrent(self, data):
        """
        生成种子文件
        {
            "file_path": "/mnt/win7.qcow2",
            "torrent_path": "/mnt/win7.torrent"
        }
        :param data:
        :return:
        """
        try:
            # resp = errcode.get_error_result()
            json_data = data.get("data")
            logger.info("create torrent %s" % json_data)
            torrents = json_data.get("torrents", [])
            for torrent in torrents:
                file_path = torrent.get("file_path")
                torrent_path = torrent.get("torrent_path")
                # if os.path.exists(file_path) and not os.path.exists(torrent_path):
                if os.path.exists(file_path):
                    ret = current_app.bt_api.make_torrent(file_path, torrent_path)
                    if ret.get("code", -1) != 0:
                        logger.error('create torrent bt api return fail {} {}'.format(torrent, ret))
                        continue
                    logger.info("create torrent bt api return success {}".format(torrent))
            resp = errcode.get_error_result()
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def add_bt_task(self, data):
        """
        添加bt任务
         {
            "torrent":  "/data/uuid.torrent"
            "save_path": "/mnt/"
            # 在save_path 存在源文件则为上传否则为下载
        }
        :param data:
        :return:
        """
        try:
            # resp = errcode.get_error_result()
            json_data = data.get("data")
            logger.info("add bt task %s" % json_data)
            torrent = json_data.get("torrent")
            save_path = json_data.get("save_path")
            ret = current_app.bt_api.add_bt_task(torrent, save_path)
            logger.info('add bt task api return {}'.format(ret))
            if "supplementary" in ret: ret.pop('supplementary')
            if "token" in ret : ret.pop('token')
            return ret
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def get_task_state(self, data):
        """
        {
            "torrent_id": torrent_id,
            "ip": ip
        }
        :param data:
        :return:
        """
        try:
            # resp = errcode.get_error_result()
            json_data = data.get("data")
            logger.info("get bt task state %s" % json_data)
            torrent_id = json_data.get("torrent_id", None)
            if not torrent_id:
                logger.error("torrent_id is null")
                resp = errcode.get_error_result(error="MessageError")
                return resp
            ip = json_data.get("ip", None)
            ret = current_app.bt_api.get_task_state(torrent_id, ip, 1) # 0-upload 1-download
            logger.info('get bt task state api return {}'.format(ret))
            ret.pop('supplementary')
            ret.pop('token')
            return ret
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp


    @timefn
    def delete_bt_task(self, data):
        """
        删除bt任务
         {
            "torrent_id": "12121"
        }
        :param data:
        :return:
        """
        try:
            # resp = errcode.get_error_result()
            json_data = data.get("data")
            logger.info("delete bt task %s" % json_data)
            task_id = json_data.get("task_id")
            # save_path = json_data.get("save_path")
            ret = current_app.bt_api.delete_bt_task(task_id)
            logger.info('delete bt task api return {}'.format(ret))
            ret.pop('supplementary')
            ret.pop('token')
            return ret
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def enter_maintain(self, data):
        try:
            logger.debug(data)
            resp = errcode.get_error_result()
            batch_no = self.create_batch_no()
            json_data = data.get("data")
            mac_list = json_data.get("mac_list")
            for mac in mac_list.split(','):
                send_data = {
                    "cmd": "enter_maintain",
                    "data": {
                        "mac": mac,
                        "params": {
                            "batch_no": batch_no
                        }
                    }
                }
                msg = json.dumps(send_data)
                self.msg_center.public(msg)
            if self.rds.ping():
                redis_key = 'voi_command:enter_maintain:{}'.format(batch_no)
                insert_data = {
                    "send_macs": mac_list,
                    "confirm_macs": "",
                    'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
            else:
                logger.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def push_bt_result(self, data):
        """
        bt 任务结果推送
        :param data:
        :return:
        """
        try:
            resp = errcode.get_error_result()
            json_data = data.get("data")
            logger.info("push bt task result %s" % json_data)
            mac = json_data.get("mac")
            torrent_id = json_data.get("torrent_id")
            result = json_data.get("result")
            # for mac in mac_list:
            table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
            qry_terminal = table_api.select_terminal_by_mac(mac)
            if qry_terminal:
                send_data = {
                    "cmd": "push_task_result",
                    "data": {
                        "mac": mac,
                        "params": {
                            "torrent_id" : torrent_id,
                            "msg": "Success" if result == 0 else "Fail",
                            "result": result
                        }
                    }
                }
                msg = json.dumps(send_data)
                self.msg_center.public(msg)
            else:
                logger.warning('mac not found in yzy_voi_terminal {}'.format(mac))
            logger.info("push bt task result: %s" % mac)
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def watermark_switch(self, data):
        """
        水印开关
        :param data:
        :return:
        """
        try:
            resp = errcode.get_error_result()
            batch_no = self.create_batch_no()
            json_data = data.get("data")
            logger.info("watermark switch %s" % json_data)
            mac_list = json_data.get("mac_list").split(',')
            switch = json_data.get("switch", 0)
            for mac in mac_list:
                table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
                qry_terminal = table_api.select_terminal_by_mac(mac)
                if qry_terminal:
                    send_data = {
                        "cmd": "watermark_switch",
                        "data": {
                            "mac": mac,
                            "params": {
                                "batch_no": batch_no,
                                "switch": switch
                            }
                        }
                    }
                    msg = json.dumps(send_data)
                    self.msg_center.public(msg)
                else:
                    logger.warning('mac not found in yzy_voi_terminal {}'.format(mac))
            if self.rds.ping():
                redis_key = 'voi_command:watermark_switch:{}'.format(batch_no)
                insert_data = {
                    "send_macs": ','.join(mac_list),
                    "confirm_macs": "",
                    'datetime': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.rds.set(redis_key, json.dumps(insert_data).encode('utf-8'), self.rds.live_seconds)
            else:
                logger.debug('Redis server error')
                resp = errcode.get_error_result(error="RedisServerError")
            logger.info("watermark switch %s : %s" %(switch, mac_list))
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def delete_bt_task(self, data):
        """
        删除bt任务
         {
            "torrent_id": 12121
        }
        :param data:
        :return:
        """
        try:
            # resp = errcode.get_error_result()
            json_data = data.get("data")
            logger.info("delete bt task %s" % json_data)
            task_id = json_data.get("task_id")
            # save_path = json_data.get("save_path")
            ret = current_app.bt_api.delete_bt_task(task_id)
            logger.info('delete bt task api return {}'.format(ret))
            if "supplementary" in ret:
                ret.pop("supplementary")
            if "token" in ret:
                ret.pop("token")
            return ret
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    @timefn
    def get_terminal_ip(self, data):
        try:
            logger.info('data: {}'.format(data))
            resp = errcode.get_error_result()
            json_data = data.get("data")
            mac = json_data.get("mac")
            table_api = db_api.YzyVoiTerminalTableCtrl(current_app.db)
            qry_terminal = table_api.select_terminal_by_mac(mac)
            terminal_values = {}
            if qry_terminal:
                terminal_values = {
                    'mac': mac,
                    'ip': qry_terminal.ip,
                    'mask': qry_terminal.mask,
                    'gateway': qry_terminal.gateway,
                    'is_dhcp': 0,
                    'dns1': qry_terminal.dns1,
                    'dns2': qry_terminal.dns2
                }
            else:
                terminal_values = {
                    'mac': mac,
                    'ip': "",
                    'mask': "",
                    'gateway': "",
                    'is_dhcp': 1,
                    'dns1': "",
                    'dns2': ""
                }
                logger.warning('mac not found in yzy_voi_terminal {}'.format(mac))
            resp["data"] = terminal_values
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp
