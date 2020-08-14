import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.errcode import get_error_result
from web_manage.common.http import server_post, terminal_post
from web_manage.common import constants
from web_manage.yzy_edu_desktop_mgr import models as education_model
from web_manage.yzy_user_desktop_mgr import models as personal_model

logger = logging.getLogger(__name__)


class UserManager(object):

    @operation_record("创建用户{param[user_name]}", module="user_group")
    def single_create_check(self, param, log_user=None):
        """
        :param param:
            {
                "group_uuid": "d02cd368-5396-11ea-ad80-000c295dd728",
                "user_name": "user2",
                "passwd": "password",
                "name": "john",
                "phone": "13144556677",
                "email": "345673456@qq.com",
                "enabled": 1
            }
        :return:
        """
        group_uuid = param.get('group_uuid')
        logger.info("create group user:%s", param['user_name'])
        if not education_model.YzyGroup.objects.filter(uuid=group_uuid, deleted=False):
            logger.error("create user failed,the group not exists")
            return get_error_result("GroupNotExists", name='')
        if personal_model.YzyGroupUser.objects.filter(user_name=param['user_name'], deleted=False):
            logger.error("create user failed,the user_name already exists")
            return get_error_result("GroupUserExists", user_name=param['user_name'])
        ret = server_post("/api/v1/group/user/create", param)
        return ret

    @operation_record("创建用户以{param[prefix]}为前缀，起始数字为{param[postfix_start]}，创建{param[user_num]}个用户",
                      module="user_group")
    def multi_create_check(self, param, log_user=None):
        """
        :param param:
            {
                "group_uuid": "00d4e728-59f8-11ea-972d-000c295dd728",
                "prefix": "ctx",
                "postfix": 2,
                "postfix_start": 1,
                "user_num": 5,
                "passwd": "12345",
                "enabled": 1
            }
        :return:
        """
        group_uuid = param.get('group_uuid')
        logger.info("multi create group user")
        if not education_model.YzyGroup.objects.filter(uuid=group_uuid, deleted=False):
            logger.info("create user failed,the group not exists")
            return get_error_result("GroupNotExists", name='')
        ret = server_post("/api/v1/group/user/multi_create", param)
        return ret

    def enable_users(self, users):
        if len(users) == 1:
            return self.enable_user(users[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for user in users:
                future = executor.submit(self.enable_user, user)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def enable_user(self, user):
        logger.info("enable group user name:%s, user:%s", user['user_name'], user['uuid'])
        if not personal_model.YzyGroupUser.objects.filter(uuid=user['uuid'], deleted=False):
            logger.info("enable group user failed, it is not exists")
            return get_error_result("GroupUserNotExists", user_name=user['user_name'])
        ret = server_post("/api/v1/group/user/enable", {"uuid": user['uuid']})
        if ret.get('code') != 0:
            logger.info("enable group user failed:%s", ret['msg'])
            return ret
        else:
            logger.info("enable group user success, name:%s, uuid:%s", user['user_name'], user['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def disable_users(self, users):
        if len(users) == 1:
            return self.disable_user(users[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for user in users:
                future = executor.submit(self.disable_user, user)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def disable_user(self, user):
        logger.info("disable group name:%s, user:%s", user['user_name'], user['uuid'])
        qry = personal_model.YzyGroupUser.objects.filter(uuid=user['uuid'], deleted=False).first()
        if not qry:
            logger.info("disable group user failed, it is not exists")
            return get_error_result("GroupUserNotExists", user_name=user['user_name'])
        ret = server_post("/api/v1/group/user/disable", {"uuid": user['uuid']})
        if ret.get('code') != 0:
            logger.info("disable group user failed:%s", ret['msg'])
            return ret
        else:
            if qry.mac:
                # 提交终端服务接口
                req_data = {
                    "handler": "WebTerminalHandler",
                    "command": "user_logout",
                    "data": {
                        "mac_list": qry.mac,
                    }
                }
                ret = terminal_post("/api/v1/terminal/task", req_data)
                if ret.get("code", -1) != 0:
                    logger.error("terminal send user logout fail: %s" % qry.mac)
            logger.info("disable group user success, name:%s, uuid:%s", user['user_name'], user['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def reset_users(self, users):
        if len(users) == 1:
            return self.reset_user(users[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for user in users:
                future = executor.submit(self.reset_user, user)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def reset_user(self, user):
        logger.info("reset group user name:%s, user:%s", user['user_name'], user['uuid'])
        if not personal_model.YzyGroupUser.objects.filter(uuid=user['uuid'], deleted=False):
            logger.info("reset group user failed, it is not exists")
            return get_error_result("GroupUserNotExists", user_name=user['user_name'])
        ret = server_post("/api/v1/group/user/reset_passwd", {"uuid": user['uuid']})
        if ret.get('code') != 0:
            logger.info("reset group user failed:%s", ret['msg'])
            return ret
        else:
            logger.info("reset group user success, name:%s, uuid:%s", user['user_name'], user['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def move_users(self, param):
        group_uuid = param.get('group_uuid')
        group = education_model.YzyGroup.objects.filter(uuid=group_uuid, deleted=False)
        if not group:
            logger.error("move user failed,the group not exists")
            return get_error_result("GroupNotExists", name=param['group_name'])
        ret = server_post("/api/v1/group/user/move", param)
        if ret.get('code') != 0:
            logger.info("move group user failed:%s", ret['msg'])
            return ret
        else:
            logger.info("move group user success, group_name:%s", param['group_name'])
        return ret

    def export_users(self, param):
        ret = server_post("/api/v1/group/user/export", param)
        if ret.get('code') != 0:
            logger.info("export group user failed:%s", ret['msg'])
            return ret
        else:
            logger.info("export group user success")
        return ret

    def delete_users(self, users):
        if len(users) == 1:
            return self.delete_user(users[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for user in users:
                future = executor.submit(self.delete_user, user)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def delete_user(self, user):
        logger.info("delete group name:%s, user:%s", user['user_name'], user['uuid'])
        qry = personal_model.YzyGroupUser.objects.filter(uuid=user['uuid'], deleted=False).first()
        if not qry:
            logger.info("delete group user failed, it is not exists")
            return get_error_result("GroupUserNotExists", user_name=user['user_name'])
        ret = server_post("/api/v1/group/user/delete", {"uuid": user['uuid']})
        if ret.get('code') != 0:
            logger.info("delete group user failed:%s", ret['msg'])
            return ret
        else:
            if qry.mac:
                # 提交终端服务接口
                req_data = {
                    "handler": "WebTerminalHandler",
                    "command": "user_logout",
                    "data": {
                        "mac_list": qry.mac,
                    }
                }
                ret = terminal_post("/api/v1/terminal/task", req_data)
                if ret.get("code", -1) != 0:
                    logger.error("terminal send user logout fail: %s" % qry.mac)

            logger.info("delete group user success, name:%s, uuid:%s", user['user_name'], user['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def enable_check(self, param, log_user=None):
        """
        :param param:
            {
                "users": [
                        {
                            "uuid": "",
                            "user_name": ""
                        }
                    ]
            }
        :return:
        """
        users = param.get('users', [])
        names = list()
        for user in users:
            names.append(user['user_name'])
        ret = self.enable_users(users)
        msg = "启用用户 %s" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="user_group")
        return ret

    def disable_check(self, param, log_user=None):
        users = param.get('users', [])
        names = list()
        for user in users:
            names.append(user['user_name'])
        ret = self.disable_users(users)
        msg = "禁用用户 %s" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="user_group")
        return ret

    def export_check(self, param, log_user=None):
        """
        :param param:
            {
                "filename": "file1",
                "users": [
                        {
                            "uuid": "",
                            "user_name": ""
                        }
                    ]
            }
        :return:
        """
        ret = self.export_users(param)
        return ret

    def import_check(self, param, log_user=None):
        """
        :param param:
            {
                "filename": "file1",
            }
        :return:
        """
        ret = server_post("/api/v1/group/user/import", param)
        if ret.get('code') != 0:
            logger.info("import group user failed:%s", ret['msg'])
            return ret
        else:
            logger.info("import group user success")
        return ret

    def reset_check(self, param, log_user=None):
        users = param.get('users', [])
        names = list()
        for user in users:
            names.append(user['user_name'])
        ret = self.reset_users(users)
        msg = "重置用户密码 %s" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="user_group")
        return ret

    def move_check(self, param, log_user=None):
        """
        :param param:
            {
                "group_uuid": "",
                "group_name": "",
                "users": [
                    {
                        "uuid": "",
                        "user_name": ""
                    },
                    ...
                ]
            }
        :return:
        """
        users = param.get('users', [])
        names = list()
        for user in users:
            names.append(user['user_name'])
        ret = self.move_users(param)
        msg = "移动用户 %s 到用户组%s" % ('/'.join(names), param['group_name'])
        insert_operation_log(msg, ret['msg'], log_user, module="user_group")
        return ret

    def delete_check(self, param, log_user=None):
        users = param.get('users', [])
        names = list()
        for user in users:
            names.append(user['user_name'])
        ret = self.delete_users(users)
        msg = "删除用户 %s" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="user_group")
        return ret

    @operation_record("更新用户{data[user_name]}", module="user_group")
    def update_user(self, data, log_user=None):
        if not personal_model.YzyGroupUser.objects.filter(uuid=data['uuid'], deleted=False):
            logger.error("update user failed, it is not exists")
            return get_error_result("GroupUserNotExists", user_name=data['user_name'])
        if data['user_name'] != data['value']['user_name']:
            if personal_model.YzyGroupUser.objects.filter(user_name=data['value']['user_name'], deleted=False):
                logger.error("the user name %s already exists", data['value']['user_name'])
                return get_error_result("GroupUserExists", user_name=data['value']['user_name'])
        ret = server_post("/api/v1/group/user/update", data)
        if ret.get('code') != 0:
            logger.info("update group user failed:%s", ret['msg'])
        else:
            logger.info("update group success, name:%s, uuid:%s", data['user_name'], data['uuid'])
        return ret
