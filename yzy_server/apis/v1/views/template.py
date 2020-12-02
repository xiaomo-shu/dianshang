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
from yzy_server.apis.v1.controllers.template_ctl import TemplateController


logger = logging.getLogger(__name__)


class TemplateAPI(MethodView):

    @time_logger
    def get(self, action):
        if action == "download":
            fullfilename = request.args.get('path')
            fullpath = TemplateController().get_downloading_path(fullfilename)

            def send_file():
                store_path = fullpath
                with open(store_path, 'rb') as targetfile:
                    while 1:
                        data = targetfile.read(5 * 1024 * 1024)  # 每次读取5M
                        if not data:
                            break
                        yield data
                try:
                    os.remove(fullpath)
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
            if action == "create":
                """
                {
                    "name": "win7_test",
                    "desc": "xxxxx",
                    "owner_id": "xxxx",
                    "os_type": "win7",
                    "classify": 1,      # 1 教学模板  2 个人模板
                    "pool_uuid": "f567aa50-26ee-11ea-9b67-562668d3ccea",
                    "network_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea",
                    "subnet_uuid": "5712bcb6-27b5-11ea-8c45-562668d3ccea",
                    "bind_ip": "10.0.0.3",
                    "vcpu": 3,
                    "ram": 4,
                    "system_disk": {
                        "image_id": "dfcd91e8-30ed-11ea-9764-000c2902e179",
                        "size": 50
                    }
                    "data_disks": [
                        {
                            "inx": 0, "size": 50
                        }
                    ]
                }
                """
                result = TemplateController().create_template(data)
            elif action == 'complete_install':
                template_uuid = data.get("uuid", "")
                result = TemplateController().system_install_complete(template_uuid)
            elif action == "start":
                template_uuid = data.get("uuid", "")
                result = TemplateController().start_template(template_uuid)

            elif action == "stop":
                template_uuid = data.get("uuid", "")
                result = TemplateController().stop_template(template_uuid)

            elif action == "hard_stop":
                template_uuid = data.get("uuid", "")
                result = TemplateController().stop_template(template_uuid, hard=True)

            elif action == "reboot":
                template_uuid = data.get("uuid", "")
                result = TemplateController().reboot_template(template_uuid)

            elif action == "hard_reboot":
                """硬重启就是直接断电然后开机"""
                template_uuid = data.get("uuid", "")
                result = TemplateController().hard_reboot_template(template_uuid)

            elif action == "reset":
                template_uuid = data.get("uuid", "")
                result = TemplateController().reset_template(template_uuid)

            elif action == "delete":
                template_uuid = data.get("uuid", "")
                result = TemplateController().delete_template(template_uuid)

            elif action == "save":
                """
                在线编辑后进行模板更新操作
                """
                template_uuid = data.get("uuid", "")
                run_date = data.get('run_date', None)
                result = TemplateController().upgrade_template(template_uuid, run_date)

            elif action == "update":
                """
                {
                    "uuid": "655a1b9c-592a-11ea-b491-000c295dd728",
                    "value": {
                        "name": "template",
                        "desc": "",
                        "network_uuid": "",
                        "subnet_uuid": "",
                        "bind_ip": "",
                        "ram": 2,
                        "vcpu": 2,
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
                result = TemplateController().update_template(data)

            elif action == "copy":
                """
                从已有模板复制一个新模板，底层就是复制模板的系统盘和数据盘，然后新建一个模板虚拟机
                {
                    "template_uuid": "e1d75ab0-3353-11ea-9aca-000c295dd728",
                    "name": "win7_template_copy",
                    "desc": "xxxxx",
                    "owner_id": "xxxx",
                    "pool_uuid": "f567aa50-26ee-11ea-9b67-562668d3ccea",
                    "network_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea",
                    "subnet_uuid": "5712bcb6-27b5-11ea-8c45-562668d3ccea",
                    "bind_ip": "10.0.0.3"
                }
                """
                result = TemplateController().copy_template(data)

            elif action == "download":
                template_uuid = data.get("uuid", "")
                result = TemplateController().download_template(template_uuid)

            elif action == "attach_source":
                """
                加载ISO到模板中
                {
                    "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                    "name": "template1"
                    "iso_uuid": ""
                }
                """
                result = TemplateController().attach_source(data)
            elif action == "detach_source":
                """
                加载ISO到模板中
                {
                    "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                    "name": "template1"
                }
                """
                result = TemplateController().detach_source(data)
            elif action == "send_key":
                """
                发送 Ctrl+Alt+Del
                """
                result = TemplateController().send_key(data)
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
                result = TemplateController().edit_template(template_uuid)
            elif action == "resync":
                """
                模板镜像重传
                {
                    "ipaddr": "172.16.1.11",
                    "image_id": "",
                    "path": "",
                    "role": 1,
                    "version": 1
                }
                """
                result = TemplateController().retransmit(data)
            elif action == "check_ip":
                result = TemplateController().check_ip(data)
            else:
                return abort_error(404)
            if result and isinstance(result, dict):
                return jsonify(result)
            else:
                return build_result("ReturnError")
        except Exception as e:
            logger.exception("template action %s failed:%s", action, e)
            return build_result("OtherError")


api_v1.add_url_rule('/template/<string:action>', view_func=TemplateAPI.as_view('template'), methods=["GET", "POST"])
