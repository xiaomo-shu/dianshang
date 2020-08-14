import logging
from web_manage.common.http import server_post
from web_manage.common.errcode import get_error_result
from web_manage.common.log import operation_record

logger = logging.getLogger(__name__)


class LogSetupManager(object):

    @operation_record("启用告警设置'{data[option][host_uuid]}'", module="log_manager")
    def create_warn_setup(self, data, log_user=None):
        logger.info("create warn log setup record")
        if not data.get('status') or data['status'] == 0:
            return get_error_result("ParameterError")
        ret = server_post("/api/v1/system/warn/setup/create", data)
        logger.info("create warn log setup record success")
        return ret

    @operation_record("更新告警设置'{data[option][host_uuid]}'", module="log_manager")
    def update_warn_setup(self, data, log_user=None):
        logger.info("update warn log setup record")
        ret = server_post("/api/v1/system/warn/setup/update", data)
        logger.info("update warn log setup record success")
        return ret

