# coding: utf-8

from flask.views import MethodView
from flask import jsonify, request, current_app
from common.utils import build_result, time_logger
from yzy_server.apis.v1 import api_v1
from yzy_server.apis.v1.controllers.index_control import create_md5_token, get_user_list, deal_task


class LoginAPI(MethodView):

    def get(self):
        data = request.get_json()
        deal_task(data)
        return jsonify({
            "api_version": "1.0"
        })

    @time_logger
    def post(self):
        data = request.get_json()
        current_app.logger.error(data)
        # deal_task(data)
        ret = {
            "user": {
                "id": 1,
                "username": "admin",
                "nickName": "管理员",
                "sex": "男",
                "avatar": "avar-20200106044342338.jpeg",
                "email": "zhengjie@tom.com",
                "phone": "18888888888",
                "dept": "研发部",
                "job": "全栈开发",
                "enabled": True,
                "createTime": 1534986716000,
                "roles": ["dept:edit", "user:list", "storage:add", "dept:add", "storage:edit", "menu:del", "roles:del", "admin", "storage:list", "job:edit", "deployHistory:list", "user:del", "server:list", "dict:add", "dept:list", "timing:add", "job:list", "dict:del", "dict:list", "app:list", "job:add", "database:list", "timing:list", "deploy:list", "roles:add", "user:add", "pictures:list", "menu:edit", "timing:edit", "menu:list", "storage:del", "roles:list", "menu:add", "job:del", "user:edit", "roles:edit", "timing:del", "dict:edit", "serverDeploy:list", "dept:del"]
            },
            "token": "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJhZG1pbiIsImF1dGgiOiJkZXB0OmVkaXQsdXNlcjpsaXN0LHN0b3JhZ2U6YWRkLGRlcHQ6YWRkLHN0b3JhZ2U6ZWRpdCxtZW51OmRlbCxyb2xlczpkZWwsYWRtaW4sc3RvcmFnZTpsaXN0LGpvYjplZGl0LGRlcGxveUhpc3Rvcnk6bGlzdCx1c2VyOmRlbCxzZXJ2ZXI6bGlzdCxkaWN0OmFkZCxkZXB0Omxpc3QsdGltaW5nOmFkZCxqb2I6bGlzdCxkaWN0OmRlbCxkaWN0Omxpc3QsYXBwOmxpc3Qsam9iOmFkZCxkYXRhYmFzZTpsaXN0LHRpbWluZzpsaXN0LGRlcGxveTpsaXN0LHJvbGVzOmFkZCx1c2VyOmFkZCxwaWN0dXJlczpsaXN0LG1lbnU6ZWRpdCx0aW1pbmc6ZWRpdCxtZW51Omxpc3Qsc3RvcmFnZTpkZWwscm9sZXM6bGlzdCxtZW51OmFkZCxqb2I6ZGVsLHVzZXI6ZWRpdCxyb2xlczplZGl0LHRpbWluZzpkZWwsZGljdDplZGl0LHNlcnZlckRlcGxveTpsaXN0LGRlcHQ6ZGVsIiwiZXhwIjoxNTc4Mzg0NDc4fQ.0RIC06VXP8vPKKljVGL6QHDbV8SYVumAND_-qqSrIf4TnbQfjMnRpxkP4LBYe4YfCNV6NajxbudR7v0WummAgA"
        }
        # return jsonify(ret)
        return build_result("Success", ret)


class createAPI(MethodView):

    def get(self):
        sum = 0
        for i in range(1000 * 1000):
            sum += i
            sum += i
            # time.sleep(1)

        return jsonify(
            {
                "token": create_md5_token("a", "12345"),
                "users": get_user_list()
            }
        )


class DictDetailAPI(MethodView):
    """

    """
    # def get(self):
    #     ret = {
    #         "content": [{
    #             "id": 5,
    #             "label": "启用",
    #             "value": "true",
    #             "sort": "1",
    #             "dict": {
    #                 "id": 5
    #             },
    #             "createTime": None
    #         }, {
    #             "id": 6,
    #             "label": "停用",
    #             "value": "false",
    #             "sort": "2",
    #             "dict": {
    #                 "id": 5
    #             },
    #             "createTime": 1572179496000
    #         }],
    #         "totalElements": 2
    #     }
    #     return jsonify(ret)


