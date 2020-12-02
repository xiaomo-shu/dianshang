import os
import socket
import time
import threading
import logging
from configparser import ConfigParser
from socketserver import BaseRequestHandler, ThreadingTCPServer
from common.constants import UKEY_DEFAULT_PORT, READ_UKEY_INTERVAL, BASE_DIR, BUF_SIZE, SEQ_ID, CLIENT_ID,IS_RESP
from yzy_ukey.ukey_tcp_protocol import YzyProtocol
from yzy_ukey.service_handler import ServiceHandler, read_auth_info_thread


logger = logging.getLogger(__name__)


class MyThreadingTCPServer(ThreadingTCPServer):
    allow_reuse_address = True



class ApiRequestHandler(BaseRequestHandler):
    """ Ukey TCP server handler"""

    header_length = YzyProtocol.header_length

    # def get_service(self, service_code):
    #     return

    # def finish(self):
    #     logger.info("Got connection close  from %s:%s" % self.client_address)

    def readAll(self, sz):
        buff = b''
        have = 0
        while have < sz:
            chunk = self.request.recv(sz - have)
            chunkLen = len(chunk)
            have += chunkLen
            buff += chunk
            if chunkLen == 0:
                # logger.error("read tcp error")
                return b''
        return buff

    def handle(self):
        # req = self.request
        self.request.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, BUF_SIZE)
        self.request.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUF_SIZE)
        self.request.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.request.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 15)
        self.request.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 3)
        self.request.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 5)

        logger.info("Got connection open from %s:%s" % self.client_address)
        while True:
            try:
                header = self.readAll(self.header_length)
                logger.debug("[Raw Request] client %s:%s, header: %s" %
                             (self.client_address[0], self.client_address[1], header))
                if not header:
                    self.handle_error("no header")
                    break
            except Exception as e:
                logger.exception("client: %s:%s" % (self.client_address[0], self.client_address[1]), exc_info=True)
                self.request.close()
                break

            try:
                paket_struct = YzyProtocol().parse_paket_header(header)
                logger.info("[Request] header: {}".format(paket_struct))
            except Exception as e:
                logger.exception("[Raw Request] client: %s:%s, parse protocol header fail: %s" %
                                 (e, self.client_address[0], self.client_address[1]), exc_info=True)
                self.handle_error(str(e))
                break

            # body_length = paket_struct.data_size + paket_struct.token_length + paket_struct.supplementary
            body_length = paket_struct.data_len
            try:
                body = self.readAll(body_length)
                if not body:
                    self.handle_error("no body")
                    break
            except Exception as e:
                logger.exception("tcp socket error: %s, %s:%s" %
                                 (e, self.client_address[0], self.client_address[1]), exc_info=True)
                self.request.close()
                break

            logger.debug("[Raw Request] client: {}:{} , body: {}, {}".format(
                self.client_address[0], self.client_address[1], len(body), body))
            paket_struct.set_data(body)
            service_handler = ServiceHandler(self.client_address[0], self.client_address[1])
            try:
                service_handler.processor(self.request, paket_struct)
            except Exception as e:
                logger.exception(str(e), exc_info=True)
                self.request.close()

            break


    def handle_error(self, error):
        logger.error(error)
        _size, msg = YzyProtocol().create_paket(SEQ_ID, CLIENT_ID, IS_RESP, error.encode("utf-8"))
        logger.debug("[Raw Response] _size: {}, msg: {}".format(_size, msg))
        self.request.send(msg)



def ukey_thread_monitor(thread_list):
    try:
        while True:
            for th in thread_list:
                status = th.isAlive()
                if not status:
                    logger.error("ukey tcp server thread_monitor: thread[%s], status[%s]" % (th.name, status))
            time.sleep(5)
    except Exception as e:
        logger.exception(str(e), exc_info=True)
        pass


def init_config(config_path="ukey_tcp_server.ini"):
    ret = {
        "interval": READ_UKEY_INTERVAL
    }
    if config_path == "ukey_tcp_server.ini":
        config_path = os.path.join(BASE_DIR, "config", config_path)
    conf = ConfigParser()
    conf.read(config_path)
    interval = conf.get("SERVER", "interval")
    if interval:
        ret["interval"] = int(interval)
        logger.info("get config from: %s, content: %s" % (config_path, ret))
    return ret


class UkeyTcpServer:

    def __init__(self, port=UKEY_DEFAULT_PORT, config_path="ukey_tcp_server.ini"):
        self.port = port
        self.config_path = config_path

    def run(self):
        try:
            conf_dict = init_config(self.config_path)
            thread_list = list()
            read_thread = threading.Thread(target=read_auth_info_thread, name="read_auth_info_thread", args=(conf_dict["interval"],))
            read_thread.start()
            thread_list.append(read_thread)

            # heartbeat_check = threading.Thread(target=voi_terminal_manager.check_client_heartbeat,
            #                                    name="terminal_heart_thread")
            # heartbeat_check.start()
            # thread_list.append(heartbeat_check)

            thread_monitor = threading.Thread(target=ukey_thread_monitor, args=(thread_list,))
            thread_monitor.start()

            logger.info("ukey tcp server start at port: %s" % self.port)
            serv = MyThreadingTCPServer(("0.0.0.0", self.port), ApiRequestHandler)
            serv.serve_forever()
        except Exception as e:
            logger.exception(str(e), exc_info=True)

