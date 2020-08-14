import os
import json
import redis
import socket
import datetime as dt
import traceback
import psutil
import common.errcode as errcode
from yzy_monitor.http_client import *
#from yzy_monitor.redis_client import RedisClient
from yzy_monitor.timer_tasks.base_task import BaseTask
from yzy_monitor.log import logger


class ResourceTask(BaseTask):
    def __init__(self, app, interval=20):
        super(ResourceTask, self).__init__(self)
        self.name = 'resource'
        self.interval = interval
        #self.hostname = socket.gethostname()
        #self.ip = socket.gethostbyname(self.hostname)
        #self.rds = RedisClient()
        self.now_date = '19700101'

    def process(self):
        try:
            self.now_date = dt.datetime.now().strftime('%Y%m%d')
            resource_info = self.get_perf_info()
            logger.info(json.dumps(resource_info, sort_keys=True, indent=4, separators=(', ', ': ')))
            if resource_info is None:
                return
            else:
                resp, body = self.request(headers={}, body=resource_info)
                logger.info('resp = {}, body = {}'.format(resp, body))
        except Exception as err:
            logger.error(err)

    def get_perf_info(self):
        try:
            merge_resp = {}
            merge_resp['type'] = 'resource'
            merge_resp['node_uuid'] = self.node_uuid
            #merge_resp['ip'] = self.ip
            #merge_resp['hostname'] = self.hostname
            utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
            merge_resp['utc'] = utc
            call_func_list = [self.get_cpu_info, self.get_memory_info, self.get_disk_info,
                              self.get_diskio_info, self.get_networkio_info]
            merge_resp['data'] = {}
            for func in call_func_list:
                resp = func()
                if resp['code'] != 0:
                    return resp
                else:
                    #for key in ['ip', 'hostname', 'utc', 'code', 'msg']:
                    for key in ['utc', 'code', 'msg']:
                        if key in resp.keys():
                            resp.pop(key)
                add_key_name = func.__name__.split('_')[1]
                merge_resp['data'][add_key_name] = resp
            return merge_resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return None

    def get_cpu_info(self):
        try:
            resp = errcode.get_error_result()
            utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
            resp['utc'] = utc
            cpu_numbers = psutil.cpu_count()
            resp['numbers'] = cpu_numbers
            cpu_utilization = psutil.cpu_percent()
            resp['utilization'] = cpu_utilization
            # insert redis
            """
            if self.rds.ping_server():
                node_key = '{}:cpu_info:{}'.format(self.ip, self.now_date)
                insert_data = resp.copy()
                insert_data.pop('code')
                insert_data.pop('msg')
                if self.rds.exists(node_key):
                    self.rds.zadd(node_key, {json.dumps(insert_data): utc})
                else:
                    self.rds.zadd(node_key, {json.dumps(insert_data): utc})
                    self.rds.expire(node_key, self.rds.live_seconds)  # 86400 seconds of a day
            """
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="GetCpuInfoFailure")
            return resp

    def get_memory_info(self):
        try:
            resp = errcode.get_error_result()
            utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
            resp['utc'] = utc
            mem_info = psutil.virtual_memory()
            resp['total'] = mem_info.total
            resp['available'] = mem_info.available
            resp['utilization'] = mem_info.percent
            # insert redis
            """
            if self.rds.ping_server():
                node_key = '{}:memory_info:{}'.format(self.ip, self.now_date)
                insert_data = resp.copy()
                insert_data.pop('code')
                insert_data.pop('msg')
                if self.rds.exists(node_key):
                    self.rds.zadd(node_key, {json.dumps(insert_data): utc})
                else:
                    self.rds.zadd(node_key, {json.dumps(insert_data): utc})
                    self.rds.expire(node_key, self.rds.live_seconds)  # 86400 seconds of a day
            """
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="GetMemoryInfoFailure")
            return resp

    def checkSsd(self, device):
        device_name = device.split('/')[-1]
        rota = os.popen('lsblk -o name,rota|grep {}'.format(device_name)).readline().split()[-1]
        return int(rota)

    def get_disk_info(self):
        try:
            resp = errcode.get_error_result()
            utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
            resp['utc'] = utc
            disk_parts = psutil.disk_partitions()
            for disk in disk_parts:
                disk_mountpoint = disk.mountpoint
                disk_usage = psutil.disk_usage(disk_mountpoint)
                resp[disk_mountpoint] = {'type': self.checkSsd(disk.device), 'total': disk_usage.total,
                                         'used': disk_usage.used, 'free': disk_usage.free,
                                         'utilization': disk_usage.percent}
            # insert redis
            """
            if self.rds.ping_server():
                node_key = '{}:disk_info:{}'.format(self.ip, self.now_date)
                insert_data = resp.copy()
                insert_data.pop('code')
                insert_data.pop('msg')
                if self.rds.exists(node_key):
                    self.rds.zadd(node_key, {json.dumps(insert_data): utc})
                else:
                    self.rds.zadd(node_key, {json.dumps(insert_data): utc})
                    self.rds.expire(node_key, self.rds.live_seconds)  # 86400 seconds of a day
            """
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="GetDiskInfoFailure")
            return resp

    def get_diskio_info(self):
        try:
            resp = errcode.get_error_result()
            utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
            resp['utc'] = utc
            diskio_parts = psutil.disk_io_counters(perdisk=True)
            virtual_block_device = os.listdir('/sys/devices/virtual/block/')
            physical_block_device = [dev for dev in diskio_parts if dev not in virtual_block_device]
            for diskio in physical_block_device:
                resp[diskio] = {'read_bytes': diskio_parts[diskio].read_bytes,
                                'write_bytes': diskio_parts[diskio].write_bytes}
            # insert redis
            """
            if self.rds.ping_server():
                node_key = '{}:diskio_info:{}'.format(self.ip, self.now_date)
                insert_data = resp.copy()
                insert_data.pop('code')
                insert_data.pop('msg')
                if self.rds.exists(node_key):
                    self.rds.zadd(node_key, {json.dumps(insert_data): utc})
                else:
                    self.rds.zadd(node_key, {json.dumps(insert_data): utc})
                    self.rds.expire(node_key, self.rds.live_seconds)  # 86400 seconds of a day
            """
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="GetDiskIoInfoFailure")
            return resp

    def get_networkio_info(self):
        try:
            resp = errcode.get_error_result()
            utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
            resp['utc'] = utc
            nics_io = psutil.net_io_counters(pernic=True)
            virtual_net_device = os.listdir('/sys/devices/virtual/net/')
            physical_net_device = [dev for dev in nics_io if dev not in virtual_net_device]
            for nic in physical_net_device:
                resp[nic] = {'bytes_send': nics_io[nic].bytes_sent, 'bytes_recv': nics_io[nic].bytes_recv}
            # insert redis
            """
            if self.rds.ping_server():
                node_key = '{}:networkio_info:{}'.format(self.ip, self.now_date)
                insert_data = resp.copy()
                insert_data.pop('code')
                insert_data.pop('msg')
                if self.rds.exists(node_key):
                    self.rds.zadd(node_key, {json.dumps(insert_data): utc})
                else:
                    self.rds.zadd(node_key, {json.dumps(insert_data): utc})
                    self.rds.expire(node_key, self.rds.live_seconds)  # 86400 seconds of a day
            """
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="GetNetworkIoInfoFailure")
            return resp