class BuildAPI(MethodView):

    def get(self):
        menus = [{
            "name": "资源管理",
            "path": "/resource",
            "hidden": False,
            "redirect": "noredirect",
            "component": "Layout",
            "alwaysShow": True,
            "meta": {
                "title": "资源管理",
                "icon": "system",
                "noCache": True
            },
            "children": [{
                "name": "Controller",
                "path": "controller",
                "hidden": False,
                "component": "resource/controller/index",
                "meta": {
                    "title": "主控管理",
                    "icon": "peoples",
                    "noCache": True
                }
            }, {
                "name": "Pool",
                "path": "pool",
                "hidden": False,
                "component": "resource/pool/index",
                "meta": {
                    "title": "资源池管理",
                    "icon": "role",
                    "noCache": True
                }
            }, {
                "name": "Network",
                "path": "network",
                "hidden": False,
                "component": "resource/network/index",
                "meta": {
                    "title": "网络管理",
                    "icon": "menu",
                    "noCache": True
                }
            }, {
                "name": "ISO",
                "path": "iso",
                "hidden": False,
                "component": "resource/iso/index",
                "meta": {
                    "title": "ISO库",
                    "icon": "dept",
                    "noCache": True
                }
            },
                {
                    "name": "Image",
                    "path": "pool/images/:uuid",
                    "hidden": True,
                    "component": "resource/pool/images",
                    "meta": {
                        "title": "基础镜像",
                        "icon": "dev",
                        "noCache": False
                    }
                }
            ]
        },
            {
                "name": "用户管理",
                "path": "/user",
                "redirect": '/user/manage',
                "hidden": False,
                "alwaysShow": True,
                "meta": {
                    "title": "用户管理",
                    "icon": "system",
                    "noCache": True
                },
                "children": [
                    {
                        "name": "User",
                        "path": "user/manage",
                        # "hidden": True,
                        "component": "user/index",
                        "meta": {
                            "title": "用户管理",
                            "icon": "dev",
                            "noCache": False
                        }
                    }
                ]
            },
            {
            "name": "桌面管理",
            "path": "/desktop",
            "hidden": False,
            "redirect": "noredirect",
            "component": "Layout",
            "alwaysShow": True,
            "meta": {
                "title": "桌面管理",
                "icon": "monitor",
                "noCache": True
            },
            "children": [{
                "name": "Template",
                "path": "template",
                "hidden": False,
                "component": "desktop/template/index",
                "meta": {
                    "title": "系统模板",
                    "icon": "Steve-Jobs",
                    "noCache": True
                }
            }, {
                "name": "Instance",
                "path": "instance",
                "hidden": False,
                "component": "desktop/instance/index",
                "meta": {
                    "title": "桌面管理",
                    "icon": "log",
                    "noCache": True
                }
            }]
        }, {
            "name": "Terminal",
            "path": "/terminal",
            "hidden": False,
            "redirect": "noredirect",
            "component": "Layout",
            "alwaysShow": True,
            "meta": {
                "title": "终端管理",
                "icon": "mnt",
                "noCache": True
            },
            "children": [{
                "name": "Group",
                "path": "terminal/group",
                "hidden": False,
                "component": "terminal/group/index",
                "meta": {
                    "title": "分组管理",
                    "icon": "server",
                    "noCache": True
                }
            }, {
                "name": "Device",
                "path": "terminal/dev",
                "hidden": False,
                "component": "terminal/device/index",
                "meta": {
                    "title": "终端管理",
                    "icon": "app",
                    "noCache": True
                }
            }]
        }, {
            "name": "系统管理",
            "path": "/sys-tools",
            "hidden": False,
            "redirect": "noredirect",
            "component": "Layout",
            "alwaysShow": True,
            "meta": {
                "title": "系统工具",
                "icon": "sys-tools",
                "noCache": True
            },
            "children": [{
                "name": "Timing",
                "path": "timing",
                "hidden": False,
                "component": "system/timing/index",
                "meta": {
                    "title": "定时任务",
                    "icon": "timing",
                    "noCache": True
                }
            }, {
                "name": "GeneratorIndex",
                "path": "generator",
                "hidden": False,
                "component": "generator/index",
                "meta": {
                    "title": "代码生成",
                    "icon": "dev",
                    "noCache": False
                }
            }, {
                "name": "Pictures",
                "path": "pictures",
                "hidden": False,
                "component": "tools/picture/index",
                "meta": {
                    "title": "图床管理",
                    "icon": "image",
                    "noCache": True
                }
            }, {
                "name": "GeneratorConfig",
                "path": "generator/config/:tableName",
                "hidden": True,
                "component": "generator/config",
                "meta": {
                    "title": "生成配置",
                    "icon": "dev",
                    "noCache": False
                }
            }, {
                "name": "Storage",
                "path": "storage",
                "hidden": False,
                "component": "tools/storage/index",
                "meta": {
                    "title": "存储管理",
                    "icon": "qiniu",
                    "noCache": True
                }
            }, {
                "name": "Email",
                "path": "email",
                "hidden": False,
                "component": "tools/email/index",
                "meta": {
                    "title": "邮件工具",
                    "icon": "email",
                    "noCache": True
                }
            }, {
                "name": "Swagger",
                "path": "swagger2",
                "hidden": False,
                "component": "tools/swagger/index",
                "meta": {
                    "title": "接口文档",
                    "icon": "swagger",
                    "noCache": True
                }
            }, {
                "name": "AliPay",
                "path": "aliPay",
                "hidden": False,
                "component": "tools/aliPay/index",
                "meta": {
                    "title": "支付宝工具",
                    "icon": "alipay",
                    "noCache": True
                }
            }, {
                "name": "Preview",
                "path": "generator/preview/:tableName",
                "hidden": True,
                "component": "generator/preview",
                "meta": {
                    "title": "生成预览",
                    "icon": "java",
                    "noCache": False
                }
            }]
        }]
        # return jsonify(menus)
        return build_result("Success", {"menus": menus})


api_v1.add_url_rule('/login', view_func=LoginAPI.as_view('login'), methods=['GET', "POST"])
api_v1.add_url_rule('/build', view_func=BuildAPI.as_view('build'), methods=['GET', "POST"])
api_v1.add_url_rule('/dictDetail', view_func=DictDetailAPI.as_view('dictDetail'), methods=['GET', "POST"])
