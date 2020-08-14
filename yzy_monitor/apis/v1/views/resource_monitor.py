import os
import re
import socket
import numpy as np
import psutil
import datetime as dt
from functools import wraps
import time
import traceback
from collections import Counter
from flask.views import MethodView
from flask import request, current_app
from flask import jsonify
import common.errcode as errcode
from common.utils import is_ip_addr, is_netmask, create_uuid, icmp_ping
from yzy_monitor.apis.v1 import api_v1
from simplepam import authenticate
from .dmidecode import get_profile, get_device_info
#from yzy_monitor.redis_client import RedisClient


def timefn(fn):
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        current_app.logger.debug("@timefn:" + fn.__name__ + " took " + str(t2 - t1) + " seconds")
        return result
    return measure_time


class ResourceMonitorHandler(MethodView):
    def __init__(self):
        self.hostname = socket.gethostname()
        #self.ip = socket.gethostbyname(self.hostname)

    @timefn
    def get(self):
        self.resp_msg = {
                "hostname": self.hostname,
                "utc": int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds()),
                "cpu": self.get_cpu_info(),
                "memory": self.get_memory_info(),
                "disk": self.get_disk_info(),
                "network": self.get_network_info(),
                "vm": self.get_vm_running()
        }
        return jsonify()


@timefn
def get_ip_info():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return ip, hostname


@api_v1.route('/monitor/resource', methods=['GET', 'POST'])
def get_resource_info():
    try:
        merge_resp = errcode.get_error_result()
        #ip_info = get_ip_info()
        #merge_resp['ip'] = ip_info[0]
        #merge_resp['hostname'] = ip_info[1]
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        merge_resp['utc'] = utc
        call_func_list = [get_cpu_info, get_memory_info, get_disk_info, get_network_info, get_vm_running,
                          get_diskio_info, get_networkio_info, get_cpuvt_info, get_service_info]
        merge_resp['data'] = {}
        for func in call_func_list:
            resp = func()
            if resp['code'] != 0:
                return resp
            else:
                if 'data' in resp.keys():
                    if 'utc' in resp['data'].keys():
                        resp['data'].pop('utc')
                    add_key_name = func.__name__.split('_')[1]
                    merge_resp['data'][add_key_name] = resp['data']
        return merge_resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="OtherError")
        return resp


@api_v1.route('/monitor/cpu', methods=['GET', 'POST'])
@timefn
def get_cpu_info():
    try:
        resp = errcode.get_error_result()
        #ip_info = get_ip_info()
        resp['data'] = {}
        # resp['data']['ip'] = ip_info[0]
        # resp['data']['hostname'] = ip_info[1]
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        resp['data']['utc'] = utc
        cpu_numbers = psutil.cpu_count()
        resp['data']['numbers'] = cpu_numbers
        cpu_utilization = psutil.cpu_percent()
        resp['data']['utilization'] = cpu_utilization
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="GetCpuInfoFailure")
        return resp


@api_v1.route('/monitor/cpuvt', methods=['GET', 'POST'])
@timefn
def get_cpuvt_info():
    try:
        resp = errcode.get_error_result()
        #ip_info = get_ip_info()
        resp['data'] = {}
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        cpu_type = "intel" if bool(os.popen('cat /proc/cpuinfo|grep "model name"|grep "Intel"').read()) else "amd"
        cpu_vt_enabled = 0
        kenel_vt_enabled = 0
        if cpu_type == "intel":
            cpu_vt_enabled = int(os.popen('egrep "vmx" /proc/cpuinfo |wc -l').readline())
            kenel_vt_enabled = int(os.popen('lsmod |grep -vE "grep|vi"|grep kvm_intel|wc -l').readline())
        else:
            cpu_vt_enabled = int(os.popen('egrep "svm" /proc/cpuinfo |wc -l').readline())
            kenel_vt_enabled = int(os.popen('lsmod |grep -vE "grep|vi"|grep kvm_amd|wc -l').readline())
        cmd = ' systemctl list-units|grep -E "libvirtd" |awk \'{print $4}\''
        libvirtd_running = (os.popen(cmd).readline().strip() == "running")
        if cpu_vt_enabled and kenel_vt_enabled and libvirtd_running:
            resp['data']['cpuvt'] = True
            resp['data']['hostname'] = socket.gethostname()
        else:
            resp['data']['cpuvt'] = False
            resp['data']['hostname'] = socket.gethostname()
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="GetCpuVtInfoFailure")
        return resp


