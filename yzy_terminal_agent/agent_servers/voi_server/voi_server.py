import socket
import json
import os
import threading
import ctypes
import logging
import traceback
from common.constants import VOI_TERMINAL_LISTEN_DEFAULT_PORT, BUF_SIZE
from yzy_terminal_agent.ext_libs.yzy_protocol import YzyProtocol, YzyProtocolPaket, YzyTorrentStruct
from .voi_manager import voi_terminal_manager
from .service_handler import ServiceHandler
from socketserver import BaseRequestHandler, TCPServer, ThreadingTCPServer
from gevent.lock import BoundedSemaphore

sem = BoundedSemaphore(5)


class MyThreadingTCPServer(ThreadingTCPServer):
    allow_reuse_address = True


logger = logging.getLogger("agentTcp")


class ApiRequestHandler(BaseRequestHandler):
    """ TCP server handler"""

    headr_length = YzyProtocol.header_length

    def get_service(self, service_code):
        return

    def finish(self):
        logger.info("Got connection close  from %s:%s" % self.client_address)

    def readAll(self, sz):
        buff = b''
        have = 0
        while (have < sz):
            chunk = self.request.recv(sz - have)
            chunkLen = len(chunk)
            have += chunkLen
            buff += chunk
            if chunkLen == 0:
                logger.error("read tcp error")
                return b''
        return buff
           
    def handle(self):
        # req = self.request
        self.request.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, BUF_SIZE)
        self.request.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUF_SIZE)

        logger.info("Got connection open from %s:%s"% self.client_address)
        while True:
            thread_id = ctypes.CDLL('libc.so.6').syscall(186)
            logger.info("from %s:%s  pid: %s, ppid: %s, tid: %s, t_ident: %s" % (self.client_address[0],
                                                                                 self.client_address[1],
                                                                                 os.getpid(), os.getppid(),
                                                                                 thread_id,
                                                                                 threading.currentThread().ident))
            msg = ''
            try:
                #msg = self.request.recv(self.headr_length)
                msg = self.readAll(self.headr_length)
                logger.info("tcp protocol header %s" % msg)
                if not msg:
                    break
            except Exception as e:
                logger.error("", exc_info=True)
                voi_terminal_manager.del_client_by_ip(self.client_address[0], self.client_address[1])
                logger.error(''.join(traceback.format_exc()))
                break

            try:
                paket_struct = YzyProtocol().parse_paket_header(msg)
                logger.debug("head: {}".format(paket_struct))
            except Exception as e:
                logger.error("parse protocol header fail: %s"% e, exc_info=True)
                logger.error(''.join(traceback.format_exc()))
                voi_terminal_manager.del_client_by_ip(self.client_address[0], self.client_address[1])
                self.request.close()
                break

            body_length = paket_struct.data_size + paket_struct.token_length + paket_struct.supplementary
            try:
                body = self.readAll(body_length)
                if not body:
                    break
                #body = self.request.recv(body_length)
            except Exception as e:
                logger.error("tcp socket error: %s" % e, exc_info=True)
                logger.error(''.join(traceback.format_exc()))
                voi_terminal_manager.del_client_by_ip(self.client_address[0], self.client_address[1])
                self.request.close()
                break
            logger.debug("tcp read body: {}, {}".format(body[:100], len(body)))
            paket_struct.set_data(body)
            service_handler = ServiceHandler(self.client_address[0], self.client_address[1])
            # func = service_handler.code_to_service_func(paket_struct.service_code)
            # if not func:
            #     logger.error("not function to %s" % paket_struct.service_code)
            #     continue
            try:
                # func(self.request, paket_struct)
                # sem.acquire(1)
                service_handler.processor(self.request, paket_struct)
                # sem.release()
            except Exception as err:
                logger.error("Error: {}".format(err))
                logger.error(''.join(traceback.format_exc()))


class VOITerminalServer:

    def __init__(self, port=VOI_TERMINAL_LISTEN_DEFAULT_PORT, max_listen=10):
        self.port = port

    def run(self):
        try:
            t = threading.Thread(target=voi_terminal_manager.run)
            t.start()
            heartbeat_check = threading.Thread(target=voi_terminal_manager.check_client_heartbeat)
            heartbeat_check.start()
            logger.info("voi terminal server start ......")
            serv = MyThreadingTCPServer(('', self.port), ApiRequestHandler)
            serv.serve_forever()
        except Exception as e:
            logger.error("", exc_info=True)
            logger.error(''.join(traceback.format_exc()))
            pass

