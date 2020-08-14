import time
import traceback
import json
import threading
import sys
sys.path.append('/usr/local/yzy-kvm/')
from yzy_terminal_agent.ext_libs.yzy_protocol import *
from yzy_terminal_agent.agent_servers.voi_server.service_code import service_code_name, name_service_code
from socket import socket, AF_INET, SOCK_STREAM
s = socket(AF_INET, SOCK_STREAM)
s.connect(('127.0.0.1', 50007))


class HeartBeatRequest(threading.Thread):
    def __init__(self, mac, token):
        threading.Thread.__init__(self)
        self.mac = mac
        self.token = token 
        print("input mac: {}, token: {}".format(mac, token))

    def run(self):
        print("HeartBeatRequest request server .........................")
        while True:
            try:
                service_name = "heartbeat"
                ret_str = json.dumps(eval(service_name + "_data"))
                service_code = name_service_code[service_name]
                sequence_code = 2
                #token = b"43210"
                _size, msg = YzyProtocol().create_paket(service_code, ret_str.encode("utf-8"), self.token,
                                                        sequence_code=sequence_code, req_or_res=YzyProtocolType.REQ, client_type=ClientType.WINDOWS)
                print("Send msg size: {}, msg: {}".format(_size, msg))
                s.send(msg)

                time.sleep(10)
            except Exception as e:
                print("tcp socket error: %s" % e)
                print(''.join(traceback.format_exc()))
                break


class ServerRequestHandler(threading.Thread):
    def __init__(self, mac, token):
        threading.Thread.__init__(self)
        self.mac = mac
        self.token = token 
        print("input mac: {}, token: {}".format(mac, token))

    def run(self):
        print("Ready geting data from server .........................")
        while True:
            msg = s.recv(24)
            if not msg:
                continue
            paket_struct = YzyProtocol().parse_paket_header(msg)
            print("Get head: {}".format(msg))
            print("Parse head: {}".format(paket_struct))
            body_length = paket_struct.data_size + paket_struct.token_length + paket_struct.supplementary
            try:
                if paket_struct.req_or_res == 2: # 1-request, 2-response
                    print("Get response: service_code[{}-{}], sequence_no[{}] 222222222222222222222222222222222".format(
                        paket_struct.service_code,
                        service_code_name[paket_struct.service_code],
                        paket_struct.sequence_code,
                    ))
                       
                         
                    body = s.recv(body_length)
                    paket_struct.set_data(body)
                    print("Get body: {}".format(body))
                    if body:
                        ret_data = paket_struct.data_json()
                        if service_code_name[paket_struct.service_code] == 'terminal_login' and paket_struct.token_length:
                            self.token = ret_data['token']
                            print("5555555555555555555555 Get token: {}".format(ret_data['token']))
                        print("Parsed body: {}".format(ret_data))
                    if service_code_name[paket_struct.service_code] == 'order_query':
                        if ret_data['data']["terminal_id"] == -1:
                            print("get order_query: -1 , continue")
                            continue
                        print("Order_query get terminal id({})".format(ret_data['data']["terminal_id"]))
                        confirm_id = int(input("#####################################################please input confirm terminal id(0 is not confirm):"))
                        if not confirm_id:
                            continue
                        input_data = {
                            "mac": self.mac,
                            "batch_no": ret_data['data']["batch_no"],
                            "terminal_id": confirm_id,
                        }
                        request_order_confirm(input_data)
                        print("send order_confirm: {}".format(input_data))
                elif paket_struct.req_or_res == 1: # 1-request, 2-response
                    print("Get request: service_code[{}-{}], sequence_no[{}] 1111111111111111111111111111111111".format(
                        paket_struct.service_code,
                        service_code_name[paket_struct.service_code],
                        paket_struct.sequence_code,
                    ))
                    body = s.recv(body_length)
                    if service_code_name[paket_struct.service_code] == 'send_torrent':
                        continue
                    paket_struct.set_data(body)
                    print("Get body: {}".format(body))
                    if body:
                        ret_data = paket_struct.data_json()
                        print("Parsed body: {}".format(ret_data))
                    ## send response
                    resp_data = {
                        "code": 0,
                        "en_msg": "Success",
                        "data": {
                            "batch_no": ret_data["batch_no"],
                            "mac": self.mac
                        }
                    }
                    _size, msg = YzyProtocol().create_paket(paket_struct.service_code,
                                                            json.dumps(resp_data).encode("utf-8"),
                                                            ret_data['token'],
                                                            sequence_code=paket_struct.sequence_code,
                                                            req_or_res=YzyProtocolType.RESP,
                                                            client_type=ClientType.WINDOWS)
                    print("Send Response size: {}, msg: {}".format(_size, msg))
                    s.send(msg)
                    ####### get order command 
                    if service_code_name[paket_struct.service_code] == 'order':
                        if ret_data["terminal_id"] == -1:
                            print("get order: -1 , continue")
                            continue
                        print("Order get terminal id({})".format(ret_data["terminal_id"]))
                        confirm_id = int(input("#####################################################please input confirm terminal id(0 is not confirm):"))
                        if not confirm_id:
                            continue
                        input_data = {
                            "mac": self.mac,
                            "batch_no": ret_data["batch_no"],
                            "terminal_id": confirm_id,
                        }
                        request_order_confirm(input_data)
                        print("send order_confirm: {}".format(input_data))

                else:
                    print("message type error")
            except Exception as e:
                print("tcp socket error: %s" % e)
                print(''.join(traceback.format_exc()))
                break


