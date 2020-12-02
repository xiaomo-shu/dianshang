import logging
import os
import stat
import shutil
import hashlib
from threading import Thread
from common.http import HTTPClient
from common import constants
from common import cmdutils
from common.utils import get_file_md5
from yzy_compute import exception
from yzy_compute.virt.libvirt.driver import LibvirtDriver
from yzy_compute import utils


class ImageService(object):

    def __init__(self, **kwargs):
        self.endpoint = kwargs.get('endpoint', None)
        if self.endpoint:
            self.http_client = HTTPClient(self.endpoint, timeout=600)

    def sync_thread(self, url, images, image_version):
        """
        sync the image
        """
        th1 = Thread(target=self.sync, args=(url, images, image_version, ))
        th1.start()
        logging.info("finish sync thread")

    def sync(self, url, image, version, task_id=None):
        dest_path = image['dest_path']
        backing_file = image['backing_file']
        if version > 1 and not os.path.exists(backing_file):
            # 模板中途添加数据盘时，需要把base文件同步过来
            logging.info("syncing the backing file:%s", backing_file)
            backing_image = {
                "image_id": image['image_id'],
                "disk_file": backing_file
            }
            self.download(url, backing_image, backing_file)
        if os.path.exists(dest_path):
            logging.info("the dest_path %s already exists", dest_path)
            if image.get('md5_sum', None):
                logging.info("need check md5, get %s md5 sum", dest_path)
                md5_sum = get_file_md5(dest_path)
                if md5_sum == image['md5_sum']:
                    logging.info("check md5 sum success, return")
                    return
                else:
                    self.download(url, image, dest_path, task_id)
        else:
            self.download(url, image, dest_path, task_id)
        if version >= constants.IMAGE_COMMIT_VERSION:
            logging.info("commit the diff file:%s", dest_path)
            stdout, stderr = cmdutils.execute('qemu-img', 'commit', '-f', 'qcow2', dest_path, run_as_root=True)
            if stderr:
                raise exception.ImageCommitError(image=dest_path, error=stderr)
            try:
                logging.debug("delete the diff file after commit")
                os.remove(dest_path)
            except:
                pass

    def download(self, url, image, dest_path, task_id=None):
        try:
            logging.info("sync the image, info:%s", image)
            # the stream args must be true, otherwise the download will be failed
            url = '%s?image_id=%s&image_path=%s&s' % (url, image['image_id'], image['disk_file'])
            if task_id:
                url = "%s&task_id=%s" % (url, task_id)
            resp, image_chunks = self.http_client.get(url)
        except Exception as e:
            logging.error("sync error:%s", e)
            raise

        logging.info("data is none, open the dst_path:%s", dest_path)
        utils.ensure_tree(os.path.dirname(dest_path))
        data = open(dest_path, 'wb')
        close_file = True

        if data is None:
            return image_chunks
        else:
            md5_sum = hashlib.md5()
            try:
                for chunk in image_chunks:
                    md5_sum.update(chunk)
                    data.write(chunk)
                if image.get('md5_sum', None):
                    logging.info("check md5, image:%s, file:%s", image['md5_sum'], md5_sum.hexdigest())
                    if md5_sum.hexdigest() != image['md5_sum']:
                        logging.error("the image md5_sum:%s, the receive md5_sum:%s", image['md5_sum'], md5_sum.hexdigest())
                        raise Exception("the image md5 sum check failed")
            except Exception as ex:
                logging.error("Error writing to %(path)s: %(exception)s",
                          {'path': dest_path, 'exception': ex})
                try:
                    os.remove(dest_path)
                except:
                    pass
                raise ex
            finally:
                if close_file:
                    # Ensure that the data is pushed all the way down to
                    # persistent storage. This ensures that in the event of a
                    # subsequent host crash we don't have running instances
                    # using a corrupt backing file.
                    data.flush()
                    self._safe_fsync(data)
                    data.close()

    # def sync_thread_single(self, url, image_id, image_type, image_version):
    #     """
    #     sync the image with single image_id and image type
    #     :param url: the interface route
    #     :param image_id: the image_id of a single disk
    #     :param image_type: the image type, system or data
    #     :param image_version: the image version
    #     :return:
    #     """
    #     th1 = Thread(target=self.sync_single, args=(url, image_id, image_type, image_version, ))
    #     th1.start()
    #     logging.info("finish sync thread")
    #
    # def sync_single(self, url, image_id, image_type, version, data=None):
    #     try:
    #         logging.info("sync the image")
    #         # the stream args must be true, otherwise the download will be failed
    #         url = '%s?image_id=%s&image_type=%s&image_version=%s' % (url, image_id, image_type, version)
    #         resp, image_chunks = self.http_client.get(url)
    #     except Exception as e:
    #         logging.error("sync error:%s", e)
    #         raise
    #     if constants.IMAGE_TYPE_SYSTEM == image_type:
    #         base_path = os.path.join(CONF.libvirt.instances_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
    #     else:
    #         base_path = os.path.join(CONF.libvirt.data_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
    #     if not os.path.isdir(base_path):
    #         utils.ensure_tree(base_path)
    #     dest_file_name = constants.IMAGE_FILE_PREFIX % str(version) + image_id
    #     dest_path = os.path.join(base_path, dest_file_name)
    #     close_file = False
    #     if data is None and dest_path:
    #         logging.info("data is none, open the dst_path:%s", dest_path)
    #         data = open(dest_path, 'wb')
    #         close_file = True
    #
    #     if data is None:
    #         return image_chunks
    #     else:
    #         try:
    #             for chunk in image_chunks:
    #                 data.write(chunk)
    #         except Exception as ex:
    #             logging.error("Error writing to %(path)s: %(exception)s",
    #                       {'path': dest_path, 'exception': ex})
    #         finally:
    #             if close_file:
    #                 # Ensure that the data is pushed all the way down to
    #                 # persistent storage. This ensures that in the event of a
    #                 # subsequent host crash we don't have running instances
    #                 # using a corrupt backing file.
    #                 data.flush()
    #                 self._safe_fsync(data)
    #                 data.close()

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

    def recreate_disks(self, disks):
        for disk in disks:
            try:
                os.remove(disk['disk_file'])
            except:
                pass
            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', disk['disk_file'], '-o',
                             'backing_file=%s' % disk['backing_file'], run_as_root=True)

    # def save(self, instance, version, images, timeout=30):
    #     logging.info("save template begin, instance:%s", instance['uuid'])
    #     virt = LibvirtDriver()
    #     virt.power_off(instance, timeout=timeout)
    #     for image in images:
    #         instance_dir = os.path.join(image['base_path'], instance['uuid'])
    #         filename = constants.DISK_FILE_PREFIX + image['image_id']
    #         source_file = os.path.join(instance_dir, filename)
    #         dest_file = utils.get_backing_file(version, image['image_id'], image['base_path'])
    #         try:
    #             logging.info("move %s to %s", source_file, dest_file)
    #             shutil.move(source_file, dest_file)
    #         except Exception as e:
    #             if isinstance(e, FileNotFoundError):
    #                 logging.error("file not found")
    #     logging.info("save template finished")

    def convert(self, template):
        source_path = template['backing_file']
        dest_path = template['dest_file']
        logging.info("start convert, source:%s, dest:%s", source_path, dest_path)
        if template['need_convert']:
            logging.info("convert from %s to %s", source_path, dest_path)
            cmdutils.execute('qemu-img', 'convert', '-f', 'qcow2', '-O', 'qcow2',
                             source_path, dest_path, run_as_root=True)
        else:
            logging.info("generate base image from origin image")
            try:
                shutil.copy(source_path, dest_path)
            except IOError as e:
                logging.error("copy image failed:%s", e)
                raise exception.ImageCopyIOError(source_path)
        logging.info("generat new image success")
        return {'path': dest_path}

    def read_in_block(self, file_path):
        with open(file_path, "rb") as f:
            while True:
                block = f.read(constants.CHUNKSIZE)
                if block:
                    yield block
                else:
                    return

    def write_header(self, data):
        try:
            vcpu = data['vcpu']
            ram = data['ram']
            disk_size = data['disk_size']
            image_path = data['image_path']
            md5_sum = get_file_md5(image_path)
            head = "yzy|os_type:%s|os_bit:%s|version:%s|vcpu:%s|ram:%s|disk:%s|md5:%s" % (
            'win7', 32, 1, vcpu, ram, disk_size, md5_sum)
            head = head.encode("utf-8")
            max_length = 200
            space_num = max_length - len(head)
            _head = head + b' ' * space_num
            file_name = "%s_c%s_r%s_d%s" % (image_path.split('/')[-1], vcpu, ram, disk_size)
            image_path_info = image_path.split('/')
            image_path_info[-1] = file_name
            file_path = '/'.join(image_path_info)
            with open(file_path, "wb+") as f:
                f.write(_head)
                for block in self.read_in_block(image_path):
                    f.write(block)
            logging.info("write head info to image %s success, dest_path:%s", image_path, file_path)
        except Exception as e:
            logging.exception("write head info failed:%s", e)
            try:
                logging.info("delete dest image file:%s", file_path)
                os.remove(file_path)
            except:
                pass
            raise e
        finally:
            try:
                logging.info("delete origin image file:%s", image_path)
                os.remove(image_path)
            except:
                pass
        return {'path': file_path}

    def copy_images(self, image):
        backing_file = image['backing_file']
        dest_file = image['dest_file']
        try:
            logging.info("copy file from %s to %s", backing_file, dest_file)
            shutil.copy(backing_file, dest_file)
        except IOError as e:
            logging.error("copy image failed:%s", e)
            raise exception.ImageCopyIOError(backing_file)
        logging.info("copy new image success")
        return True

    def delete_image(self, image):
        try:
            logging.info("delete file %s", image['disk_file'])
            if os.path.exists(image['disk_file']):
                os.remove(image['disk_file'])
        except IOError as e:
            logging.error("copy image failed:%s", e)
            raise exception.ImageDeleteIOError(image['disk_file'])
        logging.info("delete image success")
        return True

    def resize_disk(self, images):
        for image in images:
            try:
                logging.info("resize file %s", image['disk_file'])
                size = '+%sG' % image['size']
                cmdutils.execute('qemu-img', 'resize', image['disk_file'], size, run_as_root=True)
            except Exception as e:
                logging.error("resize image file failed:%s", e)
                raise exception.ImageResizeError(image=image['disk_file'], error=e)
        logging.info("resize image success")
        return True

    def create_qcow2_file(self, disk_file, size):
        dir_path = os.path.dirname(disk_file)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', disk_file, size, run_as_root=True)
        logging.info("create qcow2 file success")
        return True
