import logging
import struct
import json
from common.constants import CID, VERSION, IS_REQ, IS_RESP

logger = logging.getLogger()


class YzyProtocolPaket(object):
    def __init__(self, cid, version, seq_id, req_or_res, client_id, data_len):
        self.cid = cid.decode("utf-8")
        self.version = version
        self.seq_id = seq_id
        self.req_or_res = req_or_res
        self.client_id = client_id
        self.data_len = data_len
        self.data = None

    def __repr__(self):
        return "cid[%s], version[%s], req_or_res[%s], seq_id[%s], client_id[%s], data_len[%s]" % \
               (self.cid, self.version, self.req_or_res, self.seq_id, self.client_id, self.data_len)

    def set_data(self, body):
        self.data = body.decode('utf-8')
        # logger.debug("self.data: %s", self.data)

    def get_client_type(self):
        client_types = {
            1: "yzy_web",
            2: "yzy_server"
        }
        return client_types.get(self.client_id, "Other")

    def data_json(self):
        try:
            ret = json.loads(self.data)
        except Exception as e:
            ret = self.data.decode("utf-8")
            # logger.exception(str(e), exc_info=True)
        return ret

class YzyProtocol(object):

    header_length = 21
    header_fmt = ">3sILBBq"

    # def parse_paket(self, msg):
    #     data_size = len(msg)
    #     stat = YzyProtocolPaket()
    #     my_handle = pointer(stat)
    #     ret = self.libc.u32YzyProtocol_PaketParse(msg, data_size, byref(my_handle))
    #     logger.debug(">>>: %s", ret)
    #     logger.debug("<<<: %s" % my_handle)

    def parse_paket_header(self, header):
        if len(header) != self.header_length:
            logger.error("header parse error: %s" % header)
            raise Exception("header parse error")

        cid, version, sequence, req_or_res, client_id, data_len = struct.unpack(self.header_fmt, header)
        if cid != CID or version != VERSION or req_or_res not in (IS_REQ, IS_RESP) or not isinstance(data_len, int):
            logger.error("header parse error: cid[%s], version[%s], req_or_res[%s], data_len[%s]," %
                         (cid, version, req_or_res, data_len))
            raise Exception("header parse error")

        protocol_paket = YzyProtocolPaket(cid, version, sequence, req_or_res, client_id, data_len)
        return protocol_paket

    def create_paket(self, seq_id, client_id, req_or_resp, payload):
        """ 创建协议数据 """
        args = [CID, VERSION, seq_id, req_or_resp, client_id, len(payload), payload]
        msg = struct.pack(self.header_fmt + "%ds" % len(payload), *args)
        logger.debug("cid[%s], version[%s], seq_id[%s], req_or_resp[%s], client_id[%s], data_len[%s], payload[%s]", *args)
        return len(msg), msg