@api_v1.route('/monitor/memory', methods=['GET', 'POST'])
@timefn
def get_memory_info():
    try:
        resp = errcode.get_error_result()
        resp['data'] = {}
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        resp['data']['utc'] = utc
        mem_info = psutil.virtual_memory()
        resp['data']['total'] = mem_info.total
        resp['data']['available'] = mem_info.available
        resp['data']['utilization'] = mem_info.percent
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="GetMemoryInfoFailure")
        return resp


## return 1-ssd 2-sata
def checkSsd(device):
    device_name = device.split('/')[-1]
    rota = os.popen('lsblk -o name,rota|grep {}'.format(device_name)).readline().split()[-1]
    return int(rota)


@api_v1.route('/monitor/disk', methods=['GET', 'POST'])
@timefn
def get_disk_info():
    try:
        resp = errcode.get_error_result()
        resp['data'] = {}
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        resp['data']['utc'] = utc
        disk_parts = psutil.disk_partitions()
        for disk in disk_parts:
            disk_mountpoint = disk.mountpoint
            disk_usage = psutil.disk_usage(disk_mountpoint)
            resp['data'][disk_mountpoint] = {'type': checkSsd(disk.device), 'total': disk_usage.total,
                                             'used': disk_usage.used, 'free': disk_usage.free,
                                             'utilization': disk_usage.percent}
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="GetDiskInfoFailure")
        return resp


@api_v1.route('/monitor/diskio', methods=['GET', 'POST'])
@timefn
def get_diskio_info():
    try:
        resp = errcode.get_error_result()
        resp['data'] = {}
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        resp['data']['utc'] = utc
        diskio_parts = psutil.disk_io_counters(perdisk=True)
        virtual_block_device = os.listdir('/sys/devices/virtual/block/')
        physical_block_device = [dev for dev in diskio_parts if dev not in virtual_block_device]
        for diskio in physical_block_device:
            resp['data'][diskio] = {'read_bytes': diskio_parts[diskio].read_bytes,
                                    'write_bytes': diskio_parts[diskio].write_bytes}
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="GetDiskIoInfoFailure")
        return resp


@api_v1.route('/monitor/network', methods=['GET', 'POST'])
@timefn
def get_network_info():
    try:
        resp = errcode.get_error_result()
        # 虚拟网络装置
        virtual_net_device = os.listdir('/sys/devices/virtual/net/')
        resp['data'] = {}
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        resp['data']['utc'] = utc
        #取到两个文件内容：地址、状态
        nic_addrs = psutil.net_if_addrs()
        nic_stats = psutil.net_if_stats()
        #真实网络装置：不在虚拟网络装置中的网络装置的名字（网卡）
        physical_net_device = [dev for dev in nic_addrs.keys() if dev not in virtual_net_device]
        for nic_name in physical_net_device:
            #ip
            nic_address = ""
            #子网掩码
            nic_netmask = ""
            #地址
            nic_mac = ""
            nic_stat = False
            #网卡速度
            nic_speed = 0
            for info in nic_addrs[nic_name]:
                if str(info.family) == "AddressFamily.AF_INET":
                    nic_address = info.address
                    nic_netmask = info.netmask
                if str(info.family) == "AddressFamily.AF_PACKET":
                    nic_mac = info.address

            if nic_name in nic_stats.keys():
                nic_stat = nic_stats[nic_name].isup
            # nic_speed = 0
            try:
                ret = os.popen('ethtool %s|grep "baseT"' % nic_name).readlines()[-1]
                speed = re.sub("\D", "", ret)
                if speed:
                    nic_speed = int(speed)
            except Exception as err:
                current_app.logger.error(err)
                current_app.logger.error(''.join(traceback.format_exc()))
                nic_speed = 0

            try:
                nic_stat = bool(int(open('/sys/class/net/{}/carrier'.format(nic_name), 'r').readline()[0]))
                nic_conf_lines = os.popen('egrep -v \'^$|#\' /etc/sysconfig/network-scripts/ifcfg-{}'
                                          .format(nic_name)).readlines()
                nic_conf = {element.split('=')[0]: element.split('=')[1][:-1]  for element in nic_conf_lines}

            except Exception as err:
                current_app.logger.error(err)
                current_app.logger.error(''.join(traceback.format_exc()))
                nic_stat = False

            nic_gateway = ''
            nic_dns1 = ''
            nic_dns2 = ''
            try:
                nic_conf_lines = os.popen('egrep -v \'^$|#\' /etc/sysconfig/network-scripts/ifcfg-{}'
                                          .format(nic_name)).readlines()
                nic_conf = {element.split('=')[0].lower().strip("\""): element.split('=')[1][:-1].strip("\"")
                            for element in nic_conf_lines}
                nic_gateway = nic_conf['gateway'] if 'gateway' in nic_conf.keys() else ''
                nic_dns1 = nic_conf['dns1'] if 'dns1' in nic_conf.keys() else ''
                nic_dns2 = nic_conf['dns2'] if 'dns2' in nic_conf.keys() else ''
            except Exception as err:
                current_app.logger.error(err)
                current_app.logger.error(''.join(traceback.format_exc()))

            resp['data'][nic_name] = {'ip': nic_address, 'mac': nic_mac, 'mask': nic_netmask,
                                      'gateway': nic_gateway, 'dns1': nic_dns1, 'dns2': nic_dns2,
                                      'speed': nic_speed, 'stat': nic_stat}
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="GetNetworkInfoFailure")
        return resp


