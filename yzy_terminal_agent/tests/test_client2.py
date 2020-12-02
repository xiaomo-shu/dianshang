import time
import json
import struct
import threading
from socket import socket, AF_INET, SOCK_STREAM


data = {
    "cmd": "login",
    "data": {
        "mac": "adfasd-asdfasd",
        "ip" : "172.16.1.56"
    }
}
pay_load = {
	"mac": "11111-11111",
	"desktop" : {
        "uuid": "ed15b9cc-ce6c-4897-a96a-82d4be1ec379",
        "name": "test_voi1",
        "desc": "test_voi1",
		"disks" : [
			{
				"diff_Level" : 0,
				"real_size" : 12952666112,
				"system_type" : 0,
				"type" : 0,
				"uuid" : "9d301a05-4918-4bd6-9b15-8b652380b"
			}
		]
	}
}

# msg = json.dumps(data).encode("utf-8")
msg = b'\x01\x00\x01\x00)#\x00\x00\x01\x00\x00\x00+\x00\x00\x00\x01\x00\x01\x01\x00\x00\x00\x00{"mac": "11111-11111", "ip": "172.16.1.56"}'
msg2 = b'\x01\x00\x00\x00\x02\x00\x00\x00!\x1d\x00\x00=\x00\x00\x00\x01\x00\x01\x01\x08\x00\x00\x0012345678{"cmd": "template_disk_list", "data": {"mac": "11111-11111"}}'
msg3 = b'\x01\x00\x00\x00\x03\x00\x00\x00c\x13\x00\x00\x0e\x01\x00\x00\x01\x00\x01\x01\x08\x00\x00\x0012345678{"cmd": "compare_template", "data": {"mac": "11111-11111", "template": {"system_disks": ["voi_0_91f9d1ba-cb4a-41ba-971a-618f9e306571", "voi_1_91f9d1ba-cb4a-41ba-971a-618f9e306571"], "template_name": "voi_test1", "template_uuid": "f15a1759-789e-4e17-a3e1-e723121e9314"}}}'

bus_msg = b'\x01\x00\x00\x003#\x00\x00\x00\x00\x00\x00\x14\x00\x00\x00\x01\x01\x01\x01 \x00\x00\x00'

def create_header(service_code, token, payload, is_json=True, is_req = True):
    version_chief = 1
    version_sub = 0
    service_code = service_code
    sequence_code = 1
    if is_json:
        data_size = len(json.dumps(payload).encode("utf-8"))
        data_type = 1
    else:
        data_size = len(payload)
        data_type = 0
    # data_type = 1
    encoding = 1
    client_type = 5
    req_or_res = 1 if is_req else 2
    token_len = len(token)
    supplementary = 0
    header = struct.pack("HHIIIBBBBHH", version_chief, version_sub, service_code, sequence_code, data_size, data_type,
                         encoding, client_type, req_or_res, token_len, supplementary)
    return header


def create_msg(service_code, token, payload, is_json=True, is_req=True):
    header = create_header(service_code, token, payload, is_json, is_req)
    if is_json:
        payload = json.dumps(payload).encode("utf-8")
    format_str = "!%ds" % (len(token) + len(payload))
    payload_bin = struct.pack(format_str, token + payload)
    return header + payload_bin