# msg = json.dumps(data).encode("utf-8")
msg = b'\x01\x00\x00\x00\x01\x00\x00\x00\xb7\x15\x00\x00,\x00\x00\x00\x01\x00\x01\x01\x08\x00\x00\x0012345678{"mac": "11111-11111", "ip": "172.16.1.155"}'

def request_service(service_name):
    global token
    t = time.time()
    ret_str = json.dumps(eval(service_name + "_data"))
    print("send {} data: {}".format(service_name, ret_str))
    service_code = name_service_code[service_name]
    sequence_code = 2
    #token = b"43210"
    _size, msg = YzyProtocol().create_paket(service_code, ret_str.encode("utf-8"), token,
                                            sequence_code=sequence_code, req_or_res=YzyProtocolType.REQ, client_type=ClientType.WINDOWS)
    print("Send msg size: {}, msg: {}".format(_size, msg))
    s.send(msg)

def request_order_confirm(input_data):
    global token
    t = time.time()
    ret_str = json.dumps(input_data)
    service_name = "order_confirm"
    print("send {} data: {}".format(service_name, ret_str))
    service_code = name_service_code[service_name]
    sequence_code = 2
    #token = b"43210"
    _size, msg = YzyProtocol().create_paket(service_code, ret_str.encode("utf-8"), token,
                                            sequence_code=sequence_code, req_or_res=YzyProtocolType.REQ, client_type=ClientType.WINDOWS)
    print("Send msg size: {}, msg: {}".format(_size, msg))
    s.send(msg)
 
mac = "22:22:22:22:22:22"
token = b''
heartbeat_data = {} 
terminal_login_data = {}
terminal_logout_data = {}
get_date_time_data = {}
get_config_version_id_data = {}
update_config_info_data = {}
get_config_info_data = {}
verify_admin_user_data = {}
order_query_data = {}
order_confirm_data = {}
p_to_v_start_data = {}
p_to_v_state_data = {}
get_desktop_group_list_data = {}
diff_disk_download_data  = {}
desktop_login_data = {}
check_upload_state_data = {}

