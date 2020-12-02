import os
import logging
import shutil
import hashlib
import subprocess
from shutil import copyfile, move
from threading import  Thread
from rest_framework import status
from web_manage.yzy_resource_mgr.serializers import *
from web_manage.yzy_resource_mgr.models import *
from web_manage.yzy_edu_desktop_mgr.models import YzyInstanceTemplate, YzyInstanceDeviceInfo, YzyDesktop
from web_manage.yzy_voi_edu_desktop_mgr.models import YzyVoiTemplate, YzyVoiDeviceInfo, YzyVoiDesktop
from web_manage.common.http import server_post
from web_manage.common import constants
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.utils import get_error_result, JSONResponse, is_ip_addr, \
    create_uuid, size_to_G, size_to_M
from web_manage.yzy_system_mgr.models import YzyTask


logger = logging.getLogger(__name__)


class BaseImageManager(object):

    @property
    def os_types(self):
        return tuple([key for key in constants.IMAGE_TYPE.keys()])

    def get_object_by_uuid(self, model, uuid):
        try:
            obj = model.objects.filter(deleted=False).get(uuid=uuid)
            return obj
        except Exception as e:
            return None

    def get_object_by_name(self, model, name):
        try:
            obj = model.objects.filter(deleted=False).get(name=name)
            return obj
        except Exception as e:
            return None

    def _get_template_storage_path(self):
        template_sys = YzyNodeStorages.objects.filter(role__contains='%s' % constants.TEMPLATE_SYS).first()
        if not template_sys:
            sys_base = constants.DEFAULT_SYS_PATH
        else:
            sys_base = template_sys.path
        sys_path = os.path.join(sys_base, 'instances')
        return os.path.join(sys_path, constants.IMAGE_CACHE_DIRECTORY_NAME)

    def check_file(self, imgfile):
        chunk = imgfile.read(200)
        if b"yzy" in chunk and b"os_type:" in chunk and b"md5:" in chunk:
            return chunk
        else:
            return None

    def check_file_readble(self, imgfile):
        return self.check_file(imgfile) if hasattr(imgfile, 'read') else imgfile

    def chunks(self, file_obj, offset=None, chunk_size=64 * 2 ** 10):
        """

        :param file_obj:
        :param offset:
        :param chunk_size:
        :return:
        """
        chunk_size = chunk_size
        try:
            file_obj.seek(offset)
        except:
            pass

        while True:
            data = file_obj.read(chunk_size)
            if not data:
                break
            yield data

    def destroy(self, data, request):
        # 需判断该基础镜像是否已被引用，
        tmp_path = data['path']
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return JSONResponse(get_error_result("Success"))

    def publish(self, data, request):
        tmp_path = data['path']
        # base_path = self._get_template_storage_path()
        #
        # try:
        #     os.makedirs(base_path)
        # except:
        #     pass
        # data['path'] = os.path.join(base_path, data['uuid'])

        ser = YzyBaseImagesSerializer(data=data, context={'request': request})
        if ser.is_valid() and os.path.exists(tmp_path):
            logger.info("save image info to db")
            ser.save()
            post_data = {
                "pool_uuid": data['resource_pool'],
                "image_id": data['uuid'],
                "image_path": tmp_path,
                "md5_sum": data['md5_sum']
            }
            # move(tmp_path, data['path'])
            # os.remove(tmp_path)
            logger.info("begin upload images to other node in resource pool")
            ret = server_post('/resource_pool/images/upload', post_data)
            if ret.get("code", -1) != 0:
                logger.error("upload base image error, server return: %s", ret)
                return JSONResponse(ret)
        else:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return JSONResponse(get_error_result("OtherError"))
        return JSONResponse(ser.data)

    def upload(self, file_obj, name, os_type, resource_pool, request, image_name=None):
        base_image = self.get_object_by_name(YzyBaseImages, name)
        task = YzyTask.objects.filter(deleted=False, task_uuid=image_name).first()
        if base_image:
            logger.error("base image name repeat error")
            ret = get_error_result("BaseImageNameRepeatError")
            task.status = constants.TASK_ERROR
            task.save()
            return JSONResponse(ret)

        if os_type not in self.os_types:
            logger.error("base image os_type error: %s", os_type)
            ret = get_error_result("BaseImageOsTypeError")
            task.status = constants.TASK_ERROR
            task.save()
            return JSONResponse(ret)

        # 保存上传基础镜像文件
        size = 0
        if not file_obj:
            logger.error("base image upload fail")
            ret = get_error_result("BaseImageFileError")
            task.status = constants.TASK_ERROR
            task.save()
            return JSONResponse(ret)

        base_path = self._get_template_storage_path()
        try:
            os.makedirs(base_path)
        except:
            pass
        path = os.path.join(base_path, image_name)
        # path = os.path.join('/tmp', image_name)
        logger.info("begin save image file to %s", path)
        # 校验镜像的头信息
        try:
            os_info = self.check_file_readble(file_obj)
            if not os_info:
                logger.error("base image error!")
                ret = get_error_result("BaseImageFileError")
                return JSONResponse(ret)
            os_info = os_info.replace(b"yzy|", b"").rstrip(b' ').decode("utf-8")
            os_info = dict([i.split(":") for i in os_info.split("|")])
            md5_sum = hashlib.md5()
            with open(path, "wb+") as f:
                # _head = file_obj.truncate(200)
                for chunk in self.chunks(file_obj, offset=200):
                    size += len(chunk)
                    md5_sum.update(chunk)
                    f.write(chunk)
            f.close()
        except Exception as e:
            logger.error("save base image error", exc_info=True)
            if os.path.exists(path):
                os.remove(path)
                task.status = constants.TASK_ERROR
                task.save()
            return JSONResponse(get_error_result("BaseImageSaveError"))
        # 判断md5值
        _md5 = os_info.get("md5", "")
        if _md5 != md5_sum.hexdigest():
            logger.error("base image md5 check fail [%s]-[%s]", _md5, md5_sum.hexdigest())
            # 删除镜像
            os.remove(path)
            ret = get_error_result("BaseImageMd5Error")
            task.status = constants.TASK_ERROR
            task.save()
            return JSONResponse(ret)

        data = {
            "uuid": image_name,
            "name": name,
            "os_type": os_type,
            "path": path,
            "resource_pool": resource_pool.uuid,
            "size": str(size_to_G(size)),
            "count": resource_pool.yzy_nodes.count(),
            "md5_sum": md5_sum.hexdigest(),
            "os_bit": os_info.get('os_bit', 64),
            "vcpu": int(os_info.get('vcpu', 2)),
            "ram": float(os_info.get('ram', 2)),
            "disk": int(os_info['disk'])
        }

        task.status = constants.TASK_COMPLETE
        task.save()
        return JSONResponse(data)

    def delete(self, resource_pool_uuid, uuids):
        # pass
        resource_pool = self.get_object_by_uuid(YzyResourcePools, resource_pool_uuid)
        if not resource_pool:
            logger.error("delete resource pool base image error: not resource pool[%s]"% resource_pool_uuid)
            return get_error_result("ResourcePoolNotExist")

        # ret = get_error_result("Success")
        # for uuid in uuids:
        #     try:
        #         base_image = self.get_object_by_uuid(YzyBaseImages, uuid)
        #     except Exception as e:
        #         ret = get_error_result("ResourceImageNotExist")
        #         logger.error("delete base image: %s error!" % (uuid))
        #         break
        #     # path = ""
        #     try:
        #         path = base_image.path
        #         if os.path.exists(path):
        #             os.remove(path)
        #         base_image.delete()
        #     except:
        #         ret = get_error_result("ResourceImageDelFail")
        #         logger.error("delete base image file: %s fail"%(uuid))
        #         break
        data = {
            "pool_uuid": resource_pool_uuid,
            "uuids": uuids
        }
        ret = server_post("/resource_pool/images/delete", data)
        msg = "删除基础镜像 %s" % ('/'.join(uuids))
        insert_operation_log(msg, ret["msg"])
        return ret

    @operation_record("编辑镜像后名称 {data[name]}，系统类型 {data[os_type]}")
    def update(self, data, base_image):
        """
        镜像编辑
        :param request:
        :return:
        """
        name = data.get("name")
        os_type = data.get("os_type")
        if not (name or os_type):
            logger.error("update base image paramters error: %s", data)
            ret = get_error_result("ParamError")
            return JSONResponse(ret)

        base_image.name = name
        base_image.os_type = os_type
        results = YzyInstanceDeviceInfo.objects.filter(image_id=base_image.uuid, deleted=0).all()
        for item in results:
            ins = YzyInstanceTemplate.objects.filter(uuid=item.instance_uuid, deleted=0).first()
            if ins:
                ins.os_type = os_type
                ins.save()
                desktops = YzyDesktop.objects.filter(template=ins.uuid, deleted=0).all()
                for desktop in desktops:
                    desktop.os_type = os_type
                    desktop.save()
        results = YzyVoiDeviceInfo.objects.filter(image_id=base_image.uuid, deleted=0).all()
        for item in results:
            ins = YzyVoiTemplate.objects.filter(uuid=item.instance_uuid, deleted=0).first()
            if ins:
                ins.os_type = os_type
                ins.save()
                desktops = YzyVoiDesktop.objects.filter(template=ins.uuid, deleted=0).all()
                for desktop in desktops:
                    desktop.os_type = os_type
                    desktop.save()
        base_image.save()
        return get_error_result("Success")

    @operation_record("基础镜像重传 {image_uuid}")
    def resync(self, image_uuid, node_uuid):
        """
        重传
        :param data:
        :param base_image:
        :return:
        """
        node = self.get_object_by_uuid(YzyNodes, node_uuid)
        base_image = self.get_object_by_uuid(YzyBaseImages, image_uuid)
        if not base_image:
            return get_error_result("ResourceImageNotExist")
        data = dict()
        data["ipaddr"] = node.ip
        data["image_path"] = base_image.path
        data["image_id"] = image_uuid
        data["md5_sum"] = base_image.md5_sum
        ret = server_post("/resource_pool/images/resync", data)
        return ret


