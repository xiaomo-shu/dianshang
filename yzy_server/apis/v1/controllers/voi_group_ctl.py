import logging
from yzy_server.database.apis import voi as voi_api
from yzy_server.database import apis as db_api
from yzy_server.database import models
from common.utils import create_uuid, voi_terminal_post
from common.errcode import get_error_result
from common import constants


logger = logging.getLogger(__name__)


class VoiGroupController(object):

    def _check_params(self, data):
        if not data:
            return False
        name = data.get('name', '')
        start_ip = data.get('start_ip', '')
        end_ip = data.get('end_ip', '')
        if not (name and start_ip and end_ip):
            return False
        logger.info("check params ok")
        return True

    def create_group(self, data):
        """
        创建分组
        """
        if not self._check_params(data):
            return get_error_result("ParamError")

        group = voi_api.get_item_with_first(models.YzyVoiGroup, {'name': data['name']})
        if group:
            return get_error_result("GroupAlreadyExists", name=data['name'])
        group_uuid = create_uuid()
        group_value = {
            "uuid": group_uuid,
            "group_type": data.get('group_type', 1),
            "name": data['name'],
            "desc": data['desc'],
            "start_ip": data['start_ip'],
            "end_ip": data['end_ip']
        }
        templates = voi_api.get_item_with_all(models.YzyVoiTemplate, {"all_group": True})
        binds = list()
        for template in templates:
            binds.append({
                "uuid": create_uuid(),
                "template_uuid": template.uuid,
                "group_uuid": group_uuid
            })
        try:
            voi_api.create_voi_group(group_value)
            if binds:
                db_api.insert_with_many(models.YzyVoiTemplateGroups, binds)
            logger.info("create voi group %s success", data['name'])
        except Exception as e:
            logging.info("insert voi group info to db failed:%s", e)
            return get_error_result("GroupCreateError", name=data['name'])
        return get_error_result("Success", group_value)

    def delete_group(self, group_uuid):
        group = voi_api.get_item_with_first(models.YzyVoiGroup, {"uuid": group_uuid})
        if not group:
            logger.error("group: %s not exist", group_uuid)
            return get_error_result("GroupNotExists", name='')
        if constants.EDUCATION_DESKTOP == group.group_type:
            desktop = voi_api.get_item_with_first(models.YzyVoiDesktop, {"group_uuid": group_uuid})
            if desktop:
                logger.error("group already in use", group_uuid)
                return get_error_result("GroupInUse", name=group.name)
        binds = voi_api.get_item_with_all(models.YzyVoiTemplateGroups, {"group_uuid": group_uuid})
        for bind in binds:
            bind.soft_delete()
        group.soft_delete()
        logger.info("delete voi group %s success", group_uuid)
        ret = voi_terminal_post("/api/v1/voi/terminal/command", {"handler": "WebTerminalHandler",
                                                         "command": "delete_group",
                                                         "data": {
                                                                    "group_uuid": group_uuid
                                                                  }
                                                        }
                            )
        return ret

    def update_group(self, data):
        group_uuid = data.get('uuid', '')
        group = voi_api.get_item_with_first(models.YzyVoiGroup, {"uuid": group_uuid})
        if not group:
            logger.error("group: %s not exist", group_uuid)
            return get_error_result("GroupNotExists", name='')
        try:
            group.update(data['value'])
            group.soft_update()
        except Exception as e:
            logger.error("update voi group:%s failed:%s", group_uuid, e)
            return get_error_result("GroupUpdateError", name=group.name)
        logger.info("update voi group:%s success", group_uuid)
        return get_error_result("Success")