def set_req_data(mac):
    global heartbeat_data, terminal_login_data, terminal_logout_data, get_date_time_data, get_config_version_id_data, update_config_info_data, get_config_info_data 
    global verify_admin_user_data, order_query_data, order_confirm_data, p_to_v_start_data, p_to_v_state_data, get_desktop_group_list_data, diff_disk_download_data 
    global desktop_login_data, check_upload_state_data

    heartbeat_data = {
        #"mac": "00:50:56:C0:00:08"
        "mac": mac
    }
    
    terminal_login_data = {
        #"mac": "00:50:56:C0:00:08",
        "mac": mac,
        "ip" : "172.16.1.56"
    }

    terminal_logout_data = {
        #"mac": "00:50:56:C0:00:08",
        "mac": mac,
        "ip" : "172.16.1.56"
    }


    get_date_time_data = {
        #"mac": "00:50:56:C0:00:08",
        "mac": mac
    }

    get_config_version_id_data = {
        #"mac": "00:50:56:C0:00:08",
        "mac": mac
    }

    get_config_info_data = {
        "mac": mac
    }

    update_config_info_data = {
		"terminal_id": 1,
		"mac": mac,
		"name": "zhouli",
		"ip": "172.16.1.25",
		"is_dhcp": 0,
		"mask": "255.255.255.0",
		"gateway": "172.16.1.1",
		"dns1": "8.8.8.8",
		"dns2": "114.114.114.114",
		"platform": "x86",
		"soft_version": "2.2.2",
		"conf_version": 12,
		"disk_residue": 5.92,
		"setup_info": {
			"mode": {
				"show_desktop_type": 2, 
				"auto_desktop": 0
			},
			"program": {
				"server_ip": "172.16.1.29"
			}
		}
	}

    verify_admin_user_data = {
        "mac": mac,
		"username": "admin",
		"password": "123qwe,."
    }

    order_query_data =  {
        "mac": mac,
    }

    order_confirm_data = {
        "mac": mac,
    }

    upload_desktop_notify_data = {
        "mac": mac,
        "file_size": "2342334",
        "file_name": "file_name234234",
    }

    p_to_v_start_data = {
        "mac": mac,
        "name": "ysr_template_6",
        "desc": "add qq soft",
        "classify": 1,  # 1-教学桌面 2-个人桌面（目前固定为1）
        "system_disk": {
            "size": 100,  # size 大小的单位全部为GB
            "real_size": 8.5
        },
        "data_disks": [
            {
                "size": 100,
                "read_size": 8.5
            }
        ]
    }

    p_to_v_state_data = {
        "mac": mac,
        "os_type": "windows_7_x64",  # "windows_10_x64" "windows_7" "windows_10" "other"
        "image_name": "voi_0_8cdd60cf-c394-453e-9645-8aade056c418",
#"voi_0_abd6132f-c659-44ee-9087-6abf82c4e36f", # voi_0_8cdd60cf-c394-453e-9645-8aade056c418
        "progress": 100,
        "status": 1,
        "storage": "opt",
    }

    get_desktop_group_list_data = {
        "mac": mac,
        "ip": "172.16.1.44",
    }

    diff_disk_download_data = {
        "mac": mac,
	"desktop_group_uuid": "a624cf70-814a-4f09-b6b6-eea38da3bf14",
	"diff_disk_uuid": "2979f13d-1964-4667-bb9d-3336d7f6f6a8",
	"diff_level": 1
    }

    desktop_login_data = {
        "mac": mac,
    	"desktop_group_uuid": "4d549232-0e35-4faa-9f01-36c51e7330c1",
    	"is_dhcp": 1,
    	"ip": "192.168.1.13",
    	"netmask": "255.255.255.0",
    	"gateway": "192.168.1.254",
    	"dns1": "114.114.114.114",
    	"dns2": "8.8.8.8"
    }

    check_upload_state_data = {
        "mac": mac,
    	"desktop_group_uuid": "4d549232-0e35-4faa-9f01-36c51e7330c1"
    }

if __name__ == '__main__':
    # serv = TCPServer(('', 20000), EchoHandler)
    # serv.serve_forever()
    mac = sys.argv[1]
    os.chdir('/usr/local/yzy-kvm/yzy_terminal_agent/')
    set_req_data(mac)
    print("terminal_login_data: {},  terminal_logout_data: {}, get_date_time_data: {}".format(terminal_login_data, terminal_logout_data, get_date_time_data))
    # terminal_login()
    # terminal_logout()
    # get_date_time()

    request_service("terminal_login")
    #t = threading.Thread(target=ServerRequestHandler.run, args=(mac, token))
    #t.start()
    server_response_handler = ServerRequestHandler(mac, token)
    server_response_handler.start()
    time.sleep(10)
    token = server_response_handler.token
    print('get server token: {}'.format(token))
    request_service("get_date_time")
    request_service("get_config_version_id")
    request_service("update_config_info")
    request_service("get_config_info")
    request_service("verify_admin_user")
    request_service("order_query")
    request_service("p_to_v_start")
    time.sleep(10)
    request_service("p_to_v_state")
    request_service("get_desktop_group_list")
    request_service("diff_disk_download")
    request_service("desktop_login")
    request_service("check_upload_state")
    #t = threading.Thread(target=HeartBeatRequest.run, args=(mac, token))
    #t.start()
    heartbeat_handler = HeartBeatRequest(mac, token)
    heartbeat_handler.start()

    while True:
        #break
        time.sleep(2)
    s.close()


