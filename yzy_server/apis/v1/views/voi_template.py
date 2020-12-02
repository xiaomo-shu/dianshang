"""
模板相关的接口，教学模板和个人模板都是一样
"""
import os
import logging
from datetime import datetime
from urllib.parse import quote
from flask.views import MethodView
from flask import request, Response, jsonify
from common.utils import time_logger, build_result
from yzy_server.utils import abort_error
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.voi_template_ctl import VoiTemplateController


logger = logging.getLogger(__name__)


class VoiTemplateAPI(MethodView):

    @time_logger
    def get(self, action):
        if action == "download":
            fullfilename = request.args.get('path')
            fullpath = VoiTemplateController().get_downloading_path(fullfilename)

            def send_file():
                store_path = fullpath
                with open(store_path, 'rb') as targetfile:
                    while 1:
                        data = targetfile.read(5 * 1024 * 1024)  # 每次读取5M
                        if not data:
                            break
                        yield data
                try:
                    os.remove(fullfilename)
                except OSError as e:
                    pass

            response = Response(send_file(), content_type='application/octet-stream; charset=UTF-8')
            filename = quote(fullpath.split('/')[-1].split('_')[0] + '_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.img')
            response.headers["Content-disposition"] = "attachment; filename*=UTF-8''{}" .format(filename)
            return response

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            logger.debug("post request, data:%s", data)
            if action == "create":
                """
                {	
                    "name": "template1",
                    "desc": "this is template1",
                    "os_type": "windows_7_x64",
                    "classify": 1,
                    "network_uuid": "9c87ff12-5213-11ea-9d93-000c295dd729",
                    "subnet_uuid": "9c87ff12-5213-11ea-9d93-000c295dd728",
                    "bind_ip": "",
                    "vcpu": 2,
                    "ram": 2,
                    "groups": [
                        "9c87ff12-5213-11ea-9d93-000c295dd729"
                    ],
                    "system_disk": {
                         "image_id": "4315aa82-3b76-11ea-930d-000c295dd728",
                         "size": 50
                    },
                    "data_disks": [
                        {
                            "inx": 0,
                            "size": 50
                        }
                    ]
                }
                """
                result = VoiTemplateController().create_template(data)

            elif action == "start_upload":
                """
                {	
                    "pool_name": "",
                    "name": "template1",
                    "desc": "this is template1",
                    "os_type": "windows_7_x64",
                    "classify": 1,
                    "system_disk": {
                        "size": 100,
                        "real_size": 8.5
                    },
                    "data_disks":[
                        {
                            "size": 100,
                            "real_size": 8.5
                        },
                        ...
                    ]
                }
                """
                result = VoiTemplateController().upload_start(data)

            elif action == "upload_end":
                """
                {	
                    "uuid": "",
                    "status": true,
                    "progress": 10,
                    "os_type": "windows_7_x64"
                }
                """
                result = VoiTemplateController().upload_end(data)

            elif action == "cancel_upload":
                result = VoiTemplateController().upload_cancel(data)

            elif action == "start":
                template_uuid = data.get("uuid", "")
                result = VoiTemplateController().start_template(template_uuid)

            elif action == "stop":
                template_uuid = data.get("uuid", "")
                result = VoiTemplateController().stop_template(template_uuid)

            elif action == "hard_stop":
                template_uuid = data.get("uuid", "")
                result = VoiTemplateController().stop_template(template_uuid, hard=True)

            elif action == "reboot":
                template_uuid = data.get("uuid", "")
                result = VoiTemplateController().reboot_template(template_uuid)

            elif action == "hard_reboot":
                """硬重启就是直接断电然后开机"""
                template_uuid = data.get("uuid", "")
                result = VoiTemplateController().hard_reboot_template(template_uuid)

            elif action == "reset":
                template_uuid = data.get("uuid", "")
                result = VoiTemplateController().reset_template(template_uuid)

            elif action == "delete":
                template_uuid = data.get("uuid", "")
                result = VoiTemplateController().delete_template(template_uuid)

            elif action == "save":
                """
                在线编辑后进行模板更新操作
                """
                template_uuid = data.get("uuid", "")
                desc = data.get('desc', "")
                is_upload = data.get("is_upload", False)                # 是否为终端上传
                upload_diff_info = data.get("upload_diff_info", None)               # 终端上传差分
                result = VoiTemplateController().upgrade_template(template_uuid, desc, is_upload, upload_diff_info)

            elif action == "iso_save":
                template_uuid = data.get("uuid", "")
                result = VoiTemplateController().save_iso_template(template_uuid)

            elif action == "rollback":
                result = VoiTemplateController().rollback_template(data)

            elif action == "update":
                """
                {
                    "uuid": "655a1b9c-592a-11ea-b491-000c295dd728",
                    "name": "",
                    "value": {
                        "name": "template",
                        "desc": "",
                        "network_uuid": "",
                        "subnet_uuid": "",
                        "bind_ip": "",
                        "vcpu": 2,
                        "ram": 2,
                        "groups": [
                            "9c87ff12-5213-11ea-9d93-000c295dd729"
                        ],
                        "devices": [
                            {
                                "uuid": "c26927dc-6dad-11ea-93c8-000c29e84b9c",
                                "type": "system",
                                "device_name": "vda",
                                "boot_index": 0,
                                "size": 50
                            },
                            ...
                        ]
                    }
                }
                """
                result = VoiTemplateController().update_template(data)

            elif action == "copy":
                """
                {
                    "template_uuid": "e1d75ab0-3353-11ea-9aca-000c295dd728",
                    "name": "win7_template_copy",
                    "desc": "xxxxx",
                    "owner_id": "xxxx",
                    "groups": [],
                    "network_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea",
                    "subnet_uuid": "5712bcb6-27b5-11ea-8c45-562668d3ccea",
                    "bind_ip": "10.0.0.3"
                }
                """
                result = VoiTemplateController().copy_template(data)

            elif action == "download":
                template_uuid = data.get("uuid", "")
                result = VoiTemplateController().download_template(template_uuid)

            elif action == "attach_source":
                """
                加载ISO到模板中
                {
                    "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                    "name": "template1"
                    "iso_uuid": ""
                }
                """
                result = VoiTemplateController().attach_source(data)
            elif action == "detach_source":
                """
                加载ISO到模板中
                {
                    "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                    "name": "template1"
                }
                """
                result = VoiTemplateController().detach_source(data)
            elif action == "send_key":
                """
                发送 Ctrl+Alt+Del
                """
                result = VoiTemplateController().send_key(data)
            elif action == "edit":
                """
                编辑模板 
                1、如果模板处于关机状态，要开机
                2、将novnc URL返回
                {
                    "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                    "name": "template1"
                }
                """
                template_uuid = data.get("uuid", "")
                result = VoiTemplateController().edit_template(template_uuid)

            elif action == "console":
                """
                {
                    "uuid": "",
                    "name": ""
                }
                """
                result = VoiTemplateController().get_console(data)
            elif action == "check_upload_state":
                """
                {
                    "desktop_group_uuid": "123423"
                }
                """
                result = VoiTemplateController().check_upload_state(data)
            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.error("voi template action %s failed:%s", action, e, exc_info=True)
            return build_result("OtherError")


