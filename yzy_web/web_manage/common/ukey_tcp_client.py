import socket
import struct
import json
import time
import logging
from web_manage.common.constants import WEB_CLIENT_ID, UKEY_DEFAULT_PORT


logger = logging.getLogger()


class UkeyClient:

    sequence = 1

    def __init__(self, host="127.0.0.1", port=UKEY_DEFAULT_PORT, client_id=WEB_CLIENT_ID):
        self.ukey_host = host
        self.ukey_port = port
        self.header_length = 21
        self.recv_buff = 1024
        self.format_str = ">3sILBBq"
        self.cid = b"yzy"
        self.version = 1
        # self.sequence = 1
        self.req = 0
        self.resp = 1
        self.client_id = client_id

    def _create_sequence(self):
        seq = self.client_id * (10 ** 7) + self.sequence % (10 ** 7)
        self.sequence += 1
        return int(seq)

    def _create_req_msg(self, data):
        if isinstance(data, (dict, list, tuple)):
            data = json.dumps(data).encode()
        elif isinstance(data, bytes):
            pass
        elif isinstance(data, str):
            data = data.encode()
        else:
            return None
        data_len = len(data)
        seq = self._create_sequence()
        header = struct.pack(self.format_str, self.cid, self.version, seq, self.req, self.client_id, data_len)
        return header + data, seq

    def _parse_recv_header(self, header, sequence):
        items = struct.unpack(self.format_str, header)
        if items[0] != self.cid or items[1] != self.version or items[2] != sequence or items[3] != self.resp :
            logger.error("parse recv header error %s" % str(items))
            return False
        return items

    def is_ukey_plugin(self):
        # import pdb;pdb.set_trace()
        # command  = "check_and_open_ukey"
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((self.ukey_host, self.ukey_port))
        data = {
            "cmd": "is_ukey_plugin",
            "params": {},
            "timestamp": time.time()
        }
        msg, seq = self._create_req_msg(data)
        _socket.send(msg)
        try:
            header = _socket.recv(self.header_length)
            header_items = self._parse_recv_header(header, seq)
            if not header_items:
                logger.error("is ukey plugin recv error")
                _socket.close()
                return False
            data = _socket.recv(header_items[5])
            data_dict = json.loads(data)
            return data_dict
        except Exception as e:
            logger.exception(str(e), exc_info=True)
            return False
        finally:
            if _socket:
                _socket.close()

    def ukey_active(self, unit_name, sn):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((self.ukey_host, self.ukey_port))
        data = {
            "cmd": "ukey_active",
            "params": {
                "unit_name": unit_name,
                "sn": sn
            },
            "timestamp": time.time()
        }
        msg, seq = self._create_req_msg(data)
        _socket.send(msg)
        try:
            header = _socket.recv(self.header_length)
            header_items = self._parse_recv_header(header, seq)
            if not header_items:
                logger.error("is ukey active recv error")
                _socket.close()
                return False
            data = _socket.recv(header_items[5])
            data_dict = json.loads(data)
            return data_dict
        except Exception as e:
            logger.exception(str(e), exc_info=True)
            return False
        finally:
            if _socket:
                _socket.close()

    def read_license(self):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((self.ukey_host, self.ukey_port))
        data = {
            "cmd": "read_license",
            "params": {
            },
            "timestamp": time.time()
        }
        msg, seq = self._create_req_msg(data)
        _socket.send(msg)
        try:
            header = _socket.recv(self.header_length)
            header_items = self._parse_recv_header(header, seq)
            if not header_items:
                logger.error("read license file recv error")
                _socket.close()
                return False
            data = _socket.recv(header_items[5])
            data_dict = json.loads(data)
            return data_dict
        except Exception as e:
            logger.exception(str(e), exc_info=True)
            return False
        finally:
            if _socket:
                _socket.close()

    def get_auth_info(self):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((self.ukey_host, self.ukey_port))
        data = {
            "cmd": "get_auth_info",
            "params": {
            },
            "timestamp": time.time()
        }
        msg, seq = self._create_req_msg(data)
        _socket.send(msg)
        try:
            header = _socket.recv(self.header_length)
            header_items = self._parse_recv_header(header, seq)
            if not header_items:
                logger.error("get auth info recv error")
                _socket.close()
                return False
            data = _socket.recv(header_items[5])
            data_dict = json.loads(data)
            return data_dict
        except Exception as e:
            logger.exception(str(e), exc_info=True)
            return False
        finally:
            if _socket:
                _socket.close()