"""
# shutdonw/restart/delete/enter_maintenance_mode/clear_all_desktop
curl -H "Content-Type: application/json" http://127.0.0.1:50005/api/v1/voi/terminal/command/ -X POST -d '{
"cmd": "shutdown",
"data": {"mac_list": "00:0c:29:2c:5d:38,04:d9:f5:d5:b1:a3,00:50:56:C0:00:01,00:50:56:C0:00:02,00:50:56:C0:00:03"}}'

curl -H "Content-Type: application/json" http://172.16.1.33:50005/api/v1/voi/terminal/command/ -X POST -d '{
"cmd": "watermark_switch",
"data": {"mac_list": "00:0c:29:2c:5d:38,00:50:56:C0:00:01", "switch": 1}}'

curl -H "Content-Type: application/json" http://172.16.1.33:50005/api/v1/voi/terminal/command/ -X POST -d '{
"cmd": "modify_terminal_name",
"data": {"00:50:56:C0:00:01": "pc-1", "00:50:56:C0:00:02": "pc-2", "00:50:56:C0:00:03": "pc-2"}}'


curl -H "Content-Type: application/json" http://172.16.1.33:50005/api/v1/voi/terminal/command/ -X POST -d '{
"cmd": "modify_ip",
"data": { "mac_list": "00:50:56:C0:00:01,00:50:56:C0:00:02,00:50:56:C0:00:03",
"to_ip_list": "192.168.1.101,192.168.1.102,192.168.1.103",
"mask": "255.255.255.0",
"gateway": "192.168.1.1",
"dns1": "8.8.8.8",
"dns2": "114.114.114.114"
}}'

curl -H "Content-Type: application/json" http://172.16.1.33:50005/api/v1/voi/terminal/command/ -X POST -d '{
"cmd": "set_terminal",
"data": { 
"mac_list": "00:50:56:C0:00:01,00:50:56:C0:00:02,00:50:56:C0:00:03",
"mode": {"show_desktop_type": 0, "auto_desktop": 1},
"program": {"server_ip": "172.16.1.33"}
}}'

curl -H "Content-Type: application/json" http://172.16.1.33:50005/api/v1/voi/terminal/command/ -X POST -d '{
"cmd": "add_data_disk",
"data": {"mac_list": "00:50:56:C0:00:01,00:50:56:C0:00:02,00:50:56:C0:00:03", "batch_no": 66, "enable": 1, "restore": 1, "size": 8}}'


curl -H "Content-Type: application/json" http://172.16.1.33:50005/api/v1/voi/terminal/command/ -X POST -d '{
"cmd": "terminal_order",
"data": {"group_uuid": "00234242342342342322", "start_num": 5}}'

curl -H "Content-Type: application/json" http://172.16.1.33:50005/api/v1/voi/terminal/command/ -X POST -d '{
"cmd": "cancel_terminal_order",
"data": {"group_uuid": "00234242342342342322", "batch_num": 133, "start_num": -1}}'



curl -H "Content-Type: application/json" http://127.0.0.1:50005/api/v1/voi/terminal/command/ -X POST -d '{
"cmd": "create_torrent",
"data": {"file_path": "/opt/slow/instances/_base/669ce23d-f3ee-49dc-b7c6-cab57e22674d", "torrent_path": "/opt/slow/instances/_base/torrent_674d.torrent"}}'


curl -H "Content-Type: application/json" http://127.0.0.1:50005/api/v1/voi/terminal/command/ -X POST -d '{
"cmd": "add_bt_task",
"data": {"save_path": "/opt/slow/instances/_base/", "torrent": "/opt/slow/instances/_base/torrent_674d.torrent"}}'

curl -H "Content-Type: application/json" http://127.0.0.1:50005/api/v1/voi/terminal/command/ -X POST -d '{
"cmd": "get_task_state",
"data": {"ip": "", "torrent_id": "3895853152"}}'

curl -H "Content-Type: application/json" http://172.16.1.33:50005/api/v1/voi/terminal/command/ -X POST -d '{
"cmd": "ssh_upload_desktop",
"data": { "mac_list": "00:50:56:C0:00:01,00:50:56:C0:00:02,00:50:56:C0:00:03",
"desktop_name_list": "aaa,bbb,cccc"}}'


"""
