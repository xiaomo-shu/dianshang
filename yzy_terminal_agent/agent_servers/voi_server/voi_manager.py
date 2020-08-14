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
        self.heartbeat = False
        self.token = ""

        # 状态
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
        if terminal_mac and terminal_mac in self.clients:
            self.clients.pop(terminal_mac)
            self.ip_port_mac.pop(ip_port)

    ################################################ from client tcp message handle ####################
    def client_biz_processor(self, client, is_req, seq_id, handler_name, message):
        logger.debug("client: {}, is_req: {}, seq_id: {}, handler_name: {} message: {}".format(
            client, is_req, seq_id, handler_name, message)[:1000])
        if message.get("mac", None):
            message["mac"] = message["mac"].upper()
        if message.get("data", {}).get("mac", None):
            message["data"]["mac"] = message["data"]["mac"].upper()
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
            message["status"] = client.status
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
        return ret

    def client_terminal_login(self, client, message=None):
        logger.info("client %s login,  start......" % client)
        terminal_mac = client.mac
        terminal_ip = client.client_ip
        terminal_port = client.client_port
        client.heartbeat = True
        self.clients[terminal_mac] = client
        # self.clients[terminal_mac].heartbeat = True
        # self.
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
                "port": client.client_port
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
            self.clients[terminal_mac].heartbeat = True
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
                    "port": client.client_port
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
        resp["data"]["datetime"] = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if terminal_mac in self.clients:
            self.clients[terminal_mac].heartbeat = True
            logger.info("terminal heartbeat set True: %s " % client)
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
        payload = message["payload"]
        message["payload"] = base64.b64encode(payload).decode("utf-8")
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
            loop_seconds = 30
            while True:
                logger.debug("check clients heartbeat {}".format(self.clients))
                for mac in list(self.clients.keys()):
                    client = self.clients[mac]
                    if client.heartbeat:
                        client.heartbeat = False
                    else:
                        client.status = TerminalStatus.OFF
                        if client.socket_client.socket:
                            client.socket_client.socket.close()
                            logger.warning('client: {} no heartbeat, close socket'.format(client))
                        self.del_client_by_ip(client.client_ip, client.client_port)
                        # update database status offline
                        # 通知服务端
                        _data = {
                            "cmd": "terminal_except_exit",
                            "data": {
                                "mac": client.mac,
                                "ip": client.client_ip
                            }
                        }
                        ret = voi_terminal_post("/api/v1/voi/terminal/task/", _data)
                        logger.info("voi terminal server return: %s" % ret)
                        if ret.get("code") != 0:
                            logger.error("voi terminal logout error: %s" % ret)
                time.sleep(loop_seconds)
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
                    logger.info(
                        "do_command: {}, cmd: {}, service_code: {}, data: {}".format(mac, cmd, service_code, data))
                    terminal.socket_client.send(params, service_code, terminal.token)
                else:
                    logger.warning("send {}, terminal [{}] is offline, please check!!!".format(mac, cmd))
                    return False
            else:
                logger.error('mac {} not in clients'.format(mac))
                return False
            return True
        except Exception as e:
            logger.error(e, exc_info=True)
            return False

    def do_send_torrent(self, mac, cmd, service_code, data):
        logger.info("do send torrent task: {}, cmd: {}, service_code: {}, data: {}".format(mac, cmd, service_code, data))
        try:
            if mac in self.clients.keys():
                terminal = self.clients[mac]
                params = data.get("params", "")
                logger.info("send torrent desktop disk params: {}".format(params))
                torrent_file = params.get("torrent_file", "")
                if not os.path.exists(torrent_file):
                    logger.error("do send torrent file not exist: %s"% torrent_file)
                    return
                disk_uuid = params["uuid"]
                disk_type =  params["type"]
                sys_type = params["sys_type"]
                dif_level = params["dif_level"]
                real_size = int(params["real_size"])
                reserve_size = int(params["reserve_size"])
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
                payload = struct.pack(format_str, disk_uuid.encode("utf-8"), int(disk_type), int(sys_type), int(dif_level)
                                      , int(real_size), int(reserve_size), file_size, len(torrent_data), torrent_data)

                if terminal.socket_client.socket:
                    terminal.socket_client.send(payload, service_code, terminal.token, YzyProtocolDataType.BIN)
            else:
                logger.error('mac {} not in clients'.format(mac))
                return False
            return True
        except Exception as e:
            logger.error(e, exc_info=True)
            return False

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
                        self.deal_message(data)
                time.sleep(1)
            except Exception as e:
                logger.error(e)
                logger.error(''.join(traceback.format_exc()))


voi_terminal_manager = VOITerminalManager()
# voi_manager.start()
