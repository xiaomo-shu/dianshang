#!/usr/bin/env python
# # -*- coding: utf-8 -*-
import pdb
import sys
import json 
import os
from thrift.protocol.TMultiplexedProtocol import TMultiplexedProtocol

sys.path.append('../thrift_protocols/')
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol, TCompactProtocol
from terminal import ManageService
from terminal import FileService
from terminal import ConnectService
from terminal.ttypes import *
import time
import threading
from functools import wraps
import random

client_token_id = None 

def timefn(fn):
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        print("@timefn:" + fn.__name__ + " took " + str(t2 - t1) + " seconds")
        return result
    return measure_time


class ConnectServiceHandler():
    def __init__(self, protocol):
        self.token_id = None 
        self.protocol = protocol

    def TokenId(self, token_id):
        global client_token_id
        print('Get Sever token_id {}'.format(token_id))
        self.token_id = token_id
        client_token_id = token_id
        conn_client = ConnectService.Client(self.protocol)
        conn_client.TokenId(self.token_id)

    def Ping(self, token_id, time):
        print('Get Sever ping {} time {}'.format(token_id, time))


    def Command(self, msg):
        global mac
        print('{}.{} be called'.format(self.__class__.__name__, sys._getframe().f_code.co_name))
        print('Command Get server msg {} '.format(msg))
        if msg.cmdstr == "upload_log":
            start_time = msg.ArgsDic['start_time']
            file_name = mac + "_" + start_time + ".zip"
            for x in range(10):
                os.popen('echo "234lkslafkjsldkflasdfjasldfas" * 9000 >> {}'.format(file_name))
            file_protocol = get_protocol("FileService")
            file_client = FileService.Client(file_protocol)
            upload_log(file_name, file_client)
            file_client.trans.close()
        #print('Command Get server msg {} \n body {}'.format(msg, msg.Body))
        #print('ip: {}'.format(json.loads(msg.Body)['Ip']))


class ConnectServiceNoneHandler():
    def TokenId(self, token_id):
        pass

    def Ping(self, token_id):
        pass

    def Command(self, msg):
        pass


def startThreadService(func, *args, **kwargs):
    try:
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.start()
        return t
    except KeyboardInterrupt:
        raise
    except Exception as x:
        print("Except == {}".format(x))
    return None


def get_protocol(service_name):
    transport = TSocket.TSocket('127.0.0.1', 9999)
    transport = TTransport.TBufferedTransport(transport)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    defined_protocol = TMultiplexedProtocol(protocol, service_name)
    transport.open()#打开链接
    time.sleep(0.5)
    if transport.isOpen():
        connect_handler = ConnectServiceNoneHandler()
        conn_processor = ConnectService.Processor(connect_handler)
        if conn_processor.process(protocol, protocol):
            return defined_protocol
    return None


def mng_client_process(client_info):
    global client_token_id
    #mac = "{}:{}:{}:{}:{}:{}".format(random.randint(10,99), random.randint(10,99),
    #                                 random.randint(10,99), random.randint(10,99),
    #                                 random.randint(10,99), random.randint(10,99))

    mac_input = client_info.TerminalConfInfo.mac
    hard_info = HardwareInfo("cpuid_11111111", "harddisk_2222222", mac_input, "yunid_444444444")
    try:
        mng_protocol = get_protocol("ManageService")
        mng_client = ManageService.Client(mng_protocol)
        cmd = CommandMsg()
        cmd.cmdstr = 'order'
        cmd.batch_num = 11
        cmd.ArgsDic = {} 
        cmd.ArgsDic['terminal_id'] = "27" 
        print(mng_client.ClientLogin(client_token_id, hard_info))
        #user_info = UserInfo("user1", "123456")
        #ret = mng_client.user_login(user_info, mac_input)
        #print('mng_client.user_login get ret {}'.format(ret))
        #print('mng_client.user_login get description type{} {}'.format(type(json.loads(ret.Description)), json.loads(ret.Description)))
        while True:
             print(mng_client.update_config(client_info))
             print(mng_client.GetDateTime())
             #print(mng_client.command_confirm(cmd, str(mac_input)))
             #print(mng_client.get_desktop_info())
             time.sleep(5)
    except TTransport.TTransportException as tx:
        print("mng_client_process Error TTransport.TTransportException == {}".format(tx))
    except Exception as x:
        print("22222Error Exeption == {}".format(x))

@timefn
def download_soft(file_name, file_client):
    read_len_once = 1024*1024
    file_size = file_client.get_file_size(file_name, FileType.SOFT)
    print("File {} size is {}".format(file_name, file_size))
    readed_size = 0
    fd = open(file_name, 'wb')
    while (readed_size < file_size):
        file_info = FileCtrlInfo(file_name=file_name, 
                                 file_type=FileType.SOFT, 
                                 total_size=file_size, 
                                 operate_offset=readed_size,
                                 operate_length=read_len_once)
        read_data = file_client.read_bytes(file_info)
        fd.write(read_data)
        readed_size += read_len_once
    fd.close()
 

