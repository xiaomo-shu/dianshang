import os
import logging
from common import constants, cmdutils
from yzy_server.database import models
from yzy_server.database import apis as db_api
from common.utils import build_result, create_uuid, compute_post

logger = logging.getLogger(__name__)


class RemoteStorageController(object):

    def create_remote_storage(self, data):
        """
        创建远端存储, 目前只支持nfs
        :param data:
            {
                "name": "remote_storage_name",
                "type": "nfs"
                "server": "172.16.1.23:/mnt/nfs/",
            }
        :return:
        """
        if not (data.get('name') and data.get('type') and data.get('server_ip') and data.get('mount_point')):
            return build_result("ParamError")
        server = ':'.join([data['server_ip'], data['mount_point']])
        if db_api.get_remote_storage_by_key('name', data['name']):
            logger.error("remote storage is already exist")
            return build_result("RemoteStorageNameExistError")
        if db_api.get_remote_storage_by_key('server', server):
            logger.error("server is already added")
            return build_result("ServerExistError")
        remote_storage_uuid = create_uuid()
        remote_storage_value = {
            "uuid": remote_storage_uuid,
            "name": data['name'],
            "type": data['type'],
            "server": server
        }
        try:
            db_api.add_remote_storage(remote_storage_value)
            logger.info("add remote storage:%s success", data['name'])
        except Exception as e:
            logger.error("add remote storage failed:%s", e, exc_info=True)
            return build_result("Others")
        return build_result("Success", remote_storage_value)

    def delete_remote_storage(self, uuid):
        """
        删除远端存储
        :param data:
            {
                "uuid": "remote_storage_uuid",
            }
        :return:
        """
        if not uuid:
            return build_result("ParamError")
        remote_storage = db_api.get_remote_storage_by_key('uuid', uuid)
        if not remote_storage:
            logger.error("remote storage: {} not exist".format(uuid))
            return build_result("RemoteStorageNotExistError")
        if remote_storage.allocated:
            logger.error("the remote storage is already allocated, can not delete")
            return build_result("RemoteStorageAlreadyAllocatedError")
        remote_storage.soft_delete()
        return build_result("Success")

    def allocate_remote_storage(self, remote_storage_uuid, resource_pool_uuid):
        """
        分配远端存储
        :param data:
            {
                "uuid": "resource_pool_uuid",
            }
        :return:
        """
        if not (remote_storage_uuid and resource_pool_uuid):
            return build_result("ParamError")
        remote_storage = db_api.get_remote_storage_by_key('uuid', remote_storage_uuid)
        if not remote_storage:
            logger.error("remote storage: {} not exist".format(remote_storage_uuid))
            return build_result("RemoteStorageNotExistError")
        if remote_storage.allocated:
            logger.error("the remote storage is already allocated, can not allocated")
            return build_result("RemoteStorageAlreadyAllocatedError")
        nodes = db_api.get_node_by_pool_uuid(resource_pool_uuid)
        remote_storage_list = list()
        for node in nodes:
            # 底层挂载nfs存储
            _data = {
                "command": "mount_nfs",
                "handler": "NfsHandler",
                "data": {
                    "nfs_server": remote_storage.server,
                    "name": remote_storage.name,
                }
            }
            rep_json = compute_post(node['ip'], _data)
            ret_code = rep_json.get("code", -1)
            if ret_code != 0:
                logger.error("mount nfs failed:%s", rep_json['msg'])
                return build_result("MountNfsError", host=node['ip'])
            if 'data' not in rep_json:
                logger.error("mount nfs failed: unexpected error")
                return build_result("MountNfsError", host=node['ip'])
            storage_uuid = create_uuid()
            info = {
                'uuid': storage_uuid,
                'node_uuid': node.uuid,
                'path': constants.NFS_MOUNT_POINT_PREFIX + remote_storage.name,
                'role': '',
                'type': 2, # 1:本地存储 2：远端存储
                'total': rep_json['data'][2],
                'free': rep_json['data'][1],
                'used': rep_json['data'][0]
            }
            remote_storage_list.append(info)
        logger.info("allocate remote storage success")
        db_api.insert_with_many(models.YzyNodeStorages, remote_storage_list)
        remote_storage_info = {
            'allocated_to': resource_pool_uuid,
            'allocated': 1,
            'total': rep_json['data'][2],
            'free': rep_json['data'][1],
            'used': rep_json['data'][0]
        }
        db_api.update_remote_storage(remote_storage, remote_storage_info)
        return build_result("Success")

    def reclaim_remote_storage(self, remote_storage_uuid):
        """
        回收远端存储
        :param data:
            {
            }
        :return:
        """
        if not remote_storage_uuid:
            return build_result("ParamError")
        remote_storage = db_api.get_remote_storage_by_key('uuid', remote_storage_uuid)
        if not remote_storage:
            logger.error("remote storage: {} not exist".format(remote_storage_uuid))
            return build_result("RemoteStorageNotExistError")
        if not remote_storage.allocated:
            logger.error("the remote storage is not allocated, can not reclaim")
            return build_result("RemoteStorageNotAllocatedError")
        if remote_storage.role:
            logger.error("the remote storage is used as vm storage, can not reclaim")
            return build_result("RemoteStorageUsedError")
        instance_dir = constants.NFS_MOUNT_POINT_PREFIX + remote_storage.name + '/instances'
        base_dir = constants.NFS_MOUNT_POINT_PREFIX + remote_storage.name + '/instances/_base'
        if os.path.exists(instance_dir) and len(os.listdir(instance_dir)) > 1:
            return build_result("RemoteStorageHasImage")
        if os.path.exists(base_dir) and len(os.listdir(base_dir)):
            return build_result("RemoteStorageHasImage")
        nodes = db_api.get_node_by_pool_uuid(remote_storage.allocated_to)
        for node in nodes:
            # 底层umount nfs存储
            _data = {
                "command": "umount_nfs",
                "handler": "NfsHandler",
                "data": {
                    "name": remote_storage.name,
                }
            }
            rep_json = compute_post(node['ip'], _data)
            ret_code = rep_json.get("code", -1)
            if ret_code != 0:
                logger.error("mount nfs failed:%s", rep_json['msg'])
                return build_result("UmountNfsError", host=node['ip'])
        storages = db_api.get_node_storage_by_path(constants.NFS_MOUNT_POINT_PREFIX + remote_storage.name)
        for storage in storages:
            storage.soft_delete()
        db_api.update_remote_storage(remote_storage, {'allocated_to': None, 'allocated': 0})
        return build_result("Success")

    def show_mount(self, ip_addr):
        out, err = cmdutils.execute("showmount", "-e", "{}".format(ip_addr),
                                    run_as_root=True, ignore_exit_code=True)
        res = out.split('\n')[1:-1]
        return build_result("Success", {"mount_list": [mount_point.replace('*', '').strip() for mount_point in res]})