import os
import re
import json
import logging
from common.utils import get_error_result, constants
from yzy_terminal_agent.ext_libs.yzy_protocol import YzyProtocol, YzyProtocolType, YzyTorrentStruct
from .client_socket import ClientSocket
from .voi_manager import VOITerminal
from .voi_manager import voi_terminal_manager
from .service_code import service_code_name

logger = logging.getLogger("agentTcp")


class ServiceHandler:

    def __init__(self, client_ip, client_port):
        self.client_ip = client_ip
        self.client_port = client_port

    def processor(self, tcp_socket, protocol_paket):
        logger.debug("client tcp processor: %s" % protocol_paket)
        handler_name = service_code_name.get(protocol_paket.service_code, None)
        if not handler_name: 
            logger.error("service_code {} not config !!!".format(protocol_paket.service_code))
            return False

        client_type = protocol_paket.get_client_type()
        socket_client = ClientSocket(tcp_socket, client_type)
        logger.info("processor data length : %s"% len(protocol_paket.data))
        message = protocol_paket.data_json()
        logger.debug("Get from client data: %s" % message.keys())
        req_or_res = protocol_paket.req_or_res  # 1-req 2-reps
        if req_or_res == 1:
            mac = message.get("mac")
            token = message.get("token")
            logger.debug("Get from client Request head: {}, token: {}".format(protocol_paket, token))
        elif req_or_res == 2:
            mac = message.get("data", {}).get("mac")
            token = message.get("token")
            logger.debug("Get from client Response head: {}, token: {}".format(protocol_paket, token))
            # sequence_code get original message
        else:
            logger.error("req_or_res {} error !!!".format(req_or_res))
            return False

        if not mac:
            _terminal = voi_terminal_manager.get_client_by_token(token.decode("utf-8"))
            if not _terminal:
                logger.error("Request mac is null, drop message, please check")
                return False
            mac = _terminal.mac
            if not mac:
                logger.error("Request client mac is null, drop message, please check")
                return False
        _terminal = VOITerminal(self.client_ip, self.client_port, mac.upper())
        _terminal.set_client(socket_client, client_type)
        logger.info("get from client : %s, token: %s" % (_terminal, token))

        is_req = (True if req_or_res == 1 else False)
        seq_id = protocol_paket.sequence_code
        ret = voi_terminal_manager.client_biz_processor(_terminal, is_req, seq_id, handler_name, message)
        if not is_req:
            logger.debug("voi terminal response processor end")
            return True
        ret_str = json.dumps(ret)
        service_code = protocol_paket.service_code
        sequence_code = protocol_paket.sequence_code
        token = protocol_paket.data_json().get("token", "")
        if ret.get("code", None) == 0:
            if ret.get("data", None) and ret.get("data").get("token", None):
                token = ret.get("data").get("token").encode('utf-8')
        payload = ret_str.encode('utf-8')
        # payload = re.sub('[\\\]', '', json.dumps(ret_str)).encode('utf-8')
        logger.debug("input creat_paket: payload: {}, token: {}".format(payload, token))
        _size, msg = YzyProtocol().create_paket(service_code, payload, token,
                                                sequence_code=sequence_code, req_or_res=YzyProtocolType.RESP)
        logger.debug("_size: {}, msg: {}".format(_size, msg))
        tcp_socket.send(msg)
        logger.debug("voi terminal tcp processor end")
        return True