@timefn
def upload_log(file_name, file_client):
    write_len_once = 1024*1024
    write_len_once = 1024
    file_size = os.path.getsize(file_name)
    print("File {} size is {}".format(file_name, file_size))
    write_size = 0
    fd = open(file_name, 'rb')
    while (write_size < file_size):
        fd.seek(write_size)
        write_data = fd.read(write_len_once)
        file_info = FileCtrlInfo(file_name=file_name, 
                                 file_type=FileType.LOG, 
                                 total_size=file_size, 
                                 operate_offset=write_size,
                                 operate_length=len(write_data))
        file_client.write_bytes(file_info, write_data)
        write_size += len(write_data)
    fd.close()
 

def file_client_process():
    try:
        #transport = TSocket.TSocket()
        #transport = TTransport.TBufferedTransport(transport)
        #protocol = TBinaryProtocol.TBinaryProtocol(transport)
        #file_protocol = TMultiplexedProtocol(protocol, 'file')
        #file_client = FileService.Client(file_protocol)
        #transport.open()#打开链接
        #time.sleep(0.5)
        file_protocol = get_protocol("FileService")
        file_client = FileService.Client(file_protocol)
        #### download soft file 
        file_name = "x86_windows_v2.2.2.0.zip"
        download_soft(file_name, file_client)
        #### upload log file 
        file_name = "xxx.log"
        upload_log(file_name, file_client)

    except TTransport.TTransportException as tx:
        print("file_client_process Error TTransport.TTransportException == {}".format(tx))
    except Exception as x:
        print("Error Exeption == {}".format(x))


def cmd_server_process():
    try:
        transport = TSocket.TSocket('127.0.0.1', 9999)
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        mul_protocol = TMultiplexedProtocol(protocol, "ConnectService")
        connect_handler = ConnectServiceHandler(mul_protocol)
        conn_processor = ConnectService.Processor(connect_handler)
        transport.open()#打开链接
        #startThreadService(cmd_client_process, mul_protocol, cmdstr="TestCmd")
        while True:
             conn_processor.process(protocol, protocol)
    except TTransport.TTransportException as tx:
        print("cmd_server_process Error TTransport.TTransportException == {}".format(tx))
    except Exception as x:
        print("Error Exeption == {}".format(x))

def cmd_client_process(protocol, cmdstr=None):
    try:
        conn_client = ConnectService.Client(protocol)
        cmd = CommandMsg()
        cmd.cmdstr = cmdstr
        while True:
            conn_client.Command(cmd)
            time.sleep(3)
    except TTransport.TTransportException as tx:
        print("cmd_client_process Error TTransport.TTransportException == {}".format(tx))
    except Exception as x:
        print("Error Exeption == {}".format(x))


client_info = ClientInfo()
ip_info = IPInfo(IsDhcp=0, Ip='192.168.1.22', Subnet='255.255.255.0', Gateway='192.168.1.1', Mac='', DNS1='118.118.118.118', DNS2='8.8.8.8')
terminal_conf = TerminalConf()
terminal_conf.ip_info = ip_info
terminal_conf.platform = "ARM"
terminal_conf.soft_version = "2.2.2.0"
terminal_conf.show_desktop_type = 1
terminal_conf.auto_desktop = 0
terminal_conf.close_strategy = 0
terminal_conf.open_strategy = True
terminal_conf.server_info = ServiceInfo(Ip='127.0.0.1', Port=9999)
terminal_conf.screen_info_list = [ScreenInfo(Width=1920, Height=1080), ScreenInfo(Width=1600, Height=900), 
                                  ScreenInfo(Width=1280, Height=720), ScreenInfo(Width=800, Height=600)]
terminal_conf.current_screen_info = ScreenInfo(Width=1920, Height=1080) 
terminal_conf.show_modify_user_passwd = True
terminal_conf.termial_setup_passwd = "222222"
terminal_conf.conf_version = 0
terminal_conf.window_mode = 2
terminal_conf.disconnect_setup = DisconnectSetup(goto_local_desktop=5, goto_local_auth=True)
terminal_conf.show = DisplaySetup(show_local_button=True, goto_local_passwd="123456")
client_info.TerminalConfInfo = terminal_conf

if __name__ == "__main__":
    mac = sys.argv[1]
    mac_last = mac.split(':')[-1]
    startThreadService(cmd_server_process)
    #startThreadService(file_client_process)
    client_info.TerminalConfInfo.ip_info.Ip = "192.168.1.%s" % mac_last
    client_info.TerminalConfInfo.ip_info.Gateway = "192.168.1.1"
    client_info.TerminalConfInfo.ip_info.Mac = mac
    client_info.TerminalConfInfo.terminal_id = int(mac_last)
    client_info.TerminalConfInfo.terminal_name = "503-%s" % mac_last
    client_info.TerminalConfInfo.mac = mac
    startThreadService(mng_client_process, client_info)