@api_v1.route('/monitor/networkio', methods=['GET', 'POST'])
@timefn
def get_networkio_info():
    try:
        resp = errcode.get_error_result()
        virtual_net_device = os.listdir('/sys/devices/virtual/net/')
        resp['data'] = {}
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        resp['data']['utc'] = utc
        nics_io = psutil.net_io_counters(pernic=True)
        physical_net_device = [dev for dev in nics_io if dev not in virtual_net_device]
        for nic in physical_net_device:
            resp['data'][nic] = {'bytes_send': nics_io[nic].bytes_sent, 'bytes_recv': nics_io[nic].bytes_recv}
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="GetNetworkIoInfoFailure")
        return resp


@api_v1.route('/monitor/vm', methods=['GET', 'POST'])
@timefn
def get_vm_running():
    try:
        resp = errcode.get_error_result()
        resp['data'] = {}
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        resp['data']['utc'] = utc
        vm_counts = int(os.popen("ps -ef|grep qemu-kvm|grep -v 127.0.0.1|grep -v grep|grep -v defunct -c")
                        .readline().strip())
        resp['data']['numbers'] = vm_counts
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="GetVmInfoFailure")
        return resp


def get_server_version():
    server_version = ""
    with open('/etc/os-release') as f:
        for line in f.readlines():
            key_value = line.split('=')
            if len(key_value) == 2 and key_value[0] == "VARIANT":
                server_version = key_value[1].strip('\n"')
    return server_version


@api_v1.route('/monitor/hardware', methods=['GET', 'POST'])
@timefn
def get_hardware_info():
    try:
        resp = errcode.get_error_result()
        #ip_info = get_ip_info()
        resp['data'] = {}
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        resp['data']['utc'] = utc
        resp['data']['server_version'] = get_server_version()

        hardware_type_list = ['disk', 'gfxcard']
        for hardware_type in hardware_type_list:
            cmd = 'hwinfo --{}|grep \"Model\"'.format(hardware_type)
            hardware_model = os.popen(cmd).readlines()
            if type(hardware_model) is list:
                hardware_model = [x.split('\"')[1] for x in hardware_model]
                resp['data'][hardware_type] = dict(Counter(hardware_model))
            elif type(hardware_model) is str:
                hardware_model = hardware_model.split('\"')[1][:-1]
                resp['data'][hardware_type] = {hardware_model: 1}

        hardware_type_list = ['cpu', 'memory']
        info = get_profile()
        resp['data']['cpu'] = dict(Counter(get_device_info(info, "cpu")))
        resp['data']['memory'] = dict(Counter(get_device_info(info, "memory")))
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="GetHardwareInfoFailure")
        return resp


@api_v1.route('/monitor/service', methods=['GET', 'POST'])
@timefn
def get_service_info():
    try:
        resp = errcode.get_error_result()
        resp['data'] = {}
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        resp['data']['utc'] = utc
        services = current_app.config.get('SERVICES', ['yzy-monitor', 'httpd'])
        cmd = ' systemctl list-units|grep -E "%s" |awk \'{print $1","$4}\'' % '|'.join(services)
        results = os.popen(cmd).readlines()
        if results:
            for ret in results:
                service_nanme = ret.split('.')[0]
                service_status = ret.split(',')[1].strip()
                resp['data'][service_nanme] = service_status
        for service in [x for x in services if x not in resp['data'].keys()]:
            resp['data'][service] = 'not found'
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="GetServiceInfoFailure")
        return resp


