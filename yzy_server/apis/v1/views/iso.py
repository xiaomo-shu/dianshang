import os
import logging
from flask.views import MethodView
from flask import request, Response
from common.utils import build_result, time_logger
from common.config import SERVER_CONF
from common import constants
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.iso_ctl import down_iso_file, down_image_file

logger = logging.getLogger(__name__)


class IsoAPI(MethodView):

    @time_logger
    def get(self, action):
        if action == "download":
            fullfilename = request.args.get('filename')
            # fullfilename = ""
            def send_file():
                store_path = fullfilename
                with open(store_path, 'rb') as targetfile:
                    while 1:
                        data = targetfile.read(5 * 1024 * 1024)  # 每次读取5M
                        if not data:
                            break
                        yield data

            response = Response(send_file(), content_type='application/octet-stream')
            response.headers["Content-disposition"] = 'attachment; filename=%s' % fullfilename
            return response

        elif action == "complete":
            target_filename = request.args.get('filename')   # 获取上传文件的文件名
            task = request.args.get('task_id')  # 获取文件的唯一标识符
            chunk = 0    # 分片序号
            with open('./upload/%s' % target_filename, 'wb') as target_file:  # 创建新文件
                while True:
                    try:
                        filename = './upload/%s%d' % (task, chunk)
                        source_file = open(filename, 'rb')  # 按序打开每个分片
                        target_file.write(source_file.read())  # 读取分片内容写入新文件
                        source_file.close()
                    except IOError:
                        break
                    chunk += 1
                    logger.info("filename: %s"% filename)
                    os.remove(filename)  # 删除该分片，节约空间
            return build_result("Success")

    @time_logger
    def post(self, action):
        if action == "upload":
            iso_file = request.files["file"]
            filename = iso_file.filename
            print(filename)
            iso_file.save(filename)
            return build_result("Success")

        elif action == "down":
            data = request.get_json()
            iso_file = data.get("iso_file", "")
            return down_iso_file(iso_file)

        elif action == "accept":
            upload_file = request.files['file']
            task = request.form.get('task_id')  # 获取文件唯一标识符
            chunk = request.form.get('chunk', 0)  # 获取该分片在所有分片中的序号
            filename = '%s%s' % (task, chunk)  # 构成该分片唯一标识符
            upload_file.save('./upload/%s' % filename)  # 保存分片到本地
            # return rt('./index.html')
            return build_result("Success")


class ImageAPI(MethodView):

    @time_logger
    def get(self, action):
        if action == "download":
            image_id = request.args.get('image_id')
            base_path = request.args.get('base_path', constants.DEFAULT_SYS_PATH)
            image_version = request.args.get('image_version', 1)
            if 0 == image_version:
                task_id = request.args.get('task_id')
            # if constants.IMAGE_TYPE_SYSTEM == image_type:
            #     base_path = SERVER_CONF.libvirt.instances_path
            # else:
            #     base_path = SERVER_CONF.libvirt.data_path
            image_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
            if 0 == int(image_version):
                file_name = image_id
            else:
                file_name = constants.IMAGE_FILE_PREFIX % str(image_version) + image_id
            image_path = "%s/%s" % (image_dir, file_name)

            def send_file():
                store_path = image_path
                with open(store_path, 'rb') as targetfile:
                    while True:
                        data = targetfile.read(constants.CHUNKSIZE)
                        if not data:
                            break
                        yield data

            response = Response(send_file(), content_type='application/octet-stream')
            response.headers["Content-disposition"] = 'attachment; filename=%s' % file_name
            return response


    @time_logger
    def post(self, action):
        if action == "upload":
            iso_file = request.files["file"]
            file_name = request.args.get("name")
            system_type = request.args.get("system_type")
            filename = iso_file.filename
            print(filename)
            iso_file.save(filename)
            return build_result("Success")

        elif action == "down":
            data = request.get_json()
            image_id = data.get("image_id", "")
            image_type = data.get("image_type", "")
            # return down_iso_file(iso_file)
            return down_image_file(image_id, image_type)


api_v1.add_url_rule('/iso/<string:action>', view_func=IsoAPI.as_view('iso'), methods=["GET", "POST"])
api_v1.add_url_rule('/image/<string:action>', view_func=ImageAPI.as_view('image'), methods=["GET", "POST"])
