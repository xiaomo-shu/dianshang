import logging
from threading import  Thread
from web_manage.common.http import server_post
from web_manage.common.log import operation_record
logger = logging.getLogger(__name__)


class DatabaseBackManager(object):

    @operation_record("删除数据库备份'{param[name]}'", module="database")
    def delete_check(self, param, log_user=None):
        """
        删除数据库备份
        :param param:
            {
                "id": 1,
                "name": ""
            }
        :return:
        """
        logger.info("begin delete database file %s", param["name"])
        ret = server_post("/api/v1/system/database/delete", param)
        logger.info("delete database file %s end", param["name"])
        return ret

    @operation_record("手动备份数据库", module="database")
    def backup_check(self, param, log_user=None):
        logger.info("begin backup database")
        ret = server_post("/api/v1/system/database/backup", {})
        logger.info("backup database end")

        if ret.get("data", {}).get("path", None):
            # 如果启用了HA，把数据库备份文件同步给备控，未启用则不同步
            task = Thread(target=server_post, args=('/controller/ha_sync_web_post', {"paths": [ret["data"]["path"]]},))
            task.start()

        return ret

