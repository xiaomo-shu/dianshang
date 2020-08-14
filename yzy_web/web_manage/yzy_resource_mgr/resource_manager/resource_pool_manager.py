import logging
from web_manage.common.utils import JSONResponse, YzyWebPagination, create_uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from web_manage.yzy_resource_mgr.serializers import *
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.utils import get_error_result, errors_to_str
from web_manage.common.http import server_post
from web_manage.yzy_edu_desktop_mgr.models import YzyInstanceTemplate

logger = logging.getLogger(__name__)


class ResourcePoolManager(object):
    """ 资源池管理模块 """

    @operation_record("创建资源池 {data[name]}")
    def create_resource_pool(self, request, data):
        logging.info("start create resource pool: %s"% data)
        ser = YzyResourcePoolsSerializer(data=data, context={'request': request})
        if ser.is_valid():
            try:
                ser.save()
            except Exception as e:
                logging.error("create resource pool fail: %s"% str(e), exc_info=True)
                return get_error_result("OtherError")
            logging.info("create resource pool success!")
            return get_error_result("Success", data=ser)
        logging.error("create resource pool fail, parameters error!")
        ret =  get_error_result("ParamError")
        ret["msg"] += errors_to_str(ser.errors)
        return ret

    def delete_resource_pool(self, uuids):
        logging.info("start delete resource pools: %s"% (uuids))
        ret = get_error_result("Success")
        try:
            for uuid in uuids:
                resource_pool =  YzyResourcePools.objects.filter(deleted=False).get(uuid=uuid)
                node_count = YzyNodes.objects.filter(deleted=False, resource_pool=resource_pool).count()
                image_count = YzyBaseImages.objects.filter(deleted=False, resource_pool=resource_pool).count()
                template_count = YzyInstanceTemplate.objects.filter(deleted=False, pool=resource_pool).count()
                if node_count > 0 or image_count > 0:
                    logger.error("delete resource pool fail")
                    return get_error_result("ResourcePoolHaveNodeDeleteFail")
                if template_count > 0:
                    logger.error("delete resource pool fail")
                    return get_error_result("ResourcePoolHaveTemplateDeleteFail")
                else:
                    ret = server_post("/api/v1/resource_pool/delete", {"uuid": uuid})
                    if ret.get("code", -1) != 0:
                        return get_error_result("ResourcePoolDeleteFail")
                    else:
                        return get_error_result("Success")
            logging.info("end delete resource pools operate!")
            msg = "删除资源池 %s" % ('/'.join(uuids))
            insert_operation_log(msg, ret['msg'])
            return get_error_result("Success")
        except Exception as e:
            return get_error_result("OtherError")

    @operation_record("修改资源池 name: {data[name]}, desc: {data[desc]}")
    def update_resource_pool(self, pool, data):
        try:
            pool.name = data["name"]
            pool.desc = data["desc"]
            pool.save()
        except Exception as e:
            logger.error("update resource pool:%s failed:%s", pool.uuid, e)
            return get_error_result("ResourcePoolUpdateError", name=pool.name)
        logger.info("update resource pool:%s success", pool.uuid)
        return get_error_result("Success", data=pool)


resource_pool_mgr = ResourcePoolManager()
