from flask import current_app, request, jsonify
import configparser
import os
import threading
from common.errcode import get_error_result, get_error_name
import hashlib
import netaddr
import socket
import struct
import functools
# import fcntl
import time
import logging
import uuid
import fcntl
import traceback
import requests
from threading import Thread
from .config import SERVER_CONF
from .http import HTTPClient
from . import constants
from .cmdutils import execute
from functools import wraps
# json.loads()

logger = logging.getLogger(__name__)


class ResultThread(Thread):
    """
    实现get_result来获取线程的返回值
    """

    def __init__(self, func, args):
        super(ResultThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None


class Singleton(object):
    _instance_lock = threading.Lock()

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(Singleton, "_instance"):
            with Singleton._instance_lock:
                if not hasattr(Singleton, "_instance"):
                    Singleton._instance = object.__new__(cls)
        return Singleton._instance


def single_lock(func):
    """
    :return: 主要用于多workers时定时任务重复执行的处理
    """
    @wraps(func)
    def _deco(*args, **kwargs):
        lock_file = open(func.__name__, 'w+')
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_NB | fcntl.LOCK_EX)
            logger.debug('single_lock : %s before func', func.__name__)
            ret = func(*args, **kwargs)
            logger.debug('single_lock : %s end func', func.__name__)
            return ret
        except Exception as e:
            logger.info("get single_lock failed:%s", e)
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            lock_file.close()
            logger.debug('single_lock : %s end unlock', func.__name__)

    return _deco


class _ConfigParser(configparser.ConfigParser):

    def to_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(d[k])
        if self._defaults:
            d["DEFAULT"] = dict(self._defaults)
        return d

    def get_option(self, option=""):
        _d = self.to_dict()
        return _d.get(option)

# def iniConfigParser(file_path, option=None):
#     parse = configparser.ConfigParser()
#     parse.optionxform = str
#     # filename = "/etc/vec_server/vecServer.ini"
#     parse.read(file_path)
#
#     _dict = {}
#     if option:
#         options = parse.options(option)
#         for op in options:
#             _dict[op] = parse.get(option, op)
#     else:
#         sections = parse.sections()
#         for sec in sections:
#             _dict[sec] = {}
#             options = parse.options(sec)
#             for op in options:
#                 _dict[sec][op] = parse.get(sec, op)
#         # if 'DEFAULT' in parse:
#         #     _dict["DEFAULT"] = {}
#         #     options = parse.options('DEFAULT')
#         #     for op in options:
#         #         _dict["DEFAULT"][op] = parse.get('DEFAULT', op)
#
#     return _dict


def build_result(errcode, data=None, ext_msg="", **kwargs):
    res = get_error_result(errcode, **kwargs)
    if data is not None and isinstance(data, (dict, list, tuple, str, int, float, bool)):
        res.update({"data": data})
    if ext_msg:
        res["msg"] = res["msg"] + " {}".format(ext_msg)
    return jsonify(res)


def time_logger(func):
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        req_uuid = getattr(request, "req_uuid", str(uuid.uuid4()))
        data = request.get_json()
        t1 = time.time()
        current_app.logger.debug("request[%s] START: %s" % (req_uuid, data))
        try:
            ret = func(*args, **kwargs)
        except Exception as e:
            current_app.logger.error("request[%s] ERROR: %s"% (req_uuid, traceback.format_exc()))
            ret = get_error_result("SystemError")
        t2 = time.time()
        current_app.logger.debug("request[%s] END: %s" % (req_uuid, (t2 - t1)))
        return ret

    return wrapped_func


# def check_param(func):
#     @functools.wraps(func)
#     def wrapped_func(*args, **kwargs):
#         req_uuid = getattr(request, "req_uuid", str(uuid.uuid1()))
#         data = request.get_json()
#         t1 = time.time()
#         current_app.logger.debug("request[%s] START: %s" % (req_uuid, data))
#         try:
#             ret = func(*args, **kwargs)
#         except Exception as e:
#             current_app.logger.error("request[%s] ERROR: %s"% (req_uuid, traceback.format_exc()))
#             ret = get_error_result("SystemError")
#         t2 = time.time()
#         current_app.logger.debug("request[%s] END: %s" % (req_uuid, (t2 - t1)))
#         return ret
#
#     return wrapped_func


def is_ip_addr(ip):
    try:
        netaddr.IPAddress(ip)
        return True
    except:
        return False


def is_netmask(ip):
    ip_addr = netaddr.IPAddress(ip)
    return ip_addr.is_netmask(), ip_addr.netmask_bits()


def create_uuid():
    return str(uuid.uuid4())


