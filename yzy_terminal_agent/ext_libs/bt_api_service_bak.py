import threading
from functools import wraps
import time
import json
import traceback
import logging
import socket
import os
import sys
from common.utils import Singleton, get_error_result
from yzy_terminal_agent.ext_libs.yzy_protocol import YzyProtocol, YzyProtocolType, ClientType
from yzy_terminal_agent.ext_libs.bt_service_code import service_code_name, name_service_code


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


class BtApiServiceTask:
    def __init__(self, image_ip, socket_port, bt_port, time_out):
        super(BtApiServiceTask, self).__init__()
        self.name = 'bt'
        self.image_ip = image_ip
        self.bt_ip_port = (image_ip, socket_port)
        self.bt_port = bt_port
        self.socket = None
        self.socket_init()
        #self.start_bt_server(image_ip, bt_port, time_out)
        self.set_tracker_server(image_ip, bt_port)

    def socket_init(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(self.bt_ip_port)
        except Exception as e:
            logger.error("bt socket init fail, %s:%s"% self.bt_ip_port )
            raise Exception("bt socket connect fail !!!")

    @timefn
    def request_bt_server(self, service_name, request_data):
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if not self.socket:
                self.socket_init()

            ret_str = json.dumps(request_data)
            service_code = name_service_code[service_name]
            _size, msg = YzyProtocol().create_paket(service_code, ret_str.encode("utf-8"), b'',
                                                    sequence_code=6666,
                                                    req_or_res=YzyProtocolType.REQ,
                                                    client_type=ClientType.SERVER)
            logger.info("Send request msg size: {}, msg: {}".format(_size, msg))
            # sock.connect(self.bt_ip_port)
            self.socket.send(msg)
            head_msg = self.socket.recv(YzyProtocol.header_length)
            if not msg or len(msg) < YzyProtocol.header_length:
                get_head_len = 0 if not msg else len(msg)
                logger.error("Get head error, length {}".format(get_head_len))
            paket_struct = YzyProtocol().parse_paket_header(head_msg)
            logger.info("Receive head msg: {}".format(head_msg))
            logger.debug("Parse head: {}".format(paket_struct))
            body_length = paket_struct.data_size + paket_struct.token_length + paket_struct.supplementary
            if paket_struct.req_or_res == 2:  # 1-request, 2-response
                logger.debug("Get response: service_code[{}-{}], sequence_no[{}] ".format(
                    paket_struct.service_code,
                    service_code_name[paket_struct.service_code],
                    paket_struct.sequence_code,
                ))

                body = self.socket.recv(body_length)
                paket_struct.set_data(body)
                logger.debug("Get body: {}".format(body))
                if not body:
                    logger.error("bt api GET BODY ERROR !")
                    raise Exception("BT API GET BODY ERROR !")
                ret_data = paket_struct.data_json()
                logger.debug("Parsed body: {}".format(ret_data))
            else:
                logger.error("message head req_or_res type error")
                self.socket.close()
                return get_error_result("BtResponseMsgError")
            # sock.close()
            return ret_data
        except Exception as err:
            logger.error("tcp socket error: %s" % err)
            logger.error(''.join(traceback.format_exc()))
            if self.socket:
                self.socket.close()
                self.socket = None
            return get_error_result("OtherError")

    @timefn
    def start_bt_server(self, image_ip, bt_port, time_out):
        """
        {
            "time_out": 1000  		//可以设置超时时间
            "track_ip": 127.0.0.1
            "track_port": 1337
        }
        """
        # 1. get image network ip
        request_data = {
            'track_ip': image_ip,
            'track_port': bt_port,
            'time_out': time_out
        }
        # 2. call start_bt socket api
        service_name = "start_bt"
        ret_data = self.request_bt_server(service_name, request_data)
        if ret_data.get("code", None) != 0:
            logger.error("Start bt server error, please check!!!")
            return False
        return True

    def stop_bt_server(self):
        """
        {
            ""
        }
        """
        # 1. call stop_bt socket api
        service_name = "stop_bt"
        ret_data = self.request_bt_server(service_name, b'')
        # 2. disconnect socket
        return ret_data

    def set_tracker_server(self, image_ip, bt_port):
        """
        {
            "ip": 127.0.0.1
            "port": 1337
        }
        """
        # 1. call set_tracker socket api
        # 1. get image network ip
        request_data = {
            'ip': image_ip,
            'port': bt_port
        }
        # 2. call start_bt socket api
        service_name = "set_tracker"
        ret_data = self.request_bt_server(service_name, request_data)
        logger.info("Start set bt server: {}, return: {}".format(request_data, ret_data))
        return ret_data

    def add_bt_task(self, torrent, save_path):
        """
        {
            "torrent":  "/data/uuid.torrent"
            "save_path": "/mnt/"
            # 在save_path 存在源文件则为上传否则为下载
        }
        """
        # 1. call add_task socket api
        request_data = {
            'torrent': torrent,
            'save_path': save_path,
        }
        # 2. call start_bt socket api
        service_name = "add_task"
        ret_data = self.request_bt_server(service_name, request_data)
        return ret_data

    def delele_bt_task(self, torrent_name):
        """
        {
            "torrent": "12121.torrent"
        }
        """
        # 1. call del_task socket api
        request_data = {
            "torrent": torrent_name
        }
        # 2. call start_bt socket api
        service_name = "del_task"
        ret_data = self.request_bt_server(service_name, request_data)
        return ret_data

    def make_torrent(self, file_path, torrent_path):
        """
        {
            "file_path": "/mnt/win7.qcow2"
            "torrent_path": "/mnt/win7.torrent"
        }
        """
        # 1. call make_torrent socket api
        self.set_tracker_server(self.image_ip, self.bt_port)
        request_data = {
            "file_path": file_path,
            "torrent_path": torrent_path
        }
        # 2. call start_bt socket api
        service_name = "make_torrent"
        ret_data = self.request_bt_server(service_name, request_data)
        return ret_data

    def get_task_state(self, torrent_id, ip, torrent_type):
        """
        {
            "torrent_id": 12313,
            "ip": "192.168.11.12"",
            "type": 0  # 0-upload 1-download
        }
        """
        # 1. call get_task_state socket api
        request_data = {
            "torrent_id": torrent_id,
            "ip": ip,
            "type": torrent_type
        }
        # 2. call start_bt socket api
        service_name = "get_task_state"
        ret_data = self.request_bt_server(service_name, request_data)
        return ret_data

