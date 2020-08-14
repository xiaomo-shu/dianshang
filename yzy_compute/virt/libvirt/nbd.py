"""
We use nbd(network block device) to read the virtual machine disk file, and in windows we modify
the regedit to set the hostname and ip addr.
We must compile the nbd module in centos7, such as below:
    yum install -y rpm-build
    yum install -y m4 bc xmlto asciidoc hmaccalc newt-devel pesign perl-ExtUtils-Embed
    yum install -y perl elfutils-libelf-devel elfutils-devel binutils-devel bison audit-libs-devel java-devel numactl-devel pciutils-devel ncurses-devel  python-docutils
    uname -r
    sudo su
    # useradd builder
    # groupadd builder
    cd /home/centos
    # Get Source Code
    wget http://vault.centos.org/7.7.1908/os/Source/SPackages/kernel-3.10.0-1062.el7.src.rpm
    rpm -ivh kernel-3.10.0-1062.el7.src.rpm

    # Build Preparation
    mkdir -p ~/rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
    echo '%_topdir %(echo $HOME)/rpmbuild' > ~/.rpmmacros
    cd ~/rpmbuild/SPECS
    rpmbuild -bp --target=$(uname -m) kernel.spec
    cd ~/rpmbuild/BUILD/kernel-3.10.0-1062.el7/linux-3.10.0-1062.el7.x86_64/
    sed -i 's/REQ_TYPE_SPECIAL/REQ_TYPE_DRV_PRIV/' drivers/block/nbd.c

    # Build
    make menuconfig
    # Device Driver -> Block devices -> Set “M” On “Network block device support”

    make prepare && make modules_prepare && make
    make M=drivers/block -j8
    modinfo drivers/block/nbd.ko
    cp drivers/block/nbd.ko /lib/modules/3.10.0-1062.4.3.el7.x86_64/extra/
    depmod -a && sudo modprobe nbd max_part=16
"""
import logging
import time
import ctypes
import traceback
import binascii
import os
import uuid
from retrying import retry
from configparser import ConfigParser
from common import cmdutils
from common import constants
from yzy_compute import utils
from yzy_compute import exception


class WinRegedit(object):

    def get_adapter_name(self, reg_file):
        logging.info("get the ip interface info")
        cmdutils.execute("sed -i '1d' %s" % (reg_file,), run_as_root=True, shell=True)
        cf = ConfigParser()
        conf = reg_file
        cf.read(conf)
        sections = cf.sections()
        adapters = ""
        for section in sections:
            if section.startswith("HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\services\Tcpip\Parameters\Adapters\{"):
                adapters = section

        adapters_list = adapters.split("\\")
        interface = "HKEY_LOCAL_MACHINE\\SYSTEM\\ControlSet001\\services\\Tcpip\\Parameters\\Interfaces\\%s" % adapters_list[-1]
        cmdutils.execute("sed -i '1i Windows Registry Editor Version 5.00' %s" % (reg_file,), run_as_root=True, shell=True)
        return interface

    def _create_hex_ip(self, ipaddr, type=1):
        """windows注册表规则：reg_multi_sz,在每2个十六进制数据之后加‘00’.最后再加4个‘00’"""
        hexvalue = str(binascii.hexlify(ipaddr.encode('utf8')), 'ascii')
        hexlist = [hexvalue[i * 2:i * 2 + 2] for i in range(0, int(len(hexvalue) / 2))]
        hexhostname = ',00,'.join(hexlist) + ',00,00,00,00,00'
        value = 'hex\\(%s\\):%s' % (type, hexhostname)
        return value

    def set_fix_ip(self, reg_file):
        interface = self.get_adapter_name(reg_file)
        # "EnableDHCP"=dword:00000000
        logging.info("disable dhcp")
        cmd = 'crudini --set %s "%s" \\"EnableDHCP\\" %s' % (reg_file, interface, "dword:00000000")
        cmdutils.execute(cmd, run_as_root=True, shell=True)
        # ipaddr = self._create_hex_ip(ip, type=7)
        # cmd = 'crudini --set %s "%s" \\"IPAddress\\" %s' % (reg_file, interface, ipaddr)
        # 这样设置在 = 两边会有空格，导致merge失败
        # cmdutils.execute(cmd, run_as_root=True, shell=True)
        """
        #"IPAddress"=hex(7):30,00,2e,00,30,00,2e,00,30,00,2e,00,30,00,00,00,00,00
        cmd='vec-config --set %s "%s" \\"IPAddress\\" %s' % (reg_file,adapterName,"hex\(7\):30,00,2e,00,30,00,2e,00,30,00,2e,00,30,00,00,00,00,00")
        cmdutils.execute_cmd(thread_id,instance_uuid,
                             cmd,
                             run_as_root=True,shell=True)
        """

    # def set_dhcp(self, reg_file):
    #     interface = self.self.get_adapter_name(reg_file)
    #     # "EnableDHCP"=dword:00000001
    #     logging.info("enable dhcp")
    #     cmd = 'crudini --set %s "%s" \\"EnableDHCP\\" %s' % (reg_file, interface, "dword:00000001")
    #     cmdutils.execute_cmd(cmd, run_as_root=True, shell=True)
    #
    #     # "NameServer"=hex(1):00,00
    #     cmd = 'crudini --set %s "%s" \\"NameServer\\" %s' % (reg_file, interface, "hex\(1\):00,00")
    #     cmdutils.execute_cmd(cmd, run_as_root=True, shell=True)


