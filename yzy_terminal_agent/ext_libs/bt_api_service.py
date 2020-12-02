import threading
from functools import wraps
import time
import json
import traceback
import logging
import socket
import os
import sys
from yzy_terminal_agent.extensions import _redis
from common.utils import Singleton, get_error_result, create_md5
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
        self.rds = _redis
        self.name = 'bt'
        self.image_ip = image_ip
        self.bt_ip_port = (image_ip, socket_port)
        self.bt_port = bt_port
        #self.start_bt_server(image_ip, bt_port, time_out)
        self.set_tracker_server(image_ip, bt_port)
        # self.request_key = ""
    # def reset_ip_port(self):
    #     self.set_tracker_server(self)

    def create_batch_no(self):
        key_name = "voi_bt_torrent_batch_no"
        return self.rds.incr(key_name)

    @timefn
    def request_bt_server(self, service_name, request_data, cache_key=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            mac = ""
            if "mac" in request_data:
                mac = request_data.pop("mac")
            serial = self.create_batch_no()
            request_data.update({"serial": serial})
            ret_str = json.dumps(request_data)
            service_code = name_service_code[service_name]
            _size, msg = YzyProtocol().create_paket(service_code, ret_str.encode("utf-8"), b'',
                                                    sequence_code=6666,
                                                    req_or_res=YzyProtocolType.REQ,
                                                    client_type=ClientType.SERVER)
            logger.info("Send request msg size: {}, service_name:{}  msg: {}, mac: {}, serial: {}".format(_size,
                                                                                    service_name, msg, mac, serial))
            sock.connect(self.bt_ip_port)
            sock.send(msg)
            if cache_key:
                self.rds.set(cache_key, 1, 5)
            head_msg = sock.recv(YzyProtocol.header_length)
            if not head_msg or len(head_msg) < YzyProtocol.header_length:
                get_head_len = 0 if not head_msg else len(head_msg)
                logger.error("Get head error, length {}".format(get_head_len))
            paket_struct = YzyProtocol().parse_paket_header(head_msg)
            logger.info("Receive head msg: {}, mac: {}, serial: {}".format(head_msg, mac, serial))
            logger.debug("Parse head: {}".format(paket_struct))
            body_length = paket_struct.data_size + paket_struct.token_length + paket_struct.supplementary
            if paket_struct.req_or_res == 2:  # 1-request, 2-response
                logger.debug("Get response: service_code[{}-{}], sequence_no[{}] ".format(
                    paket_struct.service_code,
                    service_code_name[paket_struct.service_code],
                    paket_struct.sequence_code,
                ))

                body = sock.recv(body_length)
                paket_struct.set_data(body)
                logger.debug("Get body: {}, mac: {}".format(body, mac))
                if not body:
                    logger.error("Get bt return body error!")
                    raise Exception("bt api request body err")

                ret_data = paket_struct.data_json()
                logger.debug("Parsed body: {}, mac: {}".format(ret_data, mac))
            else:
                logger.error("message head req_or_res type error, mac: {}, serial: {}".format(mac, serial))
                sock.close()
                return get_error_result("BtResponseMsgError")
            sock.close()
            return ret_data
        except Exception as err:
            logger.error("tcp socket error: %s" % err)
            logger.error(''.join(traceback.format_exc()))
            sock.close()
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

    def add_bt_task(self, torrent, save_path, mac=None, batch_no=None):
        """
        {
            "torrent":  "/data/uuid.torrent"
            "save_path": "/mnt/"
            # 在save_path 存在源文件则为上传否则为下载
        }
        """
        # 1. call add_task socket api
        logger.info("add bt task start: %s, %s" % (mac, batch_no))
        request_data = {
            'torrent': torrent,
            'save_path': save_path
        }
        # 判断缓存在是否存在结果:
        request_data_str = json.dumps(request_data)
        request_data_hash = create_md5(request_data_str)
        key = "torrent:task:%s"% request_data_hash
        request_key = "torrent:request:task:%s"% request_data_hash
        response_str  = self.rds.get(key)
        if response_str:
            logger.info("add bt task, cache has respone %s, mac: %s"% (response_str, mac))
            logger.info("add bt task end: %s" % mac)
            return json.loads(response_str)
        request_cache = self.rds.get(request_key)
        if request_cache:
            logger.debug("add bt task, cache has request, mac: %s"% mac)
            # 如果已经正在请求，判断缓存中的状态
            for i in range(10):
                logger.debug("add bt task, cache has request, mac: %s, loop get cache data" % mac)
                response_str = self.rds.get(key)
                if response_str:
                    logger.info("add bt task, cache has respone %s, mac: %s" % (response_str, mac))
                    logger.info("add bt task end: %s" % mac)
                    return json.loads(response_str)
                time.sleep(1)

        # 2. call start_bt socket api
        request_data.update({"mac": mac})
        service_name = "add_task"
        ret_data = self.request_bt_server(service_name, request_data, request_key)
        logger.info("add task ret_data: %s, mac: %s"% (ret_data, mac))
        if "supplementary" in ret_data: ret_data.pop("supplementary")
        if "token" in ret_data: ret_data.pop("token")
        response_str = json.dumps(ret_data)
        self.rds.set(key, response_str, 60)
        self.rds.delete(request_key)
        logger.info("add bt task end: %s" % mac)
        return ret_data

    def delele_bt_task(self, torrent_id):
        """
        {
            "torrent": "12121.torrent"
        }
        """
        # 1. call del_task socket api
        request_data = {
            "torrent_id": torrent_id
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

