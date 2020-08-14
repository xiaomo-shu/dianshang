import logging
import re
import os
import psutil
import shutil
import datetime as dt
from common.config import FileOp
from common import constants, cmdutils
from common.errcode import get_error_result
from yzy_compute import exception
from .linuxbridge_agent import LinuxBridgeManager


class BondManager(object):

    def __init__(self):
        self.base_dir = "/etc/sysconfig/network-scripts/"
        self.file_path = "/etc/sysconfig/network-scripts/ifcfg-%s"
        self.common_content = [
            "TYPE=Ethernet",
            "ONBOOT=yes",
            # "DEFROUTE=no",
            "NM_CONTROLLED=no"
        ]
        self.backup_dir = os.path.join(self.base_dir, 'bond_backup')
        if not os.path.exists(self.backup_dir):
            os.mkdir(self.backup_dir)
        self.mac_regex = r'[A-F0-9]{2}[-:]?[A-F0-9]{2}[-:.]?[A-F0-9]{2}[-:]?[A-F0-9]{2}[-:.]?[A-F0-9]{2}[-:]?[A-F0-9]{2}'
        self.ip_regex = r'((([1-9]?|1\d)\d|2([0-4]\d|5[0-5]))\.){3}(([1-9]?|1\d)\d|2([0-4]\d|5[0-5]))'

    def list_files(self, dir_path):
        file_list = list()
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            if os.path.isfile(file_path):
                file_list.append(file_path)
        return file_list

    def update_conf(self, conf, conf_list):
        with open(conf, 'w') as fd:
            fd.write('\n'.join(conf_list))
            fd.write('\n')
            fd.flush()
            os.fsync(fd.fileno())
            fd.close()

        logging.info("file:%s, content:%s", conf, conf_list)

    def config_bond(self, bond_info, ip_list, gate_info, remove_slaves, new_flag=True):
        # bonding模块加载
        # 设置参数max_bonds=0是因为max_bonds的缺省默认值为1
        # 这会导致模块在/sys/class/net/bonding_masters中默认创建一个bond0（无任何slave）
        if not FileOp(constants.BOND_MASTERS).exist_file():
            logging.info('modprobe bonding max_bonds=0')
            self._run_cmd("modprobe bonding max_bonds=0")

        # # 删除slave网卡上的数据网络
        # for net in networks:
        #     LinuxBridgeManager().network_delete(net['network_id'], net.get('vlan_id', None))

        # 备份要修改的文件，以便出现异常时回滚
        self._backup(bond_info["dev"], *bond_info["slaves"], *remove_slaves)

        try:
            # 编辑bond时允许变更被绑定网卡，可能出现slaves减少的情况，需要更新减少网卡的配置文件，并移除slave身份
            if remove_slaves:
                for free_slave in remove_slaves:
                    ifconf = self.file_path % free_slave
                    self._remove_file(ifconf, 'free slave')
                    recover_content = [
                        "NAME=%s" % free_slave,
                        "DEVICE=%s" % free_slave,
                        "BOOTPROTO=none",
                    ]
                    recover_content.extend(self.common_content)
                    self.update_conf(ifconf, recover_content)

                    # # 从/sys/devices/virtual/net/bond0/bonding/slaves移除要删除的slave名称，否则slave身份仍会存在
                    # self._run_cmd("echo -%s > %s" % (free_slave, constants.BOND_SLAVES % bond_info['dev']))
                    self._run_cmd("ip link set dev %s nomaster" % free_slave)

                    # 启用已还原的物理网卡
                    self._run_cmd("ifup %s" % free_slave)

            # 更新slave网卡配置文件
            for slave in bond_info["slaves"]:
                ifconf = self.file_path % slave
                self._remove_file(ifconf, 'slave')
                slave_content = [
                    "NAME=%s" % slave,
                    "DEVICE=%s" % slave,
                    "BOOTPROTO=none",
                    "MASTER=%s" % bond_info['dev'],
                    "SLAVE=yes",
                ]
                slave_content.extend(self.common_content)
                self.update_conf(ifconf, slave_content)
                self._run_cmd("ifdown %s" % slave)

            # 新增bond网卡配置文件
            bond_conf = self.file_path % bond_info['dev']
            bond_content = [
                "NAME=%s" % bond_info['dev'],
                "DEVICE=%s" % bond_info['dev'],
                "TYPE=bond",
                "BONDING_MASTER=yes",
                'BONDING_OPTS="mode=%s miimon=100"' % bond_info['mode'],
                "BOOTPROTO=%s" % ("none" if 0 == len(ip_list) else "static"),
            ]
            bond_content.extend(self.common_content[1:])

            # 给bond网卡配IP
            if ip_list:
                for index, ip_info in enumerate(ip_list):
                    bond_content.append(
                        "IPADDR%s=%s" % (index, ip_info['ip'])
                    )
                    bond_content.append(
                        "NETMASK%s=%s" % (index, ip_info['netmask'])
                    )
                    # bond_content_copy = copy.deepcopy(bond_content)
                    #
                    # # 如果bond网卡上要配附属IP，则再新增一个bond网卡附属IP配置文件
                    # if index > 0:
                    #     dev_name = bond_info['dev'] + ":%s" % (index - 1)
                    #     bond_content_copy[0] = "DEVICE=%s" % dev_name
                    # else:
                    #     dev_name = bond_info['dev']
                    #
                    # bond_conf = self.file_path % dev_name
                    # info = [
                    #     "IPADDR=%s" % ip_info['ip'],
                    #     "NETMASK=%s" % ip_info['netmask'],
                    #     "GATEWAY=%s" % ip_info['gateway'],
                    # ]
                    #
                    # if ip_info.get('dns1'):
                    #     info.append("DNS1=%s" % ip_info['dns1'])
                    # if ip_info.get('dns2'):
                    #     info.append("DNS2=%s" % ip_info['dns2'])
                    #
                    # bond_content_copy += info
                    # self.update_conf(bond_conf, bond_content_copy)
                    #
                    # # server层把bond网卡的interface_ip入库时需要附属IP名称
                    # # 把server层传入的ip_list加一个字段name，再返回给server层
                    # ip_info["name"] = dev_name
            # 给bond网卡配网关、DNS
            if gate_info:
                if gate_info.get('gateway'):
                    bond_content.append("GATEWAY=%s" % gate_info['gateway'])
                if gate_info.get('dns1'):
                    bond_content.append("DNS1=%s" % gate_info['dns1'])
                if gate_info.get('dns2'):
                    bond_content.append("DNS2=%s" % gate_info['dns2'])
            self.update_conf(bond_conf, bond_content)

            # # 如果是新增bond，则需向/sys/class/net/bonding_masters添加bond名称，使bond生效
            # if new_flag:
            #     self._run_cmd("echo +%s > %s" % (bond_info["dev"], constants.BOND_MASTERS))
            # else:
            #     # 如果是编辑bond，需先关闭bond网卡再启用
            #     self._run_cmd("ifdown %s" % bond_info["dev"])

            if not new_flag:
                # 如果是编辑bond，需先关闭bond网卡再启用
                self._run_cmd("ifdown %s" % bond_info["dev"])

            # 启用bond网卡
            ifup_ret = self._run_cmd("ifup %s" % bond_info["dev"])
            # IP冲突导致网卡无此IP
            if ifup_ret:
                self._rollback(bond_info["dev"], new_flag)
                return ifup_ret

            # # 在bond网卡上创建数据网络
            # for net in networks:
            #     if constants.FLAT_NETWORK_TYPE == net['network_type']:
            #         LinuxBridgeManager().create_flat_network(net['network_id'], bond_info['dev'])
            #     elif constants.VLAN_NETWORK_TYPE == net['network_type']:
            #         LinuxBridgeManager().create_vlan_network(net['network_id'], bond_info['dev'], net['vlan_id'])
            #     else:
            #         pass

            resp = {
                "bond_nic_info": self._get_network_info(bond_info['dev'])
            }

            self._clear_backup()
            return resp
        except Exception as e:
            logging.exception("config_bond Exception: %s" % str(e), exc_info=True)
            self._rollback(bond_info["dev"], new_flag)
            return get_error_result("ConfigBondError")

    def unbond(self, bond_name, slaves):
        try:
            self._run_cmd("ip link del dev %s" % bond_name)

            # 备份要修改的文件，以便出现异常时回滚
            self._backup(bond_name, *[_d["nic"] for _d in slaves])

            # 删除bond网卡配置文件
            bond_ifconf = self.file_path % bond_name
            self._remove_file(bond_ifconf, 'bond')

            for slave in slaves:
                # # 需求已明确：解绑网卡时要保证此bond设备没有数据网络使用，因此入参中不会提供networks
                # for net in slave.get('networks', []):
                #     LinuxBridgeManager().network_delete(net['network_id'], net.get('vlan_id', None))

                # 更新slave网卡配置文件
                slave_content = [
                    "NAME=%s" % slave['nic'],
                    "DEVICE=%s" % slave['nic'],
                    "BOOTPROTO=%s" % ("static" if slave.get('ip_list') else "none"),
                ]
                slave_content.extend(self.common_content)
                ifconf = self.file_path % slave['nic']
                self._remove_file(ifconf, 'unbond slave')

                # 给slave网卡配IP
                ip_list = slave.get("ip_list", [])
                if ip_list:
                    for index, ip_info in enumerate(ip_list):
                        slave_content.append(
                            "IPADDR%s=%s" % (index, ip_info['ip'])
                        )
                        slave_content.append(
                            "NETMASK%s=%s" % (index, ip_info['netmask'])
                        )
                        # slave_content_copy = copy.deepcopy(slave_content)
                        #
                        # # 如果slave网卡上要配附属IP，则再新增一个slave网卡附属IP配置文件
                        # if index > 0:
                        #     dev_name = slave['nic'] + ":%s" % (index - 1)
                        #     slave_content_copy[0] = "DEVICE=%s" % dev_name
                        #     slave_content_copy[1] = "NAME=%s" % dev_name
                        # else:
                        #     dev_name = slave['nic']
                        #
                        # slave_conf = self.file_path % dev_name
                        # info = [
                        #     "IPADDR=%s" % ip_info['ip'],
                        #     "NETMASK=%s" % ip_info['netmask'],
                        #     "GATEWAY=%s" % ip_info['gateway'],
                        # ]
                        #
                        # if ip_info.get('dns1'):
                        #     info.append("DNS1=%s" % ip_info['dns1'])
                        # if ip_info.get('dns2'):
                        #     info.append("DNS2=%s" % ip_info['dns2'])
                        #
                        # slave_content_copy += info
                        # self.update_conf(slave_conf, slave_content_copy)
                    # 给slave网卡配网关、DNS
                    if ip_list[0].get('gateway'):
                        slave_content.append("GATEWAY=%s" % ip_list[0]['gateway'])
                    if ip_list[0].get('dns1'):
                        slave_content.append("DNS1=%s" % ip_list[0]['dns1'])
                    if ip_list[0].get('dns2'):
                        slave_content.append("DNS2=%s" % ip_list[0]['dns2'])
                self.update_conf(ifconf, slave_content)
                self._run_cmd("ifdown %s" % slave['nic'])
                ifup_ret = self._run_cmd("ifup %s" % slave['nic'])
                # IP冲突导致网卡无此IP
                if ifup_ret:
                    self._rollback(bond_name, new_flag=False)
                    return ifup_ret

            # # 从/sys/class/net/bonding_masters移除要删除的bond名称，否则该bond仍会存在
            # self._run_cmd("echo -%s > %s" % (bond_name, constants.BOND_MASTERS))
            self._clear_backup()

            # for slave in slaves:
            #     # 需求已明确：解绑网卡时要保证此bond设备没有数据网络使用，因此入参中不会提供networks
            #     for net in slave.get('networks', []):
            #         if constants.FLAT_NETWORK_TYPE == net['network_type']:
            #             LinuxBridgeManager().create_flat_network(net['network_id'], slave['nic'])
            #         elif constants.VLAN_NETWORK_TYPE == net['network_type']:
            #             LinuxBridgeManager().create_vlan_network(net['network_id'], slave['nic'], net['vlan_id'])
            #         else:
            #             pass

        except Exception as e:
            logging.exception("config_bond Exception: %s" % str(e), exc_info=True)
            self._rollback(bond_name, new_flag=False)
            return get_error_result("UnBondError")

    def _get_network_info(self, nic_name):
        """获取bond网卡的mac speed status 参照接口/monitor/network"""
        try:
            nic_addrs = psutil.net_if_addrs()
            nic_mac = ""
            nic_speed = 0
            for info in nic_addrs[nic_name]:
                if str(info.family) == "AddressFamily.AF_PACKET":
                    nic_mac = info.address

            try:
                ret = os.popen('ethtool %s|grep "Speed"' % nic_name).readlines()[-1]
                speed = re.sub("\D", "", ret)
                if speed:
                    nic_speed = int(speed)
            except Exception as e:
                logging.exception("nic_speed Exception: %s" % str(e), exc_info=True)
                nic_speed = 0

            try:
                # 网卡是否插网线
                nic_stat = bool(int(open('/sys/class/net/{}/carrier'.format(nic_name), 'r').readline()[0]))
            except Exception as e:
                logging.exception("nic_stat Exception: %s" % str(e), exc_info=True)
                nic_stat = False

            resp = {
                "nic": nic_name,
                'mac': nic_mac,
                'speed': nic_speed,
                'status': 2 if nic_stat else 1
            }
            logging.info("get_network_info resp: %s" % resp)

        except Exception as e:
            logging.exception("get_network_info Exception: %s" % str(e), exc_info=True)
            resp = dict()

        return resp

    def _run_cmd(self, cmd_str):
        code, out = cmdutils.run_cmd(cmd_str)
        if code != 0:
            if "already uses address" in out:
                mac = re.search(self.mac_regex, out).group(0)
                ip = re.search(self.ip_regex, out).group(0)
                return get_error_result("IPUsedByOtherHost", mac=mac, ip=ip)
            raise exception.BondException(error=out)
        return None

    def _remove_file(self, file_path, log_str):
        try:
            os.remove(file_path)
            logging.info("remove %s: %s", (log_str, file_path))
        except Exception as e:
            logging.error("remove %s: %s failed: %s", (log_str, file_path, str(e)))
            raise exception.BondException(error=str(e))

    def _backup(self, *args):
        if not os.path.exists(self.backup_dir):
            os.mkdir(self.backup_dir)
        for filename in args:
            if os.path.exists(self.file_path % filename):
                shutil.copy2(self.file_path % filename, os.path.join(self.backup_dir, filename))
        logging.info("_backup bond ifcfg-file finished")

    def _clear_backup(self):
        logging.info("start _clear_backup")
        try:
            for filename in os.listdir(self.backup_dir):
                os.remove(os.path.join(self.backup_dir, filename))
        except Exception as e:
            logging.exception('_clear_backup error: %s ' % str(e))
            cmdutils.run_cmd("rm -f %s" % self.backup_dir)
            os.mkdir(self.backup_dir)
        logging.info("_clear_backup finished")

    def _rollback(self, bond_name, new_flag=True):
        logging.info("start _rollback")
        if new_flag:
            # 新增bond回滚需要删除bond的master身份和ifcfg文件
            cmdutils.run_cmd("echo -%s > %s" % (bond_name, constants.BOND_MASTERS))
            try:
                os.remove(self.file_path % bond_name)
                logging.info("remove file: %s", self.file_path % bond_name)
            except Exception as e:
                logging.exception('_rollback error: %s ' % str(e))

        for filename in os.listdir(self.backup_dir):
            # 新增bond时不会备份bond的ifcfg文件，所以还原时自然也不应该存在bond的ifcfg文件，万一存在了，也不要还原它
            # 编辑、删除bond时需要还原bond的ifcfg文件
            if new_flag and filename == bond_name:
                continue
            try:
                shutil.copy2(os.path.join(self.backup_dir, filename), self.file_path % filename)
                cmdutils.run_cmd("ifdown %s" % filename)
                cmdutils.run_cmd("ifup %s" % filename)
            except Exception as e:
                logging.exception('_rollback error: %s ' % str(e))
                continue
        logging.info("_rollback finished")
        self._clear_backup()

    def add_ip_info(self, data):
        """
        {
            "name": "eth0",
            "ip_infos"[
                {
                    "ip": "172.16.1.31",
                    "netmask": "255.255.255.0"
                },
                ...
            ],
            "gate_info": {
                "gateway": "172.16.1.254",
                "dns1": "8.8.8.8",
                "dns2": "114.114.114.114"
            },
            "net_info": {
                "network_id": "",
                "physical_interface": ""
            }
        }
        :return:
        """
        try:
            nic_name = data.get("name")
            virtual_net_device = os.listdir('/sys/devices/virtual/net/')
            nic_addrs = psutil.net_if_addrs()
            physical_net_device = [dev for dev in nic_addrs.keys() if dev not in virtual_net_device]
            if nic_name.split(':')[0] not in physical_net_device:
                logging.error("add nic %s ip, not physical nic", nic_name)
                return get_error_result("NotPhysicalNICError")

            resp = dict()
            resp['data'] = {}
            utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
            resp['data']['utc'] = utc
            nic_ifcfg = "/etc/sysconfig/network-scripts/ifcfg-%s" % nic_name
            nic_content = [
                "NAME=%s" % nic_name,
                "DEVICE=%s" % nic_name,
                "TYPE=Ethernet",
                "ONBOOT=yes",
                # "DEFROUTE=no",
                "NM_CONTROLLED=no",
                "BOOTPROTO=%s" % ("static" if data.get('ip_infos') else "none")
            ]
            # with open(nic_ifcfg, 'r') as fd:
            #     lines = fd.readlines()
            # # IP信息以及需要修改的部分不继承，其余的继承原有配置
            # for line in lines:
            #     if not line.strip():
            #         continue
            #     if line.startswith("IPADDR") or line.startswith("NETMASK") \
            #             or line.startswith("GATEWAY") or line.startswith("DNS"):
            #         continue
            #     key = line.split('=')[0]
            #     if key in ['NAME', 'DEVICE', 'TYPE', 'ONBOOT', 'BOOTPROTO', 'NM_CONTROLLED', 'DEFROUTE']:
            #         continue
            #     nic_content.append(line.strip())
            logging.info("the nic content:%s", nic_content)
            # 更新IP信息
            for index, info in enumerate(data['ip_infos']):
                nic_content.append("IPADDR%s=%s" % (index, info['ip']))
                nic_content.append("NETMASK%s=%s" % (index, info['netmask']))
            if data.get('gate_info'):
                if data['gate_info'].get('gateway'):
                    nic_content.append("GATEWAY=%s" % data['gate_info']['gateway'])
                if data['gate_info'].get('dns1'):
                    nic_content.append("DNS1=%s" % data['gate_info']['dns1'])
                if data['gate_info'].get('dns2'):
                    nic_content.append("DNS2=%s" % data['gate_info']['dns2'])
            self.update_conf(nic_ifcfg, nic_content)
            # 如果是flat网络，则需要将网卡信息配置到网桥上
            net_info = data.get('net_info')
            if net_info and LinuxBridgeManager().check_bridge_exist(net_info['network_id']):
                LinuxBridgeManager().add_addition_ip(net_info['network_id'], data['ip_infos'], data['gate_info'])
            else:
                cmdutils.run_cmd("ifdown %s" % nic_name)
                cmdutils.run_cmd("ifup %s" % nic_name)
            logging.info("set nic %s ip success" % nic_name)
            resp["data"] = {
                "name": nic_name
            }
            return resp
        except Exception as e:
            logging.exception(e)
            raise e