@api_v1.route('/monitor/add_ip', methods=['POST'])
@timefn
def add_ip_info():
    """
    {
        "name": "eth0",
        "ip": "172.16.1.31",
        "netmask": "255.255.255.0",
        "gateway": "172.16.1.254",
        "dns1": "8.8.8.8",
        "dns2": "114.114.114.114"
    }
    :return:
    """
    try:
        data = request.get_json()
        nic_name = data.get("name")
        ip = data.get("ip")
        netmask = data.get("netmask")
        gateway = data.get("gateway")
        dns1 = data.get("dns1")
        dns2 = data.get("dns2")
        if not (is_ip_addr(ip) and is_netmask(netmask)[0] and is_ip_addr(gateway)):
            current_app.logger.error("add nic %s ip, param error"% (nic_name))
            return errcode.get_error_result("IpInfoParamError")
        if dns2 and not is_ip_addr(dns2):
            current_app.logger.error("add nic %s ip, dns2 error" % (nic_name))
            return errcode.get_error_result("IpInfoParamError")

        resp = errcode.get_error_result()
        virtual_net_device = os.listdir('/sys/devices/virtual/net/')
        resp['data'] = {}
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        resp['data']['utc'] = utc
        nic_addrs = psutil.net_if_addrs()
        nic_stats = psutil.net_if_stats()
        physical_net_device = [dev for dev in nic_addrs.keys() if dev not in virtual_net_device]
        if nic_name.split(':')[0] not in physical_net_device:
            current_app.logger.error("add nic %s ip, not physical nic"% nic_name)
            return errcode.get_error_result("NotPhysicalNICError")
        nic_ifcfg = "/etc/sysconfig/network-scripts/ifcfg-%s" % nic_name
        if os.path.exists(nic_ifcfg):
            resp = errcode.get_error_result(error="IpConfFileExistsError")
            return resp
        ifcfg_str = "TYPE=Ethernet\nPROXY_METHOD=none\nBROWSER_ONLY=no\nBOOTPROTO=static\nDEFROUTE=yes"\
                    "\nIPV4_FAILURE_FATAL=no\nIPV6INIT=yes\nIPV6_AUTOCONF=yes\nIPV6_DEFROUTE=yes\nIPV6_FAILURE_FATAL=no"\
                    "\nIPV6_ADDR_GEN_MODE=stable-privacy\nNAME={name}\nUUID={uuid}\nDEVICE={nic}\nONBOOT=yes\nIPADDR={ip}"\
                    "\nNETMASK={netmask}\nGATEWAY={gateway}\nDNS1={dns1}"

        uuid = create_uuid()
        ifcfg_str = ifcfg_str.format(**{"uuid": uuid, "nic": nic_name, "ip": ip, "netmask": netmask,
                                        "gateway": gateway, "dns1": dns1, "name": nic_name})
        if dns2:
            ifcfg_str += "\nDNS2=%s"% dns2
        with open(nic_ifcfg, "w") as f:
            f.write(ifcfg_str)
        ret = icmp_ping(gateway)
        if ret:
            # 启动命令 ifup eth0:0
            os.system("ifup %s" % nic_name)
            current_app.logger.info("interface %s add ip %s, gateway %s is link", nic_name, ip, gateway)
        else:
            # 如果网关不通
            # 需维护route 表
            os.system("ifup %s" % nic_name)
            os.system("route del default gw %s" % gateway)
            current_app.logger.info("interface %s add ip %s, gateway %s is not link", nic_name, ip, gateway)
        # 重启网络服务
        os.system("systemctl restart network")
        current_app.logger.info("add nic %s ip success"% nic_name)
        resp["data"] = {
            "name": nic_name
        }
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="AddIpConfFileFailure")
        return resp


