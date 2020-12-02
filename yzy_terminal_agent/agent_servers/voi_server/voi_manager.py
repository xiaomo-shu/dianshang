import os
import json
import logging
import threading
import ctypes
import traceback
import struct
import base64
import datetime as dt
import time
from yzy_terminal_agent.ext_libs.yzy_protocol import YzyProtocol, YzyTorrentStruct, YzyProtocolDataType
from yzy_terminal_agent.ext_libs.redis_pub_sub import RedisMessageCenter
from common.utils import Singleton, voi_terminal_post, get_error_result, bytes_to_section
from yzy_terminal_agent.database import api as db_api
from flask_sqlalchemy import SQLAlchemy
from .service_code import name_service_code


db = SQLAlchemy()
logger = logging.getLogger("agentTcp")


class TerminalStatus:
    OFF = 0
    UEFI = 1
    LINUX = 2
    WINDOWS = 3
    SERVER = 4
    U_LINUX = 5


class VOITerminal:
    """
    voi客户端
    """

    def __init__(self, client_ip, client_port, mac):
        self.mac = mac
        self.client_ip = client_ip
        self.client_port = client_port
        self.heartbeat = TerminalStatus.OFF
        self.alive_timestamp = dt.datetime.now()
        self.token = ""

        # 状态
        self.last_status = TerminalStatus.OFF
        self.status = TerminalStatus.OFF
        self.socket_client = None

    def __repr__(self):
        return "%s:%s[%s][%s][heartbeat-%s]" % (self.client_ip, self.client_port, self.mac, self.token, self.heartbeat)

    @property
    def is_online(self):
        if self.status == TerminalStatus.OFF:
            return False
        return True

    def set_client(self, client, client_type):
        if client_type == "uefi":
            self.status = TerminalStatus.UEFI
        elif client_type == "linux":
            self.status = TerminalStatus.LINUX
        elif client_type == "windows":
            self.status = TerminalStatus.WINDOWS
        elif client_type == "u_linux":
            self.status = TerminalStatus.U_LINUX
        self.socket_client = client

    def send_msg(self, msg):
        if self.socket_client:
            self.socket_client.send(msg)


