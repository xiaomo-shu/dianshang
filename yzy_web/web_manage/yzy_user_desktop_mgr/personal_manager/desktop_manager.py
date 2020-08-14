import logging

from web_manage.yzy_resource_mgr import models as resource_model
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.errcode import get_error_result
from web_manage.common.http import server_post
from web_manage.yzy_user_desktop_mgr import models as personal_model

logger = logging.getLogger(__name__)


class DesktopManager(object):

    @operation_record("创建个人桌面组{param[name]}", module="personal_desktop")
    def create_check(self, param, log_user=None):
        logger.info("create personal desktop group")
        pool_uuid = param.get('pool_uuid')
        if log_user:
            param['owner_id'] = log_user['id']
        else:
            param['owner_id'] = 1
        if not resource_model.YzyResourcePools.objects.filter(uuid=pool_uuid, deleted=False):
            logger.info("create personal desktop group error, resource pool not exists")
            return get_error_result("ResourcePoolNotExist")
        if personal_model.YzyPersonalDesktop.objects.filter(name=param['name'], deleted=False):
            logger.error("create personal desktop group error, desktop group already exists")
            return get_error_result("DesktopAlreadyExist", name=param['name'])
        ret = server_post("/api/v1/desktop/personal/create", param)
        logger.info("create personal desktop group success")
        return ret

    def start_dekstops(self, desktops):
        success_num = 0
        failed_num = 0
        for desktop in desktops:
            logger.info("start personal desktop group, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
            if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
                logger.info("start personal desktop group, it is not exists")
                return get_error_result("DesktopNotExist", name=desktop['name'])
            ret = server_post("/api/v1/desktop/personal/start", {"uuid": desktop['uuid']})
            if ret.get('code') != 0:
                logger.info("start personal desktop group failed:%s", ret['msg'])
                return ret
            else:
                success_num += ret['data']['success_num']
                failed_num += ret['data']['failed_num']
                logger.info("start personal desktop group success, name:%s", desktop['name'])
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def stop_desktops(self, desktops, hard=False):
        success_num = 0
        failed_num = 0
        for desktop in desktops:
            logger.info("stop personal desktop group, name:%s, uuid:%s, hard:%s", desktop['name'], desktop['uuid'], hard)
            if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
                logger.info("stop personal desktop group, it is not exists")
                return get_error_result("DesktopNotExist", name=desktop['name'])
            if hard:
                ret = server_post("/api/v1/desktop/personal/hard_stop", {"uuid": desktop['uuid']})
            else:
                ret = server_post("/api/v1/desktop/personal/stop", {"uuid": desktop['uuid']})
            if ret.get('code') != 0:
                logger.info("stop personal desktop group failed:%s", ret['msg'])
                return ret
            else:
                success_num += ret['data']['success_num']
                failed_num += ret['data']['failed_num']
                logger.info("stop personal desktop group success, name:%s", desktop['name'])
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def delete_desktops(self, desktops):
        success_num = 0
        failed_num = 0
        for desktop in desktops:
            logger.info("delete personal desktop group, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
            if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
                logger.info("delete personal desktop group, it is not exists")
                return get_error_result("DesktopNotExist", name=desktop['name'])
            ret = server_post("/api/v1/desktop/personal/delete", {"uuid": desktop['uuid']})
            if ret.get('code') != 0:
                logger.info("delete personal desktop group failed:%s", ret['msg'])
                return ret
            else:
                success_num += ret['data']['success_num']
                failed_num += ret['data']['failed_num']
                logger.info("delete personal desktop group success, name:%s", desktop['name'])
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def enter_maintenance(self, desktops):
        for desktop in desktops:
            logger.info("personal desktop group enter maintenance, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
            if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
                logger.info("personal desktop group enter maintenance failed, it is not exists")
                return get_error_result("DesktopNotExist", name=desktop['name'])
            ret = server_post("/api/v1/desktop/personal/enter_maintenance", {"uuid": desktop['uuid']})
            if ret.get('code') != 0:
                logger.info("personal desktop group enter maintenance failed:%s", ret['msg'])
                return ret
            else:
                logger.info("personal desktop group enter maintenance success, name:%s", desktop['name'])
        return get_error_result("Success")

    def exit_maintenance(self, desktops):
        for desktop in desktops:
            logger.info("personal desktop group exit maintenance, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
            if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
                logger.info("stop personal desktop group, it is not exists")
                return get_error_result("DesktopNotExist", name=desktop['name'])
            ret = server_post("/api/v1/desktop/personal/exit_maintenance", {"uuid": desktop['uuid']})
            if ret.get('code') != 0:
                logger.info("personal desktop group exit maintenance failed:%s", ret['msg'])
                return ret
            else:
                logger.info("personal desktop group exit maintenance success, name:%s", desktop['name'])
        return get_error_result("Success")

    def reboot_desktops(self, desktops):
        success_num = 0
        failed_num = 0
        for desktop in desktops:
            logger.info("reboot personal desktop group, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
            if not personal_model.YzyPersonalDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
                logger.info("reboot personal desktop group, it is not exists")
                return get_error_result("DesktopNotExist", name=desktop['name'])
            ret = server_post("/api/v1/desktop/personal/reboot", {"uuid": desktop['uuid']})
            if ret.get('code') != 0:
                logger.info("reboot personal desktop group failed:%s", ret['msg'])
                return ret
            else:
                success_num += ret['data']['success_num']
                failed_num += ret['data']['failed_num']
                logger.info("reboot personal desktop group success, name:%s", desktop['name'])
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def start_check(self, param, log_user=None):
        """
        :param param:
            {
                "desktops": [
                        {
                            "name": "desktop1",
                            "uuid": ""
                        },
                        ...
                    ]
            }
        :return:
        """
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.start_dekstops(desktops)
        msg = "个人桌面组'%s'开机" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    def stop_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.stop_desktops(desktops)
        msg = "个人桌面组'%s'关机" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    def hard_stop_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.stop_desktops(desktops, hard=True)
        msg = "个人桌面组'%s'强制关机" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    def reboot_check(self, param, log_user=None):
        """
        桌面很多时，重启时间很长，考虑用多线程
        """
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.reboot_desktops(desktops)
        msg = "个人桌面组'%s'重启" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    def enter_maintenance_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.enter_maintenance(desktops)
        msg = "个人桌面组'%s'开启维护模式" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    def exit_maintenance_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.exit_maintenance(desktops)
        msg = "个人桌面组'%s'关闭维护模式" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    def delete_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.delete_desktops(desktops)
        msg = "删除个人桌面组'%s'" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="personal_desktop")
        return ret

    @operation_record("更新个人桌面组{data[name]}", module="personal_desktop")
    def update_desktop(self, data, log_user=None):
        logger.info("update personal desktop group, name:%s, uuid:%s", data['name'], data['uuid'])
        if not personal_model.YzyPersonalDesktop.objects.filter(uuid=data['uuid'], deleted=False):
            logger.info("update personal desktop group error, it is not exists")
            return get_error_result("DesktopNotExist", name=data['name'])
        ret = server_post("/api/v1/desktop/personal/update", data)
        if ret.get('code') != 0:
            logger.info("update personal desktop group failed:%s", ret['msg'])
        else:
            logger.info("update personal desktop group success, uuid:%s", data['name'])
        return ret
