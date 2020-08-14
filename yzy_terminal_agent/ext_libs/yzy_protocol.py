import os
import re
import json
import struct
import random
import logging
import base64
from common import constants
from yzy_terminal_agent.extensions import _redis
from ctypes import *

logger = logging.getLogger(__name__)

# VOI 协议tag
VOI_PROTOCOL_TAG = (ord('Y') << 24) | (ord('Z') << 16) | (ord('Y') << 8) | 0xfb
VOI_VERSION_CHEIF = 1
VOI_VERSION_SUB = 0


class YzyProtocolStatus:
    SUCCESS = 0
    PARAMETER_ERR = 1
    INSUFFICIENT_SPACE = 2
    PROTOCOL_ERR = 3


class YzyProtocolDataType:
    BIN = 0
    JSON = 1
    PROTOBUF = 2


class ClientType:
    UEFI = 1
    LINUX = 2
    WINDOWS = 3
    SERVER = 4
    U_LINUX = 5


class YzyProtocolType:
    REQ = 1
    RESP= 2


class YzyProtocolPaket(Structure):

    def set_data(self, data):
        # supplementary = self.supplementary
        # token_len = self.token_length
        # offset = token_len + supplementary
        if self.data_type == YzyProtocolDataType.JSON:
            data = re.sub('[\n\t]', '', data.decode('utf8'))
            self.data = data.encode('utf-8')
            logger.debug(self.data)
        else:
            logger.info("set data: %s, %s"% (len(data), data[:100]))
            self.data = data

    def data_json(self):
        ret = dict()
        try:
            supplementary_len = self.supplementary
            # logger.debug(supplementary_len)
            supplementary = self.data[:supplementary_len]
            token_len = self.token_length
            # logger.debug(token_len)
            token = self.data[supplementary_len: token_len]
            _data = self.data[supplementary_len + token_len:]
            # logger.debug(token)
            # logger.debug(_data)
            logger.debug("supplementary_len : {}, token_len:{}, token: {}, _data: {}, data_len: {}".format(
                 supplementary_len, token_len, token, _data[:1000], len(self.data)))
            if self.data_type == YzyProtocolDataType.JSON:
                ret = json.loads(_data)
            else:
                data_base64 = base64.b64encode(_data).decode("utf-8")
                ret = {"payload": data_base64}
            ret["supplementary"] = supplementary
            ret["token"] = token
        except Exception as e:
            logger.error("", exc_info=True)
        return ret

    def get_service_code(self):
        # ret = self.data_json()
        return self.service_code

    def get_client_type(self):
        client_types = {
            1: "uefi",
            2: "linux",
            3: "windows",
            4: "server",
            5: "u_linux"
        }
        return client_types.get(self.client_type, "Other")

    def __repr__(self):
        return ("verion-%s service_code-%s sequence_code-%s client_type-%s req_or_res-%s "
                            "data_size-%s token-lenght-%s supplementary-%s") % (
                            self.version_chief, self.service_code,
                            self.sequence_code, self.get_client_type(),
                            self.req_or_res, self.data_size,
                            self.token_length, self.supplementary)


YzyProtocolPaket._fields_ = [
        ('version_chief', c_int),
        ('version_sub', c_int),
        ('service_code', c_int),
        ('sequence_code', c_int),
        ('data_size', c_int),
        ('data_type', c_int),
        ('encoding', c_int),
        ('client_type', c_int),
        ('req_or_res', c_int),
        ('token_length', c_int),
        ('supplementary', c_int),
        # ('data', c_char_p)
    ]


