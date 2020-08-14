#!/usr/bin/env python
# # -*- coding: utf-8 -*-

import sys
import os
from thrift.TMultiplexedProcessor import TMultiplexedProcessor
from thrift.protocol import TBinaryProtocol, TCompactProtocol
from thrift.server import TServer
from thrift.transport import TTransport, TSocket
sys.path.append('./gen-py')
from terminal import ManageService
from terminal import FileService
from terminal import ConnectService
from terminal.ttypes import *

import threading
import hashlib
import time
import datetime as dt


client_list = {}
client_list_tmp = {}

dir_map = {FileType.LOG: "/tmp/zhouli/log/",
           FileType.SOFT: "/tmp/zhouli/soft/",
           FileType.PATCH: "/tmp/zhouli/patch/"}

def get_md5(input_str):
    md5 = hashlib.md5()
    md5.update(input_str.encode('utf8'))
    md5_value = md5.hexdigest()    
    return md5_value


class ConnectServiceHandler():
    def client_connected(self, oprot):
        global client_list_tmp
        try:
            client = ConnectService.Client(oprot)
            client_md5 = get_md5(str(oprot))
            client_list_tmp[client_md5] = oprot
            if oprot.trans.isOpen():
                client.TokenId(client_md5)
                print('Client.token_id called {}'.format(client_md5))
        except TTransport.TTransportException as tx:
            print("1111111 client_connected Error TTransport.TTransportException == {}".format(tx))
        except Exception as x:
            print("Error Exeption == {}".format(x))

    def client_closed(self, oprot):
        client = ConnectService.Client(oprot)
        client_md5 = get_md5(str(oprot))
        client_list_tmp.pop(client_md5)
        if client_md5 in client_list.keys():
            client_list.pop(client_md5)
            print('Delete client oprot == {}'.format(client_md5))

    def Command(self, msg):
        print('Get client Command == {}'.format(msg.cmdstr))

    def TokenId(self, token_id):
        global client_list
        if token_id in client_list_tmp.keys():
            client_list[token_id] = client_list_tmp[token_id]
            print('Add Client = {}'.format(token_id))

    def Ping(self, token_id, time):
        try:
            print('Get client ping.............. {} '.format(token_id))
            if token_id in client_list.keys():
                if client_list[token_id].trans.isOpen():
                    client = ConnectService.Client(client_list[token_id])
                    int_time = int(dt.datetime.now().timestamp() - dt.datetime.utcfromtimestamp(0).timestamp())
                    client.Ping(token_id, int_time)
        except TTransport.TTransportException as tx:
            print("2222222 Ping Error TTransport.TTransportException == {}".format(tx))
        except Exception as x:
            print("Error Exeption == {}".format(x))

   
class ManageServiceHandler:
     def user_login(self, user): # ;//登录方法 判断是否激活
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         return True

     def user_modify_passwd(self, old_user, new_user):
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         return True

     def get_dskgrop_info(self, mac, user):
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         #return list<DesktopGropInfo>
         return None

     def get_desktop_info(self):
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         #return list<TerminalDesktopInfo>
         return None

     def desktop_open(self, desktop_group_info, mac, user):
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         dsk_info = DesktopInfo() 
         return dsk_info

     def desktop_close(self, desktop_info):
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         return True

     def get_config_version(self, mac):
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         return mac

     def get_config(self, mac):
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         #return TerminalConf 
         return None

     def update_config(self, client_info):
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         return True

     def datetime(self):
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         #return string
         return "2020-03-03 14:40:22"


class FileServiceHandler():
     def get_file_size(self, file_name, file_type): # ;(self, 1:string fileName);
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         file_abs_path = dir_map[file_type] + file_name
         file_size = os.path.getsize(file_abs_path)
         print('{} size: {} '.format(file_abs_path, file_size))
         return file_size

     def read_bytes(self, read_info): # ;(self, 1:string fileName,2:i64 offset,3:i32 length);
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         global dir_map
         file_abs_path = dir_map[read_info.file_type] + read_info.file_name
         if not os.path.exists(file_abs_path):
             print("Error Exeption file not exists {}".format(file_abs_path))
             return None
         fd = None
         try:
             fd = open(file_abs_path, 'rb')
             fd.seek(read_info.operate_offset)
             read_data = fd.read(read_info.operate_length)
             fd.close() 
             return read_data
         except Exception as x:
             print("Error Exeption == {}".format(x))
             fd.close() 
             return None

     def write_bytes(self, write_info, data): # ;(self, 1:string fileName,2:i64 offset,3:i32 length);
         print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
         global dir_map
         file_abs_path = dir_map[write_info.file_type] + write_info.file_name
         fd = None
         try:
             fd = open(file_abs_path, 'wb')
             fd.seek(write_info.operate_offset)
             read_data = fd.write(data)
             fd.close() 
             return True
         except Exception as x:
             print("Error Exeption == {}".format(x))
             fd.close() 
             return False

def do_command_call():
    global client_list 
    try:
        while True:
            client_tmp_list = client_list.copy()
            for token_id in client_tmp_list.keys():
                client = ConnectService.Client(client_tmp_list[token_id])
                int_time = int(dt.datetime.now().timestamp() - dt.datetime.utcfromtimestamp(0).timestamp())
                client.Ping(token_id, int_time)
                time.sleep(1)
            time.sleep(1)
    except TTransport.TTransportException as tx:
        print("do_command_call Error TTransport.TTransportException == {}".format(tx))
    except Exception as x:
        print("Error Exeption == {}".format(x))
        

def thrift_connect_handler(server):
    global connect_handler
    while True:
        try:
            [msq_type, protocol] = server.conn_mq.get()
            if msq_type:
                connect_handler.client_connected(protocol)
            else:
                connect_handler.client_closed(protocol)
        except Exception as x:
            print("Error Exeption == {}".format(x))

    
mng_handler = ManageServiceHandler()
mng_processor = ManageService.Processor(mng_handler)

file_handler = FileServiceHandler()
file_processor = FileService.Processor(file_handler)

connect_handler = ConnectServiceHandler()
conn_processor = ConnectService.Processor(connect_handler)

tfactory = TTransport.TBufferedTransportFactory()
pfactory = TBinaryProtocol.TBinaryProtocolFactory()

processor = TMultiplexedProcessor() #使用TMultiplexedProcessor接收多个处理
processor.registerProcessor("ManageService", mng_processor)
processor.registerProcessor("FileService", file_processor)
processor.registerProcessor("ConnectService", conn_processor)


transport = TSocket.TServerSocket('0.0.0.0', 9999)
#server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
server.setNumThreads(6000) # 1个主线程 1个监听线程 + 多少个通信线程
# start client connect handler: save client socket info
conn_mq_thread = threading.Thread(target=thrift_connect_handler, args=(server,)) 
conn_mq_thread.start()
t = threading.Thread(target=server.serve)
#t.setDaemon(self.daemon)
t.start()
# send client rpc loop client_list
t_client = threading.Thread(target=do_command_call)
t_client.start()