base_image_mgr = BaseImageManager()


class IsoManager(object):

    def get_object_by_name(self, model, name):
        try:
            obj = model.objects.filter(deleted=False).get(name=name)
            return obj
        except Exception as e:
            return None
    
    def get_object_by_uuid(self, model, uuid):
        try:
            obj = model.objects.filter(deleted=False).get(uuid=uuid)
            return obj
        except Exception as e:
            return None

    def delete_iso(self, uuid):
        try:
            iso = self.get_object_by_uuid(YzyISO, uuid)
            mounted = YzyInstanceTemplate.objects.filter(attach=iso.uuid, deleted=False)
            if mounted:
                return get_error_result("ISOAlreadyMounted", name=iso.name)
            if os.path.exists(iso.path):
                os.remove(iso.path)
            iso.delete()
            return get_error_result("Success", {"success_num": 1, "failed_num": 0})
        except Exception as e:
            logger.error("delete iso failed:%s", e)
            return get_error_result("ISOFileNotExistError")

    def delete(self, uuids):
        if 1 == len(uuids):
            return self.delete_iso(uuids[0])
        failed_num = 0
        success_num = 0
        logger.info("start delete isos: %s", uuids)
        for uuid in uuids:
            result = self.delete_iso(uuid)
            if result.get('code') != 0:
                failed_num += 1
            else:
                success_num += 1
        logging.info("delete isos end, success_num:%s, failed_num:%s", success_num, failed_num)
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def upload(self, request, iso_type, os_type, file_obj):
        uuid = create_uuid()
        md5_sum = hashlib.md5()
        file_name = file_obj.name
        iso_name = file_name

        if not file_name.endswith(".iso"):
            check_name = "%s.iso" % file_name
        else:
            check_name = file_name
        iso_obj = self.get_object_by_name(YzyISO, check_name)
        if iso_obj:
            logger.error("upload ISO file: %s is exist", file_name)
            return JSONResponse(get_error_result("ISOFileExistError"))

        template_sys = YzyNodeStorages.objects.filter(role__contains='%s' % constants.TEMPLATE_DATA).first()
        if not template_sys:
            data_base = constants.DEFAULT_DATA_PATH
        else:
            data_base = template_sys.path
        base_path = os.path.join(data_base, "iso")
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        tmp_path = os.path.join(base_path, iso_name)

        size = 0
        logger.info("upload file to %s", tmp_path)
        with open(tmp_path, "wb+") as f:
            for chunk in file_obj.chunks():
                size += len(chunk)
                f.write(chunk)
                md5_sum.update(chunk)
            f.close()

        if not file_name.endswith(".iso"):
            iso_name = "%s.iso" % file_name
        else:
            iso_name = file_name
        path = os.path.join(base_path, iso_name)
        # todo 执行命令打包
        if not file_name.endswith(".iso"):
            logger.info("upload iso: %s begin mkisofs", file_name)
            returncode = subprocess.call(["mkisofs", "-l", "-J", "-L", "-R", "-r", "-v", "-hide-rr-moved", "-o", path, tmp_path])
            logger.info("delete file %s", tmp_path)
            os.remove(tmp_path)
            if returncode != 0:
                return JSONResponse(get_error_result("ISOFileUploadError"))
            logger.info("upload iso file: %s exchange to iso type: %s", file_name, returncode)

            md5_sum = hashlib.md5()
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(constants.CHUNKSIZE)
                    if not chunk:
                        break
                    md5_sum.update(chunk)
        else:
            pass
            # move(tmp_path, path)

        # 如果启用了HA，把ISO库文件同步给备控，未启用则不同步
        task = Thread(target=server_post, args=('/controller/ha_sync_web_post', {"paths": [path]},))
        task.start()

        data = {
            "uuid": uuid,
            "name": iso_name[:120],
            "os_type": os_type,
            "path": path,
            "type": iso_type,
            "md5_sum": md5_sum.hexdigest(),
            "size": size_to_M(size)
        }
        ser = YzyISOSerializer(data=data, context={'request': request})
        if ser.is_valid():
            logger.info("save iso info to db")
            ser.save()
            # if os.path.exists(tmp_path):
            #     logger.info("delete file ")
            #     os.remove(tmp_path)
            return JSONResponse(ser.data)
        else:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(path):
                os.remove(path)
            return JSONResponse(ser.errors)


iso_mgr = IsoManager()
