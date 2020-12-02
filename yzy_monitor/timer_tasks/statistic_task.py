import os
import socket
import datetime as dt
import traceback
import psutil
from flask import current_app
from yzy_monitor.timer_tasks.base_task import BaseTask
from yzy_monitor.log import logger
from common import constants


class StatisticTask(BaseTask):
    def __init__(self, app, interval=1):
        super(StatisticTask, self).__init__(self)
        self.app = app
        self.name = 'statistic'
        self.interval = interval
        self.record_cnt = 60
        self.disk_list = self.get_disk_list()
        self.bond_master_file = constants.BOND_MASTERS
        self.bond_slave_file = constants.BOND_SLAVES

    def get_disk_io_ticks(self, dev_name):
        """
        read file: /proc/diskstats, every line have 14 elements, get "use" digital
            major minor name rio rmerge rsect ruse wio wmerge wsect wuse running use aveq
        return: {"sad": 11123, "sdb": 2222}
        """
        disk_io_use_ticks = 0
        try:
            with open('/proc/diskstats', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    dev_name = line.split()[2]
                    use_ticks = line.split()[-2]
                    if dev_name == dev_name:
                        disk_io_use_ticks = int(use_ticks)
                        break
        except Exception as err:
            logger.error("exception: %s", err, exc_info=True)
        return disk_io_use_ticks

    def compute_io_util(self, interval, current_io_ticks, previous_io_ticks):
        """
        input:
            interval: seconds
            previous_io_ticks: Ticks in milliseconds
        """
        io_util = '%0.2f' % ((int(current_io_ticks) - int(previous_io_ticks)) / (int(interval) * 1000) * 100)
        return io_util

    def get_bonds_dict(self):
        ret_data = {'bond_masters': [], 'bond_slaves': []}
        if os.path.exists(self.bond_master_file):
            with open(self.bond_master_file) as f:
                master_content = f.read()
                if master_content:
                    bonds = master_content[:-1].split(' ')
                    ret_data['bond_masters'] = bonds
                    for bond in bonds:
                        bond_slave_file = self.bond_slave_file % bond
                        if os.path.exists(bond_slave_file):
                            with open(bond_slave_file) as f:
                                slave_content = f.read()
                                if slave_content:
                                    ret_data['bond_slaves'].extend(slave_content[:-1].split(' '))
                                else:
                                    logger.error('{} bond slave file is null!!!'.format(bond_slave_file))
                                    return None
                        else:
                            logger.error('{} bond slave file not exists!!!'.format(bond_slave_file))
                            return None
                    return ret_data
                else:
                    logger.warning('{} bond slave file is null!!!'.format(self.bond_master_file))
                    return None
        else:
            return None

    def get_disk_list(self):
        cmd_ret = os.popen('lsblk -d --output NAME,TYPE|awk \'$2 == "disk"{print $1}\'').readlines()
        disk_list = [x[:-1] for x in cmd_ret]
        return disk_list

    def process(self):
        try:
            utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
            with self.app.app_context():
                current_app.statistic['utc'] = utc
            call_func_list = [self.get_cpu_util, self.get_memory_util, self.get_disk_util, self.get_nic_util,
                              self.get_diskio_util]
            for func in call_func_list:
                func()
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))

    def get_cpu_util(self):
        try:
            cpu_utilization = psutil.cpu_percent()
            with self.app.app_context():
                if cpu_utilization:
                    if len(current_app.statistic['cpu_util']) == self.record_cnt:
                        current_app.statistic['cpu_util'].pop(0)
                    current_app.statistic['cpu_util'].append(cpu_utilization)
                logger.debug(current_app.statistic['cpu_util'])
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))

    def get_memory_util(self):
        try:
            mem_info = psutil.virtual_memory()
            with self.app.app_context():
                if mem_info.percent:
                    if not current_app.statistic['memory_util'].keys():
                        current_app.statistic['memory_util']['used'] = []
                        current_app.statistic['memory_util']['percent'] = []
                    if len(current_app.statistic['memory_util']['percent']) == self.record_cnt:
                        current_app.statistic['memory_util']['percent'].pop(0)
                        current_app.statistic['memory_util']['used'].pop(0)
                    current_app.statistic['memory_util']['percent'].append(mem_info.percent)
                    current_app.statistic['memory_util']['used'].append(mem_info.used)
                logger.debug(current_app.statistic['memory_util'])
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))

    def get_disk_util(self):
        try:
            disk_parts = psutil.disk_partitions()
            with self.app.app_context():
                for disk in disk_parts:
                    disk_mountpoint = disk.mountpoint
                    disk_usage = psutil.disk_usage(disk_mountpoint)
                    if disk_mountpoint not in current_app.statistic['disk_util'].keys():
                        current_app.statistic['disk_util'][disk_mountpoint] = {}
                    current_app.statistic['disk_util'][disk_mountpoint]['rate'] = "%0.2f" % disk_usage.percent
                    current_app.statistic['disk_util'][disk_mountpoint]['used'] = disk_usage.used
                    current_app.statistic['disk_util'][disk_mountpoint]['total'] = disk_usage.total
                logger.debug(current_app.statistic['disk_util'])
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))

    def get_nic_util(self):
        try:
            nics_io = psutil.net_io_counters(pernic=True)
            virtual_net_device = os.listdir('/sys/devices/virtual/net/')
            physical_net_device = [dev for dev in nics_io if dev not in virtual_net_device and not dev.startswith("tap")]
            monitor_net_devices = physical_net_device
            # add bond, drop bond's slave physical nic
            bond_info = self.get_bonds_dict()
            if bond_info:
                bond_masters = bond_info.get("bond_masters", [])
                bond_slaves = bond_info.get("bond_slaves", [])
                monitor_net_devices.extend(bond_masters)
                monitor_net_devices = [dev for dev in monitor_net_devices if dev not in bond_slaves]

            with self.app.app_context():
                for nic in monitor_net_devices:
                    bytes_send = nics_io[nic].bytes_sent
                    bytes_recv = nics_io[nic].bytes_recv
                    if nic not in current_app.statistic['nic_util'].keys():
                        current_app.statistic['nic_util'][nic] = {}
                        current_app.statistic['nic_util'][nic]['ip'] = ""
                        if (nic in psutil.net_if_addrs()) and (psutil.net_if_addrs()[nic][0].family == socket.AF_INET):
                            current_app.statistic['nic_util'][nic]['ip'] = psutil.net_if_addrs()[nic][0].address
                        current_app.statistic['nic_util'][nic]['read_bytes'] = []
                        current_app.statistic['nic_util'][nic]['write_bytes'] = []

                    if len(current_app.statistic['nic_util'][nic]['write_bytes']) == self.record_cnt:
                        current_app.statistic['nic_util'][nic]['write_bytes'].pop(0)
                    current_app.statistic['nic_util'][nic]['write_bytes'].append(bytes_send)

                    if len(current_app.statistic['nic_util'][nic]['read_bytes']) == self.record_cnt:
                        current_app.statistic['nic_util'][nic]['read_bytes'].pop(0)
                    current_app.statistic['nic_util'][nic]['read_bytes'].append(bytes_recv)
                logger.debug(current_app.statistic['nic_util'])
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))

    def get_diskio_util(self):
        try:
            with self.app.app_context():
                disks_io = psutil.disk_io_counters(perdisk=True)
                for disk_name in self.get_disk_list():
                    # disk_io = disks_io[disk_name]
                    write_bytes = disks_io[disk_name].write_bytes
                    read_bytes = disks_io[disk_name].read_bytes
                    io_use_ticks = self.get_disk_io_ticks(disk_name)
                    if disk_name not in current_app.statistic['disk_io_util'].keys():
                        current_app.statistic['disk_io_util'][disk_name] = {}
                        current_app.statistic['disk_io_util'][disk_name]['read_bytes'] = []
                        current_app.statistic['disk_io_util'][disk_name]['write_bytes'] = []
                        current_app.statistic['disk_io_util'][disk_name]['io_use_ticks'] = []

                    if len(current_app.statistic['disk_io_util'][disk_name]['write_bytes']) == self.record_cnt:
                        current_app.statistic['disk_io_util'][disk_name]['write_bytes'].pop(0)
                        current_app.statistic['disk_io_util'][disk_name]['read_bytes'].pop(0)
                        current_app.statistic['disk_io_util'][disk_name]['io_use_ticks'].pop(0)
                    current_app.statistic['disk_io_util'][disk_name]['write_bytes'].append(write_bytes)
                    current_app.statistic['disk_io_util'][disk_name]['read_bytes'].append(read_bytes)
                    current_app.statistic['disk_io_util'][disk_name]['io_use_ticks'].append(io_use_ticks)
                logger.debug(current_app.statistic['disk_io_util'])
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
