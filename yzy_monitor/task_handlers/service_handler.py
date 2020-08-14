import os
import traceback
from flask import current_app
import common.errcode as errcode
from yzy_monitor.task_handlers.base_handler import BaseHandler, BaseProcess


class ServiceHandler(BaseHandler):
    def __init__(self):
        super(ServiceHandler, self).__init__()
        self.type = "ServiceHandler"

    def deal(self, task):
        p = ServiceHandlerProcess(task)
        r = p.process()
        return r


class ServiceHandlerProcess(BaseProcess):
    def __init__(self, task):
        super(ServiceHandlerProcess, self).__init__(task)
        self.name = os.path.basename(__file__).split('.')[0]

    def start(self):
        try:
            resp = errcode.get_error_result()
            service_name = self.task.get('data').get('service')
            service_list = []
            if type(service_name) is str:
                service_list.append(service_name)
            elif type(service_name) is list:
                service_list = service_name
            else:
                current_app.logger.error('request data type error')
                return errcode.get_error_result("MessageError")
            for service in service_list: 
                current_app.logger.debug('start {}'.format(service))
                if service:
                    os.popen('systemctl start {}'.format(service))
            return resp
        except Exception as err:
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    def stop(self):
        try:
            resp = errcode.get_error_result()
            service_name = self.task.get('data').get('service')
            service_list = []
            if type(service_name) is str:
                service_list.append(service_name)
            elif type(service_name) is list:
                service_list = service_name
            else:
                current_app.logger.error('request data type error')
                return errcode.get_error_result("MessageError")
            for service in service_list: 
                current_app.logger.debug('stop {}'.format(service))
                if service:
                    os.popen('systemctl stop {}'.format(service))
            return resp
        except Exception as err:
            current_app.logger.error(err)
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    def restart(self):
        try:
            resp = errcode.get_error_result()
            service_name = self.task.get('data').get('service')
            service_list = []
            if isinstance(service_name, str):
                service_list.append(service_name)
            elif isinstance(service_name, list):
                service_list = service_name
            else:
                current_app.logger.error('request data type error')
                return errcode.get_error_result("MessageError")
            for service in service_list: 
                current_app.logger.info('restart {}'.format(service))
                os.popen('systemctl restart {}'.format(service))
            return resp
        except Exception as err:
            current_app.logger.error(err)
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    def status(self):
        try:
            resp = errcode.get_error_result()
            service_name = self.task.get('data').get('service')
            current_app.logger.debug('start {}'.format(service_name))
            status = "not found"
            if service_name:
                cmd = 'systemctl status %s|grep "Active"|awk -F\')\' \'{print $1}\'|awk -F\'(\' \'{print $2}\'' \
                      % service_name
                status = os.popen(cmd).readline().strip('\n')
            resp['data'] = {}
            if not status:
                status = "not found"
            resp['data']['status'] = status
            return resp
        except Exception as err:
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    def enable(self):
        try:
            resp = errcode.get_error_result()
            service_name = self.task.get('data').get('service')
            service_list = []
            if type(service_name) is str:
                service_list.append(service_name)
            elif type(service_name) is list:
                service_list = service_name
            else:
                current_app.logger.error('request data type error')
                return errcode.get_error_result("MessageError")
            for service in service_list: 
                current_app.logger.debug('enable {}'.format(service))
                if service:
                    os.popen('systemctl enable --now {}'.format(service))
                    os.popen('systemctl start {}'.format(service))
            return resp
        except Exception as err:
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp

    def disable(self):
        try:
            resp = errcode.get_error_result()
            service_name = self.task.get('data').get('service')
            service_list = []
            if type(service_name) is str:
                service_list.append(service_name)
            elif type(service_name) is list:
                service_list = service_name
            else:
                current_app.logger.error('request data type error')
                return errcode.get_error_result("MessageError")
            for service in service_list: 
                current_app.logger.debug('disable {}'.format(service))
                if service:
                    os.popen('systemctl disable --now {}'.format(service))
                    os.popen('systemctl stop {}'.format(service))
            return resp
        except Exception as err:
            current_app.logger.error(''.join(traceback.format_exc()))
            resp = errcode.get_error_result(error="OtherError")
            return resp
