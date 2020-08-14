import logging
import os
import shutil
import hashlib
import stat
from common.http import HTTPClient
from common.utils import get_error_result
from yzy_upgrade.apis.v1.controllers import constants
from yzy_upgrade.utils import decompress_package


logger = logging.getLogger(__name__)


class UpgradeAgent(object):

    def get_package_from_controller(self, data):
        """本计算节点从主控节点下载升级包"""
        logger.info("get_package_from_controller: data: %s" % data)
        package_id = data.get("package_id")
        package_path = data.get("package_path")
        controller_image_ip = data.get("controller_image_ip")
        md5_value = data.get("md5_value")
        if not package_id or not package_path or not controller_image_ip:
            return get_error_result("UpgradeRequestParamError")

        url = constants.UPGRADE_FILE_DOWNLOAD_URL
        data = {
            "package_id": package_id,
            "package_path": package_path,
        }
        logger.info("get_package_from_controller: url: %s, data: %s" % (url, data))
        package_chunks = self._download(controller_image_ip, url, package_id, package_path)
        logger.info("start to save the package on path: %s" % package_path)

        base_path, filename = os.path.split(package_path)
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        data = open(package_path, 'wb')
        close_file = True
        md5_sum = hashlib.md5()

        try:
            for chunk in package_chunks:
                md5_sum.update(chunk)
                data.write(chunk)

            ret = get_error_result("Success")

            if md5_value:
                logging.info("check md5, md5_value:%s, file_md5_sum:%s", md5_value, md5_sum.hexdigest())
                if md5_sum.hexdigest() != md5_value:
                    logging.error("the package_id: %s, md5_value:%s, the receive file_md5_sum:%s" %
                                  (package_id, md5_value,md5_sum.hexdigest()))
                    ret = get_error_result("UpgradePackageMd5Failed")

            # 解压升级包
            if not decompress_package(package_path):
                ret = get_error_result("UpgradePackageFormatError")

        except Exception:
            logger.exception("get upgrade package from controller error", exc_info=True)
            ret = get_error_result("OtherError")
        finally:
            if close_file:
                # Ensure that the data is pushed all the way down to
                # persistent storage. This ensures that in the event of a
                # subsequent host crash we don't have running instances
                # using a corrupt backing file.
                data.flush()
                self._safe_fsync(data)
                data.close()

        return ret

    def delete_dirty_package(self, data):
        """删除本计算节点上的残包"""
        package_id = data.get("package_id")
        package_path = data.get("package_path")
        if not package_id or not package_path:
            return get_error_result("UpgradeRequestParamError")

        try:
            # 删除升级包
            if os.path.exists(package_path):
                os.remove(package_path)
            # 删除解压用的临时目录
            if os.path.exists(constants.UPGRADE_TMP_PATH):
                shutil.rmtree(constants.UPGRADE_TMP_PATH)
            return get_error_result("Success")
        except Exception as e:
            logger.exception("delete the package failed: package_path: %s" % package_path, exc_info=True)
            return get_error_result("OtherError")

    def _download(self, endpoint, url, package_id, package_path):
        try:
            http_client = HTTPClient(endpoint=endpoint)
            logging.info("download the upgrade package %s" % package_id)
            # the stream args must be true, otherwise the download will be failed
            url = '%s?package_id=%s&package_path=%s' % (url, package_id, package_path)
            resp, package_chunks = http_client.get(url)
            return package_chunks
        except Exception as e:
            logging.error("download the upgrade package error:%s", e)
            raise

    @staticmethod
    def _safe_fsync(fh):
        """Performs os.fsync on a filehandle only if it is supported.

        fsync on a pipe, FIFO, or socket raises OSError with EINVAL.  This
        method discovers whether the target filehandle is one of these types
        and only performs fsync if it isn't.

        :param fh: Open filehandle (not a path or fileno) to maybe fsync.
        """
        logging.debug("fsync the file")
        fileno = fh.fileno()
        mode = os.fstat(fileno).st_mode
        # A pipe answers True to S_ISFIFO
        if not any(check(mode) for check in (stat.S_ISFIFO, stat.S_ISSOCK)):
            os.fsync(fileno)