@api_v1.route('/monitor/update_ip', methods=['POST'])
@timefn
def update_ip_info():
    """
    {
        "name": "eth0",
        "ip": "172.16.1.31",
        "netmask": "255.255.255.0",
        "gateway": "172.16.1.254",
        "dns1": "8.8.8.8",
        "dns2": "114.114.114.114"
    }
    :return:
    """
    try:
        data = request.get_json()
        nic_name = data.get("name")
        ip = data.get("ip")
        netmask = data.get("netmask")
        gateway = data.get("gateway")
        dns1 = data.get("dns1")
        dns2 = data.get("dns2")
        if not (is_ip_addr(ip) and is_netmask(netmask)[0] and is_ip_addr(gateway)):
            current_app.logger.error("update nic %s ip, param error"% (nic_name))
            return errcode.get_error_result("IpInfoParamError")
        if dns2 and not is_ip_addr(dns2):
            current_app.logger.error("update nic %s ip, dns2 error" % (nic_name))
            return errcode.get_error_result("IpInfoParamError")

        resp = errcode.get_error_result()
        virtual_net_device = os.listdir('/sys/devices/virtual/net/')
        resp['data'] = {}
        utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
        resp['data']['utc'] = utc
        nic_addrs = psutil.net_if_addrs()
        nic_stats = psutil.net_if_stats()
        physical_net_device = [dev for dev in nic_addrs.keys() if dev not in virtual_net_device]
        if nic_name not in physical_net_device:
            current_app.logger.error("add nic %s ip, not physical nic"% nic_name)
            return errcode.get_error_result("NotPhysicalNICError")
        nic_ifcfg = "/etc/sysconfig/network-scripts/ifcfg-%s" % nic_name
        if not os.path.exists(nic_ifcfg):
            resp = errcode.get_error_result(error="IpConfFileNoFound")
            return resp

        ifcfg_str = "TYPE=Ethernet\nPROXY_METHOD=none\nBROWSER_ONLY=no\nBOOTPROTO=static\nDEFROUTE=yes"\
                    "\nIPV4_FAILURE_FATAL=no\nIPV6INIT=yes\nIPV6_AUTOCONF=yes\nIPV6_DEFROUTE=yes\nIPV6_FAILURE_FATAL=no"\
                    "\nIPV6_ADDR_GEN_MODE=stable-privacy\nNAME={name}\nUUID={uuid}\nDEVICE={nic}\nONBOOT=yes\nIPADDR={ip}"\
                    "\nNETMASK={netmask}\nGATEWAY={gateway}\nDNS1={dns1}"

        uuid = create_uuid()
        ifcfg_str = ifcfg_str.format(**{"uuid": uuid, "nic": nic_name, "ip": ip, "netmask": netmask,
                                        "gateway": gateway, "dns1": dns1, "name": nic_name})
        os.system("ifdown %s"% nic_name)
        if dns2:
            ifcfg_str += "\nDNS2=%s"% dns2
        with open(nic_ifcfg, "w") as f:
            f.write(ifcfg_str)
        # 维护路由表
        # 判断新增网关是否能通
        ret = icmp_ping(gateway)
        if ret:
            # 启动命令 ifup eth0:0
            os.system("ifup %s"% nic_name)
            current_app.logger.info("interface %s update ip %s, gateway %s is link", nic_name, ip, gateway)
        else:
            # 如果网关不通
            # 需维护route 表
            os.system("ifup %s" % nic_name)
            os.system("route del default gw %s"% gateway)
            current_app.logger.info("interface %s update ip %s, gateway %s is not link", nic_name, ip, gateway)
        # 重启网络服务
        os.system("systemctl restart network")
        current_app.logger.info("update nic %s ip success"% nic_name)
        resp["data"] = {
            "name": nic_name
        }
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="UpdateIpConfFileFailure")
        return resp


@api_v1.route('/monitor/delete_ip', methods=['POST'])
@timefn
def delete_ip_info():
    """
    {
        "name": "eth0:0",
        "ip": "172.16.1.31",
        "netmask": "255.255.255.0",
        "gateway": "172.16.1.254",
        "dns1": "8.8.8.8",
        "dns2": "114.114.114.114"
    }
    :return:
    """
    try:
        data = request.get_json()
        name = data.get("name","")
        if name.find(":") == -1:
            current_app.logger.error("delete dev ip: %s, is main device"% name)
            return errcode.get_error_result("MainNICIpDelError")
        try:
            os.system("ifdown %s"% name)
        except:
            pass

        nic_ifcfg = "/etc/sysconfig/network-scripts/ifcfg-%s" % name
        if os.path.exists(nic_ifcfg):
            os.remove(nic_ifcfg)
        current_app.logger.info("delete dev ip: %s success"% name)
        return errcode.get_error_result()
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="DeleteIpConfFileFailure")
        return resp