class YzyTorrentStruct(Structure):
    """
    种子文件结构
    """
    pass

    def format_str(self, data_len):
        data = "%ds"% data_len
        return "<36sbbiqqqq" + data

    def save(self, bin_data, dir_path):
        head = bin_data[:66]
        uuid, disk_type, sys_type, dif_level, real_size, reserve_size, data_len = struct.unpack("<36sbbiqqq", head)
        if data_len != len(bin_data[66:]):
            raise Exception("torrent file len error!!!")
        uuid = uuid.decode("utf-8")
        torrent_name = "voi_%s_%s.torrent"% (dif_level, uuid)
        file_path = os.path.join(dir_path, torrent_name)
        with open(file_path, "wb") as f:
            f.write(bin_data[66:])
        logger.info("torrent: %s save success!!!"% file_path)
        return file_path

    # def set_data(self, data):
    #     # supplementary = self.supplementary
    #     # token_len = self.token_length
    #     # offset = token_len + supplementary
    #     self.data = data
    #
    # def data_json(self):
    #     ret = dict()
    #     try:
    #         supplementary_len = self.supplementary
    #         # logger.debug(supplementary_len)
    #         supplementary = self.data[:supplementary_len]
    #         token_len = self.token_length
    #         # logger.debug(token_len)
    #         token = self.data[supplementary_len: token_len]
    #         _data = self.data[supplementary_len + token_len:]
    #         # logger.debug(token)
    #         # logger.debug(_data)
    #         ret = json.loads(_data)
    #         ret["supplementary"] = supplementary
    #         ret["token"] = token
    #     except Exception as e:
    #         logger.error("", exc_info=True)
    #     return ret
    #
    # def get_service_code(self):
    #     # ret = self.data_json()
    #     return self.service_code
    #
    # def get_client_type(self):
    #     client_types = {
    #         1: "uefi",
    #         2: "linux",
    #         3: "windows",
    #         4: "server"
    #     }
    #     return client_types[self.client_type]
    #
    # def __repr__(self):
    #     return "verion-%s service_code-%s sequence_code-%s client_type-%s"% (
    #                         self.version_chief, self.service_code,
    #                         self.sequence_code, self.get_client_type())


YzyTorrentStruct._fields_ = [
        ('uuid', c_int),
        ('type', c_int),
        ('sys_type', c_int),
        ('dif_level', c_int),
        ('real_size', c_int),
        ('reserve_size', c_int),
        ('data_len', c_int)
    ]


class YzyProtocol:

    header_length = 24

    def __init__(self):
        self.rdb = _redis
        # self.header_length = 24
        self.libc = cdll.LoadLibrary(os.path.join(os.getcwd(), "ext_libs/libyzyProtocol.so"))
        self.libc.u32YzyProtocol_PaketCreate.argtypes = [c_int, c_int, c_int, c_int, c_int, c_char_p,
                                                         c_int, c_int, c_int, c_char_p, POINTER(c_int), POINTER(c_void_p)]
        self.libc.u32YzyProtocol_PaketCreate.restype = c_int

    def create_seq_code(self):
        """ 获取数据包序号 """
        key_name = "yzy_protocol_sequence_code"
        return self.rdb.incr(key_name)
        # return random.randint(1, 10000)

    def protocol_free(self, ptr):
        """ 释放内存 """
        self.libc.vYzyProtocol_Free(ptr)

    def create_paket(self, service_code, pu_payload, token, sequence_code=None,
                     encoding = 0, data_type = YzyProtocolDataType.JSON, req_or_res = YzyProtocolType.REQ,
                     client_type=ClientType.SERVER):
        """ 创建协议数据 """
        if sequence_code is None:
            sequence_code = self.create_seq_code()
        data_size = len(pu_payload)
        token_len = len(token)
        pu_pkt_size = c_int()
        pkt_data = c_void_p(0)
        ppv_pkt_data = byref(pkt_data)
        ret = self.libc.u32YzyProtocol_PaketCreate(service_code, sequence_code, data_size, data_type, encoding,
                                    pu_payload, client_type, req_or_res, token_len, token, byref(pu_pkt_size), ppv_pkt_data)

        if ret != YzyProtocolStatus.SUCCESS:
            logger.error("create paket error : %s"% ret)
            # logger.debug("create paket error : %s"% ret)
            raise Exception("create paket error: %s"% ret)
        ptrt = POINTER(c_char * pu_pkt_size.value)
        ptr = cast(pkt_data, POINTER(c_char * pu_pkt_size.value))
        indices = ptrt(ptr.contents)
        msg = b""
        for i in indices.contents:
            msg += i
        self.protocol_free(pkt_data)
        logger.debug("data_size: {}".format(data_size))
        return pu_pkt_size.value, msg

    def create_paket_tag(self, service_code, pu_payload, token, sequence_code=None,
                     encoding = 0, data_type = YzyProtocolDataType.JSON, req_or_res = YzyProtocolType.REQ,
                     client_type=ClientType.SERVER):
        """ 创建协议数据 """
        if sequence_code is None:
            sequence_code = self.create_seq_code()
        tag = VOI_PROTOCOL_TAG
        version_chief = VOI_VERSION_CHEIF
        version_sub = VOI_VERSION_SUB
        supplemenetary = 0
        data_size = len(pu_payload)
        token_len = len(token)
        # pu_pkt_size = c_int()
        # pkt_data = c_void_p(0)
        # ppv_pkt_data = byref(pkt_data)
        # ret = self.libc.u32YzyProtocol_PaketCreate(service_code, sequence_code, data_size, data_type, encoding,
        #                             pu_payload, client_type, req_or_res, token_len, token, byref(pu_pkt_size), ppv_pkt_data)
        #
        # if ret != YzyProtocolStatus.SUCCESS:
        #     logger.error("create paket error : %s"% ret)
        #     # logger.debug("create paket error : %s"% ret)
        #     raise Exception("create paket error: %s"% ret)
        # ptrt = POINTER(c_char * pu_pkt_size.value)
        # ptr = cast(pkt_data, POINTER(c_char * pu_pkt_size.value))
        # indices = ptrt(ptr.contents)
        # msg = b""
        # for i in indices.contents:
        #     msg += i
        # self.protocol_free(pkt_data)
        # fmt = "IHHIIIBBBBHH%ds"% data_size
        # msg = struct.pack(fmt, tag, version_chief, version_sub, service_code, sequence_code, data_size, data_type,
        #                     encoding, client_type, req_or_res, token_len, supplemenetary, pu_payload)
        fmt = "HHIIIBBBBHH32s%ds"% data_size
        msg = struct.pack(fmt, version_chief, version_sub, service_code, sequence_code, data_size, data_type,
                            encoding, client_type, req_or_res, token_len, supplemenetary, token, pu_payload)
        logger.debug("data_size: {}".format(data_size))
        return len(msg), msg

    def parse_paket(self, msg):
        data_size = len(msg)
        stat = YzyProtocolPaket()
        my_handle = pointer(stat)
        ret= self.libc.u32YzyProtocol_PaketParse(msg, data_size, byref(my_handle))
        logger.debug(">>>: %s", ret)
        logger.debug("<<<: %s"% my_handle)

    def parse_paket_header(self, header):
        if len(header) != self.header_length:
            logger.error("the header parse error: %s"% header)
            # logger.debug("the protocol header parse error: %s"% header)
            raise Exception("the header parse error")
        version_chief, version_sub, service_code, sequence_code, data_size, data_type, encoding, client_type, req_or_res,\
        token_len, supplementary = struct.unpack("HHIIIBBBBHH", header)
        data = b""
        protocol_paket = YzyProtocolPaket(
            version_chief=version_chief, version_sub=version_sub, service_code=service_code, sequence_code=sequence_code,
            data_size=data_size, data_type=data_type, encoding=encoding, client_type=client_type,
            req_or_res=req_or_res, token_length=token_len, supplementary=supplementary
        )
        protocol_paket.set_data(data)
        return protocol_paket


