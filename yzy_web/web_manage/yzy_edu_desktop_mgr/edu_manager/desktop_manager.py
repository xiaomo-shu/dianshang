import logging

from web_manage.yzy_resource_mgr import models as resource_model
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.errcode import get_error_result
from web_manage.common.http import server_post
from web_manage.yzy_edu_desktop_mgr import models as education_model

logger = logging.getLogger(__name__)


class DesktopManager(object):

    @operation_record("创建教学桌面组{param[name]}", module="education_desktop")
    def create_check(self, param, log_user=None):
        logger.info("create desktop group")
        pool_uuid = param.get('pool_uuid')
        group_uuid = param.get('group_uuid')
        if log_user:
            param['owner_id'] = log_user['id']
        else:
            param['owner_id'] = 1
        if not resource_model.YzyResourcePools.objects.filter(uuid=pool_uuid, deleted=False):
            logger.info("create desktop group error, resource pool not exists")
            return get_error_result("ResourcePoolNotExist")
        if not education_model.YzyGroup.objects.filter(uuid=group_uuid, deleted=False):
            logger.info("create desktop group error, education group not exists")
            return get_error_result("GroupNotExists", name='')
        # 名字冲突检测只在分组范围内
        if education_model.YzyDesktop.objects.filter(name=param['name'], group=group_uuid, deleted=False):
            logger.error("create desktop group error, desktop group already exists")
            return get_error_result("DesktopAlreadyExist", name=param['name'])
        ret = server_post("/api/v1/desktop/education/create", param)
        logger.info("create desktop group end:%s", ret)
        return ret

    def start_dekstops(self, desktops):
        success_num = 0
        failed_num = 0
        for desktop in desktops:
            logger.info("start desktop group, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
            if not education_model.YzyDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
                logger.info("start desktop group, it is not exists")
                return get_error_result("DesktopNotExist", name=desktop['name'])
            ret = server_post("/api/v1/desktop/education/start", {"uuid": desktop['uuid']})
            if ret.get('code') != 0:
                logger.info("start desktop group failed:%s", ret['msg'])
                return ret
            else:
                success_num += ret['data']['success_num']
                failed_num += ret['data']['failed_num']
                logger.info("start desktop group success, name:%s", desktop['name'])
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def stop_desktops(self, desktops, hard=False):
        success_num = 0
        failed_num = 0
        for desktop in desktops:
            logger.info("stop desktop group, name:%s, uuid:%s, hard:%s", desktop['name'], desktop['uuid'], hard)
            if not education_model.YzyDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
                logger.info("stop desktop group, it is not exists")
                return get_error_result("DesktopNotExist", name=desktop['name'])
            if hard:
                ret = server_post("/api/v1/desktop/education/hard_stop", {"uuid": desktop['uuid']})
            else:
                ret = server_post("/api/v1/desktop/education/stop", {"uuid": desktop['uuid']})
            if ret.get('code') != 0:
                logger.info("stop desktop group failed:%s", ret['msg'])
                return ret
            else:
                success_num += ret['data']['success_num']
                failed_num += ret['data']['failed_num']
                logger.info("stop desktop group success, name:%s", desktop['name'])
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def delete_desktops(self, desktops):
        success_num = 0
        failed_num = 0
        for desktop in desktops:
            logger.info("delete desktop group, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
            if not education_model.YzyDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
                logger.info("delete desktop group, it is not exists")
                return get_error_result("DesktopNotExist", name=desktop['name'])
            ret = server_post("/api/v1/desktop/education/delete", {"uuid": desktop['uuid']})
            if ret.get('code') != 0:
                logger.info("delete desktop group failed:%s", ret['msg'])
                return ret
            else:
                success_num += ret['data']['success_num']
                failed_num += ret['data']['failed_num']
                logger.info("delete desktop group success, name:%s", desktop['name'])
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def reboot_desktops(self, desktops):
        success_num = 0
        failed_num = 0
        for desktop in desktops:
            logger.info("reboot desktop group, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
            if not education_model.YzyDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
                logger.info("reboot desktop group, it is not exists")
                return get_error_result("DesktopNotExist", name=desktop['name'])
            ret = server_post("/api/v1/desktop/education/reboot", {"uuid": desktop['uuid']})
            if ret.get('code') != 0:
                logger.info("reboot desktop group failed:%s", ret['msg'])
                return ret
            else:
                success_num += ret['data']['success_num']
                failed_num += ret['data']['failed_num']
                logger.info("reboot desktop group success, name:%s", desktop['name'])
        return get_error_result("Success", data={"failed_num": failed_num, "success_num": success_num})

    def active_desktops(self, desktops):
        for desktop in desktops:
            logger.info("active desktop group, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
            if not education_model.YzyDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
                logger.info("active desktop group failed, it is not exists")
                return get_error_result("DesktopNotExist", name="")
            ret = server_post("/api/v1/desktop/education/active", {"uuid": desktop['uuid']})
            if ret.get('code') != 0:
                logger.info("active desktop group failed:%s", ret['msg'])
                return ret
            else:
                logger.info("active desktop group success, name:%s", desktop['name'])
        return get_error_result("Success")

    def inactive_desktops(self, desktops):
        for desktop in desktops:
            logger.info("inactive desktop group, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
            if not education_model.YzyDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
                logger.info("inactive desktop group failed, it is not exists")
                return get_error_result("DesktopNotExist", name="")
            ret = server_post("/api/v1/desktop/education/inactive", {"uuid": desktop['uuid']})
            if ret.get('code') != 0:
                logger.info("inactive desktop group failed:%s", ret['msg'])
                return ret
            else:
                logger.info("inactive desktop group success, name:%s", desktop['name'])
        return get_error_result("Success")

    def active_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.active_desktops(desktops)
        msg = "教学桌面组'%s'激活" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="education_desktop")
        return ret

    def inactive_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.inactive_desktops(desktops)
        msg = "教学桌面组'%s'未激活" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="education_desktop")
        return ret

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
        msg = "教学桌面组'%s'开机" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="education_desktop")
        return ret

    def stop_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.stop_desktops(desktops)
        msg = "教学桌面组'%s'关机" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="education_desktop")
        return ret

    def hard_stop_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.stop_desktops(desktops, hard=True)
        msg = "教学桌面组'%s'强制关机" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="education_desktop")
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
        msg = "教学桌面组'%s'重启" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="education_desktop")
        return ret

    def delete_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.delete_desktops(desktops)
        msg = "删除教学桌面组'%s'" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="education_desktop")
        return ret

    @operation_record("更新教学桌面组{data[name]}", module="education_desktop")
    def update_desktop(self, data, log_user=None):
        logger.info("update desktop group, name:%s, uuid:%s", data['name'], data['uuid'])
        if not education_model.YzyDesktop.objects.filter(uuid=data['uuid'], deleted=False):
            logger.info("update desktop group error, it is not exists")
            return get_error_result("DesktopNotExist", name=data['name'])
        if data['name'] != data['value']['name']:
            if education_model.YzyDesktop.objects.filter(name=data['value']['name'], deleted=False):
                return get_error_result("NameExistsError", name=data['value']['name'])
        ret = server_post("/api/v1/desktop/education/update", data)
        if ret.get('code') != 0:
            logger.info("update desktop group failed:%s", ret['msg'])
        else:
            logger.info("update desktop group success, name:%s", data['name'])
        return ret