@api_v1.route('/monitor/exchange_ip', methods=['POST'])
@timefn
def exchange_ip_info():
    """
    {
        "name1": "eth0",
        "name2": "eth0:0",
    }
    :return:
    """
    try:
        data = request.get_json()
        nic_name_1 = data.get("name1")
        nic_name_2 = data.get("name2")
        nic_ifcfg_1 = "/etc/sysconfig/network-scripts/ifcfg-%s" % nic_name_1
        nic_ifcfg_2 = "/etc/sysconfig/network-scripts/ifcfg-%s" % nic_name_2
        if not os.path.exists(nic_ifcfg_1) or not os.path.exists(nic_ifcfg_2):
            resp = errcode.get_error_result(error="IpConfFileNoFound")
            return resp
        with open(nic_ifcfg_1, "r+") as f1:
            with open(nic_ifcfg_2, "r+") as f2:
                ifcfg_str_1 = f1.read()
                ifcfg_str_1 = ifcfg_str_1.replace(nic_name_1, nic_name_2)
                ifcfg_str_2 = f2.read()
                ifcfg_str_2 = ifcfg_str_2.replace(nic_name_2, nic_name_1)
                f1.seek(0)
                f1.truncate()
                f1.write(ifcfg_str_2)
                f2.seek(0)
                f2.truncate()
                f2.write(ifcfg_str_1)
        os.system("ifdown %s"% nic_name_1)
        os.system("ifup %s"% nic_name_1)
        os.system("ifdown %s" % nic_name_2)
        os.system("ifup %s"% nic_name_2)
        current_app.logger.info("exchange nic1 %s nic2 %s ip success"% (nic_name_1, nic_name_2) )
        resp = errcode.get_error_result()
        resp["data"] = {
            "name1": nic_name_2,
            "name2": nic_name_1,
        }
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="ExchangeIpConfFileFailure")
        return resp


@api_v1.route('/monitor/port_status', methods=['POST'])
@timefn
def get_port_status():
    try:
        resp = errcode.get_error_result()
        resp['data'] = {}
        data = request.get_json()
        ports = data.get("ports", None)
        if not ports:
            resp = errcode.get_error_result(error="MessageError")
            return resp
        port_list = [int(port) for port in ports.split(',')]
        conn_list = psutil.net_connections()
        status_cnt_dict = {port: 0 for port in port_list}
        for conn in conn_list:
            if conn.laddr.port in port_list and conn.status == 'ESTABLISHED':
                status_cnt_dict[conn.laddr.port] += 1
        for port in port_list:
            if status_cnt_dict[port] >= 4:
                resp['data'][port] = True
            else:
                resp['data'][port] = False
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="SystemError")
        return resp


@api_v1.route('/monitor/verify_password', methods=['POST'])
@timefn
def verify_password():
    try:
        resp = errcode.get_error_result()
        data = request.get_json()
        user = data.get("user", None)
        password = data.get("password", "")
        if user:
            if not authenticate(user, password, 'system-auth'):
                resp = errcode.get_error_result(error="VerifyPasswordError")
        else:
            resp = errcode.get_error_result(error="MessageError")
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="SystemError")
        return resp


@api_v1.route('/monitor/resource_statis', methods=['POST'])
@timefn
def resource_statis():
    resp = errcode.get_error_result()
    data = request.get_json()
    node_name = data.get("node_name", "")
    node_uuid = data.get("node_uuid", "")
    node_ip = data.get("node_ip", "")
    try:
        period = int(data.get("statis_period", 0))
        statistic = current_app.statistic
        current_app.logger.debug(statistic)
        if period > 1:
            data_cnt = int(period)
            resp['data'] = {}
            resp['data']['utc'] = statistic['utc']
            resp['data']['cpu_util'] = '%0.2f' % np.array(statistic['cpu_util'][-data_cnt:]).mean()
            resp['data']['memory_util'] = '%0.2f' % np.array(statistic['memory_util']['percent'][-data_cnt:]).mean()

            resp['data']['disk_util'] = statistic['disk_util']

            resp['data']['nic_util'] = {}
            for nic in statistic['nic_util'].keys():
                read_bytes_arr = np.array(statistic['nic_util'][nic]['read_bytes'])
                write_bytes_arr = np.array(statistic['nic_util'][nic]['write_bytes'])
                read_bytes_util = read_bytes_arr[-data_cnt:][1:] - read_bytes_arr[-data_cnt:][:-1]
                write_bytes_util = write_bytes_arr[-data_cnt:][1:] - write_bytes_arr[-data_cnt:][:-1]
                sum_bytes_util = read_bytes_util + write_bytes_util
                resp['data']['nic_util'][nic] = {}
                resp['data']['nic_util'][nic]['ip'] = statistic['nic_util'][nic]['ip']
                resp['data']['nic_util'][nic]['read_bytes_avg'] = int("%d" % read_bytes_util.mean())
                resp['data']['nic_util'][nic]['read_bytes_max'] = int("%d" % read_bytes_util.max())
                resp['data']['nic_util'][nic]['write_bytes_avg'] = int("%d" % write_bytes_util.mean())
                resp['data']['nic_util'][nic]['write_bytes_max'] = int("%d" % write_bytes_util.max())
                resp['data']['nic_util'][nic]['sum_bytes_avg'] = int("%d" % sum_bytes_util.mean())
                resp['data']['nic_util'][nic]['sum_bytes_max'] = int("%d" % sum_bytes_util.max())

            current_app.logger.debug(resp)
        else:
            resp = errcode.get_error_result(error="MessageError")
        resp['data']['node_name'] = node_name
        resp['data']['node_uuid'] = node_uuid
        resp['data']['node_ip'] = node_ip
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="SystemError")
        resp['data']['node_name'] = node_name
        resp['data']['node_uuid'] = node_uuid
        resp['data']['node_ip'] = node_ip
        return resp


