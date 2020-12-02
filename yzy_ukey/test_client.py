import time
import socket
import struct
import json

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("172.16.1.253", 50010))
# print(s.recv(1024).decode())

format_str = ">3sILBBq"
cid = b"yzy"
version = 1
sequence = 1
req_or_resp = 0
client_id = 1
# data_len = 10

_d = dict()
_d["cmd"] = "get_auth_info"
# _d["params"] = {"unit_name": "云之翼", "sn": "00d353cb-1866-cfe5-78e6-079c5c1b7807"}
_d["params"] = {}
_d["timestamp"] = str(time.time())
d_json = json.dumps(_d).encode()
data_len = len(d_json)

data = struct.pack(format_str, cid, version, sequence, req_or_resp, client_id, data_len)
print(len(data))
while True:
    # if data:
    #     print(s.recv(1024).decode())
    # data = input("Please input your name: ")
    # if not data:
    #     continue
    data += d_json
    s.send(data)
    print(data)
    print(s.recv(1024).decode())
    if data == "exit":
        break
    time.sleep(5)
s.close()