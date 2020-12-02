# -*- coding:utf-8 -*-
import glob
import os
import uuid
import shutil
import logging
try:    import ConfigParser
except: import configparser as ConfigParser
try:    import commands
except: import subprocess as commands


logging.basicConfig(level=logging.INFO,
                    filename=os.path.join(os.path.dirname(__file__), 'ipset.log'),
                    filemode='a',
                    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                    )

WLAN_PATH = '/sys/class/net/*/wireless'
NIC_PATH = '/sys/class/net/*/device'
SYSTEM_CENTOS = 'centos'
SYSTEM_UBUNTU = 'ubuntu'
REDHAT_RELEASE = '/etc/redhat-release'
LSB_RELEASE = '/etc/lsb-release'


def run_cmd(cmd, ignore_log=False):
    (status, output) = commands.getstatusoutput(cmd)
    if not ignore_log:
        if status != 0:
            logging.error('cmd:%s, status:%s, output:%s', cmd, status, output)
        else:
            logging.info('cmd:%s, status:%s, output:%s', cmd, status, output)
    return status, output


class IpSetting(object):

    def wlans(self):
        return [b.split('/')[-2] for b in glob.glob(WLAN_PATH)]

    def nics(self):
        return list(set([b.split('/')[-2] for b in glob.glob(NIC_PATH)]) - set(self.wlans()))

    def check_system_type(self):
        if os.path.exists(REDHAT_RELEASE):
            return SYSTEM_CENTOS
        elif os.path.exists(LSB_RELEASE):
            return SYSTEM_UBUNTU
        else:
            raise Exception("unknown system type")

    def read_ip_info(self, conf_path):
        conf = ConfigParser.ConfigParser()
        conf.read(conf_path)
        mac, ipaddr, netmask, gateway, dns1, dns2 = None, None, None, None, None, None
        if conf.has_option('setting', 'mac_1'):
            mac = conf.get('setting', 'mac_1')
        if conf.has_option('setting', 'ip_1_1'):
            ipaddr = conf.get('setting', 'ip_1_1')
        if conf.has_option('setting', 'netmask_1_1'):
            netmask = conf.get('setting', 'netmask_1_1')
        if conf.has_option('setting', 'gateway_1_1'):
            gateway = conf.get('setting', 'gateway_1_1')
        if conf.has_option('setting', 'dns_1_1'):
            dns1 = conf.get('setting', 'dns_1_1')
        if conf.has_option('setting', 'dns_1_2'):
            dns2 = conf.get('setting', 'dns_1_2')
        nic_name = self.nics()[0]
        logging.info("get ip info, nic:%s, mac:%s, ip:%s, netmask:%s, gateway:%s, dns1:%s, dns2:%s", nic_name,
                     mac, ipaddr, netmask, gateway, dns1, dns2)
        if not (mac and ipaddr and netmask):
            return {
                "nic_name": nic_name
            }
        return {
            "nic_name": nic_name,
            "mac": mac,
            "ipaddr": ipaddr,
            "netmask": netmask,
            "gateway": gateway,
            "dns1": dns1,
            "dns2": dns2
        }

    def set_centos_nic_info(self, ip_path):
        nic_name = self.nics()[0]
        if not os.path.exists(ip_path):
            net_info = [
                "TYPE=Ethernet",
                "PROXY_METHOD=no",
                "BROWSER_ONLY=no",
                "BOOTPROTO=dhcp",
                "DEFROUTE=yes",
                "IPV4_FAILURE_FATAL=no",
                "NAME=%s" % nic_name,
                "DEVICE=%s" % nic_name,
                "ONBOOT=yes"
            ]
        else:
            ip_info = self.read_ip_info(ip_path)
            net_info = [
                "BOOTPROTO=static",
                "DEVICE=%s" % nic_name,
                "HWADDR=%s" % ip_info['mac'],
                "ONBOOT=yes",
                "TYPE=Ethernet",
                "USERCTL=no",
                # "NM_CONTROLLED=no",
                "IPADDR=%s" % ip_info['ipaddr'],
                "NETMASK=%s" % ip_info['netmask'],
                "GATEWAY=%s" % ip_info['gateway']
            ]
            if ip_info.get('dns1'):
                net_info.append("DNS1=%s" % ip_info['dns1'])
            if ip_info.get('dns2'):
                net_info.append("DNS2=%s" % ip_info['dns2'])
        ifcfg_path = '/etc/sysconfig/network-scripts/ifcfg-%s' % nic_name
        with open(ifcfg_path, 'w') as fd:
            fd.write("\n".join(net_info))

    def set_ubuntu_nic_info(self, ip_path, ubuntu_version):
        if not os.path.exists(ip_path):
            net_info = [
                "auto lo",
                "iface lo inet loopback"
            ]
        else:
            ip_info = self.read_ip_info(ip_path)
            net_info = [
                "auto lo",
                "iface lo inet loopback",
                "auto %s" % ip_info['nic_name'],
                "iface %s inet static" % ip_info['nic_name'],
                "address %s" % ip_info['ipaddr'],
                "netmask %s" % ip_info['netmask'],
                "gateway %s" % ip_info['gateway']
            ]
            dns_info = list()
            if ip_info.get('dns1'):
                dns_info.append("nameserver %s" % ip_info['dns1'])
            if ip_info.get('dns2'):
                dns_info.append("nameserver %s" % ip_info['dns2'])
            if dns_info:
                with open('/etc/resolv.conf', 'w') as fd:
                    fd.write("\n".join(dns_info))
            if float(ubuntu_version) >= 17.10:
                net_info = [
                    "network:",
                    "  ethernets:",
                    "    ens3:",
                    "      addresses: [%s/24]" % ip_info["ipaddr"],
                    "      dhcp4: no",
                    "      optional: true",
                    "      gateway4: %s" % ip_info["gateway"],
                    "      nameservers:",
                    "        addresses: [%s]" % ip_info['dns1'],
                    "  version: 2",
                    "  renderer: NetworkManager"
                ]
                with open('/etc/netplan/01-installer-config.yaml', 'w') as fd:
                    fd.write("\n".join(net_info))
                # 使网卡配置生效
                os.popen('sudo netplan apply')
                return
            else:
                with open('/etc/network/interfaces', 'w') as fd:
                    fd.write("\n".join(net_info))
                return
        with open('/etc/network/interfaces', 'w') as fd:
            fd.write("\n".join(net_info))

    def set_nic_info(self):
        sys_type = self.check_system_type()
        logging.info("get system type:%s", sys_type)
        if REDHAT_RELEASE == sys_type:
            self.set_centos_nic_info()
        elif LSB_RELEASE == sys_type:
            self.set_ubuntu_nic_info()
        else:
            logging.info("unknown system type:%s", sys_type)

    def get_ubuntu_version(self):
        cmd = 'grep "DISTRIB_RELEASE=" %s | awk -F= \'{print $2}\'' % LSB_RELEASE
        version = os.popen(cmd).read()
        return version.strip()

    def set_ip(self):
        tmp_dir = os.path.join("/tmp", str(uuid.uuid1()))
        os.makedirs(tmp_dir)
        (status, output) = run_cmd('mount /dev/sr0 %s' % tmp_dir)
        logging.info("mount config drive to /mnt, status:%s, output:%s", status, output)
        try:
            ip_path = os.path.join(tmp_dir, 'ipinfo', 'ip.ini')
            sys_type = self.check_system_type()
            logging.info("get system type:%s", sys_type)
            if SYSTEM_CENTOS == sys_type:
                self.set_centos_nic_info(ip_path)
                (status, output) = run_cmd('systemctl restart network')
                logging.info("restart network status:%s, output:%s", status, output)
                # centos8已废弃network服务
                if status != 0:
                    (status, output) = run_cmd('systemctl restart NetworkManager')
                    logging.info("restart NetworkManager status:%s, output:%s", status, output)
            elif SYSTEM_UBUNTU == sys_type:
                ubuntu_version = self.get_ubuntu_version()
                self.set_ubuntu_nic_info(ip_path, ubuntu_version)
                (status, output) = run_cmd('systemctl restart networking')
                logging.info("restart networking status:%s, output:%s", status, output)
            else:
                logging.info("unknown system type:%s", sys_type)
        except Exception as e:
            logging.error("set ip info failed:%s", e)
        finally:
            (status, output) = run_cmd('umount %s' % tmp_dir)
            logging.info("umount /mnt status:%s, output:%s", status, output)
            shutil.rmtree(tmp_dir)


if __name__ == '__main__':
    IpSetting().set_ip()