@api_v1.route('/monitor/resource_perf_for_web', methods=['POST'])
@timefn
def resource_perf_for_web():
    try:
        resp = errcode.get_error_result()
        data = request.get_json()
        period = int(data.get("statis_period", 0))
        node_uuid = data.get("node_uuid", "")
        node_name = data.get("node_name", "")
        statistic = current_app.statistic
        current_app.logger.debug(statistic)
        if period > 1:
            data_cnt = int(period)
            resp['data'] = {"node_name": node_name, "node_uuid": node_uuid}
            resp['data']['server_time'] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            resp['data']['cpu_util'] = float('%0.2f' % np.array(statistic['cpu_util'][-data_cnt:]).mean())
            resp['data']['memory_util'] = {}
            resp['data']['memory_util']['used'] = int(np.array(statistic['memory_util']['used'][-data_cnt:]).mean())
            resp['data']['memory_util']['percent'] = \
                float('%0.2f' % np.array(statistic['memory_util']['percent'][-data_cnt:]).mean())

            resp['data']['nic_util'] = {}
            for nic in statistic['nic_util'].keys():
                read_bytes_arr = np.array(statistic['nic_util'][nic]['read_bytes'])
                write_bytes_arr = np.array(statistic['nic_util'][nic]['write_bytes'])
                read_bytes_util = read_bytes_arr[-data_cnt:][1:] - read_bytes_arr[-data_cnt:][:-1]
                write_bytes_util = write_bytes_arr[-data_cnt:][1:] - write_bytes_arr[-data_cnt:][:-1]
                resp['data']['nic_util'][nic] = {}
                resp['data']['nic_util'][nic]['ip'] = statistic['nic_util'][nic]['ip']
                resp['data']['nic_util'][nic]['read_bytes_avg'] = int("%d" % read_bytes_util.mean())
                resp['data']['nic_util'][nic]['write_bytes_avg'] = int("%d" % write_bytes_util.mean())

            resp['data']['disk_io_util'] = {}
            for disk_name in statistic['disk_io_util'].keys():
                read_bytes_arr = np.array(statistic['disk_io_util'][disk_name]['read_bytes'])
                write_bytes_arr = np.array(statistic['disk_io_util'][disk_name]['write_bytes'])
                read_bytes_util = read_bytes_arr[-data_cnt:][1:] - read_bytes_arr[-data_cnt:][:-1]
                write_bytes_util = write_bytes_arr[-data_cnt:][1:] - write_bytes_arr[-data_cnt:][:-1]
                resp['data']['disk_io_util'][disk_name] = {}
                resp['data']['disk_io_util'][disk_name]['read_bytes_avg'] = int("%d" % read_bytes_util.mean())
                resp['data']['disk_io_util'][disk_name]['write_bytes_avg'] = int("%d" % write_bytes_util.mean())

            # process_list = [p.info for p in psutil.process_iter(
            #     ['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'create_time', 'exe'])]
            process_list = [{'pid': p.pid, 'user': p.username(), 'cpu': float('%0.2f' % p.cpu_percent()),
                             'mem': float('%0.2f' % p.memory_percent()),
                             'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(p.create_time())),
                             'command': p.name()} for p in
                            psutil.process_iter(['pid', 'name', 'username', 'cpu_percent',
                                                 'memory_percent', 'create_time', 'exe'])]
            process_list.sort(key=lambda x: x["cpu"], reverse=True)
            resp['data']['process_list'] = process_list[:10]
            current_app.logger.debug(resp)
        else:
            resp = errcode.get_error_result(error="MessageError")
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="SystemError")
        return resp


