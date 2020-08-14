import logging
import os
import hashlib
import shutil
import stat
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from common.config import SERVER_CONF
from common.cmdutils import execute
from yzy_upgrade.utils import chunks, decompress_package
from common.utils import get_error_result, create_uuid, upgrade_post, icmp_ping
from yzy_server.database import apis as db_api
from common import constants as const
from yzy_upgrade.apis.v1.controllers import constants


logger = logging.getLogger(__name__)


class UpgradeManager(object):

    def get_base_image_status(self, pool):
        """
        :return: 0-正常 1-数据同传中
        镜像状态，只要有一个基础镜像同传则资源池同传
        镜像状态，无同传，则资源池正常
        """
        for node in pool.nodes:
            if node.deleted == 1:
                continue
            logger.info("node: %s, status: %s" % (node.ip, node.status))
            if constants.STATUS_SHUTDOWN == node.status:
                return 3
        state = list()

        base_images = db_api.get_images_with_all({"pool_uuid": pool.uuid})
        for image in base_images:
            hosts_state = list()
            # 获取每个基础镜像在所有节点的状态
            for host in pool.nodes:
                if host.deleted == 1:
                    continue
                task = db_api.get_task_first_with_progress_desc(
                    {"image_id": image.uuid, "host_uuid": host.uuid, "deleted": 0}
                )
                if task:
                    logger.info("base_image: task: image_id: %s, host_uuid: %s, status: %s" % (image.uuid, host.uuid, task.status))
                    if "error" == task.status:
                        status = 2
                    elif "end" == task.status:
                        status = 0
                    else:
                        status = 1
                else:
                    status = 0
                hosts_state.append(status)
            # 确定每个基础镜像状态
            if 2 in hosts_state:
                image_status = 2
            elif 1 in set(hosts_state):
                image_status = 1
            else:
                image_status = 0
            state.append(image_status)
        # 确定资源池状态
        if 2 in state:
            return 2
        elif 1 in set(state):
            return 1
        else:
            return 0

    def get_storages_status(self, template):
        result = []
        parts = db_api.get_node_storage_all({"node_uuid": template.host_uuid})
        devices = db_api.get_devices_by_instance(template.uuid)
        for part in parts:
            if str(constants.TEMPLATE_SYS) in part.role:
                for device in devices:
                    if constants.IMAGE_TYPE_SYSTEM == device.type:
                        task = db_api.get_task_first_with_progress_desc(
                            {"image_id": device.uuid, "host_uuid": template.host_uuid}
                        )
                        if task:
                            logger.info(
                                "sys_image: task: image_id: %s, host_uuid: %s, status: %s" %
                                (device.uuid, template.host_uuid, task.status)
                            )

                        if not task or task.status == "end":
                            status = 0
                        elif task.status == "error":
                            status = 2
                        else:
                            status = 1
                        result.append(status)
                        break
            if str(constants.TEMPLATE_DATA) in part.role:
                for device in devices:
                    if constants.IMAGE_TYPE_DATA == device.type:
                        task = db_api.get_task_first_with_progress_desc(
                            {"image_id": device.uuid, "host_uuid": template.host_uuid, "deleted": 0}
                        )
                        if task:
                            logger.info(
                                "data_image: task: image_id: %s, host_uuid: %s, status: %s" %
                                (device.uuid, template.host_uuid, task.status)
                            )

                        if not task or task.status == "end":
                            status = 0
                        elif task.status == "error":
                            status = 2
                        else:
                            status = 1
                        result.append(status)
        # 确定模板差异盘状态
        if 1 in set(result):
            return 1
        else:
            return 0

    def upload(self, file_obj):
        # 保存上传的升级包文件
        size = 0
        logger.info("go to upload func")
        package_id = create_uuid()
        base_path = constants.UPGRADE_FILE_PATH

        if not os.path.exists(base_path):
            os.makedirs(base_path)

        package_path = os.path.join(base_path, "".join([package_id, ".tar.gz"]))
        logger.info("begin save upgrade compress file to %s", package_path)
        try:
            md5_sum = hashlib.md5()
            with open(package_path, "wb") as f:
                for chunk in chunks(file_obj):
                    size += len(chunk)
                    md5_sum.update(chunk)
                    f.write(chunk)
            f.close()
            md5_sum = md5_sum.hexdigest()

            # 解压升级包
            if not decompress_package(package_path):
                return get_error_result("UpgradePackageFormatError", data={"package_path": package_path})

            # 校验升级包
            if not self._check_package():
                return get_error_result("PackageNotMatchSystem", data={"package_path": package_path})

        except Exception:
            logger.exception("save upgrade package error", exc_info=True)
            return get_error_result("OtherError", data={"package_path": package_path})

        return get_error_result("Success",
                                data={"package_id": package_id, "package_path": package_path, "md5_value": md5_sum})

    def rollback_upload(self):
        # 回滚: 清空升级包目录、临时目录
        self._clean_pkg_dirs()

    def publish(self, package_id, package_path, md5_value=None):
        logger.info("sync the upgrade package to compute nodes")
        controller_image = db_api.get_controller_image()
        nodes = db_api.get_node_with_all({})
        tasks = list()
        failed_nodes = list()
        bind = SERVER_CONF.addresses.get_by_default('upgrade_bind', '')
        if bind:
            port = bind.split(':')[-1]
        else:
            port = constants.UPGRADE_DEFAULT_PORT

        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for node in nodes:
                if node.type in [constants.ROLE_MASTER_AND_COMPUTE, constants.ROLE_MASTER]:
                    continue
                task = executor.submit(
                    self._sync_download_package, "http://%s:%s" % (controller_image.ip, port),
                    node.ip, package_id, package_path, md5_value
                )
                tasks.append(task)
            for future in as_completed(tasks):
                res = future.result()
                if res.get("code") != 0:
                    logger.error("node :%s sync upgrade package failed: %s", res.get("ipaddr", ""), res.get("msg", ""))
                    failed_nodes.append({"ipaddr": res.get("ipaddr", ""), "msg": res.get("msg", "")})

        if failed_nodes:
            return get_error_result("UploadPackageSyncError", {"failed_nodes": failed_nodes})

        return get_error_result("Success")

    def rollback_publish(self, package_id, package_path):
        logger.info("rollback publish upgrade package on compute nodes")
        nodes = db_api.get_node_with_all({})
        tasks = list()
        failed_nodes = list()

        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for node in nodes:
                task = executor.submit(
                    self._sync_delete_package, node.ip, package_id, package_path
                )
                tasks.append(task)
            for future in as_completed(tasks):
                res = future.result()
                if res.get("code") != 0:
                    logger.error("node: %s rollback publish upgrade package failed: %s",
                                 res.get("ipaddr", ""), res.get("msg", ""))
                    failed_nodes.append({"ipaddr": res.get("ipaddr", ""), "msg": res.get("msg", "")})

        if failed_nodes:
            return get_error_result("UploadPackageSyncError", {"failed_nodes": failed_nodes})

        return get_error_result("Success")

    def check_node_status(self):
        nodes = db_api.get_node_with_all({})
        master = None
        slaves = list()
        for node in nodes:
            if not icmp_ping(node.ip) or node.status == constants.STATUS_SHUTDOWN:
                return get_error_result("NodeIPConnetFail")
            if node.type in [constants.ROLE_MASTER_AND_COMPUTE, constants.ROLE_MASTER]:
                master = node.ip
            else:
                slaves.append(node.ip)
        return {"master": master, "slaves": slaves}

    def notify_slaves(self, slave_ips, url):
        tasks = list()
        failed_nodes = list()

        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for node_ip in slave_ips:
                task = executor.submit(upgrade_post, node_ip, url, data={})
                tasks.append(task)
            for future in as_completed(tasks):
                res = future.result()
                if res.get("code") != 0:
                    logger.error("url:%s failed: %s, msg: %s" % (url, res.get("ipaddr", ""), res.get("msg", "")))
                    failed_nodes.append({"ipaddr": res.get("ipaddr", ""), "msg": res.get("msg", "")})

        return failed_nodes

    def stop_services(self, master=False):
        try:
            service_list = ["yzy-compute", "yzy-monitor"]
            if master:
                service_list = ["yzy-web", "nginx", "yzy-server", "yzy-compute", "yzy-monitor",
                                "yzy-terminal", "yzy-terminal-agent", "yzy-scheduler"]

            for service_name in service_list:
                logger.info("stop service %s", service_name)
                stdout, stderr = execute("systemctl", "stop", service_name)
                if stderr:
                    return get_error_result("StopServiceError", service=service_name)

        except Exception as e:
            logger.exception("stop services exception: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

        logger.info("stop services success")
        return get_error_result()

    def rollback_services(self, master=False):
        try:
            service_list = ["yzy-compute", "yzy-monitor"]
            if master:
                service_list.extend(["yzy-server", "yzy-scheduler",
                                     "yzy-terminal", "yzy-terminal-agent",
                                     "nginx", "yzy-web"])

            for service_name in service_list:
                logger.info("restart service %s", service_name)
                stdout, stderr = execute("systemctl", "restart", service_name)
                if stderr:
                    return get_error_result("StartServiceError", service=service_name)

        except Exception as e:
            logger.exception("rollback_services Exception: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

        # 检查旧版服务是否启动成功
        failed_ret = self._check_services_status(master)
        if failed_ret:
            return get_error_result("StartServiceError", service=", ".join(failed_ret))

        # 回滚完成，清空升级包目录、临时目录
        self._clean_pkg_dirs()

        return get_error_result()

    def upgrade_process(self, master=False):
        # 备份节点上的旧版代码，不备份升级服务
        res = self._backup_yzy_server()
        if not res:
            return get_error_result("UpgradeBackupFailed")

        # 清理项目目录，保留旧版升级服务、static、templates、config
        self._clear_server_dir()

        # 把临时目录中的新版代码拷贝到项目目录，不拷贝升级服务，config目录只拷贝新增文件
        res = self._copy_dir(constants.UPGRADE_KVM_PATH, const.BASE_DIR)
        if not res:
            return get_error_result("CopyFileFailed")

        # 执行升级脚本
        res = self._run_script(os.path.join(constants.UPGRADE_KVM_PATH, constants.UPGRADE_SCRIPT_RELATIVE_PATH))
        if not res:
            return get_error_result("RunUpgradeScriptFailed")

        # 启动新版服务
        res = self._start_services(master)
        if res.get('code') != 0:
            return res
        time.sleep(2)
        # 检查新版服务是否启动成功
        failed_ret = self._check_services_status(master)
        if failed_ret:
            return get_error_result("StartServiceError", service=", ".join(failed_ret))

        # 升级完成，清空升级包目录、临时目录、备份目录
        self._clean_pkg_dirs()

        logger.info('upgrade process success')
        return get_error_result()

    def rollback_process(self, master=False):
        # 若已备份，则使用备份还原；若未备份，则直接启动服务
        if os.path.exists(constants.UPGRADE_BACKUP_PATH):
            logger.info('backup exists, use backup to rollback')
            # 执行回滚脚本
            res = self._run_script(os.path.join(constants.UPGRADE_KVM_PATH, constants.ROLLBACK_SCRIPT_RELATIVE_PATH))
            if not res:
                return get_error_result("RunRollbackScriptFailed")

            # 清空项目目录
            self._clear_server_dir(all=True)

            # 把备份代码拷贝到项目目录
            res = self._rollback_yzy_server(constants.UPGRADE_BACKUP_PATH, const.BASE_DIR)
            if not res:
                return get_error_result("MoveFileFailed")

        else:
            logger.info('backup don`t exists, start services to rollback')

        # 启动旧版服务
        res = self._start_services(master)
        if res.get('code') != 0:
            return res

        # 检查旧版服务是否启动成功
        failed_ret = self._check_services_status(master)
        if failed_ret:
            return get_error_result("StartServiceError", service=", ".join(failed_ret))

        # 回滚完成，清空升级包目录、临时目录、备份目录
        self._clean_pkg_dirs()

        logger.info("rollback upgrade process success")
        return get_error_result()

    def _check_package(self):
        # try:
        #     # 校验升级包版本，默认各计算节点与主控节点版本一致
        #     sys_version = self._get_version(os.path.join(const.BASE_DIR, "version"))
        #     pkg_sversion = self._get_version(os.path.join(constants.UPGRADE_TMP_PATH, constants.KVM_NAME, 'sversion'))
        #     if pkg_sversion != sys_version:
        #         logger.error(
        #             "Upgrade package not support current version. sys_version:%s VS pkg_sversion:%s",
        #             sys_version, pkg_sversion
        #         )
        #         return False
        # except Exception as e:
        #     logger.exception("_check_package Exception: %s" % str(e), exc_info=True)
        #     return False
        #
        # logger.info("sys_version: %s, pkg_sversion: %s" % (sys_version, pkg_sversion))
        return True

    def _get_version(self, path):
        version = ""
        try:
            if os.path.exists(path):
                with open(path, 'r') as fd:
                    version = fd.read()
                    version = version.rstrip(r'\n')
                    if '_' in version:
                        version = version.split('_')[3]
            else:
                logger.error("path not exsits: %s" % path)
        except Exception as e:
            version = ""
            logger.exception("_get_version Exception: %s" % str(e), exc_info=True)
        return version

    def _sync_download_package(self, controller_image_ip, ipaddr, package_id, package_path, md5_value=None):
        """通知计算节点同步升级包"""
        url = constants.UPGRADE_FILE_SYNC_URL
        data = {
            "controller_image_ip": controller_image_ip,
            "package_id": package_id,
            "package_path": package_path,
            "md5_value": md5_value,
            "command": "download"
        }
        rep_json = upgrade_post(ipaddr, url, data, timeout=300)
        if rep_json.get("code") != 0:
            logger.error("sync the package to host:%s failed:%s", ipaddr, rep_json)
        else:
            logger.info("sync the package to host:%s success", ipaddr)

        rep_json["ipaddr"] = ipaddr
        return rep_json

    def _sync_delete_package(self, ipaddr, package_id, package_path):
        """通知计算节点删除残包"""
        url = constants.UPGRADE_FILE_SYNC_URL
        data = {
            "package_id": package_id,
            "package_path": package_path,
            "command": "delete"
        }
        rep_json = upgrade_post(ipaddr, url, data)
        if rep_json.get("code") != 0:
            logger.info("delete the package on host:%s failed:%s", ipaddr, rep_json["data"])
        else:
            logger.info("delete the package on host:%s success", ipaddr)

        return rep_json

    def _start_services(self, master=False):
        try:
            service_list = ["yzy-compute", "yzy-monitor"]
            if master:
                service_list.extend(["yzy-server", "yzy-scheduler", "yzy-terminal",
                                     "yzy-terminal-agent", "nginx", "yzy-web"])

            for service_name in service_list:
                logger.info("start service %s", service_name)
                stdout, stderr = execute("systemctl", "start", service_name)
                if stderr:
                    return get_error_result("StartServiceError", service=service_name)

        except Exception as e:
            logger.exception("start services exception: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

        return get_error_result()

    def _backup_yzy_server(self):
        # 清空备份目录
        if os.path.exists(constants.UPGRADE_BACKUP_PATH):
            shutil.rmtree(constants.UPGRADE_BACKUP_PATH, True)
        os.makedirs(constants.UPGRADE_BACKUP_PATH)

        # 把项目目录下的代码移动到备份目录中
        try:
            logger.info("backup yzy-kvm to %s", constants.UPGRADE_BACKUP_PATH)
            for name in os.listdir(const.BASE_DIR):
                # 过滤掉升级服务本身，不备份
                if name == 'yzy_upgrade' or name.endswith('.lock') or name.endswith('.pid'):
                    continue
                file_path = os.path.join(const.BASE_DIR, name)
                if os.path.isdir(file_path):
                    shutil.copytree(file_path, os.path.join(constants.UPGRADE_BACKUP_PATH, name))
                else:
                    shutil.copy2(file_path, os.path.join(constants.UPGRADE_BACKUP_PATH, name))
        except Exception as e:
            logger.exception("backup yzy-kvm failed: %s" % str(e), exc_info=True)
            return False

        # 检查备份是否成功
        if not self._check_backup(constants.UPGRADE_BACKUP_PATH, const.BASE_DIR):
            logger.error("check backup failed")
            return False

        logger.info("backup yzy-kvm success")
        return True

    def _check_backup(self, backup_path, origin_path):
        try:
            # 比较备份文件与原始文件的size是否一致
            for name in os.listdir(backup_path):
                backup_name = os.path.join(backup_path, name)
                origin_name = os.path.join(origin_path, name)
                if os.path.isdir(backup_name):
                    ret = self._check_backup(backup_name, origin_name)
                    if not ret:
                        return ret
                else:
                    backup_size = os.path.getsize(backup_name)
                    origin_size = os.path.getsize(origin_name)
                    if not backup_size == origin_size:
                        return False
            return True
        except Exception as e:
            logger.exception("_check_backup Exception: %s" % str(e), exc_info=True)
            return False

    def _clear_server_dir(self, all=False):
        for name in os.listdir(const.BASE_DIR):
            # 过滤掉升级服务本身，不清除
            if name == 'yzy_upgrade':
                continue
            if not all and name in ['static', 'templates', 'config']:
                continue
            file_path = os.path.join(const.BASE_DIR, name)
            if os.path.isdir(file_path):
                shutil.rmtree(file_path, True)
            else:
                try:
                    os.remove(file_path)
                except:
                    pass
        logger.info("clear the dir %s success", const.BASE_DIR)

    def _run_script(self, script_path):
        try:
            if not os.path.exists(script_path):
                logger.error("script_path %s do not exist", script_path)
                return True

            logger.info("run script: %s", script_path)
            os.chmod(script_path, stat.S_IEXEC)
            stdout, stderr = execute(script_path, shell=True, run_as_root=True)
            logger.info("stdout:%s, stderr:%s", stdout, stderr)
            if stderr:
                logger.error("run script failed: %s, stderr: %s", script_path, stderr)
                return False
        except Exception as e:
            logger.exception("_run_script Exception: %s" % str(e), exc_info=True)
            return False

        logger.info("run script success: %s" % script_path)
        return True

    def _rollback_yzy_server(self, source_path, dest_path):
        try:
            for name in os.listdir(source_path):
                file_path = os.path.join(source_path, name)
                if name in ['yzy_upgrade']:
                    continue
                if os.path.isdir(file_path):
                    logger.info("copy %s to %s", file_path, os.path.join(dest_path, name))
                    shutil.copytree(file_path, os.path.join(dest_path, name))
                else:
                    logger.info("copy %s to %s", file_path, os.path.join(dest_path, name))
                    shutil.copy2(file_path, os.path.join(dest_path, name))
        except Exception as e:
            logger.exception("copy %s to %s failed: %s" % (source_path, dest_path, str(e)), exc_info=True)
            return False

        logger.info("rollback server success")
        return True

    def _copy_dir(self, source_path, dest_path):
        try:
            for name in os.listdir(source_path):
                # 不拷贝升级服务
                if name in ['yzy_upgrade']:
                    continue
                if name.startswith('yzy_') or name == 'version':
                    file_path = os.path.join(source_path, name)
                    logger.info("copy %s to %s", file_path, os.path.join(dest_path, name))
                    shutil.copy(file_path, os.path.join(dest_path, name))
                elif name == 'html':
                    file_path = os.path.join(source_path, name)
                    logger.info("copy %s to %s", file_path, os.path.join(dest_path, name))
                    shutil.copytree(file_path, os.path.join(dest_path, name))
                # config只拷贝新增的文件
                elif name == "config":
                    dest_base = os.path.join(dest_path, 'config')
                    source_base = os.path.join(source_path, 'config')
                    for file in os.listdir(source_base):
                        source_file = os.path.join(source_base, file)
                        dest_file = os.path.join(dest_base, file)
                        if not os.path.isdir(source_file):
                            # 新增
                            if not os.path.exists(dest_file):
                                logger.info("copy %s to %s", source_file, dest_file)
                                shutil.copy(source_file, dest_file)
                else:
                    pass
            logger.info("merger yzy kvm config")
            SERVER_CONF.update_config()
        except Exception as e:
            logger.exception("copy %s to %s failed: %s" % (source_path, dest_path, str(e)), exc_info=True)
            return False
        return True

    def _check_services_status(self, master=False):
        service_list = ["yzy-compute", "yzy-monitor"]
        if master:
            service_list.extend(["yzy-server", "yzy-scheduler", "yzy-terminal",
                                 "yzy-terminal-agent", "nginx", "yzy-web"])

        failed_ret = list()
        try:
            for service_name in service_list:
                stdout, stderr = execute("systemctl", "status", service_name)
                if not "active (running)" in stdout:
                    failed_ret.append(service_name)
        except Exception as e:
            logger.exception("_check_services_status Exception: %s" % (str(e)), exc_info=True)
            return service_list

        logger.info("check services status: %s" % ", ".join(service_list))
        if failed_ret:
            logger.info("check services status failed: %s" % ", ".join(failed_ret))
        return failed_ret

    def _clean_pkg_dirs(self):
        dirs = []
        if os.path.exists(constants.UPGRADE_TMP_PATH):
            shutil.rmtree(constants.UPGRADE_TMP_PATH, True)
            dirs.append(constants.UPGRADE_TMP_PATH)
        if os.path.exists(constants.UPGRADE_FILE_PATH):
            shutil.rmtree(constants.UPGRADE_FILE_PATH, True)
            dirs.append(constants.UPGRADE_FILE_PATH)
        if os.path.exists(constants.UPGRADE_BACKUP_PATH):
            shutil.rmtree(constants.UPGRADE_BACKUP_PATH, True)
            dirs.append(constants.UPGRADE_BACKUP_PATH)

        logger.info("remove dirs: %s" % ", ".join(dirs))