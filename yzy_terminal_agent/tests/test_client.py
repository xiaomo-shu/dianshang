import time
from socket import socket, AF_INET, SOCK_STREAM
n = 0
sockets = []
while n < 1000:
    s = socket(AF_INET, SOCK_STREAM)
    s.connect(('172.16.1.29', 9001))
    sockets.append(s)
    n += 1


def main():
    t = time.time()
    for inx, s in enumerate(sockets):
        s.send(b'%s Hello %s'% (inx, str(t).encode("utf-8")))
        h = s.recv(8192)
        print("%s: %s"% (inx,h))


if __name__ == '__main__':
    # serv = TCPServer(('', 20000), EchoHandler)
    # serv.serve_forever()
    while True:
        main()
        time.sleep(2)
    # main()