@api_v1.route('/monitor/resource_perf_for_database', methods=['POST'])
@timefn
def resource_perf_for_database():
    try:
        resp = errcode.get_error_result()
        data = request.get_json()
        period = int(data.get("statis_period", 0))
        statistic = current_app.statistic
        current_app.logger.debug(statistic)
        if period > 1:
            data_cnt = int(period)
            resp['data'] = {}
            resp['data']['utc'] = statistic['utc']
            resp['data']['cpu_util'] = '%0.2f' % np.array(statistic['cpu_util'][-data_cnt:]).mean()
            resp['data']['memory_util'] = {}
            resp['data']['memory_util']['used'] = int(np.array(statistic['memory_util']['used'][-data_cnt:]).mean())
            resp['data']['memory_util']['percent'] = \
                float('%0.2f' % np.array(statistic['memory_util']['percent'][-data_cnt:]).mean())

            resp['data']['nic_util'] = {}
            for nic in statistic['nic_util'].keys():
                read_bytes_arr = np.array(statistic['nic_util'][nic]['read_bytes'])
                write_bytes_arr = np.array(statistic['nic_util'][nic]['write_bytes'])
                read_bytes_util = read_bytes_arr[-data_cnt:][1:] - read_bytes_arr[-data_cnt:][:-1]
                write_bytes_util = write_bytes_arr[-data_cnt:][1:] - write_bytes_arr[-data_cnt:][:-1]
                resp['data']['nic_util'][nic] = {}
                resp['data']['nic_util'][nic]['ip'] = statistic['nic_util'][nic]['ip']
                resp['data']['nic_util'][nic]['read_bytes_avg'] = int("%d" % read_bytes_util.mean())
                resp['data']['nic_util'][nic]['write_bytes_avg'] = int("%d" % write_bytes_util.mean())
                nic_max_speed = psutil.net_if_stats()[nic].speed
                nic_avg_read_speed = (read_bytes_arr[-1] - read_bytes_arr[0]) / data_cnt / 1024 / 1024
                nic_avg_write_speed = (write_bytes_arr[-1] - write_bytes_arr[0]) / data_cnt / 1024 / 1024
                read_util_rate = nic_avg_read_speed / nic_max_speed * 100
                write_util_rate = nic_avg_write_speed / nic_max_speed * 100
                resp['data']['nic_util'][nic]['read_speed'] = float('%0.2f' % nic_avg_read_speed)
                resp['data']['nic_util'][nic]['write_speed'] = float('%0.2f' % nic_avg_read_speed)
                resp['data']['nic_util'][nic]['read_util_rate'] = float('%0.2f' % read_util_rate)
                resp['data']['nic_util'][nic]['write_util_rate'] = float('%0.2f' % write_util_rate)

            resp['data']['disk_io_util'] = {}
            for disk_name in statistic['disk_io_util'].keys():
                read_bytes_arr = np.array(statistic['disk_io_util'][disk_name]['read_bytes'])
                write_bytes_arr = np.array(statistic['disk_io_util'][disk_name]['write_bytes'])
                io_use_ticks_arr = np.array(statistic['disk_io_util'][disk_name]['io_use_ticks'])
                read_bytes_util = read_bytes_arr[-data_cnt:][1:] - read_bytes_arr[-data_cnt:][:-1]
                write_bytes_util = write_bytes_arr[-data_cnt:][1:] - write_bytes_arr[-data_cnt:][:-1]
                first_io_ticks = io_use_ticks_arr[-data_cnt:][0]
                last_io_ticks = io_use_ticks_arr[-data_cnt:][-1]
                # util = ( current_tot_ticks - previous_tot_ticks ) /  (period_seconds * 1000) * 100, tick: milliseconds
                # tot_ticks: total time spent doing I/Os (ms), including write/read io
                io_util_rate = float('%0.2f' %
                                     ((int(last_io_ticks) - int(first_io_ticks)) / (int(data_cnt) * 1000) * 100))
                resp['data']['disk_io_util'][disk_name] = {}
                resp['data']['disk_io_util'][disk_name]['read_bytes_avg'] = int("%d" % read_bytes_util.mean())
                resp['data']['disk_io_util'][disk_name]['write_bytes_avg'] = int("%d" % write_bytes_util.mean())
                resp['data']['disk_io_util'][disk_name]['io_util_rate'] = io_util_rate

            current_app.logger.debug(resp)
        else:
            resp = errcode.get_error_result(error="MessageError")
        return resp
    except Exception as err:
        current_app.logger.error(err)
        current_app.logger.error(''.join(traceback.format_exc()))
        resp = errcode.get_error_result(error="SystemError")
        return resp


api_v1.add_url_rule('/monitor', view_func=ResourceMonitorHandler.as_view('monitor'), methods=['GET', 'POST'])
