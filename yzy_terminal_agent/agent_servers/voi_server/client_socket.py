import json
import logging
import threading
from yzy_terminal_agent.ext_libs.yzy_protocol import YzyProtocol, YzyProtocolType, ClientType, YzyProtocolDataType
from gevent.lock import BoundedSemaphore

sem = BoundedSemaphore(1)
locker = threading.Lock()

logger = logging.getLogger("agentTcp")


class ClientSocket:

    def __init__(self, socket, socket_type):
        self.socket = socket
        self.socket_type = socket_type

    def client_type(self):
        return self.socket_type

    def send(self, payload_data, service_code, token="", data_type=YzyProtocolDataType.JSON, supplemenetary=""):
        # locker.acquire()
        if payload_data:
            if data_type == YzyProtocolDataType.JSON :
                send_data = json.dumps(payload_data).encode("utf-8")
            else:
                send_data = payload_data
        else:
            send_data = b''
        _size, msg = YzyProtocol().create_paket(service_code, send_data, token.encode('utf-8'),
                                                req_or_res=YzyProtocolType.REQ, supplemenetary=supplemenetary)
        # sem.acquire(1)
        self.socket.sendall(msg)
        logger.debug("Request terminal: msg_size {}, msg: {}".format(_size, msg[:1000]))
        # sem.release()

    def recv(self, max_recv=8192):
        msg = self.socket.recv(max_recv)
        return msg

