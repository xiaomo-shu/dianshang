import glob
import os
import commands
import logging
import ConfigParser

logging.basicConfig(level=logging.INFO,
                    filename='ipset.log',
                    filemode='w',
                    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                    )

WLAN_PATH = '/sys/class/net/*/wireless'
NIC_PATH = '/sys/class/net/*/device'
CONF_PATH = '/mnt/ipinfo/ip.ini'


def wlans():
    return [b.split('/')[-2] for b in glob.glob(WLAN_PATH)]


def nics():

    return list(set([b.split('/')[-2] for b in glob.glob(NIC_PATH)]) - set(wlans()))


def set_nic_info():
    conf = ConfigParser.ConfigParser()
    conf.read(CONF_PATH)
    mac = conf.get('setting', 'mac_1')
    ipaddr = conf.get('setting', 'ip_1_1')
    netmask = conf.get('setting', 'netmask_1_1')
    gateway = conf.get('setting', 'gateway_1_1')
    nic_name = nics()[0]
    str = '''BOOTPROTO=static
DEVICE=%s
HWADDR=%s
ONBOOT=yes
TYPE=Ethernet
USERCTL=no
IPADDR=%s
NETMASK=%s
GATEWAY=%s
    ''' % (nic_name, mac, ipaddr, netmask, gateway)
    ifcfg_path = '/etc/sysconfig/network-scripts/ifcfg-%s' % nic_name
    with open(ifcfg_path, 'w') as fd:
        fd.write(str)


if __name__ == '__main__':
    (status, output) = commands.getstatusoutput('mount /dev/disk/by-label/config-2 /mnt')
    logging.info("mount config drive to /mnt, status:%s, output:%s", status, output)
    if os.path.exists(CONF_PATH):
        try:
            set_nic_info()
        except Exception as e:
            logging.error("set nic info failed:%s", e)
            exit(1)
        (status, output) = commands.getstatusoutput('systemctl restart network')
        logging.info("restart network status:%s, output:%s", status, output)
        (status, output) = commands.getstatusoutput('umount /mnt')
        logging.info("umount /mnt status:%s, output:%s", status, output)
    else:
        logging.info("can not found ipinfo file")
        exit(1)