class VoiTemplateDiskAPI(MethodView):

    @time_logger
    def post(self, action):
        try:
            data = request.get_json()
            logger.info("post request, data:%s", data)
            if action == "list":
                """ 模板磁盘列表 """
                result = VoiTemplateController().get_template_disk_list(data)
            elif action == "sync":
                result = VoiTemplateController().sync_template_disk_info(data)
            elif action == "init":
                result = VoiTemplateController().init_template_disk_info(data)
            elif action == "send":
                result = VoiTemplateController().send_template_disk_info(data)
            elif action == "single_send":
                result = VoiTemplateController().send_template_disk_info_single(data)
            elif action == "desktop":
                result = VoiTemplateController().get_info_by_system_disk(data)
            elif action == "upload":
                result = VoiTemplateController().upload_template_diff_disk(data)
            elif action == "save_torrent":
                result = VoiTemplateController().save_torrent_file(data)
            elif action == "download":
                result = VoiTemplateController().download_template_diff_disk(data)
            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")

        except Exception as e:
            logger.error("voi template action %s failed:%s", action, e, exc_info=True)
            return build_result("OtherError")


api_v1.add_url_rule('/voi/template/<string:action>', view_func=VoiTemplateAPI.as_view('voi_template'),
                    methods=["GET", "POST"])
api_v1.add_url_rule('/voi/template_disk/<string:action>', view_func=VoiTemplateDiskAPI.as_view('voi_template_disk'),
                    methods=["GET", "POST"])
