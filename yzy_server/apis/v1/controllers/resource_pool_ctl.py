# -*- coding:utf-8 -*-
import logging
import traceback
import os

from flask import current_app, Response
from yzy_server.database import apis as db_api
from common.utils import build_result, create_uuid, compute_post, ResultThread
from common.config import SERVER_CONF
from common import constants
from yzy_server.utils import Task


logger = logging.getLogger(__name__)


class ResourcePoolController(object):

    def get_pool_nodes(self, pool_uuid):
        pool = db_api.get_resource_pool_by_key("uuid", pool_uuid)
        if not pool:
            return build_result("ResourcePoolNotExist")
        node_list = list()
        for node in pool.nodes:
            if not node.deleted:
                node_list.append(node.to_json())
        return build_result("Success", {"node_list": node_list})

    def get_resource_pool_list(self):
        """
        获取资源池列表
        :return:
        """

        def _(nodes):
            for n in nodes:
                if n.status != "active":
                    return False
            return True

        resource_pool_list = []
        resource_pools = db_api.get_resource_pool_list()
        for rp in resource_pools:
            resource_pool_list.append(
                {
                    "name": rp.name,
                    "uuid": rp.uuid,
                    "default": rp.default,
                    "node_num": len(rp.nodes),
                    "status": 1 if _(rp.nodes) else 0,
                    "desc": rp.desc
                }
            )
        return build_result("Success", {"resource_pool_list": resource_pool_list})

    def create_resource_pool(self, data):
        """
        :param data:
            {
                "name": "default",
                "desc": "this is default pool",
                "default": 1
            }
        :return:
        """
        if not data:
            return build_result("ParamError")
        if not data.get('name', ''):
            return build_result("ParamError")
        res_pool = db_api.get_resource_pool_by_key("name", data['name'])
        if res_pool:
            return build_result("ResourcePoolNameExistErr", name=data['name'])

        _uuid = create_uuid()
        data['uuid'] = _uuid
        try:
            db_api.add_resource_pool(data)
        except Exception as e:
            current_app.logger.error(traceback.format_exc())
            return build_result("ResourcePoolAddError", name=data['name'])
        return build_result("Success")

    def delete_resource_pool(self, pool_uuid):
        pool = db_api.get_resource_pool_by_key('uuid', pool_uuid)
        if not pool:
            logger.error("resource pool: %s not exist", pool_uuid)
            return build_result("ResourcePoolNotExist")
        if pool.default:
            logger.error("the resource pool is default one, can not delete")
            return build_result("ResourceDefaultError", name=pool.name)
        pool.soft_delete()
        return build_result("Success")

    def update_resource_pool(self, data):
        """
        :param data:
            {
                "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea",
                "value": {
                    "name": "pool1",
                    "desc": "this is pool1"
                }
            }
        :return:
        """
        pool_uuid = data.get('uuid', '')
        pool = db_api.get_resource_pool_by_key('uuid', pool_uuid)
        if not pool:
            logger.error("resource pool: %s not exist", pool_uuid)
            return build_result("ResourcePoolNotExist")
        try:
            pool.update(data['value'])
            pool.soft_update()
        except Exception as e:
            logger.error("update resource pool:%s failed:%s", pool_uuid, e)
            return build_result("ResourcePoolUpdateError", name=pool.name)
        logger.info("update resource pool:%s success", pool_uuid)
        return build_result("Success")

    def sync_base(self, ipaddr, server_ip, image_id, image_path, host_uuid=None, md5_sum=None, version=0):
        """节点同步镜像"""
        task = Task(image_id=image_id, host_uuid=host_uuid, version=version)
        task_id = create_uuid()
        task.begin(task_id, "start sync the image to host:%s" % ipaddr)
        template_sys = db_api.get_template_sys_storage()
        if template_sys:
            base_path = os.path.join(template_sys.path, 'instances')
        else:
            base_path = constants.DEFAULT_SYS_PATH
        image = {
            "image_id": image_id,
            "image_path": image_path,
            "base_path": base_path,
            "md5_sum": md5_sum
        }
        bind = SERVER_CONF.addresses.get_by_default('server_bind', '')
        if bind:
            port = bind.split(':')[-1]
        else:
            port = constants.SERVER_DEFAULT_PORT
        endpoint = "http://%s:%s" % (server_ip, port)
        command_data = {
            "command": "sync",
            "handler": "TemplateHandler",
            "data": {
                "image_version": 0,
                "task_id": task_id,
                "endpoint": endpoint,
                "url": constants.IMAGE_SYNC_URL,
                "image": image
            }
        }
        rep_json = compute_post(ipaddr, command_data, timeout=600)
        if rep_json.get('code') != 0:
            logger.info("sync the image to host:%s failed:%s", ipaddr, rep_json['data'])
            task.error(task_id, "sync the image to host:%s failed:%s" % (ipaddr, rep_json['data']))
        else:
            logger.info("sync the base to host:%s success", ipaddr)
            task.end(task_id, "sync the image to host:%s success" % ipaddr)
        # 如果同步失败，考虑添加数据库记录
        return rep_json

    def upload_images(self, data):
        """
        web端上传镜像后，服务端这边主要是做镜像同步
        :param data:
            {
                "pool_uuid": "d1c76db6-380a-11ea-a26e-000c2902e179",
                "image_id": "d2699e42-380a-11ea-a26e-000c2902e179",
                "image_path": "",
                "md5_sum": ""
            }
        :return:
        """
        pool_uuid = data.get('pool_uuid')
        pool = db_api.get_resource_pool_by_key("uuid", pool_uuid)
        if not pool:
            logger.error("resource pool: %s not exist", pool_uuid)
            return build_result("ResourcePoolNotExist")
        logger.info("sync the diff disk file to compute nodes")
        controller_image = db_api.get_controller_image()
        # controller = db_api.get_controller_node()
        nodes = db_api.get_node_by_pool_uuid(pool_uuid)
        ips = list()
        tasks = list()
        # failed_nodes = list()
        for item in nodes:
            # if item.ip != controller.ip:
            info = {
                "ipaddr": item.ip,
                "host_uuid": item.uuid
            }
            ips.append(info)
        logger.info("start sync base image, nodes:%s", ips)
        for item in ips:
            th = ResultThread(self.sync_base, (item['ipaddr'], controller_image.ip, data['image_id'], data['image_path'],
                                               item['host_uuid'], data['md5_sum']))
            tasks.append(th)
        for task in tasks:
            task.start()
        # with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
        #     for ipaddr in ips:
        #         task = executor.submit(self.sync_base, ipaddr, node.ip, data['image_id'])
        #         tasks.append(task)
        #     for future in as_completed(tasks):
        #         res = future.result()
        #         if res.get('code') != 0:
        #             logger.error("node :%s sync base image failed:%s", res['ipaddr'], res.get('msg', ''))
        #             failed_nodes.append(res['ipaddr'])
        # if failed_nodes:
        #     return build_result("ResourceImageSyncError", {"failed_nodes": failed_nodes})
        return build_result("Success")

    def publish_images(self, data):
        return build_result("Success")

    def retransmit_image(self, data):
        node = db_api.get_node_with_first({'ip': data['ipaddr']})
        tasks = db_api.get_task_all({'image_id': data['image_id'], 'host_uuid': node.uuid})
        for task in tasks:
            task.soft_delete()

        version = data.get('version', 0)
        controller_image = db_api.get_controller_image()
        res = self.sync_base(data['ipaddr'], controller_image.ip, data['image_id'], data['image_path'], node.uuid,
                             data.get('md5_sum', None), version)
        if res.get('code') != 0:
            return build_result("ResourceImageReError")
        return build_result("Success")

    def download_image(self, image_id, image_path, task_id=None):
        # if 0 == int(image_version):
        #     file_name = image_id
        # else:
        #     file_name = constants.IMAGE_FILE_PREFIX % str(image_version) + image_id
        file_name = image_path.split('/')[-1]
        image_size = os.path.getsize(image_path)
        record_num = int(image_size/constants.CHUNKSIZE/20)
        if task_id:
            logger.info("record the sending info, task_id:%s", task_id)
            task_latest = db_api.get_task_first({'task_id': task_id})
            host_uuid = task_latest.host_uuid
            version = task_latest.version
            task = Task(image_id, host_uuid, version)
            task.next(task_id, "send image to host")

        def send_file(count=0):
            store_path = image_path
            with open(store_path, 'rb') as targetfile:
                while True:
                    data = targetfile.read(constants.CHUNKSIZE)
                    if not data:
                        break
                    yield data
                    count += 1
                    if count == record_num and task_id:
                        task.next(task_id, "send image running")
                        count = 0
        logger.info("begin to send file %s", image_path)
        response = Response(send_file(), content_type='application/octet-stream')
        response.headers["Content-disposition"] = 'attachment; filename=%s' % file_name
        return response

    def delete_images(self, data):
        """
        删除基础镜像，支持批量操作
        1、先删除各个节点的镜像，再删除主控的基础镜像
        2、批量操作，未删除成功的继续删除下一个
        {
            "resource_uuid" : "xxxx-xxxxx",
            "uuids": [
                "xxxxxxxxxxx",
                "111111111111"
            ]
        }
        :param data:
        :return:
        """

        pool_uuid = data.get('pool_uuid')
        pool = db_api.get_resource_pool_by_key("uuid", pool_uuid)
        if not pool:
            logger.error("resource pool: %s not exist", pool_uuid)
            return build_result("ResourcePoolNotExist")

        template_sys = db_api.get_template_sys_storage()
        if template_sys:
            base_path = os.path.join(template_sys.path, 'instances')
        else:
            base_path = constants.DEFAULT_SYS_PATH

        nodes = db_api.get_node_by_pool_uuid(pool_uuid)
        success_num = 0
        fail_num = 0
        image_uuids = data.get("uuids", [])
        for uuid in image_uuids:
            try:
                image = db_api.get_image_with_first({"uuid": uuid})
                if not image:
                    logger.error("delete base image fail: %s not exist" % uuid)
                    fail_num += 1
                    continue

                # 判断是否被引用
                instances = db_api.get_devices_with_all({"image_id" : uuid})
                if instances:
                    logger.error("delete base image fail: %s is use"% uuid)
                    fail_num += 1
                    continue

                # 从各个节点上删除对应的基础镜像
                command_data = {
                    "command": "delete_base",
                    "handler": "TemplateHandler",
                    "data": {
                        "image_version": 0,
                        "image": {
                            "image_id": uuid,
                            "base_path": base_path
                        }
                    }
                }

                for node in nodes:
                    node_ip = node.ip
                    rep_json = compute_post(node_ip, command_data)
                    if rep_json.get("code", -1) != 0:
                        fail_num += 1
                        logger.error("delete base image fail: node %s image %s delete error", node.uuid, uuid)
                        break

                # 删除主控节点的基础镜像
                # image_path = os.path.join(base_path, uuid)
                image_path = image.path
                logger.info("delete main contraller base image: %s"% image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)
                image.soft_delete()
                success_num += 1
                logger.info("delete base image success: image %s", uuid)
            except Exception as e:
                logger.error("delete base image exception: image %s"% uuid, exc_info=True)
                fail_num += 1
        if success_num > 0:
            ext_msg = " 成功: %d个, 失败: %d个" % (success_num, fail_num)
            return build_result("Success", ext_msg=ext_msg)
        # 一个成功的执行都没有
        return build_result("ResourceImageDelFail")


