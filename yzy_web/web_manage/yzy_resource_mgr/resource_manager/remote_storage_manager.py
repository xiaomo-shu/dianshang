import logging
from web_manage.common.http import server_post
from web_manage.yzy_resource_mgr.serializers import *
from web_manage.common.utils import get_error_result, is_ip_addr

logger = logging.getLogger(__name__)

class RemoteStorageManager(object):

    def create_remote_storage(self, data):
        # 检查nfs服务器的有效性，远端存储名称有效性 等等
        ip_addr = data.get('server_ip')
        mount_point = data.get('mount_point')
        if not is_ip_addr(ip_addr):
            return get_error_result("IpAddressError")
        out = server_post("/remote_storage/show_mount", {'ip_addr': ip_addr})
        if mount_point not in out['data']['mount_list']:
            return get_error_result("InvalidNfsServerError")
        ret = server_post("/remote_storage/create", data)
        if ret.get("code", -1) != 0:
            return get_error_result("RemoteStorageAddFail", reason=ret.get("msg"))
        else:
            return get_error_result("Success")

    def delete_remote_storage(self, uuid):
        ret = server_post("/api/v1/remote_storage/delete", {"uuid": uuid})
        if ret.get("code", -1) != 0:
            return get_error_result("RemoteStorageDeleteFail", reason=ret.get("msg"))
        else:
            return get_error_result("Success")

    def allocate_remote_storage(self, remote_storage_uuid, resource_pool_uuid):
        ret = server_post("/api/v1/remote_storage/allocate",
                          {"remote_storage_uuid": remote_storage_uuid, 'resource_pool_uuid': resource_pool_uuid})
        if ret.get("code", -1) != 0:
            return get_error_result("RemoteStorageAllocateError", reason = ret.get("msg"))
        else:
            return get_error_result("Success")

    def reclaim_remote_storage(self, remote_storage_uuid):
        ret = server_post("/api/v1/remote_storage/reclaim",
                          {"remote_storage_uuid": remote_storage_uuid})
        if ret.get("code", -1) != 0:
            return get_error_result("RemoteStorageReclaimError", reason = ret.get("msg"))
        else:
            return get_error_result("Success")

    def list_nfs_mount_point(self, nfs_server_ip):
        ret = server_post("/remote_storage/show_mount", {'ip_addr': nfs_server_ip})
        return ret['data']['mount_list']


remote_storage_mgr = RemoteStorageManager()