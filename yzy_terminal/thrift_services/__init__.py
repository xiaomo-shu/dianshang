import os
import sys
import time
import threading
import logging
import importlib
from flask import current_app
from yzy_terminal.thrift.TMultiplexedProcessor import TMultiplexedProcessor
from yzy_terminal.thrift.protocol import TBinaryProtocol, TCompactProtocol
from yzy_terminal.thrift.server import TServer
from yzy_terminal.thrift.transport import TTransport, TSocket
from yzy_terminal.thrift_services.connect_service_handler import *
from yzy_terminal.thrift_services.manage_service_handler import *
from yzy_terminal.database import api as db_api
from common.utils import is_ip_addr
from yzy_terminal.thrift_services.file_service_handler import FileServiceHandler
import yzy_terminal.thrift_protocols.terminal.FileService as service_cls


def do_status_check(app):
    # 1. iterate mac_token:
    #    1.1 if token_status exists
    #       1.1.1 if status is False:
    #           update yzy_terminal status to '0'
    #           close client
    #           pop mac_token, token_client, token_status
    #       1.1.2 if status is True:
    #           reset status to False(terminal call Ping to set True every 10 seconds)
    #    1.2 if token_status not exists, print error

        # set loop_seconds must > 10
    loop_seconds = 30
    while True:
        try:
            with app.app_context():
                table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                token_client = app.token_client
                mac_token = app.mac_token
                token_status = app.token_status
                logging.debug('token_client {}, mac_token {}, token_status {}'.format(token_client,
                                                                                     mac_token, token_status))
                mac_token_keys = list(mac_token.keys())
                token_client_keys = list(token_client.keys())

                # update database data not in mac_token
                all_online_terminals = table_api.select_all_online_terminal()
                all_online_terminals = [qry.mac for qry in all_online_terminals if qry.mac]
                except_terminals = [mac for mac in all_online_terminals if mac not in mac_token_keys]
                if except_terminals:
                    logging.debug("database except terminals: {}, set offline".format(except_terminals))
                    table_api.update_terminal_by_macs(except_terminals, db_api.TerminalStatus.OFFLINE)

                for mac in mac_token_keys:
                    token_id = mac_token[mac]
                    if token_id in token_status.keys():
                        if token_status[token_id]:
                            token_status[token_id] = False
                        else:
                            mac_token.pop(mac)
                            token_status.pop(token_id)
                            logging.debug('pop mac_token, pop token_status {}'.format(mac))
                            if token_id in token_client_keys:
                                token_client[token_id].trans.close()
                                token_client.pop(token_id)
                                logging.debug('close client, pop token_client {}'.format(mac))
                            else:
                                logging.error('token_id no key in token_client !!!')
                            qry = table_api.select_terminal_by_mac(mac)
                            if qry:
                                table_api.update_terminal_by_mac(**{'mac': mac, 'status': '0'})
                                logging.debug('set yzy_terminal offline {}'.format(mac))
                            else:
                                logging.error('mac not in yzy_terminal {} !!!'.format(mac))
                    else:
                        logging.error('token_id no key in token_status !!!')
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
        time.sleep(loop_seconds)


def thrift_connect_handler(server, connect_handler, app):
    while True:
        try:
            [msq_type, protocol] = server.conn_mq.get()
            if msq_type:
                connect_handler.client_connected(protocol)
            else:
                connect_handler.client_closed(protocol, app)
        except Exception as x:
            logging.error("[{}]: Error Exeption == {}".format(sys._getframe().f_lineno, x))


def set_terminal_offline(app):
    with app.app_context():
        table_api = db_api.YzyTerminalTableCtrl(current_app.db)
        table_api.reset_all_terminal_offline()


def setup_and_start(app):
    token_client = app.token_client
    mac_token = app.mac_token
    token_status = app.token_status
    order_lock = app.order_lock
    logging.info('starting thrift server ..............................')
    try:
        # 0. update all terminal status to offline
        set_terminal_offline(app)

        # 1. create processor and register processor
        processor = TMultiplexedProcessor()

        # path = os.path.dirname(os.path.abspath(__file__))
        # service_dir, service_package = os.path.split(path)
        # services_files = os.listdir(path)
        # for file_name in services_files:
        #     if file_name.endswith('.py') and file_name not in ('__init__.py', 'connect_service_handler.py',
        #                                                        'manage_service_handler.py'):
        #         full_file_name = file_name.split('.')[0]
        #         package = 'yzy_terminal.%s' % service_package + "." + full_file_name
        #         logging.debug(package)
        #         module = __import__(package, fromlist=['.'])
        #         names = full_file_name.split('_')
        #         handler_class_name = names[0].capitalize() + names[1].capitalize() + names[2].capitalize()
        #         service_class_name = names[0].capitalize() + names[1].capitalize()
        #         handler_cls = getattr(module, ''.join(handler_class_name))
        #         logging.debug("handler_class_name {} ,service_class_name {}".format(handler_class_name, service_class_name))
        #         sub_handler = handler_cls()
        #         logging.debug('cwd = {}'.format(os.getcwd()))
        #         package = 'yzy_terminal.thrift_protocols.terminal'
        #         module_terminal = __import__(package, fromlist=['yzy_terminal/thrift_protocols/'])
        #         service_cls = getattr(module_terminal, ''.join(service_class_name))
        #         sub_processor = service_cls.Processor(sub_handler)
        #         processor.registerProcessor(service_class_name, sub_processor)

        service_class_name = 'FileService'
        sub_handler = FileServiceHandler()
        logging.debug('cwd = {}'.format(os.getcwd()))
        sub_processor = service_cls.Processor(sub_handler)
        processor.registerProcessor(service_class_name, sub_processor)

        # 2. create connect processor and register connect processor (twoway communication)
        connect_handler = ConnectServiceHandler(token_client, mac_token, token_status)
        conn_processor = ConnectService.Processor(connect_handler)
        processor.registerProcessor("ConnectService", conn_processor)
        manage_handler = ManageServiceHandler(app)
        mng_processor = ManageService.Processor(manage_handler)
        processor.registerProcessor("ManageService", mng_processor)
        # 3. start serve
        transport = TSocket.TServerSocket("0.0.0.0", 9999)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()
        server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
        server.setNumThreads(6000) # 1个主线程 1个监听线程 + 多少个通信线程

        # start client connect handler: save client socket info
        conn_mq_thread = threading.Thread(target=thrift_connect_handler, 
                                          args=(server, connect_handler, app))
        conn_mq_thread.start()

        # start thrift server
        t = threading.Thread(target=server.serve)
        t.start()
        # 4. start web task handler thread
        web_thread = threading.Thread(target=do_status_check, args=(app,))
        web_thread.start()
        logging.info('start thrift server successfully ..............................') 
    except Exception as err:
        logging.error(err)
        logging.debug(''.join(traceback.format_exc()))
        raise Exception("load service error")

