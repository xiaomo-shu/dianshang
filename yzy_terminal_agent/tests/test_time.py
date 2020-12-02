import time
import datetime as dt
import threading


def print_time():
    while True:
        time.sleep(5)
        print("%s" % dt.datetime.now())


th = threading.Thread(target=print_time)
th.start()
while True:
    time.sleep(10)