def main(n=1):
    print("thread %s"% n)
    msg = b'\x01\x00\x01\x00)#\x00\x00\x01\x00\x00\x00+\x00\x00\x00\x01\x00\x02\x01\x00\x00\x00\x00{"mac": "11111-11%03d", "ip": "172.16.1.56"}' % n
    s = socket(AF_INET, SOCK_STREAM)
    s.connect(('192.169.27.197', 50007))
    t = time.time()
    s.send(msg)
    h = s.recv(8192)
    print(h)
    s1 = h[h.find(b"{"):]
    js_s1 = json.loads(s1)
    print(s1)
    token_bin = js_s1["data"]["token"].encode("utf-8")
    heart_msg = b'\x01\x00\x01\x00(#\x00\x00\x01\x00\x00\x00\x16\x00\x00\x00\x01\x00\x01\x01 \x00\x00\x00%s{"mac": "11111-11%03d"}'%(token_bin, n)
    heart_msg_str = heart_msg
    bus_msg_str = create_msg(9011, token_bin, pay_load)
    print(bus_msg_str)
    count = 0
    while True:
        print("模拟心跳/.......")
        s.send(heart_msg_str)
        time.sleep(5)
        # s.send(bus_msg_str)
        # s.recv(msg2)
        header = s.recv(24)
        print(header)
        version_chief, version_sub, service_code, sequence_code, data_size, data_type, encoding, client_type, req_or_res, \
        token_len, supplementary = struct.unpack("HHIIIBBBBHH", header)
        print(service_code)
        if service_code == 9000:
            count += 1
            print("心跳。。。。。")
            body = s.recv(data_size + token_len)
            print(b"body: " + body)
        elif service_code == 1015:
            print("thread %s 发送种子文件： %s" % (n, data_size + token_len))
            recv_token  = s.recv(token_len)
            print("获取到的token: %s"% recv_token)
            recv_size = data_size
            torrent_file = b""
            while recv_size > 0 :
                if recv_size > 8192:
                    h2 = s.recv(8192)
                    torrent_file += h2
                    # print(b"torrent: " + h2, len(h2))
                    print(b"> 8192", len(h2))
                    recv_size -= len(h2)
                else:
                    h3 = s.recv(recv_size)
                    torrent_file += h3
                    # print(b"torrent__h3: "+h3, len(h3), recv_size)
                    print(b" < 8192", len(h3), recv_size)
                    recv_size -= len(h3)
                    print(b"recv_size: ", recv_size)

            with open("torrent/torrent_test%s.torrent" % n, "wb") as f:
                f.write(torrent_file[66:])
            print("thread %s torrent_test write success !!!!!"% n)
        elif service_code == 1017:
            print("data_size: ", data_size)
            h3 = s.recv(token_len + data_size)
            print(b"h3: " + h3, len(h3))
            print("h3: %s"% h3[token_len:])
            ret_json = json.loads(h3[token_len:])
            batch_no = ret_json["batch_no"]
            data = {
                "code": 0,
                "msg": "Success",
                "data": {
                    "mac": "11111-11%03d" % n,
                    "batch_no": batch_no
                }
            }

            # data_str = json.dumps(data).encode("utf-8")
            bus_msg_str = create_msg(1017, token_bin, data, is_json=True, is_req=False)
            print("bus msg: %s" % bus_msg_str)
            _count = 10
            while _count:
                time.sleep(1)
                print("sleep ...... ")
                _count -= 1

            s.sendall(bus_msg_str)
            print("bus msg: %s success!!!"% bus_msg_str)
        elif service_code == 9007:
            print("9007 data_size: ", data_size)
            h4 = s.recv(token_len + data_size)
            print(b"h4: " + h4, len(h4))

        else:
            print("data_size: ", data_size)
            h4 = s.recv(token_len + data_size)
            print(b"h4: " + h4, len(h4))

        # if count == 5:
        #     data = {
        #         "mac": "11111-11111",
        #         "ip": "172.16.1.56"
        #     }
        #     bus_msg_str = create_msg(9007, token_bin, data, is_json=True, is_req=True)
        #     print("9007 bus msg : %s" % bus_msg_str)
        #     s.sendall(bus_msg_str)
        #     print("9007 bus msg: %s success!!!" % bus_msg_str)

        #     # 发送种子
        #     test_torrent = b""
        #     with open("torrent_test.torrent", "rb") as f:
        #         test_torrent = f.read()
        #     # {
        #     #     "disk_uuid": "2ab1a8a0-dc98-4109-b4f4-59000a54fdc4",
        #     #     "disk_type": 1,
        #     #     "sys_type": 1,
        #     #     "dif_level": 0,
        #     #     "real_size": 24,
        #     #     "torrent_file": "/opt/test.torrent",
        #     #     "reserve_space": 50
        #     # }
        #     _len = len(test_torrent)
        #     format_str = "<36sbbiqqq%ss" % _len
        #     torrent_payload = struct.pack(format_str, b"2ab1a8a0-dc98-4109-b4f4-59000a54fdc4",
        #                                   1, 1, 0, 24, 50, _len, test_torrent)
        #     msg = create_msg(9014, token_bin, torrent_payload, False)
        #     _s = s.sendall(msg)
        #     print("发送种子： ", _s)


def upload_log():
    msg = b'\x01\x00\x01\x00)#\x00\x00\x01\x00\x00\x00+\x00\x00\x00\x01\x00\x02\x01\x00\x00\x00\x00{"mac": "11111-test2", "ip": "172.16.1.56"}'
    s = socket(AF_INET, SOCK_STREAM)
    s.connect(('192.169.27.197', 50007))
    t = time.time()
    s.send(msg)
    h = s.recv(8192)
    print(h)
    s1 = h[h.find(b"{"):]
    js_s1 = json.loads(s1)
    print(s1)
    token_bin = js_s1["data"]["token"].encode("utf-8")
    pay_load = b""
    with open("test.txt", "rb") as f:
        pay_load = f.read()

    bus_msg_str = create_msg(9999, token_bin, pay_load, False)
    print(bus_msg_str)
    s.send(bus_msg_str)
    header = s.recv(24)
    print(header)
    version_chief, version_sub, service_code, sequence_code, data_size, data_type, encoding, client_type, req_or_res, \
    token_len, supplementary = struct.unpack("HHIIIBBBBHH", header)
    print(service_code)
    body = s.recv(data_size + token_len)
    print(b"body: " + body)


if __name__ == '__main__':
    upload_log()
    # serv = TCPServer(('', 20000), EchoHandler)
    # serv.serve_forever()
    # while True:
    #     main()
    #     time.sleep(5)
    # threads = list()
    # for i in range(30):
    #     th = threading.Thread(target=main, args=(i,))
    #     threads.append(th)
    #
    # for th in threads:
    #     th.start()
    #     time.sleep(0.01)
        # th.join()