class VOITerminalManager(threading.Thread):

    __metaclass__ = Singleton

    def __init__(self):
        super(VOITerminalManager, self).__init__()
        self.clients = {}
        self.token_clients = {}
        self.ip_port_mac = {}

    def ip_port_str(self, ip, port):
        return "%s:%s" % (ip, port)

    def get_client_by_mac(self, terminal_mac):
        return self.clients.get(terminal_mac)

    def get_client_by_token(self, token):
        return self.token_clients.get(token)

    def del_client_by_ip(self, ip, port):
        ip_port = self.ip_port_str(ip, port)
        terminal_mac = self.ip_port_mac.get(ip_port)
        self.ip_port_mac.pop(ip_port)
        if terminal_mac and terminal_mac in self.clients.keys():
            client = self.clients[terminal_mac]
            if self.ip_port_str(client.client_ip, client.client_port) == ip_port:
                self.client_except_exit(client)
                self.clients.pop(terminal_mac)

    ################################################ from client tcp message handle ####################
    def client_biz_processor(self, client, is_req, seq_id, handler_name, message):
        logger.debug("client: {}, is_req: {}, seq_id: {}, handler_name: {} message: {}".format(
            client, is_req, seq_id, handler_name, message)[:1000])
            # client, is_req, seq_id, handler_name, message))
        if message.get("mac", None):
            message["mac"] = message["mac"].upper()
        terminal_mac = client.mac
        method_name = "client_%s" % handler_name
        if (not message.get('token', None) and method_name != "client_terminal_login") or \
                (message.get('token', None) and
                 self.clients.get(terminal_mac, None) and
                 (message['token'].decode('utf-8') != self.clients[terminal_mac].token)):
            ret = get_error_result("TerminalTokenError", msg="en")
            logger.error("voi terminal token error: %s" % client)
            return ret
        if hasattr(self, method_name):
            func = getattr(self, method_name)
            ret = func(client, message)
            logger.debug("Client request method_name(no flask request): {}, ret: {}".format(method_name, ret))
            return ret
        logger.info("terminal_mac: {}, client: {}, method_name: {}".format(terminal_mac, client, method_name))
        if terminal_mac in self.clients.keys():
            thread_id = ctypes.CDLL('libc.so.6').syscall(186)
            thread_ident = threading.currentThread().ident
            logger.info("terminal clients: %s pid: %s, ppid: %s, tid: %s, t_ident: %s" % (self.clients,
                                                                                          os.getpid(), os.getppid(),
                                                                                          thread_id,
                                                                                          thread_ident))
            message.pop('supplementary')
            message.pop('token')
            message["service_name"] = handler_name
            message["terminal_mac"] = terminal_mac
            message["terminal_ip"] = client.client_ip
            # 通知服务端
            _data = {
                # "cmd": handler_name if is_req else (handler_name + "_response"),
                "cmd": handler_name if is_req else "command_response",
                "data": message
            }
            logger.info("voi terminal request server : %s" % _data)
            ret = voi_terminal_post("/api/v1/voi/terminal/task/", _data)
            logger.info("voi terminal server return: %s" % ret)
        else:
            ret = get_error_result("TerminalNotLogin", msg="en")
            logger.error("voi terminal not login: %s" % client)
            client.socket_client.socket.close()
        return ret

    def client_terminal_login(self, client, message=None):
        logger.info("client %s login,  start......" % client)
        terminal_mac = client.mac
        terminal_ip = client.client_ip
        terminal_port = client.client_port
        client.heartbeat = client.status
        self.clients[terminal_mac] = client
        ip_port = self.ip_port_str(terminal_ip, terminal_port)
        self.ip_port_mac[ip_port] = terminal_mac
        thread_id = ctypes.CDLL('libc.so.6').syscall(186)
        logger.info("terminal clients: %s pid: %s, ppid: %s, tid: %s, t_ident: %s" % (self.clients,
                                                                                      os.getpid(), os.getppid(),
                                                                   thread_id, threading.currentThread().ident))
        # 通知服务端
        _data = {
            "cmd": "terminal_login",
            "data": {
                "mac": terminal_mac,
                "ip": client.client_ip,
                "status": client.status,
                "port": client.client_port,
                "desktop_uuid": message.get("desktop_uuid", "")
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/task/", _data)
        logger.info("voi terminal server return: %s" % ret)
        if ret.get("code") != 0:
            logger.error("voi terminal login error: %s" % ret)
        else:
            token = ret.get("data").get("token","")
            # self.clients[terminal_mac].token = token
            client.token = token
            client.alive_timestamp = dt.datetime.now()
            self.token_clients[token] = client

        logger.info("client %s,  end......" % client)
        return ret

    def client_terminal_logout(self, client, message=None): 
        logger.info("client_logout: %s" % client)
        terminal_mac = client.mac
        if terminal_mac in self.clients.keys():
            self.clients.pop(terminal_mac)
            thread_id = ctypes.CDLL('libc.so.6').syscall(186)
            logger.info("terminal clients: %s pid: %s, ppid: %s, tid: %s, t_ident: %s" % (self.clients,
                                                                                          os.getpid(), os.getppid(),
                                                                       thread_id, threading.currentThread().ident))
            # 通知服务端
            _data = {
                "cmd": "terminal_logout",
                "data": {
                    "mac": terminal_mac,
                    "ip": client.client_ip,
                    "port": client.client_port
                }
            }
            ret = voi_terminal_post("/api/v1/voi/terminal/task/", _data)
            logger.info("voi terminal server return: %s" % ret)
            if ret.get("code") != 0:
                logger.error("voi terminal client_logout error: %s"% ret)
            logger.info("client %s,  end......" % client)
            return ret
        else:
            logger.error("voi terminal logout error: %s is not exist" % terminal_mac)
            logger.info("client %s,  end......" % client)
            return get_error_result("Success", "en")

    def client_except_exit(self, client, message=None):
        terminal_mac = client.mac
        terminal_ip = client.client_ip
        terminal_port = client.client_port
        logger.info("client_except_exit: %s" % terminal_mac)
        if terminal_mac in self.clients.keys():
            self.clients[terminal_mac] = client
            self.clients[terminal_mac].heartbeat = False
            # self.clients[terminal_mac].alive_timestamp = dt.datetime.now()
            ip_port = self.ip_port_str(terminal_ip, terminal_port)
            self.ip_port_mac[ip_port] = terminal_mac
            thread_id = ctypes.CDLL('libc.so.6').syscall(186)
            logger.info("terminal clients: %s pid: %s, ppid: %s, tid: %s, t_ident: %s" % (self.clients,
                                                                                          os.getpid(), os.getppid(),
                                                                       thread_id, threading.currentThread().ident))
            # 通知服务端
            _data = {
                "cmd": "terminal_except_exit",
                "data": {
                    "mac": terminal_mac,
                    "ip": client.client_ip,
                }
            }
            ret = voi_terminal_post("/api/v1/voi/terminal/task/", _data)
            logger.info("voi terminal server return: %s"% ret)
            if ret.get("code") != 0:
                logger.error("voi terminal client_except_exit error: %s"% ret)
                return ret
        else:
            logger.debug("voi terminal client_except_exit: %s is not exist" % terminal_mac)
            logger.info("client %s,  end......" % client)
            return get_error_result("Success", "en")

    def client_heartbeat(self, client, message=None):
        logger.debug("terminal clients: %s " % self.clients.keys())
        terminal_mac = client.mac
        resp = get_error_result("Success", msg="en")
        resp["data"] = {}
        now_timestamp = dt.datetime.now()
        resp["data"]["datetime"] = now_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        if terminal_mac in self.clients:
            terminal = self.clients[terminal_mac]
            self.clients[terminal_mac].last_status = terminal.heartbeat
            self.clients[terminal_mac].heartbeat = client.status
            self.clients[terminal_mac].alive_timestamp = now_timestamp
        else:
            logger.error("terminal : %s is not exist" % client)
        return resp

    def client_torrent_upload(self, client, message=None):
        """ 客户端上传种子
        """
        logger.info("client upload template torrent file: %s, message: %s" % (client, message.keys()))
        message.pop('supplementary')
        message.pop('token')
        # message["service_name"] =
        # payload = message["payload"]
        # message["payload"] = base64.b64encode(payload).decode("utf-8")
        # message["payload"] = payload
        message["mac"] = client.mac
        message["ip"] = client.client_ip
        # message["data"] = base64.b64encode(message["data"].encode("utf-8")).decode("utf-8")
        message["is_json"] = True
        # terminal_mac = client.mac
        # terminal_ip = client.client_ip
        _data = {
            "cmd": "torrent_upload",
            "data": message
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/task/", _data)
        logger.info("voi terminal server return: %s" % ret)
        if ret.get("code") != 0:
            logger.error("voi terminal client_except_exit error: %s" % ret)
            return ret
        logger.info("client upload template torrent file success!!!!")
        return ret

    ################################################ client heartbeat check handle ####################
    def reset_all_terminals(self):
        _data = {
            "cmd": "restart_reset_terminals",
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/task/", _data)

    def check_client_heartbeat(self):
        try:
            self.reset_all_terminals()
            # set loop_seconds must > 10
            # exit_count = 6
            # cal_count = 0
            loop_seconds = 10
            off_line = 2 * loop_seconds
            max_off_line = 2 * 60
            # update_loop_seconds = 10
            while True:
                # is_exit_flag = False
                # if cal_count >= exit_count:
                #     is_exit_flag = True
                #     cal_count = 0
                tmp_timestamp = dt.datetime.now()
                logger.debug("check clients heartbeat {}".format(self.clients))
                online_macs = list()
                for mac in list(self.clients.keys()):
                    try:
                        client = self.clients[mac]
                        online_macs.append({"mac": mac, "status": int(client.heartbeat)})
                        alive_timestamp = client.alive_timestamp
                        time_seconds = (tmp_timestamp - alive_timestamp).seconds
                        if off_line < time_seconds < max_off_line:
                            client.heartbeat = False
                        elif time_seconds >= max_off_line:
                            client.status = TerminalStatus.OFF
                            if client.socket_client.socket:
                                client.socket_client.socket.close()
                                logger.warning('client: {} no heartbeat, close socket'.format(client))
                            self.clients.pop(mac)
                            logger.info("clear client: {}".format(client))
                            # self.del_client_by_ip(client.client_ip, client.client_port)
                            # update database status offline
                            # 通知服务端500
                            _data = {
                                "cmd": "terminal_except_exit",
                                "data": {
                                    "mac": client.mac,
                                    "ip": client.client_ip
                                }
                            }
                            ret = voi_terminal_post("/api/v1/voi/terminal/task/", _data)
                            logger.info("voi terminal except exit: {}, server return: {}".format(client, ret))
                            if ret.get("code") != 0:
                                logger.error("voi terminal except exit: {}, server return: {}".format(_data, ret))
                    except Exception as e:
                        logger.error("voi terminal check heartbeat error", exc_info=True)
                        continue

                if online_macs:
                    # macs_str = ",".join(online_macs)
                    logger.debug("check clients heartbeat online macs: %s"% online_macs)
                    # 通知终端在线
                    req_data = {
                        "cmd": "terminal_online_update",
                        "data": {
                            "terminals": online_macs,
                        }
                    }
                    ret = voi_terminal_post("/api/v1/voi/terminal/task/", req_data)
                    logger.debug("check clients heartbeat update terminals online macs: %s, ret: %s"%(online_macs, ret))
                time.sleep(loop_seconds)
                # cal_count += 1
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))

    ################################################ from web redis publish message handle ####################
    def do_command(self, mac, cmd, service_code, data):
        try:
            if mac in self.clients.keys():
                terminal = self.clients[mac]
                params = data.get("params", "")
                logger.info("params: {}".format(params))
                if terminal.socket_client.socket:
                    ret = terminal.socket_client.send(params, service_code, terminal.token)
                    logger.info(
                        "ret: {}, do_command: {}, cmd: {}, service_code: {}, data: {}".format(ret, mac, cmd, service_code, data))
                else:
                    logger.warning("send {}, terminal [{}] is offline, please check!!!".format(mac, cmd))
        except Exception as e:
            logger.error(e, exc_info=True)
        return True

    def do_send_torrent(self, mac, cmd, service_code, data):
        logger.info("do send torrent task: {}, cmd: {}, service_code: {}, data: {}".format(mac, cmd, service_code, data))
        try:
            if mac in self.clients.keys():
                terminal = self.clients[mac]

                params = data.get("params", "")
                torrent_file = params.get("torrent_file", "")
                if not os.path.exists(torrent_file):
                    logger.error("do send torrent file not exist: %s"% torrent_file)
                    return
                desktop_group_uuid = params["desktop_group_uuid"]
                task_uuid = params["task_uuid"]
                disk_uuid = params["uuid"]
                disk_type =  params["type"]
                sys_type = params["sys_type"]
                dif_level = params["dif_level"]
                real_size = int(params["real_size"])
                reserve_size = int(params["reserve_size"])
                operate_id = int(params["operate_id"])
                base_file = torrent_file.replace(".torrent", "")
                # 获取实际大小
                if not os.path.exists(base_file):
                    logger.error("do send torrent base qcow2 file not exist %s"% base_file)
                    return

                file_size = bytes_to_section(os.path.getsize(base_file))
                torrent_data = b""
                with open(torrent_file, "rb") as f:
                    torrent_data = f.read()
                format_str = YzyTorrentStruct().format_str(len(torrent_data))
                payload = struct.pack(format_str, disk_uuid.encode("utf-8"), int(disk_type), int(sys_type),
                                      int(dif_level), int(real_size), int(reserve_size), file_size, len(torrent_data),
                                      task_uuid.encode("utf-8"), desktop_group_uuid.encode("utf-8"), int(operate_id), torrent_data)
                                      # torrent_data)

                if terminal.socket_client.socket:
                    ret = terminal.socket_client.send(payload, service_code, terminal.token, YzyProtocolDataType.BIN,
                                                        task_uuid)
                    logger.info("ret: {}, send {} torrent desktop disk task_uuid：{}, params: {}".format(ret, mac,
                                                                                                    task_uuid, params))
            else:
                logger.error('mac {} not in clients'.format(mac))
        except Exception as e:
            logger.error(e, exc_info=True)
            logger.error(''.join(traceback.format_exc()))
        return True

    def do_upload_desktop(self, mac, cmd, service_code, data):
        logger.info("do upload disk: {}, cmd: {}, service_code: {}, data: {}".format(mac, cmd, service_code, data))
        send_cnt = 0
        for terminal_mac, terminal in self.clients.items():
            if mac == terminal_mac:
                desktop = data.get("desktop", "")
                logger.info("upload desktop disk: {}".format(desktop))
                # disks = desktop.get("disks", [])
                if terminal.socket_client.socket:
                    terminal.socket_client.send(desktop, service_code, terminal.token, YzyProtocolDataType.JSON)
                    send_cnt += 1

        if not send_cnt:
            logger.warning("all terminals are offline, please check!!!")
        return True

    # def do_send_desktop(self, mac, cmd, service_code, data):
    #     logger.info("do send desktop: {}, cmd: {}, service_code: {}, data: {}".format(mac, cmd, service_code, data))
    #     send_cnt = 0
    #     for terminal_mac, terminal in self.clients.items():
    #         if mac == terminal_mac:
    #             logger.info("send desktop info: {}".format(data))
    #             # disks = desktop.get("disks", [])
    #             if terminal.socket_client.socket:
    #                 terminal.socket_client.send(data, service_code, terminal.token, YzyProtocolDataType.JSON)
    #                 send_cnt += 1
    #
    #     if not send_cnt:
    #         logger.warning("all terminals are offline, please check!!!")
    #     return True

    def deal_message(self, data):
        """
        消息处理
        :param data:
        :return:
        """
        logger.debug("deal_message :%s" % data)
        cmd = data.get("cmd")
        _data = data.get("data")
        mac = _data.get("mac")
        try:
            service_code = name_service_code.get(cmd, None)
            if not service_code:
                logger.error("No web request cmd: {}".format(cmd))
                return None
            method_name = "do_%s" % cmd
            logger.info("Web request method: {}, data: {}".format(method_name, _data))
            if hasattr(self, method_name):
                func = getattr(self, method_name)
                func(mac, cmd, service_code, _data)
            else:  # do command, send to terminal
                self.do_command(mac, cmd, service_code, _data)
        except Exception as e:
            logger.error(e, exc_info=True)
            logger.error(''.join(traceback.format_exc()))
        return

    def run(self):
        msg_center = RedisMessageCenter()
        msg_center.clear_queue()

        repeat_msg_center = RedisMessageCenter("yzy::repeat_torrent")
        repeat_msg_center.clear_queue()
        # message = msg_center.subscribe()
        while True:
            logger.debug("terminal manager running ....%s"% threading.currentThread().ident)
            logger.debug("termianl number: %s"% len(self.clients))
            try:
                # recv_data = message.parse_response()
                # logger.debug("terminal manager receive :%s"% recv_data)
                # msg, channel, data = recv_data
                # data = json.loads(data)
                # logger.debug(data)
                # self.deal_message(data)
                logger.info("terminal queue msg length : %s" % msg_center.get_llen())
                while msg_center.get_llen():
                    recv_data = msg_center.get_item()
                    logger.debug("terminal manager receive :%s"% recv_data)
                    # msg, channel, data = recv_data
                    if recv_data:
                        data = json.loads(recv_data)
                        logger.debug(data)
                        cmd = data.get("cmd", "")
                        _data = data.get("data", {})
                        if cmd == "send_torrent":
                            params = _data.get("params", {})
                            repeat_num = params.get("repeat_num", 0)
                            if repeat_num > 1:
                                continue
                            # send_timestamp = params.get("send_timestamp")
                            # if send_timestamp:
                            #     t = int(time.time()) - send_timestamp
                            #     if t < 5:
                            #         msg_center.public(json.dumps(data))
                            #         continue
                            self.deal_message(data)
                            params["repeat_num"] += 1
                            params["send_timestamp"] = int(time.time())
                            # repeat_msg_center.public(json.dumps(data))
                        else:
                            self.deal_message(data)

                # repeat_msg_task = repeat_msg_center.get_all_items()
                # for task in repeat_msg_task:
                #     data = json.loads(task)
                #     logger.debug("repeat_msg_task deal: %s"% data)
                #     cmd = data.get("cmd", "")
                #     _data = data.get("data", {})
                #     if cmd == "send_torrent":
                #         params = _data.get("params", {})
                #         repeat_num = params.get("repeat_num", 0)
                #         if repeat_num > 1:
                #             continue
                #         send_timestamp = params.get("send_timestamp")
                #         if send_timestamp:
                #             t = int(time.time()) - send_timestamp
                #             if t < 60 * 2:
                #                 # repeat_msg_center.public(json.dumps(data))
                #                 continue
                #         self.deal_message(data)
                #         # 删除
                #         repeat_msg_center.clear_value(task)
                #         params["repeat_num"] += 1
                #         params["send_timestamp"] = int(time.time())
                #         # repeat_msg_center.public(json.dumps(data))

                time.sleep(1)
            except Exception as e:
                logger.error(e)
                logger.error(''.join(traceback.format_exc()))


voi_terminal_manager = VOITerminalManager()
# voi_manager.start()
