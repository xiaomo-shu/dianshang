import logging

from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.errcode import get_error_result
from web_manage.common.http import server_post
from web_manage.yzy_user_desktop_mgr import models as personal_model

logger = logging.getLogger(__name__)


class InstanceManager(object):

    @operation_record("个人桌面组{param[desktop_name]}中新增{param[instance_num]}个桌面", module="personal_desktop")
    def create_check(self, param, log_user=None):
        """
        :param param:
            {
                "desktop_uuid": "a7f2ba44-593f-11ea-b458-000c295dd728",
                "desktop_name": "desktop1",
                "desktop_type": 2,
                "instance_num": 5,
                "create_info": {
                    "172.16.1.11": 5
                }
            }
        :return:
        """
        desktop_uuid = param.get('desktop_uuid', '')
        logger.info("create instance in desktop group:%s", desktop_uuid)
        if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
            logger.info("desktop group not exists")
            return get_error_result("DesktopNotExist", name=param['desktop_name'])
        ret = server_post("/api/v1/instance/create", param)
        logger.info("create instance in desktop group success")
        return ret

    def start_instances(self, param):
        success_num = 0
        failed_num = 0
        desktop_uuid = param.get('desktop_uuid')
        logger.info("start instance:%s", param['instances'])
        if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
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
        if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
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

    def hard_stop_instances(self, param):
        success_num = 0
        failed_num = 0
        desktop_uuid = param.get('desktop_uuid')
        logger.info("hard stop instance:%s", param['instances'])
        if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
            logger.info("hard stop instance failed,the desktop group not exists")
            return get_error_result("DesktopNotExist", name=param['desktop_name'])
        ret = server_post("/api/v1/instance/hard_stop", param)
        if ret.get('code') != 0:
            logger.info("hard stop instance failed:%s", ret['msg'])
            return ret
        else:
            success_num += ret['data']['success_num']
            failed_num += ret['data']['failed_num']
            logger.info("hard stop instances success, success_num:%s, failed_num:%s", success_num, failed_num)
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def delete_instances(self, param):
        success_num = 0
        failed_num = 0
        desktop_uuid = param.get('desktop_uuid')
        logger.info("delete instance:%s", param['instances'])
        if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
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
        if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
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
        msg = "个人桌面组'%s'中的桌面'%s'开机" % (param['desktop_name'], '/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    def stop_check(self, param, log_user=None):
        instances = param.get('instances', [])
        names = list()
        for instance in instances:
            names.append(instance['name'])
        ret = self.stop_instances(param)
        msg = "个人桌面组'%s'中的桌面'%s'关机" % (param['desktop_name'], '/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    def hard_stop_check(self, param, log_user=None):
        instances = param.get('instances', [])
        names = list()
        for instance in instances:
            names.append(instance['name'])
        ret = self.hard_stop_instances(param)
        msg = "个人桌面组'%s'中的桌面'%s'强制关机" % (param['desktop_name'], '/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    def delete_check(self, param, log_user=None):
        instances = param.get('instances', [])
        names = list()
        for instance in instances:
            names.append(instance['name'])
        ret = self.delete_instances(param)
        msg = "删除个人桌面组'%s'中的桌面'%s'" % (param['desktop_name'], '/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    def reboot_check(self, param, log_user=None):
        instances = param.get('instances', [])
        names = list()
        for instance in instances:
            names.append(instance['name'])
        ret = self.reboot_instances(param)
        msg = "个人桌面组'%s'中的桌面'%s'重启" % (param['desktop_name'], '/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    def add_groups(self, param):
        success_num = 0
        failed_num = 0
        desktop_uuid = param.get('desktop_uuid')
        logger.info("desktop add groups:%s", param['groups'])
        if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
            logger.info("desktop add groups failed,the desktop group not exists")
            return get_error_result("DesktopNotExist", name=param['desktop_name'])
        ret = server_post("/api/v1/instance/add_group", param)
        if ret.get('code') != 0:
            logger.info("desktop add groups:%s", ret['msg'])
            return ret
        else:
            success_num += ret['data']['success_num']
            failed_num += ret['data']['failed_num']
            logger.info("desktop add groups success")
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def add_group_check(self, param, log_user=None):
        """
        :param param:
            {
                "desktop_uuid": "ea2bbe72-593c-11ea-9631-000c295dd728",
                "desktop_name": "desktop1",
                "groups": [
                        {
                            "group_uuid": "",
                            "group_name": ""
                        }
                    ]
            }
        :return:
        """
        groups = param.get('groups', [])
        names = list()
        for group in groups:
            names.append(group['group_name'])
        ret = self.add_groups(param)
        msg = '个人桌面组"%s"添加绑定用户组"%s"' % (param['desktop_name'], '、'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    def delete_groups(self, param):
        success_num = 0
        failed_num = 0
        desktop_uuid = param.get('desktop_uuid')
        logger.info("desktop delete groups:%s", param['groups'])
        if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
            logger.info("desktop delete groups failed,the desktop group not exists")
            return get_error_result("DesktopNotExist", name=param['desktop_name'])
        ret = server_post("/api/v1/instance/delete_group", param)
        if ret.get('code') != 0:
            logger.info("desktop delete groups:%s", ret['msg'])
            return ret
        else:
            success_num += ret['data']['success_num']
            failed_num += ret['data']['failed_num']
            logger.info("desktop delete groups success")
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def delete_group_check(self, param, log_user=None):
        """
        :param param:
            {
                "desktop_uuid": "ea2bbe72-593c-11ea-9631-000c295dd728",
                "desktop_name": "desktop1",
                "groups": [
                        {
                            "uuid": "",
                            "group_name": ""
                        }
                    ]
            }
        :return:
        """
        groups = param.get('groups', [])
        names = list()
        for group in groups:
            names.append(group['group_name'])
        ret = self.delete_groups(param)
        msg = '个人桌面组"%s"移除绑定用户组"%s"' % (param['desktop_name'], '、'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    @operation_record("桌面{param[instance_name]}修改绑定到用户{param[user_name]}", module="personal_desktop")
    def change_bind_check(self, param, log_user=None):
        """
        :param param:
            {
                "user_uuid": "",
                "user_name": "sss",
                "instance_uuid": "",
                "instance_name": "PC1"
            }
        :return:
        """
        logger.info("instance %s change bind user:%s", param['instance_name'], param['user_name'])
        ret = server_post("/api/v1/instance/change_bind", param)
        if ret.get('code') != 0:
            logger.info("instance change bind failed:%s", ret['msg'])
            return ret
        else:
            logger.info("instance change bind success")
        return ret

    def change_group(self, param):
        desktop_uuid = param.get('desktop_uuid', '')
        logger.info("desktop %s change group:%s", param['desktop_name'], param['group_name'])
        if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop_uuid, deleted=False):
            logger.info("change group failed,the desktop group not exists")
            return get_error_result("DesktopNotExist", name=param['desktop_name'])
        ret = server_post("/api/v1/instance/change_group", param)
        if ret.get('code') != 0:
            logger.info("change group failed:%s", ret['msg'])
            return ret
        else:
            logger.info("change group success")
        return ret

    def change_group_check(self, param, log_user=None):
        """
        :param param:
            {
                "desktop_uuid": "",
                "desktop_name": "",
                "group_uuid": "7380f97e-74d3-11ea-b50b-000c29e84b9c"
                "group_name": "group1"
            }
        :return:
        """
        ret = self.change_group(param)
        msg = '桌面组"%s"更换用户组"%s"' % (param['desktop_name'], param['group_name'])
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret
