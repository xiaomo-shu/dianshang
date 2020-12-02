import time
import functools
import logging
import json
from retrying import retry
from datetime import datetime, timedelta
from .desktop_ctl import BaseController
from yzy_server.database import apis as db_api
from common.utils import build_result, create_uuid, find_ips, is_ip_addr, create_md5, monitor_post, compute_post
from common import constants
from libs.yzyRedis import yzyRedis
from .system_ctl import LicenseManager


logger = logging.getLogger(__name__)


class TerminalController(object):

    @retry(stop_max_attempt_number=5, wait_fixed=5000, wait_incrementing_increment=1000)
    def check_concurrency(self, redis, host_ip, terminal_id, ram):
        try:
            info = {"node": host_ip, "ram": ram}
            redis.rds.hset(constants.PARALELL_QUEUE, terminal_id, value=json.dumps(info))
            count = 0
            ram_sum = 0
            for value in redis.rds.hvals(constants.PARALELL_QUEUE):
                value = json.loads(value)
                if value['node'] == host_ip:
                    count += 1
                    ram_sum += value['ram']
            logger.info("terminal_id:%s, queue count:%s, ram_sum:%s", terminal_id, count, ram_sum)
            if count > constants.PARALELL_NUM:
                logger.info("check concurrency raise exception")
                raise Exception("the parallel queue is reach maxed")
            command_data = {
                "command": "check_ram",
                "handler": "InstanceHandler",
                "data": {
                    "allocated": ram_sum
                }
            }
            rep_json = compute_post(host_ip, command_data)
            if rep_json.get("code", -1) != 0:
                logger.error("check ram available in %s failed", host_ip)
                raise Exception("check ram available failed")
            if not rep_json.get('data', {}).get('result', True):
                logger.error("can not allocate memory")
                raise Exception("can not allocate memory")
        except Exception as e:
            redis.rds.hdel(constants.PARALELL_QUEUE, terminal_id)
            raise e

    @retry(stop_max_attempt_number=3, wait_fixed=2000, wait_incrementing_increment=1000)
    def check_auth_num(self, redis, size):
        try:
            res = redis.incr(constants.AUTH_SIZE_KEY)
            logger.info("current auth size:%s, total:%s", res, size)
            if res > size:
                raise Exception("auth size is %s, expired", )
        except Exception as e:
            raise e

    def auth_session(self, func):
        # 判断登录session
        @functools.wraps(func)
        def wrapped_func(self, data, *args, **kwargs):
            session_id = data.get("session_id", "")
            session = db_api.get_group_user_session_first({"session_id": session_id})
            if not session:
                logger.error("terminal user query desktop group error: %s not exist" % session_id)
                return build_result("TerminalUserLogout")

            user = db_api.get_group_user_with_first({"uuid": session.user_uuid})
            if not user:
                logger.error("terminal user query desktop group error: %s not exist" % session.user_uuid)
                return build_result("TerminalUserNotExistError")

            if not user.enabled:
                logger.error("terminal user query desktop group error: %s is unenabled" % user.user_name)
                return build_result("TerminalUserUnenabledError")
            return func(self, data)

        return wrapped_func

    def get_spice_link(self, host_ports):
        # {
        #   "172.16.1.30": ["5901","5902"],
        #   "172.16.1.31": ["5901","5902"],
        #   "172.16.1.32": ["5901","5902"]
        # }
        # return
        # {
        #  "172.16.1.39": {"5901": true}
        # }
        _d = dict()
        for k, v in host_ports.items():
            if not v:
                continue
            _d[k] = {}
            ports = ",".join(v)
            ret = monitor_post(k, "/api/v1/monitor/port_status", {"ports": ports})
            if ret.get("code", -1) == 0:
                data = ret["data"]
            else:
                logger.error("monitor %s %s spice ports return: %s"% (k, ports, ret))
                data = {}
            for i in v:
                _d[k].update({i: data.get(i, False)})

        return _d


    def user_login(self, data):
        """ 终端用户登录 """
        user_name = data.get("user_name", "")
        passwd = data.get("password","")
        mac = data.get("mac")
        if not (user_name and passwd and mac):
            logger.error("terminal user login error: param error %s"% data)
            return build_result("ParamError")

        user = db_api.get_group_user_with_first({"user_name": user_name})
        if not user:
            logger.error("terminal user login error: %s not exist"% user_name)
            return build_result("TerminalUserNotExistError")
        if not user.validate_password(passwd):
            logger.error("terminal user login error: %s password error"% user_name)
            return build_result("TerminalAccountError")
        if not user.enabled:
            logger.error("terminal user login error: %s is unenabled"% user_name)
            return build_result("TerminalUserUnenabledError")
        session = db_api.get_group_user_session_first({"user_uuid": user.uuid})
        if session:
            logger.info("terminal user login : %s session is exist"% user_name)
            session.soft_delete()

        old_mac = None
        if not user.mac:
            # 没有绑定的终端
            users = db_api.get_group_user_with_all({"mac": mac})
            for _user in users:
                session = db_api.get_group_user_session_first({"user_uuid": _user.uuid})
                if session:
                    session.soft_delete()
        else:
            if user.mac != mac:
                old_mac = user.mac
        try:
            session_id = create_md5(str(time.time()))
            expire_time = datetime.now() + timedelta(hours=2)
            values = {
                "session_id": session_id,
                "user_uuid": user.uuid,
                "expire_time": expire_time
            }
            db_api.create_group_user_session(values)
            users = db_api.get_group_user_with_all({"mac": mac})
            for old_user in users:
                old_user.mac = ''
            user.online = 1
            user.mac = mac
            user.soft_update()
        except Exception as e:
            logger.error("terminal user login fail: %s"% user_name, exc_info=True)
            return build_result("SystemError")
        user_info = user.to_json()
        user_info["session_id"] = session_id
        user_info["expire_time"] = expire_time.strftime("%Y-%m-%d %H:%M:%S")
        if old_mac:
            user_info["old_mac"] = old_mac
        logger.info("terminal user login success: %s"% user.to_json())
        return build_result("Success", user_info)

    def user_logout(self, data):
        """ 终端用户注销 """
        session_id = data.get("session_id", "")
        session = db_api.get_group_user_session_first({"session_id": session_id})
        if not session:
            logger.error("terminal user logout error: %s not exist" % session_id)
            return build_result("Success")
        user = db_api.get_group_user_with_first({"uuid" : session.user_uuid})
        if user:
            logger.info("terminal user logout: %s"% user.user_name)
            user.online = 0
            user.mac = ""
            user.soft_update()

        session.soft_delete()
        logger.info("terminal user logout success: %s"% session.user_uuid)
        return build_result("Success")

    def user_password_change(self, data):
        """ 终端用户密码修改 """
        user_name = data.get("user_name", "")
        passwd = data.get("password", "")
        user = db_api.get_group_user_with_first({"user_name": user_name})
        if not user:
            logger.error("terminal user login error: %s not exist" % user_name)
            return build_result("TerminalUserNotExistError")
        if not user.validate_password(passwd):
            logger.error("terminal user login error: %s password error" % user_name)
            return build_result("TerminalAccountError")
        if not user.enabled:
            logger.error("terminal user login error: %s is unenabled" % user_name)
            return build_result("TerminalUserUnenabledError")

        new_password = data.get("new_password","")
        if not new_password:
            return build_result("ParamError")

        user.change_password(new_password)
        user.online = 0
        user.mac = ""
        user.soft_update()
        # session.soft_delete()
        logger.info("terminal user %s change password success!"% user.user_name)
        return build_result("Success")

    def person_desktop_groups(self, data):
        """ 个人桌面组列表 """
        session_id = data.get("session_id", "")
        session = db_api.get_group_user_session_first({"session_id": session_id})
        if not session:
            logger.error("terminal user query desktop group error: %s not exist" % session_id)
            return build_result("TerminalUserLogout")

        user = db_api.get_group_user_with_first({"uuid": session.user_uuid})
        if not user:
            logger.error("terminal user query desktop group error: %s not exist"% session.user_uuid)
            return build_result("TerminalUserNotExistError")

        if not user.enabled:
            logger.error("terminal user query desktop group error: %s is unenabled" % user.user_name)
            return build_result("TerminalUserUnenabledError")

        # 个人桌面组分为随机桌面组和静态桌面组
        desktop_uuids = list()
        # 随机桌面
        random_desktop_groups = db_api.get_random_desktop_with_all({"group_uuid": user.group_uuid})
        for group in random_desktop_groups:
            desktop_uuids.append(group.desktop_uuid)

        # instance_uuids = list()
        static_instances = db_api.get_instance_with_all({"user_uuid": user.uuid})
        for instance in static_instances:
            desktop_uuids.append(instance.desktop_uuid)

        # instances = db_api.get_instance_all_by_uuids(instance_uuids)
        # for instance in instances:
        #     desktop_uuids.append(instance.desktop_uuid)

        desktop_groups = db_api.get_personal_desktop_all_by_uuids(desktop_uuids)
        _groups = list()
        for desktop in desktop_groups:
            _d = {
                "uuid": desktop.uuid,
                "name": desktop.name,
                "desc": desktop.template.desc,
                "maintenance": desktop.maintenance,
                "order_num": desktop.order_num,
                "os_type": desktop.os_type
            }
            _groups.append(_d)

        _groups = sorted(_groups, key=lambda _groups: _groups['order_num'])
        logger.info("person terminal desktop group list: %s"% _groups)
        return build_result("Success", _groups)

    def edu_desktop_groups(self, data):
        """ 教学桌面组列表 """
        logger.debug("get education desktop info, terminal_id:%s, terminal_ip:%s",
                     data.get("terminal_id", 0), data.get("terminal_ip", ""))
        terminal_id = data.get("terminal_id", 0)
        if not terminal_id:
            logger.error("terminal id param error: %s"% terminal_id)
            return build_result("ParamError")

        terminal_ip = data.get("terminal_ip", "")
        if not is_ip_addr(terminal_ip):
            logger.error("terminal edu desktop group info error, %s not ip"% terminal_ip)
            return build_result("IPAddrError", ipaddr=terminal_ip)

        groups = db_api.get_group_with_all({"group_type": constants.EDUCATION_DESKTOP})
        terminal_group = None
        for group in groups:
            if group.start_ip and group.end_ip:
                if terminal_ip in find_ips(group.start_ip, group.end_ip):
                    terminal_group = group
                    break

        _groups = list()
        if not terminal_group:
            logger.error("terminal group not exist: %s"% terminal_ip)
            return build_result("Success", _groups)

        logger.debug("get education desktop terminal ip: %s, terminal_group: %s", terminal_ip, terminal_group.uuid)
        terminal_id = int(terminal_id)
        # 查找分组
        desktops = db_api.get_desktop_with_all({"group_uuid": terminal_group.uuid, "active": True})
        logger.debug("get education desktop terminal ip: %s, desktops_len: %s", terminal_ip, len(desktops))
        for desktop in desktops:
            # 判断是否总数大于序号
            if desktop.instance_num < terminal_id:
                continue

            _d = {
                "uuid": desktop.uuid,
                "name": desktop.name,
                "desc": desktop.template.desc,
                "active": desktop.active,
                "order_num": desktop.order_num,
                "os_type": desktop.os_type
            }
            _groups.append(_d)

        _groups = sorted(_groups, key=lambda _groups: _groups['order_num'])
        logger.debug("edu terminal_ip %s desktop group list: %s" % (terminal_ip, _groups))
        return build_result("Success", _groups)

    def person_instance(self, data):
        """ 个人桌面的详情 """
        session_id = data.get("session_id", "")
        desktop_uuid = data.get("desktop_uuid", "")
        desktop_name = data.get("desktop_name", "")
        auth_info = LicenseManager().get_auth_info()
        # 0-过期 1-宽限期 2-试用期 3-正式版
        # if 0 == auth_info.get('auth_type') or (1 == auth_info.get('auth_type') and auth_info.get('delay_days', 0) == 0)\
        #         or (2 == auth_info.get('auth_type') and auth_info.get('expire_time', 0) == 0):
        if auth_info.get("auth_type", 0) == 0:
            return build_result("AuthExpired")
        if self.get_links_num() >= auth_info.get('vdi_size', 0):
            return build_result("AuthSizeExpired")
        # 判断用户的登录状态
        session = db_api.get_group_user_session_first({"session_id": session_id})
        if not session:
            logger.error("terminal user query desktop group error: %s not exist" % session_id)
            return build_result("TerminalUserLogout")

        user = db_api.get_group_user_with_first({"uuid": session.user_uuid})
        if not user:
            logger.error("terminal user query desktop group error: %s not exist" % session.user_uuid)
            return build_result("TerminalUserNotExistError")

        if not user.enabled:
            logger.error("terminal user query desktop group error: %s is unenabled" % user.user_name)
            return build_result("TerminalUserUnenabledError")

        desktop_group = db_api.get_personal_desktop_with_first({"uuid": desktop_uuid})
        if not desktop_group:
            logger.error("person desktop not exist: %s" % desktop_uuid)
            return build_result("DesktopNotExist", name=desktop_name)

        # 查找当前用户分配的随机及静态桌面
        instances = list()
        # 静态桌面
        static_instances = db_api.get_instance_with_all({"user_uuid": user.uuid})
        for obj in static_instances:
            instances.append(obj)

        random_instances = db_api.get_user_random_instance_with_all({"user_uuid": user.uuid})
        for obj in random_instances:
            instances.append(obj.instance)

        # 查找桌面的spice链接状态
        host_spice_ports = dict()
        current_instance = None
        for instance in instances:
            host_ip = instance.host.ip
            if host_ip not in host_spice_ports:
                host_spice_ports[host_ip] = []
            if instance.spice_port:
                host_spice_ports[host_ip].append(str(instance.spice_port))
            if instance.desktop_uuid == desktop_uuid:
                current_instance = instance

        # 获取所有个人桌面的链接状态
        ret = self.get_spice_link(host_spice_ports)
        if current_instance:
            host_ip = current_instance.host.ip
            spice_port = current_instance.spice_port
            if spice_port and ret.get(host_ip, {}).get(spice_port):
                logger.info("terminal user request the same instance: user %s, desktop %s", user.uuid, desktop_uuid)
                instance_info = current_instance.instance_base_info()
                instance_info.update({"os_type": desktop_group.os_type})
                return build_result("Success", instance_info)
            else:
                # 如果是随机桌面，需要释放
                if desktop_group.desktop_type == constants.RANDOM_DESKTOP:
                    for _obj in random_instances:
                        if _obj.instance_uuid == current_instance.uuid:
                            _obj.soft_delete()
                            break
                    current_instance.allocated = 0
                    current_instance.soft_update()

        # 判断已链接数是否大于等于2
        count = 0
        for k, v in ret.items():
            for i, j in v.items():
                if j:
                    count += 1
        if count >= 2:
            logger.error("user %s person desktop instance much 2", user.uuid)
            return build_result("TerminalPersonalInstanceNumError")

        # 如果桌面组状态为维护
        if desktop_group.maintenance:
            logger.error("person desktop is maintenance: %s", desktop_uuid)
            return build_result("TerminalPersonMaintenance")

        subnet = db_api.get_subnet_by_uuid(desktop_group.subnet_uuid)
        # if not subnet:
        #     logger.error("person instance start error: not subnet %s" % desktop_group.subnet_uuid)
        #     return build_result("TerminalPersonStartError")
        # 启动桌面
        controller = BaseController()
        template = db_api.get_instance_template(desktop_group.template_uuid)
        sys_base, data_base = controller._get_storage_path_with_uuid(template.sys_storage,
                                                                     template.data_storage)
        if desktop_group.desktop_type == constants.RANDOM_DESKTOP:
            # 随机桌面
            instance = db_api.get_instance_by_desktop_first_alloc(desktop_uuid)
            if not instance:
                logger.error("person desktop not instance to alloc")
                return build_result("TerminalPersonInstanceNotAlloc")

            ret = controller.create_instance(desktop_group, subnet, instance, sys_base, data_base)
            if ret.get('code') != 0:
                logger.error("person instance start error: %s", instance.uuid)
                return build_result("TerminalPersonStartError")

            # 记录数据库
            instance_binds = db_api.get_user_random_instance_with_all({"instance_uuid": instance.uuid})
            # 清除其他绑定关系
            for random_ins in random_instances:
                if random_ins.desktop_uuid == desktop_uuid:
                    instance = random_ins.instance
                    instance.allocated = 0
                    instance.terminal_mac = None
                    instance.link_time = None
                    instance.soft_update()
                    random_ins.soft_delete()
            for random_ins in instance_binds:
                random_ins.soft_delete()

            values = {
                "uuid": create_uuid(),
                "desktop_uuid": desktop_uuid,
                "user_uuid": user.uuid,
                "instance_uuid": instance.uuid
            }
            db_api.create_user_random_instance(values)
            instance.allocated = 1
            instance.link_time = datetime.now()
            instance.spice_link = 1
            instance.terminal_mac = user.mac
            instance.soft_update()
            logger.info("random person instance start succes: %s", instance.uuid)
        else:
            static_instance_bind = db_api.get_instance_with_first({"desktop_uuid": desktop_uuid, "user_uuid": user.uuid})
            if not static_instance_bind:
                logger.error("static person desktop not bind: desktop group %s, user %s", desktop_uuid, user.uuid)
                return build_result("TerminalPersonInstanceNotAlloc")
            instance = static_instance_bind
            ret = controller.create_instance(desktop_group, subnet, instance, sys_base, data_base)
            if ret.get('code') != 0:
                logger.error("person instance start error: %s", instance.uuid)
                return build_result("TerminalPersonStartError")
            logger.info("static person instance start succes: %s", instance.uuid)
            instance.link_time = datetime.now()
            instance.terminal_mac = user.mac
            instance.spice_link = 1
            instance.soft_update()
        data = {
            "spice_host": instance.host.ip,
            "spice_token": instance.spice_token,
            "spice_port": instance.spice_port,
            "name": instance.name,
            "uuid": instance.uuid,
            "os_type": desktop_group.os_type
        }
        edu_instance = db_api.get_instance_first(
            {"terminal_mac": user.mac, "classify": constants.EDUCATION_DESKTOP, "status": constants.STATUS_ACTIVE})
        if edu_instance:
            desktop = db_api.get_desktop_by_uuid(edu_instance.desktop_uuid)
            controller.stop_instance(edu_instance, desktop)

        return build_result("Success", data)

    def person_instance_close(self, data):
        """ 关闭个人终端的所有桌面 """
        session_id = data.get("session_id", "")
        session = db_api.get_group_user_session_first({"session_id": session_id})
        if not session:
            logger.error("terminal user query desktop group error: %s not exist" % session_id)
            return build_result("TerminalUserLogout")

        user = db_api.get_group_user_with_first({"uuid": session.user_uuid})
        if not user:
            logger.error("terminal user query desktop group error: %s not exist" % session.user_uuid)
            return build_result("TerminalUserNotExistError")

        if not user.enabled:
            logger.error("terminal user query desktop group error: %s is unenabled" % user.user_name)
            return build_result("TerminalUserUnenabledError")

        contraller = BaseController()
        random_instances = db_api.get_user_random_instance_with_all({"user_uuid": user.uuid})

        static_instances = db_api.get_instance_with_all({"classify": constants.PERSONAL_DEKSTOP, "user_uuid": user.uuid})
        for i in random_instances:
            desktop = i.desktop
            instance = i.instance
            # sys_restore = desktop.sys_restore
            if not contraller.stop_instance(instance, desktop):
                logger.error("terminal close personal instance fail: %s"% instance.uuid)
            instance.allocated = 0

        desktop_uuids = list()
        for instance in static_instances:
            desktop_uuid = instance.desktop_uuid
            if desktop_uuid not in desktop_uuids:
                desktop_uuids.append(desktop_uuid)
        desktop_dict = dict()
        desktops = db_api.get_personal_desktop_all_by_uuids(desktop_uuids)
        for desktop in desktops:
            desktop_dict[desktop.uuid] = desktop

        for instance in static_instances:
            desktop = desktop_dict[instance.desktop_uuid]
            if not contraller.stop_instance(instance, desktop):
                logger.error("terminal close personal instance fail: %s" % instance.uuid)

        logger.info("terminal close personal instance success !!!")
        return build_result("Success")

    def get_links_num(self):
        count = 0
        instances = db_api.get_instance_with_all({})
        rep_data = dict()
        for instance in instances:
            host_ip = instance.host.ip
            if host_ip not in rep_data:
                rep_data[host_ip] = list()
            if instance.spice_port:
                rep_data[host_ip].append(instance.spice_port)

        for k, v in rep_data.items():
            ports = ",".join(list(set(v)))
            if ports:
                ports_status = monitor_post(k, "/api/v1/monitor/port_status", {"ports": ports})
            else:
                ports_status = {}
            if ports_status.get('code', -1) != 0:
                logger.error("from node %s get port status:%s", k, ports_status)
                continue
            logger.info("from node %s get port status:%s", k, ports_status)
            for port, link in ports_status.get("data", {}).items():
                if link:
                    count += 1
        logger.info("the instance link count:%s", count)
        return count

    def education_instance(self, data):
        """教学桌面详情"""
        logger.info("open the education desktop, desktop_uuid:%s, terminal_id:%s, terminal_ip:%s",
                    data.get("desktop_uuid", ""), data.get("terminal_id", 0), data.get("ip", ""))
        desktop_uuid = data.get("desktop_uuid", "")
        terminal_id = data.get("terminal_id", 0)
        terminal_mac = data.get("mac", "")
        terminal_ip = data.get("ip", "")
        auth_info = LicenseManager().get_auth_info()
        # 0-过期 1-宽限期 2-试用期 3-正式版
        # if 0 == auth_info.get('auth_type') or (1 == auth_info.get('auth_type') and auth_info.get('delay_days', 0) == 0)\
        #         or (2 == auth_info.get('auth_type') and auth_info.get('expire_time', 0) == 0):
        if auth_info.get("auth_type", 0) == 0:
            return build_result("AuthExpired")
        if self.get_links_num() >= auth_info.get('vdi_size', 0):
            return build_result("AuthSizeExpired")
        # # 授权个数控制，使用redis，配合后台监控线程每8s重置一下已连接个数
        # redis = yzyRedis()
        # try:
        #     redis.init_app()
        #     self.check_auth_num(redis, auth_info.get('vdi_size', 0))
        # except Exception as e:
        #     logger.error("check auth error:%s", e)
        #     return build_result("AuthSizeExpired")
        # 根据桌面组和终端序号查到桌面
        instance = db_api.get_instance_with_first({"desktop_uuid": desktop_uuid, "terminal_id": terminal_id,
                                                   "classify": constants.EDUCATION_DESKTOP})
        if not instance:
            logger.error("education instance not exist: %s %s", desktop_uuid, terminal_id)
            return build_result("TerminalEduInstanceNotAlloc")

        desktop_group = db_api.get_desktop_by_uuid(desktop_uuid)
        subnet = db_api.get_subnet_by_uuid(desktop_group.subnet_uuid)
        if not subnet:
            logger.error("person instance start error: not subnet %s", desktop_group.subnet_uuid)
            return build_result("TerminalEducationStartError")

        host_ip = instance.host.ip
        try:
            # 并发数控制
            redis = yzyRedis()
            try:
                redis.init_app()
                self.check_concurrency(redis, host_ip, terminal_id, desktop_group.ram)
            except Exception as e:
                logger.error("allocate resource error:%s, instance:%s, return", e, instance.uuid)
                return build_result("ResourceAllocateError")

            # 如果已经链接，判断mac地址是否相同
            spice_port = instance.spice_port
            # ret = dict()
            online = False
            if spice_port:
                ret = self.get_spice_link({host_ip: [str(spice_port)]})
                if ret.get(host_ip, {}).get(str(spice_port)):
                    online = True

            controller = BaseController()
            template = db_api.get_instance_template(desktop_group.template_uuid)
            sys_base, data_base = controller._get_storage_path_with_uuid(template.sys_storage,
                                                                         template.data_storage)
            logger.info("get education instance, desktop_name:%s, terminal_id:%s, terminal_mac:%s",
                        desktop_group.name, terminal_id, terminal_mac)
            if online:
                # spice_port有链接并且有terminal_mac才是真正有终端连接
                # spice_port有链接(但实际SPICE_PORT被其他桌面复用), instance.terminal_mac 为空的情况，是需要正常启动
                if (not instance.terminal_mac) or (instance.terminal_mac and instance.terminal_mac == terminal_mac):
                    # mac相同，关闭当前开启
                    ins_ret = controller.create_instance(desktop_group, subnet, instance,
                                                         sys_base, data_base, terminal=True)
                    if ins_ret.get('code') != 0:
                        logger.error("education instance start error: %s", instance.uuid)
                        return build_result("TerminalEducationStartError")

                else:
                    # mac不相同，提示终端冲突
                    logger.error("education instance online terminal mac: %s, mac: %s", instance.terminal_mac, terminal_mac)
                    return build_result("TerminalEduInstanceRepeatError")

            else:
                # 不在线
                logger.info("eduction instance not link, uuid:%s, name:%s", instance.uuid, instance.name)
                ins_ret = controller.create_instance(desktop_group, subnet, instance,
                                                     sys_base, data_base, terminal=True)
                if ins_ret.get('code') != 0:
                    logger.error("education instance start error: %s", instance.uuid)
                    return build_result("TerminalEducationStartError")

            instance.terminal_mac = terminal_mac
            instance.terminal_ip = terminal_ip
            instance.spice_link = 1
            instance.link_time = datetime.now()
            instance.soft_update()
            data = {
                "spice_host": instance.host.ip,
                "spice_token": ins_ret['data'].get('spice_token', ''),
                "spice_port": ins_ret['data'].get('spice_port', ''),
                "name": instance.name,
                "uuid": instance.uuid,
                "os_type": desktop_group.os_type
            }
            return build_result("Success", data)
        except Exception as e:
            logger.exception("open education desktop error:%s", e)
            raise e
        finally:
            try:
                redis.rds.hdel(constants.PARALELL_QUEUE, terminal_id)
            except:
                pass

    def close_education_instance(self, data):
        """ 关闭教学桌面 """
        terminal_mac = data.get("mac", "")
        instances = db_api.get_instance_with_all({"terminal_mac": terminal_mac})

        desktop_uuids = list()
        for instance in instances:
            desktop_uuid = instance.desktop_uuid
            if desktop_uuid not in desktop_uuids:
                desktop_uuids.append(desktop_uuid)

        contraller = BaseController()
        desktop_dict = dict()
        desktops = db_api.get_desktop_with_all_by_uuids(desktop_uuids)
        for desktop in desktops:
            desktop_dict[desktop.uuid] = desktop

        for instance in instances:
            desktop = desktop_dict[instance.desktop_uuid]
            if not contraller.stop_instance(instance, desktop):
                logger.error("terminal close personal instance fail: %s" % instance.uuid)
        return build_result("Success")

    def terminal_instance_match(self, data):
        """ 所有终端ip对应的桌面ip"""
        # ips = data.get("ips", "")
        # ips = ips.split(",")
        # terminal_ips = list()
        # for i in ips:
        #     if not is_ip_addr(i):
        #         continue
        #     terminal_ips.append(i)
        # items = {}
        groups = db_api.get_group_with_all({"group_type": constants.EDUCATION_DESKTOP})
        group_dict = dict()
        for group in groups:
            start_ip = group.start_ip
            end_ip = group.end_ip
            uuid = group.uuid
            group_dict[uuid] = find_ips(start_ip, end_ip)

        desktop_group_dict = {}
        desktops = db_api.get_desktop_with_all_by_groups(list(group_dict.keys()))
        for i in desktops:
            desktop_group_dict[i.uuid] = i.group_uuid

        terminals = list()
        for i in data:
            terminal_ip = i["terminal_ip"]
            if not is_ip_addr(terminal_ip):
                continue
            for uuid, ips in group_dict.items():
                # start_ip = group.start_ip
                # end_ip = group.end_ip
                # if find_ips(start_ip, end_ip)
                if terminal_ip in ips:
                    i["group_uuid"] = uuid
                    terminals.append(i)
                    break

        # 找到所有云桌面
        ret = list()
        instances = db_api.get_instance_with_all({"classify": constants.EDUCATION_DESKTOP})
        for terminal in terminals:
            group_uuid = terminal["group_uuid"]
            terminal_id = terminal["terminal_id"]
            for instance in instances:
                desktop_uuid = instance.desktop_uuid
                _group_uuid = desktop_group_dict.get(desktop_uuid)
                _terminal_id = instance.terminal_id
                _instance_ip = instance.ipaddr
                if _group_uuid == group_uuid and terminal_id == _terminal_id and _instance_ip:
                    terminal["desktop_ip"] = _instance_ip
                    ret.append(terminal)
                    break

        return build_result("Success", ret)

    def terminal_instance_close(self, data):
        """
        终端发起单个桌面关闭请求
        {
            "uuid": "xxxxxxxx"
        }
        :param data:
        :return:
        """
        instance_uuid = data.get("desktop_uuid", "")
        instance = db_api.get_instance_with_first({"uuid": instance_uuid})
        if not instance:
            logger.error("terminal close instance error: %s not exist"% instance_uuid)
            return build_result("TerminalInstanceNotExist")

        desktop_uuid = instance.desktop_uuid
        desktop_type = instance.classify
        if desktop_type == constants.EDUCATION_DESKTOP:
            desktop = db_api.get_desktop_by_uuid(desktop_uuid)
        else:
            desktop = db_api.get_personal_desktop_with_first({"uuid": desktop_uuid})
        contraller = BaseController()
        sys_restore = desktop.sys_restore
        if not contraller.stop_instance(instance, desktop):
            logger.error("terminal close instance error: %s close fail"% instance_uuid)
            return build_result("TerminalInstanceCloseFail")
        logger.info("terminal close instance success ! %s"% instance_uuid)
        return build_result("Success")

    def terminal_group_list(self, data):
        """
        终端分组
        获取所有分组
        :param data:
        :return:
        """
        items = dict()
        ret = list()
        groups = db_api.get_group_with_all(items)
        for group in groups:
            _d = dict()
            _d["uuid"] = group.uuid
            _d["name"] = group.name
            _d["start_ip"] = group.start_ip
            _d["end_ip"] = group.end_ip
            _d["group_type"] = group.group_type
            ret.append(_d)

        return build_result("Success", ret)

    def education_group(self, data):
        terminal_ip = data.get("terminal_ip", "")
        if not is_ip_addr(terminal_ip):
            return build_result("ParamError")
        _group = None
        edu_groups = db_api.get_group_with_all({"group_type": constants.EDUCATION_DESKTOP})
        for group in edu_groups:
            start_ip = group.start_ip
            end_ip = group.end_ip
            if terminal_ip in find_ips(start_ip, end_ip):
                _group = group
                break
        if not _group:
            return build_result("Success")
        ret = {
            "name": _group.name,
            "uuid": _group.uuid,
        }
        return build_result("Success", ret)

    def person_group(self):
        person_groups = db_api.get_group_with_all({"group_type": constants.PERSONAL_DEKSTOP})
        ret = {
            "groups": [x.uuid for x in person_groups]
        }
        return build_result("Success", ret)











