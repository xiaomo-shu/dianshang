import logging
import json
from .desktop_ctl import BaseController
from yzy_server.database import apis as db_api
from yzy_server.database import models
from common.errcode import get_error_result
from common.utils import create_uuid

logger = logging.getLogger(__name__)


class VoiDesktopController(BaseController):

    def _check_params(self, data):
        if not data:
            return False
        name = data.get('name', '')
        group_uuid = data.get('group_uuid', '')
        template_uuid = data.get('template_uuid', '')
        if not (name and group_uuid and template_uuid):
            return False
        logger.info("check params ok")
        return True

    def create_voi_desktop(self, data):
        """
        创建教学桌面组
        :param data:
            {
                "name": "desktop2",
                "owner_id": "",
                "group_uuid": "d02cd368-5396-11ea-ad80-000c295dd728",
                "template_uuid": "6f1006c0-56d1-11ea-aec0-000c295dd728",
                "sys_restore": 1,
                "data_restore": 1,
                "prefix": "pc",
                "postfix": 3,
                "postfix_start": 5,
                "show_info": true,
                "auto_update": true
            }
        :return:
        """
        if not self._check_params(data):
            return get_error_result("ParamError")
        group = db_api.get_item_with_first(models.YzyVoiGroup, {"uuid": data['group_uuid']})
        if not group:
            logger.error("voi group: %s not exist", data['group_uuid'])
            return get_error_result("GroupNotExists", name="")
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": data['template_uuid']})
        if not template:
            logger.error("voi template: %s not exist", data['template_uuid'])
            return get_error_result("TemplateNotExist")
        has_group = db_api.get_item_with_first(models.YzyVoiDesktop, {})
        # if constants.PERSONAL_DEKSTOP == template.classify:
        #     return get_error_result("TemplatePersonalError", name=template.name)

        # add desktop
        desktop_uuid = create_uuid()
        desktop_value = {
            "uuid": desktop_uuid,
            "owner_id": data['owner_id'],
            "name": data['name'],
            "group_uuid": data['group_uuid'],
            "template_uuid": data['template_uuid'],
            "os_type": template.os_type,
            "sys_restore": data['sys_restore'],
            "data_restore": data['data_restore'],
            "prefix": data['prefix'],
            "use_bottom_ip": data.get('use_bottom_ip', True),
            "ip_detail": json.dumps(data['ip_detail']) if data.get('ip_detail') else '',
            # "postfix": data.get('postfix', 1),
            # "postfix_start": data.get('postfix_start', 1),
            "active": False,
            "default": False if has_group else True,
            "show_info": data.get('show_info', False),
            "auto_update": data.get('auto_update', False)
        }
        try:
            db_api.create_voi_desktop(desktop_value)
            logger.info("create voi desktop %s success", data['name'])
        except Exception as e:
            logging.info("insert voi desktop info to db failed:%s", e)
            return get_error_result("DesktopCreateFail", name=data['name'])
        return get_error_result("Success")

    def active_voi_desktop(self, desktop_uuid):
        desktop = db_api.get_item_with_first(models.YzyVoiDesktop, {'uuid': desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        desktop.active = True
        desktop.soft_update()
        logger.info("active voi desktop %s success", desktop.name)
        return get_error_result("Success")

    def inactive_voi_desktop(self, desktop_uuid):
        desktop = db_api.get_item_with_first(models.YzyVoiDesktop, {'uuid': desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        desktop.active = False
        desktop.soft_update()
        logger.info("inactive voi desktop %s success", desktop.name)
        return get_error_result("Success")

    def set_default_voi_desktop(self, desktop_uuid):
        desktop = db_api.get_item_with_first(models.YzyVoiDesktop, {'uuid': desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        if desktop.default:
            return get_error_result("Success")
        default_one = db_api.get_item_with_first(models.YzyVoiDesktop, {'default': True})
        desktop.default = True
        desktop.soft_update()
        default_one.default = False
        default_one.soft_update()
        logger.info("set default voi desktop %s success", desktop.name)
        return get_error_result("Success")

    def delete_voi_desktop(self, desktop_uuid):
        """
        删除桌面组
        """
        desktop = db_api.get_item_with_first(models.YzyVoiDesktop, {"uuid": desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        try:
            # 清除桌面组与终端的绑定关系
            terminal_desktop_binds = db_api.get_item_with_all(models.YzyVoiTerminalToDesktops,
                                                              {"desktop_group_uuid": desktop_uuid})
            for bind in terminal_desktop_binds:
                # type: 0-upload, 1-download
                bt_task = db_api.get_item_with_first(models.YzyVoiTorrentTask,
                                                     {"terminal_mac": bind.terminal_mac,
                                                      "type": 1})
                # status == 1, task running
                if bt_task and bt_task.status == 1:
                    return get_error_result("TerminalTorrentDownloading")
                bind.soft_delete()
            logger.info("delete voi desktop, clear terminal desktop bind success!!")
            
            desktop.soft_delete()
            logger.info("delete voi desktop, uuid:%s, name:%s", desktop.uuid, desktop.name)
            if desktop.default:
                default_one = db_api.get_item_with_first(models.YzyVoiDesktop, {})
                if default_one:
                    default_one.default = True
                    default_one.soft_update()
                    logger.info("the delete desktop is default, set %s as default", default_one.name)
            return get_error_result("Success")
        except Exception as e:
            logger.error("delete voi desktop failed:%s", e, exc_info=True)
            return get_error_result("DesktopDeleteFail")

    def update_voi_desktop(self, data):
        """
        :param data:
        {
            "uuid": "",
            "value": {
                "name": "",
                ...
            }
        }
        :return:
        """
        desktop_uuid = data.get('uuid', '')
        desktop = db_api.get_item_with_first(models.YzyVoiDesktop, {"uuid": desktop_uuid})
        if not desktop:
            logger.error("desktop %s not exist", desktop_uuid)
            return get_error_result("DesktopNotExist", name="")
        try:
            if data['value'].get('ip_detail'):
                data['value']['ip_detail'] = json.dumps(data['value']['ip_detail'])
            else:
                data['value']['ip_detail'] = ''
            desktop.update(data['value'])
            desktop.soft_update()

            terminal_desktop_binds = db_api.get_item_with_all(models.YzyVoiTerminalToDesktops,
                                                              {"desktop_group_uuid": desktop_uuid})
            for bind in terminal_desktop_binds:
                bind.soft_delete()
            logger.info("update voi desktop, clear terminal desktop bind success!!")
        except Exception as e:
            logger.error("update voi desktop %s failed:%s", desktop_uuid, e, exc_info=True)
            return get_error_result("DesktopUpdateFail", name=desktop.name)
        logger.info("update voi desktop %s success", desktop_uuid)
        return get_error_result("Success")
