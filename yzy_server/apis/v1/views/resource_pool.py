import logging
from flask.views import MethodView
from flask import request, current_app
from common.utils import build_result, time_logger
from common import constants
from yzy_server.utils import abort_error
from yzy_server.apis.v1 import api_v1

from yzy_server.apis.v1.controllers.resource_pool_ctl import ResourcePoolController


logger = logging.getLogger(__name__)


class ResourcePoolAPI(MethodView):

    pool = ResourcePoolController()

    @time_logger
    def get(self, action):
        if action == "list":
            return self.pool.get_resource_pool_list()

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            current_app.logger.info("post data:%s", data)
            if action == "create":
                """
                {
                    "name": "default",
                    "desc": "this is default pool",
                    "default": 1
                }
                """
                result = self.pool.create_resource_pool(data)
                if result:
                    return result
            elif action == "list":
                result = self.pool.get_resource_pool_list()
                if result:
                    return result

            elif action == "delete":
                pool_uuid = data.get("uuid", "")
                result = self.pool.delete_resource_pool(pool_uuid)
                if result:
                    return result
            elif action == "update":
                """
                {
                    "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea",
                    "value": {
                        "name": "pool1",
                        "desc": "this is pool1"
                    }
                }
                """
                result = self.pool.update_resource_pool(data)
                if result:
                    return result
            elif action == "node":
                # get node with resource pool
                pool_uuid = data.get("uuid", "")
                result = self.pool.get_pool_nodes(pool_uuid)
                if result:
                    return result

            return abort_error(404)
        except Exception as e:
            logger.error("resource pool action %s failed:%s", action, e)
            return build_result("OtherError")


class ResourcePoolImagesAPI(MethodView):

    @time_logger
    def get(self, action):
        if action == "download":
            image_id = request.args.get('image_id', '')
            image_path = request.args.get('image_path', constants.DEFAULT_SYS_PATH)
            # image_version = request.args.get('image_version', 1)
            task_id = request.args.get('task_id', None)
            return ResourcePoolController().download_image(image_id, image_path, task_id)

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "upload":
                """
                {
                    "pool_uuid": "d1c76db6-380a-11ea-a26e-000c2902e179",
                    "image_id": "d2699e42-380a-11ea-a26e-000c2902e179",
                    "image_path": "/opt/slow/instances/_base/d2699e42-380a-11ea-a26e-000c2902e179",
                    "md5_sum": ""
                }
                """
                if not data:
                    return build_result("ParamError")
                return ResourcePoolController().upload_images(data)
            elif action == "resync":
                """
                {
                    "ipaddr": "172.16.1.11",
                    "image_id": "",
                    "image_path": "",
                    "md5_sum": ""
                }
                """
                return ResourcePoolController().retransmit_image(data)
            elif action == "publish":
                return ResourcePoolController().publish_images(data)

            elif action == "delete":
                # 删除基础镜像
                return ResourcePoolController().delete_images(data)

            return abort_error(404)
        except Exception as e:
            logger.error("resource pool image action %s failed:%s", action, e)
            return build_result("OtherError")


api_v1.add_url_rule('/resource_pool/<string:action>', view_func=ResourcePoolAPI.as_view('resource_pool'),
                    methods=["GET", "POST"])
api_v1.add_url_rule('/resource_pool/images/<string:action>', view_func=ResourcePoolImagesAPI.as_view('images'),
                    methods=["GET", "POST"])


