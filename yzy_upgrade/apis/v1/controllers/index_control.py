import logging
import os
import time
from flask import Response
from common.utils import get_error_result
from common.utils import build_result
from yzy_server.database import apis as db_api
from yzy_upgrade.apis.v1.controllers import constants
from yzy_upgrade.apis.v1.controllers.upgrade_manager import UpgradeManager
from yzy_upgrade.apis.v1.controllers.upgrade_agent import UpgradeAgent
from .self_upgrade import upgrade_cluster


logger = logging.getLogger(__name__)


class IndexController(object):

    def __init__(self):
        self.manger = UpgradeManager()
        self.agent = UpgradeAgent()

    def check(self):
        # 检测是否处于基础镜像同传状态
        pools = db_api.get_resource_pool_list()
        for pool in pools:
            status = self.manger.get_base_image_status(pool)
            if status != 0:
                logger.info("pool: %s, status: %d" % (pool.name, status))
                return get_error_result("ImageTaskRunning")

        # 检测是否有模板差异盘同传
        templates = db_api.get_template_with_all({})
        for template in templates:
            if template.status in [constants.STATUS_SAVING, constants.STATUS_CREATING, constants.STATUS_COPING,
                                   constants.STATUS_ROLLBACK, constants.STATUS_UPDATING]:
                logger.info("template: %s, status: %d" % (template.name, template.status))
                return get_error_result("ImageTaskRunning")
        templates = db_api.get_voi_template_with_all({})
        for template in templates:
            if template.status in [constants.STATUS_SAVING, constants.STATUS_CREATING, constants.STATUS_COPING,
                                   constants.STATUS_ROLLBACK, constants.STATUS_UPDATING]:
                logger.info("template: %s, status: %d" % (template.name, template.status))
                return get_error_result("ImageTaskRunning")
            # status = self.manger.get_storages_status(template)
            # if status != 0:
            #     logger.info("template: %s, status: %d" % (template.name, status))
            #     return get_error_result("ImageTaskRunning")

        # TODO 检测终端升级包没有处于分发状态
        return get_error_result("Success")

    def download_package(self, data):
        if not data or not data.get('package_path'):
            return build_result("UpgradeRequestParamError")

        package_path = data["package_path"]
        file_name = package_path.split("/")[-1]

        def send_file():
            store_path = package_path
            with open(store_path, "rb") as targetfile:
                while True:
                    data = targetfile.read(constants.CHUNKSIZE)
                    if not data:
                        break
                    yield data

        logger.info("begin to send file %s", package_path)
        response = Response(send_file(), content_type="application/octet-stream")
        response.headers["Content-disposition"] = "attachment; filename=%s" % file_name
        return response

    def upload_and_publish(self, file_obj):
        if not file_obj:
            logger.error("no file_obj to upload")
            return get_error_result("NoPackageToUpload")

        if not file_obj.filename.endswith('.tar.gz'):
            return get_error_result("PackageTypeError")

        # 上传升级包并解压校验，失败则回滚（主控删除升级包、清空临时目录）
        upload_ret = self.manger.upload(file_obj)
        if upload_ret.get("code") != 0:
            logger.error("upgrade package upload fail, start rollback_upload")
            self.manger.rollback_upload()
            return upload_ret

        logger.info("upgrade package upload success")

        # 向计算节点分发升级包，失败则回滚（计算节点和主控都删除升级包、清空临时目录）
        data = upload_ret["data"]
        publish_ret = self.manger.publish(data["package_id"], data["package_path"], data.get("md5_value"))
        if publish_ret.get("code") != 0:
            logger.error("upgrade package publish fail, start rollback_publish")
            self.manger.rollback_publish(data["package_id"], data["package_path"])
            logger.error("upgrade package publish fail, start rollback_upload")
            self.manger.rollback_upload()
            return publish_ret

        logger.info("upgrade package publish success")
        if os.path.exists(constants.SELF_UPGRADE_FLAG):
            need_self = True
        else:
            need_self = False
        return get_error_result("Success", {"self_upgrade": need_self})

    def sync(self, data):
        if not data:
            return get_error_result("UpgradeRequestParamError")

        command = data.pop('command')
        if command == 'download':
            return self.agent.get_package_from_controller(data)
        elif command == 'delete':
            return self.agent.delete_dirty_package(data)
        else:
            return get_error_result("UpgradeRequestParamError")

    def start_upgrade(self):
        # 确保所有节点都在线
        ret = self.manger.check_node_status()
        if ret.get('code', 0) != 0:
            return ret
        logger.info("start upgrade, check node status success")
        master_ip = ret['master']
        slave_ips = ret['slaves']
        # 停旧版服务，失败则回滚（重启旧版服务）
        ret = self._stop_services(master_ip, slave_ips)
        if ret.get('code', 0) != 0:
            rollback_failed_nodes = self._rollback_services(master_ip, slave_ips)
            if rollback_failed_nodes:
                return get_error_result("RollbackServiceError", data={"rollback_failed_nodes": rollback_failed_nodes})
            logger.info('rollback services success')
            return ret

        time.sleep(2)
        logger.info("stop services in all nodes success")
        # 执行升级过程，失败则回滚（使用备份还原，重启旧版服务）
        ret = self._start_upgrade(master_ip, slave_ips)
        if ret.get('code', 0) != 0:
            rollback_failed_nodes = self._rollback_upgrade(master_ip, slave_ips)
            if rollback_failed_nodes:
                return get_error_result("RollbackUpgradeError", data={"rollback_failed_nodes": rollback_failed_nodes})
            logger.info('rollback upgrade in all nodes success')
            return ret

        logger.info("upgrade service in all nodes success")
        return get_error_result()

    def stop_slave_services(self):
        return self.manger.stop_services(master=False)

    def upgrade_slave(self):
        return self.manger.upgrade_process(master=False)

    def rollback_slave_upgrade(self):
        return self.manger.rollback_process(master=False)

    def rollback_slave_services(self):
        return self.manger.rollback_services(master=False)

    def _stop_services(self, master_ip, slave_ips):
        # 主控节关闭自己的服务
        ret = self.manger.stop_services(master=True)
        if ret.get('code') != 0:
            logger.error("stop service failed: %s" % master_ip)
            ret['data'] = {'failed_nodes': [master_ip]}
            return ret

        # 通知各计算节点关闭服务
        failed_nodes = self.manger.notify_slaves(slave_ips, url="api/v1/index/stop_slave_services")
        if failed_nodes:
            logger.error("stop service failed: ", failed_nodes)
            ret = get_error_result("StopSlavesServiceError", data={'failed_nodes': failed_nodes})
            return ret

        return get_error_result()

    def _rollback_services(self, master_ip, slave_ips):
        """回滚：重启旧版服务"""
        ret = []
        # 通知各计算节点回滚
        failed_nodes = self.manger.notify_slaves(slave_ips, url="api/v1/index/rollback_slave_services")
        if failed_nodes:
            logger.error("rollback services failed:", failed_nodes)
            ret.extend(failed_nodes)

        # 主控节点回滚
        result = self.manger.rollback_services(master=True)
        if result.get('code') != 0:
            logger.error("rollback services failed: %s" % master_ip)
            ret.append({"ipaddr": master_ip, "msg": result.get("msg", "")})

        return ret

    def _start_upgrade(self, master_ip, slave_ips):
        """备份、替换、运行升级脚本、启服务"""
        # 通知各计算节点升级
        failed_nodes = self.manger.notify_slaves(slave_ips, url="api/v1/index/upgrade_slave")
        if failed_nodes:
            logger.error("upgrade process failed:", failed_nodes)
            ret = get_error_result("UpgradeSlavesError", data={'failed_nodes': failed_nodes})
            return ret

        # 主控节点升级自己
        ret = self.manger.upgrade_process(master=True)
        if ret.get('code') != 0:
            logger.error("upgrade process failed: %s" % master_ip)
            ret['data'] = {'failed_nodes': [master_ip]}
            return ret

        return get_error_result()

    def _rollback_upgrade(self, master_ip, slave_ips):
        """回滚：使用备份还原，重启旧版服务"""
        ret = []
        # 通知各计算节点回滚
        failed_nodes = self.manger.notify_slaves(slave_ips, url="api/v1/index/rollback_slave_upgrade")
        if failed_nodes:
            logger.error("rollback upgrade failed:", failed_nodes)
            ret.extend(failed_nodes)

        # 主控节点回滚
        result = self.manger.rollback_process(master=True)
        if result.get('code') != 0:
            logger.error("rollback upgrade failed: %s" % master_ip)
            ret.append({"ipaddr": master_ip, "msg": result.get("msg", "")})

        return ret

    def get_self_upgrade_status(self):
        if os.path.exists(constants.SELF_UPGRADE_FILE):
            return get_error_result()
        return get_error_result("OtherError")