def create_md5(s, salt=''):
    new_s = str(s) + salt
    m = hashlib.md5(new_s.encode())
    return m.hexdigest()


def get_file_md5(file_name):
    """
    计算文件的md5
    :param file_name:
    :return:
    """
    m = hashlib.md5()
    with open(file_name, 'rb') as fobj:
        while True:
            data = fobj.read(constants.CHUNKSIZE)
            if not data:
                break
            m.update(data)

    return m.hexdigest()


def find_ips(start, end):
    ipstruct = struct.Struct('>I')
    start, = ipstruct.unpack(socket.inet_aton(start))
    end, = ipstruct.unpack(socket.inet_aton(end))
    return [socket.inet_ntoa(ipstruct.pack(i)) for i in range(start, end+1)]


def find_next_ip(start):
    ipstruct = struct.Struct('>I')
    start, = ipstruct.unpack(socket.inet_aton(start))
    return socket.inet_ntoa(ipstruct.pack(start + 1))


def check_vlan_id(vlan_id):
    if not vlan_id.isdigit():
        return False
    vlan_id = int(vlan_id)
    if 1 <= vlan_id <= 4094:
        return True
    return False


def get_exe_cmd(command):
    ret_cmd = command
    for path in ['/sbin', '/usr/sbin', '/bin', '/usr/bin']:
        if os.path.exists(os.path.join(path, command)):
            ret_cmd = os.path.join(path, command)
            break
    return ret_cmd


def icmp_ping(ip_addr, num=1, timeout=2, count=1):
    cmd = get_exe_cmd("ping")
    for _ in range(0, count):
        try:
            execute(cmd, '-c', "%s" % num, '-W', "%s" % timeout, ip_addr, loglevel=logging.DEBUG)
            break
        except Exception as e:
            logger.error("ping %s failed", ip_addr)
            logger.debug("ping host failed:%s", e, exc_info=True)
            continue
    else:
        return False
    return True


def get_compute_url(ipaddr):
    bind = SERVER_CONF.addresses.get_by_default('compute_bind', '')
    if bind:
        port = bind.split(':')[-1]
    else:
        port = constants.COMPUTE_DEFAULT_PORT
    endpoint = 'http://%s:%s' % (ipaddr, port)
    url = "/api/v1/"
    return endpoint, url


def compute_post(ipaddr, data, timeout=120):
    endpoint, url = get_compute_url(ipaddr)
    http_client = HTTPClient(endpoint, timeout=timeout)
    headers = {
        "Content-Type": "application/json"
    }
    try:
        resp, body = http_client.post(url, data=data, headers=headers)
    except requests.exceptions.Timeout as e:
        ret = get_error_result("ComputeServiceTimeout", ipaddr=ipaddr)
        ret['data'] = "节点'%s'请求超时" % ipaddr
        return ret
    except requests.exceptions.ConnectionError as e:
        ret = get_error_result("ComputeServiceUnavaiable", ipaddr=ipaddr)
        ret['data'] = "节点'%s'计算服务连接失败" % ipaddr
        return ret
    except socket.gaierror as e:
        ret = get_error_result("ComputeServiceUnavaiable", ipaddr=ipaddr)
        ret['data'] = "节点'%s'计算服务连接失败" % ipaddr
        return ret
    except (socket.error, socket.timeout, IOError) as e:
        ret = get_error_result("ComputeServiceUnavaiable", ipaddr=ipaddr)
        ret['data'] = "节点'%s'计算服务连接失败" % ipaddr
        return ret
    except Exception as e:
        return get_error_result("ComputeServiceUnavaiable", ipaddr=ipaddr)
    return body


def monitor_post(ipaddr, url, data, timeout=10):
    bind = SERVER_CONF.addresses.get_by_default('monitor_bind', '')
    if bind:
        port = bind.split(':')[-1]
    else:
        port = constants.MONITOR_DEFAULT_PORT
    endpoint = 'http://%s:%s' % (ipaddr, port)
    http_client = HTTPClient(endpoint, timeout=timeout)
    headers = {
        "Content-Type": "application/json"
    }
    try:
        resp, body = http_client.post(url, data=data, headers=headers)
    except Exception as e:
        ret = get_error_result("MonitorServiceUnavaiable", ipaddr=ipaddr)
        ret['data'] = "监控服务连接失败"
        return ret
    return body


