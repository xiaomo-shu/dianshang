import time
from socket import socket, AF_INET, SOCK_STREAM

while True:
    s = socket(AF_INET, SOCK_STREAM)
    t1 = time.time()
    s.connect(('192.169.27.197', 50007))
    t2 = time.time()
    s.close()
    print(t2 - t1)
    time.sleep(0.01)
