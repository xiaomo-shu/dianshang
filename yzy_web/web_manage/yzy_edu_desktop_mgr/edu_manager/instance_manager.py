import logging

from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.errcode import get_error_result
from web_manage.common.http import server_post
from web_manage.yzy_edu_desktop_mgr import models as education_model

logger = logging.getLogger(__name__)


class InstanceManager(object):

    @operation_record("教学桌面组{param[desktop_name]}中新增{param[instance_num]}个桌面", module="education_desktop")
    def create_check(self, param, log_user=None):
        """
        :param param:
            {
                "desktop_uuid": "ea2bbe72-593c-11ea-9631-000c295dd728",
                "desktop_name": "desktop1",
                "desktop_type": 1,
                "instance_num": 2,
                "create_info": {
                    "172.16.1.11": 2
                }
            }
        :return:
        """
        desktop_uuid = param.get('desktop_uuid', '')
        logger.info("create instance in desktop group:%s", desktop_uuid)
        if not education_model.YzyDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
            logger.info("desktop group not exists")
            return get_error_result("DesktopNotExist", name=param['desktop_name'])
        ret = server_post("/api/v1/instance/create", param)
        logger.info("create instance in desktop group end:%s", ret)
        return ret

    def start_instances(self, param):
        success_num = 0
        failed_num = 0
        desktop_uuid = param.get('desktop_uuid')
        logger.info("start instance:%s", param['instances'])
        if not education_model.YzyDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
            logger.info("start instance failed,the desktop group not exists")
            return get_error_result("DesktopNotExist", name=param['desktop_name'])
        ret = server_post("/api/v1/instance/start", param)
        if ret.get('code') != 0:
            logger.info("start instance failed:%s", ret['msg'])
            return ret
        else:
            success_num += ret['data']['success_num']
            failed_num += ret['data']['failed_num']
            logger.info("start instances success, success_num:%s, failed_num:%s", success_num, failed_num)
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def stop_instances(self, param):
        success_num = 0
        failed_num = 0
        desktop_uuid = param.get('desktop_uuid')
        logger.info("stop instance:%s", param['instances'])
        if not education_model.YzyDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
            logger.info("stop instance failed,the desktop group not exists")
            return get_error_result("DesktopNotExist", name=param['desktop_name'])
        ret = server_post("/api/v1/instance/stop", param)
        if ret.get('code') != 0:
            logger.info("stop instance failed:%s", ret['msg'])
            return ret
        else:
            success_num += ret['data']['success_num']
            failed_num += ret['data']['failed_num']
            logger.info("stop instances success, success_num:%s, failed_num:%s", success_num, failed_num)
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def delete_instances(self, param):
        success_num = 0
        failed_num = 0
        desktop_uuid = param.get('desktop_uuid')
        logger.info("delete instance:%s", param['instances'])
        if not education_model.YzyDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
            logger.info("delete instance failed,the desktop group not exists")
            return get_error_result("DesktopNotExist", name=param['desktop_name'])
        ret = server_post("/api/v1/instance/delete", param)
        if ret.get('code') != 0:
            logger.info("delete instance failed:%s", ret['msg'])
            return ret
        else:
            success_num += ret['data']['success_num']
            failed_num += ret['data']['failed_num']
            logger.info("delete instances success, success_num:%s, failed_num:%s", success_num, failed_num)
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def reboot_instances(self, param):
        success_num = 0
        failed_num = 0
        desktop_uuid = param.get('desktop_uuid')
        logger.info("reboot instance:%s", param['instances'])
        if not education_model.YzyDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
            logger.info("reboot instance failed,the desktop group not exists")
            return get_error_result("DesktopNotExist", name=param['desktop_name'])
        ret = server_post("/api/v1/instance/reboot", param)
        if ret.get('code') != 0:
            logger.info("reboot instance failed:%s", ret['msg'])
            return ret
        else:
            success_num += ret['data']['success_num']
            failed_num += ret['data']['failed_num']
            logger.info("reboot instances success, success_num:%s, failed_num:%s", success_num, failed_num)
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def start_check(self, param, log_user=None):
        """
        :param param:
            {
                "desktop_uuid": "ea2bbe72-593c-11ea-9631-000c295dd728",
                "desktop_name": "desktop1",
                "desktop_type": 1,
                "instances": [
                        {
                            "uuid": "",
                            "name": ""
                        }
                    ]
            }
        :return:
        """
        instances = param.get('instances', [])
        names = list()
        for instance in instances:
            names.append(instance['name'])
        ret = self.start_instances(param)
        msg = "教学桌面组'%s'中的桌面'%s'开机" % (param['desktop_name'], '/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="education_desktop")
        return ret

    def stop_check(self, param, log_user=None):
        instances = param.get('instances', [])
        names = list()
        for instance in instances:
            names.append(instance['name'])
        ret = self.stop_instances(param)
        msg = "教学桌面组'%s'中的桌面'%s'关机" % (param['desktop_name'], '/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="education_desktop")
        return ret

    def delete_check(self, param, log_user=None):
        instances = param.get('instances', [])
        names = list()
        for instance in instances:
            names.append(instance['name'])
        ret = self.delete_instances(param)
        msg = "删除教学桌面组'%s'中的桌面'%s'" % (param['desktop_name'], '/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="education_desktop")
        return ret

    def reboot_check(self, param, log_user=None):
        instances = param.get('instances', [])
        names = list()
        for instance in instances:
            names.append(instance['name'])
        ret = self.reboot_instances(param)
        msg = "教学桌面组'%s'中的桌面'%s'重启" % (param['desktop_name'], '/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="education_desktop")
        return ret

    def get_console_check(self, param, log_user=None):
        """
        :param param:
            {
                "uuid": "",
                "name": ""
            }
        :return:
        """
        ret = server_post("/api/v1/instance/console", param)
        logger.info("get instance %s console end, ret:%s", param['uuid'], ret)
        return ret
