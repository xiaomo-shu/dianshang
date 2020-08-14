import socket
import json
import datetime as dt
import traceback
import os
import configparser
import common.errcode as errcode
from yzy_monitor.timer_tasks.base_task import BaseTask
from yzy_monitor.log import logger
from common.constants import BASE_DIR


class ServiceTask(BaseTask):
    def __init__(self, app, interval=20):
        super(ServiceTask, self).__init__(self)
        self.name = 'service'
        self.interval = interval
        #self.hostname = socket.gethostname()
        #self.ip = socket.gethostbyname(self.hostname)
        self.services = []
        self.get_services()

    def get_services(self):
        try:
            # work_dir = os.getcwd()
            work_dir = os.path.join(BASE_DIR, 'config')
            conf = configparser.ConfigParser()
            conf.read('{}/monitor_services.ini'.format(work_dir))
            for key in conf['SERVICES']:
                if conf['SERVICES'][key] == "true":
                    self.services.append(key)
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))

    def process(self):
        try:
            resource_info = self.get_service_info()
            logger.info(json.dumps(resource_info, sort_keys=True, indent=4, separators=(', ', ': ')))
            if resource_info is None:
                return
            else:
                resp, body = self.request(headers={}, body=resource_info)
                logger.info('resp = {}, body = {}'.format(resp, body))
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))

    def get_service_info(self):
        try:
            resp = {}
            resp['data'] = {}
            utc = int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(0)).total_seconds())
            resp['utc'] = utc
            #resp['hostname'] = self.hostname
            #resp['ip'] = self.ip
            resp['type'] = 'service'
            resp['node_uuid'] = self.node_uuid
            cmd = 'systemctl list-units|grep -E "%s"' % '|'.join(self.services)
            results = os.popen(cmd).readlines()
            if results:
                for ret in results:
                    service_name = ret.split('.')[0].split()[-1].strip()
                    service_status = ret.split('.')[1].split()[3].strip()
                    resp['data'][service_name] = service_status
            for service in [x for x in self.services if x not in resp['data'].keys()]:
                resp['data'][service] = 'not found'
            return resp
        except Exception as err:
            logger.error(err)
            logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="GetServiceInfoFailure")
            return resp

