import time
import json
from socket import socket, AF_INET, SOCK_STREAM
s = socket(AF_INET, SOCK_STREAM)
s.connect(('localhost', 50007))

data = {
    "cmd": "login",
    "data": {
        "mac": "adfasd-asdfasd11",
        "ip" : "172.16.1.56"
    }
}

msg = json.dumps(data).encode("utf-8")


def main():
    t = time.time()
    print(len(msg))
    s.send(msg)
    h = s.recv(8192)
    print(h)

if __name__ == '__main__':
    # serv = TCPServer(('', 20000), EchoHandler)
    # serv.serve_forever()
    while True:
        main()
        time.sleep(1)
    # main()