class NbdManager(object):

    def __init__(self, instance):
        self.instance = instance
        thread_id = ctypes.CDLL('libc.so.6').syscall(186)
        self.thread_id = thread_id

    def _umount_nbd(self, mount_point):
        try:
            cmdutils.execute('umount', mount_point, run_as_root=True)
        except Exception as e:
            logging.error("umount the nbd device failed:%s", e)
            raise

    @retry(stop_max_attempt_number=6)
    def umount_nbd(self, mount_point):
        try:
            logging.info("umount nbd")
            self._umount_nbd(mount_point)
        except:
            pass

    @retry(stop_max_attempt_number=6)
    def check_and_mount(self, device, mount_point):
        """check if the nbd device exists"""
        logging.info("check nbd mount state")
        stdout, stderr = cmdutils.execute('ls', device, run_as_root=True)
        if stderr:
            time.sleep(0.5)
            raise Exception("the nbd partitions not found")
        logging.info("mount the nbd device to %s", mount_point)
        stdout, stderr = cmdutils.execute('mount.ntfs-3g', device, mount_point, run_as_root=True)
        if stderr:
            time.sleep(0.5)
            raise Exception("mount device failed")

    @retry(stop_max_attempt_number=3)
    def disconnect_nbd(self, nbd_device, mount_point):
        self.umount_nbd(mount_point)
        logging.info("disconnect nbd, nbd_device:%s", nbd_device)
        stdout, stderr = cmdutils.execute('qemu-nbd', '-d', nbd_device, run_as_root=True)
        if stderr:
            message = "Instance[%s] disconnect nbd[%s] failed:%s" % (nbd_device, self.instance['uuid'], stderr)
            logging.error(message)
            raise exception.NBDDisconnectException(message)
        logging.info("disconnect nbd success")

    def _connect(self, nbd_device, disk_file, mount_point):
        """connect the disk image to nbd, and mount the system partition"""
        try:
            logging.info("connect the virtual disk to nbd device")
            cmdutils.execute('qemu-nbd', '-c', nbd_device, disk_file, run_as_root=True)
            if constants.OS_TYPE_XP == self.instance['os_type'] or \
                    constants.OS_TYPE_LINUX == self.instance['os_type']:
                nbdpoint='p1'
            else:
                nbdpoint='p2'
            device = '%s%s' % (nbd_device, nbdpoint)
            self.check_and_mount(device, mount_point)
            return True
        except Exception:
            fault = traceback.format_exc()
            message = "Instance[%s] connect nbd device[%s] error:%s " % (self.instance['uuid'], nbd_device, fault)
            logging.error(message)
            try:
                self.umount_nbd(mount_point=mount_point)
            except:
                pass
            raise exception.NBDConnectException(message=message)

    def _get_reg_location(self):
        if 'winxp' == self.instance['os_type']:
            return 'WINDOWS/system32/config/system'
        else:
            return 'Windows/System32/config/SYSTEM'

    def _create_hex_hostname(self, hostname, type=1):
        """windows注册表规则：reg_se,在每2个十六进制数据之后加‘00’.最后再加2个‘00’"""
        hexvalue = str(binascii.hexlify(hostname.encode('utf8')), 'ascii')
        hexlist = [hexvalue[i * 2:i * 2 + 2] for i in range(0, int(len(hexvalue) / 2))]
        hexhostname = ',00,'.join(hexlist) + ',00,00,00'
        value = 'hex(%s):%s' % (type, hexhostname)
        return value

    def create_hostname_reg_file(self, hostname, reg_file):
        compute_name = self._create_hex_hostname(hostname)
        reg_content = 'Windows Registry Editor Version 5.00\n\n'
        reg_content = reg_content + '[HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\services\Tcpip\Parameters]\n'
        reg_content = reg_content + '"Hostname"=%s\n' % (compute_name)
        reg_content = reg_content + '"NV Hostname"=%s\n\n' % (compute_name)

        reg_content = reg_content + '[HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Control\ComputerName\ComputerName]\n'
        reg_content = reg_content + '"ComputerName"=%s\n' % (compute_name)

        # reg_content = reg_content + '[HKEY_LOCAL_MACHINE\SYSTEM\Select]\n'
        # reg_content = reg_content + '"Default"=dword:00000001\n'
        # reg_content = reg_content + '"LastKnownGood"=dword:00000002\n'
        with open(reg_file, 'w') as f:
            f.write(reg_content)
        os.chmod(reg_file, 0o777)
        logging.info("create reg file with hostname")

    def _set_hostname(self, mount_point):
        try:
            reg_file = '%s.reg' % self.instance['uuid']
            self.create_hostname_reg_file(self.instance['name'], reg_file)
            merge_cmd = "hivexregedit --merge %s/%s --prefix 'HKEY_LOCAL_MACHINE\SYSTEM' %s" % \
                  (mount_point, self._get_reg_location(), reg_file)
            cmdutils.execute(merge_cmd, run_as_root=True, shell=True)
            logging.info("merge hostname info to regedit success")
            try:
                os.remove(reg_file)
                logging.info("remove hostname reg file")
            except:
                pass
        except Exception as e:
            message = "%s,instance_uuid[%s] set compute name error:%s" % (self.thread_id, self.instance['uuid'], e)
            logging.error(message)
            raise exception.ModifyComputeNameException(message)

    def _set_ip_address(self, mount_point, network_info=None):
        """
        [setting]
        --网卡数量
        mac_number=2

        ------------1号网卡参数-----------
        --网卡MAC地址
        mac_1=00-0C-29-C0-A5-52
        --是否开启DHCP
        dhcp_1=1
        --1号网卡IP数量
        ip_number_1=2
        --1号网卡类型，1为IPV6
        ip_type_1=0
        --1号网卡1号IP
        ip_1_1=192.168.182.110
        --1号网卡1号子网掩码
        netmask_1_1=255.255.255.0
        --1号网卡1号默认网关
        gateway_1_1=192.168.182.1
        --1号网卡2号IP
        ip_1_2=192.168.182.111
        --1号网卡2号子网掩码
        netmask_1_2=255.255.255.0
        --1号网卡2号默认网关
        gateway_1_2=192.168.182.2
        ---------2号网卡参数------------
        mac_2=00-0C-29-C0-A5-53
        ip_number_2=1
        ip_type_2=0
        ip_1_2=192.168.182.110
        netmask_1_2=255.255.255.0
        gateway_1_2=192.168.182.1
        --DNS数量
        dns_number=2
        dns_1=8.8.8.8
        dns_2=9.9.9.9
        """
        try:
            if not network_info:
                return
            ip_info = network_info[0]
            if not ip_info.get('fixed_ip', None):
                return

            # reg_file = '%s.reg' % uuid.uuid1()
            # para_path = '\\ControlSet001\\services\\Tcpip\\Parameters'
            # export_cmd = "hivexregedit --export --prefix 'HKEY_LOCAL_MACHINE\\SYSTEM' " \
            #       "%s/%s '%s' > %s" % (mount_point, self._get_reg_location(), para_path, reg_file)
            # logging.info("export tcpip info to reg_file:%s", reg_file)
            # cmdutils.execute(export_cmd, run_as_root=True, shell=True)
            #
            # logging.info("set fixip mode")
            # winreg = WinRegedit()
            # winreg.set_fix_ip(reg_file)
            # logging.info("merge the regedit")
            # merge_cmd = "hivexregedit --merge %s/%s --prefix 'HKEY_LOCAL_MACHINE\SYSTEM' %s" % \
            #             (mount_point, self._get_reg_location(), reg_file)
            # cmdutils.execute(merge_cmd, run_as_root=True, shell=True)
            #
            # try:
            #     os.remove(reg_file)
            #     logging.info("remove ip reg file")
            # except:
            #     pass

            logging.info("set the network info to ip file")
            ip_file_path = os.path.join(mount_point, 'ipinfo')
            ip_file = os.path.join(ip_file_path, 'ip.ini')
            utils.ensure_tree(ip_file_path)
            # cmdutils.execute('crudini', '--set', ip_file, "setting", "iptype", "FIX", run_as_root=True)
            # cmdutils.execute('crudini', '--set', ip_file, "setting", "complete", "NO", run_as_root=True)
            # cmdutils.execute('crudini', '--set', ip_file, "setting", "os", self.instance['os_type'],
            #                  run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "mac_number", 1,
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "mac_1", ip_info.get('mac_addr'),
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "dhcp_1", 0,
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "ip_number_1", 1,
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "ip_type_1", 0,
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "ip_1_1", ip_info.get('fixed_ip'),
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "netmask_1_1", ip_info.get('netmask'),
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "gateway_1_1", ip_info.get('gateway'),
                             run_as_root=True)
            dns_server = ip_info.get('dns_server', [])
            if dns_server:
                cmdutils.execute('crudini', '--set', ip_file, "setting", "dns_number_1", len(dns_server),
                                 run_as_root=True)
                for index, dns in enumerate(dns_server):
                    key = 'dns_1_%s' % (index + 1)
                    cmdutils.execute('crudini', '--set', ip_file, "setting", key, dns, run_as_root=True)
        except Exception as e:
            message = 'instance_uuid[%s] set ip info error:%s' % (self.instance['uuid'], e)
            logging.error(message)
            raise exception.SetIPAddressException(message)


    def modify_guest_meta(self, disk_file, network_info=None):
        nbd_id = self.thread_id % 16
        mount_point = '/mnt/%s' % nbd_id
        try:
            utils.ensure_tree(mount_point)
        except:
            pass
        nbd_device = '/dev/nbd%s' % nbd_id
        logging.info("modify guest info start, nbd_device:%s, mount_point:%s", nbd_device, mount_point)
        try:
            self.disconnect_nbd(nbd_device, mount_point)
        except:
            pass
        try:
            # connect the virtual disk file with nbd
            self._connect(nbd_device, disk_file, mount_point)
            if constants.OS_TYPE_WINDOWS == self.instance['os_type']:
                logging.info('start modify[%s] reg' % self.instance['uuid'])
                self._set_hostname(mount_point)
                self._set_ip_address(mount_point, network_info)
                logging.info('end modify[%s] reg' % self.instance['uuid'])
        except Exception as e:
            logging.error("modify the guest metadata failed:%s", e)
        finally:
            try:
                self.disconnect_nbd(nbd_device, mount_point)
            except:
                pass
