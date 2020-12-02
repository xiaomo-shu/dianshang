import logging
from flask.views import MethodView
from yzy_server.apis.v1 import api_v1
from yzy_server.utils import abort_error
from flask import jsonify, request, current_app
from common.utils import build_result, time_logger
from yzy_server.apis.v1.controllers.remote_storage_ctl import RemoteStorageController

logger = logging.getLogger(__name__)

class RemoteStorageAPI(MethodView):
    
    def get(self, action):
        if action == "list":
            return RemoteStorageController().get_remote_storage_list()

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            if action == "create":
                return RemoteStorageController().create_remote_storage(data)

            elif action == "delete":
                remote_storage_uuid = data.get("uuid", "")
                return RemoteStorageController().delete_remote_storage(remote_storage_uuid)

            elif action == 'allocate':
                remote_storage_uuid = data.get("remote_storage_uuid", "")
                resource_pool_uuid = data.get("resource_pool_uuid", "")
                return RemoteStorageController().allocate_remote_storage(remote_storage_uuid, resource_pool_uuid)

            elif action == 'reclaim':
                remote_storage_uuid = data.get("remote_storage_uuid", "")
                return RemoteStorageController().reclaim_remote_storage(remote_storage_uuid)

            elif action == 'show_mount':
                ip_addr = data.get("ip_addr", "")
                return RemoteStorageController().show_mount(ip_addr)
            else:
                return abort_error(404)
        except Exception as e:
            logger.exception("remote storage action %s failed:%s", action, e)
            return build_result("OtherError")


api_v1.add_url_rule('/remote_storage/<string:action>', view_func=RemoteStorageAPI.as_view('remote_storage'),
                    methods=["GET", "POST"])