if __name__ == "__main__":
    # yzy_protocol = YzyProtocol()
    # service_code = 1
    # data_size = 5
    # data_type = 1
    # encoding = 0
    # pu_payload = b"hello"
    # client_type = 1
    # req_or_res = 1
    # token = b"12345678"
    # token_len = len(token)
    # pk_size = c_int()
    # HANDLE = c_void_p
    # my_handle = HANDLE(0)
    # pk_ret = byref(my_handle)
    # ret = yzy_protocol.create_paket(service_code, pu_payload, token)
    # logger.debug(">>>: %s, %s"% ret)
    # logger.debug("<<<: %s"% pk_size.value)
    # logger.debug("<<<: %s"% my_handle.value)
    #
    #
    # ptrt = POINTER(c_char * pk_size.value)
    # mydblPtr = cast(my_handle, POINTER(c_char * pk_size.value))
    # indices = ptrt(mydblPtr.contents)
    # r = b""
    # for i in indices.contents:
    #     r += i
    # logger.debug(r)
    yzy_protocol = YzyProtocol()
    service_code = 1
    data_size = 5
    data_type = 1
    encoding = 0
    pu_payload = b"hello"
    client_type = 1
    req_or_res = 1
    token = b"12345678"
    token_len = len(token)
    pk_size = c_int()
    HANDLE = c_void_p
    ret = yzy_protocol.create_paket(service_code, pu_payload, token)
    logger.debug(">>>: %s, %s" % ret)
    msg = ret[1]
    # ret = yzy_protocol.parse_paket(msg)
    ret = yzy_protocol.parse_paket_header(msg[:yzy_protocol.header_length])
    logger.debug(ret.data)