def terminal_post(url, data):
    bind = SERVER_CONF.addresses.get_by_default('terminal_bind', '')
    if bind:
        port = bind.split(':')[-1]
    else:
        port = constants.TERMINAL_DEFAULT_PORT
    endpoint = 'http://127.0.0.1:%s' % port
    http_client = HTTPClient(endpoint, timeout=10)
    headers = {
        "Content-Type": "application/json"
    }
    try:
        resp, body = http_client.post(url, data=data, headers=headers)
    except Exception as e:
        ret = get_error_result("TerminalServiceUnavaiable")
        ret['data'] = "终端管理服务连接失败"
        return ret
    return body


def voi_terminal_post(url, data, timeout=60):
    bind = SERVER_CONF.addresses.get_by_default('voi_terminal_bind', '')
    if bind:
        port = bind.split(':')[-1]
    else:
        port = constants.VOI_TERMINAL_DEFAULT_PORT
    endpoint = 'http://127.0.0.1:%s' % port
    http_client = HTTPClient(endpoint, timeout=timeout)
    headers = {
        "Content-Type": "application/json"
    }
    try:
        resp, body = http_client.post(url, data=data, headers=headers)
    except Exception as e:
        ret = get_error_result("TerminalServiceUnavaiable")
        ret['data'] = "VOI终端管理服务连接失败"
        return ret
    return body


def server_post(url, data, version=None, timeout=180):
    if not version:
        version = "v1"
    bind = SERVER_CONF.addresses.get_by_default('server_bind', '')
    if bind:
        port = bind.split(':')[-1]
    else:
        port = constants.SERVER_DEFAULT_PORT
    endpoint = 'http://127.0.0.1:%s' % port
    http_client = HTTPClient(endpoint, timeout=timeout)
    headers = {
        "Content-Type": "application/json"
    }
    if not url.startswith("/api/"):
        url = "/api/%s/%s"% (version, url.lstrip('/'))

    try:
        resp, body = http_client.post(url, data=data, headers=headers)
    except requests.exceptions.ConnectionError as e:
        ret = get_error_result("ServerServiceUnavaiable")
        ret['data'] = "节点server服务计算服务连接失败"
        return ret
    except requests.exceptions.Timeout as e:
        ret = get_error_result("ServerServiceTimeout")
        ret['data'] = "节点server服务请求超时"
        return ret
    except socket.gaierror as e:
        ret = get_error_result("ServerServiceUnavaiable")
        ret['data'] = "节点server服务计算服务连接失败"
        return ret
    except (socket.error, socket.timeout, IOError) as e:
        ret = get_error_result("ServerServiceUnavaiable")
        ret['data'] = "节点server服务计算服务连接失败"
        return ret
    except Exception as e:
        return get_error_result("ServerServiceUnavaiable")
    return body


def upgrade_post(ipaddr, url, data, timeout=60):
    bind = SERVER_CONF.addresses.get_by_default('upgrade_bind', '')
    if bind:
        port = bind.split(':')[-1]
    else:
        port = constants.UPGRADE_DEFAULT_PORT
    endpoint = 'http://%s:%s' % (ipaddr, port)
    http_client = HTTPClient(endpoint, timeout=timeout)
    headers = {
        "Content-Type": "application/json"
    }
    try:
        logger.debug("endpoint:%s, url: %s, data: %s: headers: %s" % (endpoint, url, data, headers))
        resp, body = http_client.post(url, data=data, headers=headers)
        if isinstance(body, dict):
            body['ipaddr'] = ipaddr
    except requests.exceptions.Timeout as e:
        ret = get_error_result("UpgradeServiceTimeout")
        ret['data'] = "节点升级服务请求超时"
        ret['ipaddr'] = ipaddr
        return ret
    except Exception as e:
        logger.error("UpgradeServiceUnavailable", exc_info=True)
        ret = get_error_result("UpgradeServiceUnavailable", ipaddr=ipaddr)
        ret['data'] = "节点升级服务连接失败"
        ret['ipaddr'] = ipaddr
        return ret
    return body


def check_node_status(ipaddr):
    command = {
                "command": "ping",
                "handler": "NetworkHandler"
            }
    ret = compute_post(ipaddr, command)
    return ret


def size_to_G(size, bit=2):
    return round(size / constants.Gi, bit)


def size_to_M(size, bit=2):
    return round(size / constants.Mi, bit)


def gi_to_section(size):
    return int(size * 1024 * 1024 * 2)


def bytes_to_section(_bytes):
    return int(_bytes / 512)


def section_to_G(section):
    return int(section / 2 / 1024 / 1024)



if __name__ == "__main__":
    pass
    # _c = _ConfigParser()
    # _c.read("test.ini")
    # print(_c.to_dict())
    # print(_c.get_option("GOBAL"))
    # # print(iniConfigParser("test.ini"))
    import requests
    requests.post()
