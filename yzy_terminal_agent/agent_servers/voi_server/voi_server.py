import socket
import json
import time
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
        self.request.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.request.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 15)
        self.request.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 3)
        self.request.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 5)

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
                logger.info("client %s:%s tcp protocol header %s" % (self.client_address[0],
                                                                     self.client_address[1], msg))
                if not msg:
                    break
            except Exception as e:
                logger.error("client: %s:%s" % (self.client_address[0], self.client_address[1]), exc_info=True)
                voi_terminal_manager.del_client_by_ip(self.client_address[0], self.client_address[1])
                logger.error(''.join(traceback.format_exc()))
                break

            try:
                paket_struct = YzyProtocol().parse_paket_header(msg)
                logger.debug("head: {}".format(paket_struct))
            except Exception as e:
                logger.error("client: %s:%s, parse protocol header fail: %s"% (e, self.client_address[0],
                                                                            self.client_address[1]), exc_info=True)
                logger.error(''.join(traceback.format_exc()))
                voi_terminal_manager.del_client_by_ip(self.client_address[0], self.client_address[1])
                self.request.close()
                break

            body_length = paket_struct.data_size + paket_struct.token_length + paket_struct.supplementary
            try:
                body = self.readAll(body_length)
                if not body:
                    break
            except Exception as e:
                logger.error("tcp socket error: %s, %s:%s"%(e, self.client_address[0],
                                                              self.client_address[1]), exc_info=True)
                voi_terminal_manager.del_client_by_ip(self.client_address[0], self.client_address[1])
                self.request.close()
                break
            logger.debug("client: {}:{} tcp read body: {}, {}".format(self.client_address[0],
                                                              self.client_address[1], len(body), body))
            paket_struct.set_data(body)
            service_handler = ServiceHandler(self.client_address[0], self.client_address[1])
            try:
                service_handler.processor(self.request, paket_struct)
            except Exception as err:
                logger.error("Error: {}".format(err))
                logger.error(''.join(traceback.format_exc()))


def voi_thread_monitor(thread_list):
    try:
        while True:
            for th in thread_list:
                logger.info("voi server thread_monitor : %s the status is: %s"% (th.name, th.isAlive()))
            time.sleep(5)
    except:
        logger.error("", exc_info=True)
        pass


class VOITerminalServer:

    def __init__(self, port=VOI_TERMINAL_LISTEN_DEFAULT_PORT, max_listen=10):
        self.port = port

    def run(self):
        try:
            thread_list = list()
            t = threading.Thread(target=voi_terminal_manager.run, name="terminal_message_thread")
            t.start()
            thread_list.append(t)
            heartbeat_check = threading.Thread(target=voi_terminal_manager.check_client_heartbeat,
                                               name="terminal_heart_thread")
            heartbeat_check.start()
            thread_list.append(heartbeat_check)
            thread_monitor = threading.Thread(target=voi_thread_monitor, args=(thread_list,))
            thread_monitor.start()
            logger.info("voi terminal server start ......")
            serv = MyThreadingTCPServer(('', self.port), ApiRequestHandler)
            serv.serve_forever()
        except Exception as e:
            logger.error("", exc_info=True)
            logger.error(''.join(traceback.format_exc()))
            pass

