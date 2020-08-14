import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from web_manage.common import constants
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.errcode import get_error_result
from web_manage.common.http import server_post
from web_manage.yzy_voi_edu_desktop_mgr import models as voi_education_model

logger = logging.getLogger(__name__)


class VoiDesktopManager(object):

    @operation_record("创建教学桌面组{param[name]}", module="voi_edu_desktop")
    def create_check(self, param, log_user=None):
        logger.info("create voi desktop group")
        group_uuid = param.get('group_uuid')
        if log_user:
            param['owner_id'] = log_user['id']
        else:
            param['owner_id'] = 1
        if not voi_education_model.YzyVoiGroup.objects.filter(uuid=group_uuid, deleted=False):
            logger.info("create voi desktop group error, education group not exists")
            return get_error_result("GroupNotExists", name='')
        # 同一个教学模板，在同一教学分组下只能创建一个教学桌面
        if voi_education_model.YzyVoiDesktop.objects.filter(group=group_uuid,
                                                            template=param['template_uuid'], deleted=False):
            logger.error("the template already created desktop")
            return get_error_result("TemplateAlreadyUsed")
        # 名字冲突检测只在分组范围内
        if voi_education_model.YzyVoiDesktop.objects.filter(name=param['name'], deleted=False):
            logger.error("create voi desktop group error, desktop group already exists")
            return get_error_result("DesktopAlreadyExist", name=param['name'])
        ret = server_post("/api/v1/voi/desktop/education/create", param)
        logger.info("create voi desktop group end:%s", ret)
        return ret

    def delete_desktops(self, desktops):
        if len(desktops) == 1:
            return self.delete_desktop(desktops[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for desktop in desktops:
                future = executor.submit(self.delete_desktop, desktop)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def active_desktops(self, desktops):
        if len(desktops) == 1:
            return self.active_desktop(desktops[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for desktop in desktops:
                future = executor.submit(self.active_desktop, desktop)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def inactive_desktops(self, desktops):
        if len(desktops) == 1:
            return self.inactive_desktop(desktops[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for desktop in desktops:
                future = executor.submit(self.inactive_desktop, desktop)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def delete_desktop(self, desktop):
        logger.info("delete voi desktop group, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
        if not voi_education_model.YzyVoiDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
            logger.info("delete voi desktop group, it is not exists")
            return get_error_result("DesktopNotExist", name=desktop['name'])
        ret = server_post("/api/v1/voi/desktop/education/delete", {"uuid": desktop['uuid']})
        if ret.get('code') != 0:
            logger.info("delete voi desktop group failed:%s", ret['msg'])
            return ret
        else:
            logger.info("delete voi desktop group success, name:%s", desktop['name'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def active_desktop(self, desktop):
        logger.info("active voi desktop group, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
        if not voi_education_model.YzyVoiDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
            logger.info("active voi desktop group failed, it is not exists")
            return get_error_result("DesktopNotExist", name="")
        ret = server_post("/api/v1/voi/desktop/education/active", {"uuid": desktop['uuid']})
        if ret.get('code') != 0:
            logger.info("active voi desktop group failed:%s", ret['msg'])
            return ret
        else:
            logger.info("active voi desktop group success, name:%s", desktop['name'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def inactive_desktop(self, desktop):
        logger.info("inactive voi desktop group, name:%s, uuid:%s", desktop['name'], desktop['uuid'])
        if not voi_education_model.YzyVoiDesktop.objects.filter(uuid=desktop['uuid'], deleted=False):
            logger.info("inactive voi desktop group failed, it is not exists")
            return get_error_result("DesktopNotExist", name="")
        ret = server_post("/api/v1/voi/desktop/education/inactive", {"uuid": desktop['uuid']})
        if ret.get('code') != 0:
            logger.info("inactive voi desktop group failed:%s", ret['msg'])
            return ret
        else:
            logger.info("inactive voi desktop group success, name:%s", desktop['name'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def active_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.active_desktops(desktops)
        msg = "教学桌面组'%s'激活" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="voi_edu_desktop")
        return ret

    def inactive_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.inactive_desktops(desktops)
        msg = "教学桌面组'%s'未激活" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="voi_edu_desktop")
        return ret

    def delete_check(self, param, log_user=None):
        desktops = param.get('desktops', [])
        names = list()
        for desktop in desktops:
            names.append(desktop['name'])
        ret = self.delete_desktops(desktops)
        msg = "删除教学桌面组'%s'" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="voi_edu_desktop")
        return ret

    @operation_record("将教学桌面组{param[name]}设为默认", module="voi_edu_desktop")
    def default_check(self, param, log_user=None):
        logger.info("set the desktop %s as default", param['name'])
        if not voi_education_model.YzyVoiDesktop.objects.filter(uuid=param['uuid'], deleted=False):
            return get_error_result("DesktopNotExist", name=param['name'])
        ret = server_post("/api/v1/voi/desktop/education/default", param)
        logger.info("set voi desktop group as default end:%s", ret)
        return ret

    @operation_record("更新教学桌面组{data[name]}", module="voi_edu_desktop")
    def update_desktop(self, data, log_user=None):
        logger.info("update voi desktop group, name:%s, uuid:%s", data['name'], data['uuid'])
        if not voi_education_model.YzyVoiDesktop.objects.filter(uuid=data['uuid'], deleted=False):
            logger.info("update voi desktop group error, it is not exists")
            return get_error_result("DesktopNotExist", name=data['name'])
        if data['name'] != data['value']['name']:
            if voi_education_model.YzyVoiDesktop.objects.filter(name=data['value']['name'], deleted=False):
                return get_error_result("DesktopAlreadyExist", name=data['value']['name'])
        ret = server_post("/api/v1/voi/desktop/education/update", data)
        if ret.get('code') != 0:
            logger.info("update voi desktop group failed:%s", ret['msg'])
        else:
            logger.info("update voi desktop group success, name:%s", data['name'])
        return ret
