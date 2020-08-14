# -*- coding:utf-8 -*-
import logging
import time
import json
import datetime as dt
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from functools import wraps
from common.config import SERVER_CONF
from yzy_server.database import apis as db_api
from yzy_server.database import models
from common.utils import build_result


engine = create_engine(
    SERVER_CONF.addresses.get_by_default('sqlalchemy_database_uri',
                                         'mysql+mysqlconnector://root:123qwe,.@localhost:3306/yzy_kvm_db?'))
logger = logging.getLogger(__name__)


def timefn(fn):
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        logger.info("@timefn:" + fn.__name__ + " took " + str(t2 - t1) + " seconds")
        return result

    return measure_time


class MonitorNodeController(object):
    @timefn
    def get_perf_info(self, node_uuid, statis_hours, step_min):
        try:
            ret_data = {}
            # import pdb;pdb.set_trace()
            freq_min = '%sT' % step_min
            end_datetime = dt.datetime.now()
            start_datetime = end_datetime - dt.timedelta(hours=statis_hours)
            start_datetime = start_datetime.strftime('%Y-%m-%d %H:%M:%S')
            end_datetime = end_datetime.strftime('%Y-%m-%d %H:%M:%S')
            sql = "select node_datetime, monitor_info from yzy_monitor_half_min where \
            node_uuid = \'{}\' and \'{}\' <= node_datetime and node_datetime <= \'{}\'".format(
                node_uuid, start_datetime, end_datetime)
            logger.info("sql: {}".format(sql))
            df = pd.read_sql(sql, engine, index_col=['node_datetime'])

            # cpu
            series_cpu_util = df['monitor_info'].apply(lambda x: float(json.loads(x)['cpu_util']))
            out_cpu_util = series_cpu_util.resample(freq_min).mean()
            ret_data['time'] = [x.strftime('%Y-%m-%d %H:%M:%S') for x in out_cpu_util.index.array]
            out_cpu_util = out_cpu_util.fillna(0).astype(np.float64)
            ret_data["cpu_util"] = list(float('%0.2f' % x) for x in out_cpu_util.values)

            # memory
            ret_data["memory_util"] = {}
            mem_percent = df['monitor_info'].apply(
                lambda x: json.loads(x)['memory_util'].get("percent", 0))
            mem_percent = mem_percent.resample(freq_min).mean()
            mem_percent = mem_percent.fillna(0).astype(np.float64)
            ret_data["memory_util"]['percent'] = list(float('%0.2f' % x) for x in mem_percent.values)
            mem_used = df['monitor_info'].apply(
                lambda x: json.loads(x)['memory_util'].get("used", 0))
            mem_used = mem_used.resample(freq_min).mean()
            ret_data["memory_util"]['used'] = mem_used
            mem_used = mem_used.fillna(0).astype(np.float64)
            ret_data["memory_util"]['used'] = list(int(x) for x in mem_used.values)

            # disk io
            ret_data["disk_io_util"] = {}
            disk_list = df['monitor_info'].apply(lambda x: ','.join(json.loads(x)['disk_io_util'].keys()))
            disk_list = ','.join(disk_list.unique())
            disk_list = set(disk_list.split(','))
            for disk in disk_list:
                disk_io_read = df['monitor_info'].apply(
                    lambda x: json.loads(x)['disk_io_util'].get(disk, {}).get("read_bytes_avg", 0))
                disk_io_read = disk_io_read.resample(freq_min).mean()
                logger.info("disk: {}, disk_io_read: {}".format(disk, disk_io_read[:10]))
                logger.info("disk: {}, disk_io_read: {}".format(disk, disk_io_read[-10:]))
                disk_io_write = df['monitor_info'].apply(
                    lambda x: json.loads(x)['disk_io_util'].get(disk, {}).get("write_bytes_avg", 0))
                disk_io_write = disk_io_write.resample(freq_min).mean()
                logger.info("disk: {}, disk_io_write: {}".format(disk, disk_io_write[:10]))
                logger.info("disk: {}, disk_io_write: {}".format(disk, disk_io_write[-10:]))
                ret_data["disk_io_util"][disk] = {}
                disk_io_read = disk_io_read.fillna(0).astype(np.float64)
                disk_io_write = disk_io_write.fillna(0).astype(np.float64)
                ret_data["disk_io_util"][disk]["read_bytes_avg"] = list(int(x) for x in disk_io_read.values)
                ret_data["disk_io_util"][disk]["write_bytes_avg"] = list(int(x) for x in disk_io_write.values)

            # nic io
            ret_data["nic_util"] = {}
            nic_list = df['monitor_info'].apply(lambda x: ','.join(json.loads(x)['nic_util'].keys()))
            nic_list = ','.join(nic_list.unique())
            nic_list = set(nic_list.split(','))
            for nic in nic_list:
                nic_io_read = df['monitor_info'].apply(
                    lambda x: json.loads(x)['nic_util'].get(nic, {}).get("read_bytes_avg", 0))
                nic_io_read = nic_io_read.resample(freq_min).mean()
                logger.info("nic: {}, nic_io_read: {}".format(nic, nic_io_read[:10]))
                logger.info("nic: {}, nic_io_read: {}".format(nic, nic_io_read[-10:]))
                nic_io_write = df['monitor_info'].apply(
                    lambda x: json.loads(x)['nic_util'].get(nic, {}).get("write_bytes_avg", 0))
                nic_io_write = nic_io_write.resample(freq_min).mean()
                logger.info("nic: {}, nic_io_write: {}".format(nic, nic_io_write[:10]))
                logger.info("nic: {}, nic_io_write: {}".format(nic, nic_io_write[-10:]))
                ret_data["nic_util"][nic] = {}
                nic_io_read = nic_io_read.fillna(0).astype(np.float64)
                nic_io_write = nic_io_write.fillna(0).astype(np.float64)
                ret_data["nic_util"][nic]["read_bytes_avg"] = list(int(x) for x in nic_io_read.values)
                ret_data["nic_util"][nic]["write_bytes_avg"] = list(int(x) for x in nic_io_write.values)
        except Exception as err:
            logger.error("get history monitor info fail!", exc_info=True)
            return build_result("OtherError")

        return ret_data

    @timefn
    def get_history_perf(self, data):
        logger.info("get data: {}".format(data))
        node_uuid = data.get("node_uuid")
        statis_hours = data.get("statis_hours")
        step_minutes = data.get("step_minutes")
        if not (node_uuid and statis_hours and step_minutes):
            return build_result("ParamError")
        node = db_api.get_item_with_all(models.YzyNodes, {"uuid": node_uuid})
        if not node:
            return build_result("ParamError")
        _data = self.get_perf_info(node_uuid, statis_hours, step_minutes)
        _data.update({"node_uuid": node_uuid})
        return build_result("Success", data=_data)
