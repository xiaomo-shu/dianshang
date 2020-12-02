import os
import requests
import inspect
import traceback
import logging
import string
import copy
import hashlib
from threading import  Thread
from functools import wraps
from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES
from yzy_server.database import apis as db_api
from common import cmdutils, constants
from common.config import SERVER_CONF
from common.utils import compute_post

BEGIN = 'begin'
END = 'end'
RUNNING = 'running'
ERROR = 'error'

logger = logging.getLogger(__name__)

def abort_error(code, message=None, **kwargs):
    if message is None:
        message = HTTP_STATUS_CODES.get(code, '')

    response = jsonify(code=code, msg=message, data={}, **kwargs)
    response.status_code = code
    return response


def insert_operation_log(msg, result, log_user=None):
    if log_user is None:
        uid = None
        uname = "admin"
        user_ip = ''
    else:
        uid = log_user["id"]
        uname = log_user["user_name"]
        user_ip = log_user["user_ip"]
    values = {
        "content": msg,
        "result": result,
        "user_id": uid,
        "user_name": uname,
        "user_ip": user_ip
    }
    db_api.add_operation_log(values)


def operation_record(msg=""):
    """
    记录操作日志
    :param msg: 操作日志内容，如果操作日志中包含参数，则使用{参数名}格式的字符串，例如：
            添加资源池{pool_name}，pool_name是函数中的某个参数，如果pool_name包含在字典
            中，则是{pool[pool_name]}这种格式
    :return:
    """
    def wrapper1(func):
        @wraps(func)
        def wrapper2(*args, **kwargs):
            arg_dict = inspect.getcallargs(func, *args, **kwargs)
            ex = None
            ret = None
            result = 'OK'
            try:
                ret = func(*args, **kwargs)
                data = ret.get_json()
                if not data.get('code') == 0:
                    result = data.get('msg', 'unknown error')
            except Exception as ex:
                result = str(ex)
                traceback.print_exc()
            if msg == "":
                logmsg = "Call {} {}".format(func.__name__, result)
            else:
                logmsg = msg.format(**arg_dict)
            user = arg_dict.get('log_user', None)
            try:
                insert_operation_log(logmsg, result, user)
            except:
                pass

            if ex is not None:
                raise ex
            return ret
        return wrapper2
    return wrapper1


class HttpClient:
    def __init__(self, app=None):
        self.app = app
        self.command_data = {}
        self.data = {}
        self.json_data = {}

    def set_command(self, command, handler, data):
        if not isinstance(data, dict):
            raise Exception("the data is not dict")

        _d = {
            "command": command,
            "handler": handler,
            "data": data
        }
        self.command_data = _d

    def set_data(self, data):
        if not isinstance(data, dict):
            raise Exception("the data is not dict")
        self.data = data

    def set_json(self, data):
        if not isinstance(data, dict):
            raise Exception("the data is not dict")
        self.json_data = data

    def compute_post(self):
        url = self.app.config[""]
        response = requests.post()


class TaskBase(object):

    def add_task(self, task_id, status, context, progress=0, image_id=None, host_uuid=None, version=0):
        values = {
            'task_id': task_id,
            'status': status,
            'context': context,
            'progress': progress,
            'image_id': image_id if image_id else '',
            'host_uuid': host_uuid,
            'version': version
        }
        step = db_api.get_task_step(task_id)
        values['step'] = step + 1
        if status == BEGIN or status == RUNNING:
            values['progress'] = values['step'] * 4 if values['step'] * 4 else 98
            if values['progress'] >= 100:
                values['progress'] = 99
        elif status == ERROR:
            values['progress'] = values['step'] * 4
            if values['progress'] >= 100:
                values['progress'] = 99
        else:
            values['progress'] = 100
        db_api.add_task_info(values)


class Task(TaskBase):
    def __init__(self, image_id="", host_uuid='', version=0):
        super(Task, self).__init__()
        self.image_id = image_id
        self.host_uuid = host_uuid
        self.version = version

    def _format_context(self, context, *args):
        try:
            message = context % args
        except (ValueError, TypeError):
            message = context.format(*args)
        return message

    def begin(self, task_id, context, *args):
        context = self._format_context(context, *args)
        self.add_task(task_id, BEGIN, context, image_id=self.image_id, host_uuid=self.host_uuid, version=self.version)

    def next(self, task_id, context, *args):
        context = self._format_context(context, *args)
        self.add_task(task_id, RUNNING, context, image_id=self.image_id, host_uuid=self.host_uuid, version=self.version)

    def end(self, task_id, context, *args):
        context = self._format_context(context, *args)
        self.add_task(task_id, END, context, image_id=self.image_id, host_uuid=self.host_uuid, version=self.version)

    def error(self, task_id, context, *args):
        context = self._format_context(context, *args)
        self.add_task(task_id, ERROR, context, image_id=self.image_id, host_uuid=self.host_uuid, version=self.version)


def get_host_and_peer_ip(ha_info_obj):
    """
    获取主控节点（VIP所在节点）的IP、备控节点的IP和uuid。
    通过此方法能够找出当前真实的主控节点，避免数据库中节点角色可能更新不及时导致的错误。
    :param ha_info_obj:
    :return:
    """
    try:
        ips = (ha_info_obj.master_ip, ha_info_obj.backup_ip)
        # 确定peer（无VIP节点）的ip和node_uuid
        # 由于前端调VIP的yzy-web，而yzy-web只会调本地的yzy-server，则本节点一定是vip_host
        code, out = cmdutils.run_cmd("ip addr |grep {ip}".format(ip=ips[0]), ignore_log=True)
        if code == 0 and ips[0] in out:
            vip_host_ip = ips[0]
            peer_host_ip = ips[1]
            peer_uuid = ha_info_obj.backup_uuid
        else:
            vip_host_ip = ips[1]
            peer_host_ip = ips[0]
            peer_uuid = ha_info_obj.master_uuid
        # logger.info("vip_host_ip: %s, peer_host_ip: %s" % (vip_host_ip, peer_host_ip))
        return vip_host_ip, peer_host_ip, peer_uuid
    except Exception as e:
        logger.exception("%s", str(e), exc_info=True)


def get_voi_ha_backup_network_info(template_obj, backup_uuid, template_uuid=None):
    """
    获取备控节点的网络信息，用于在备控上同步创建VOI模板
    :param template_obj:
    :param backup_uuid:
    :param template_uuid:
    :return:
    """
    try:
        if template_uuid:
            template_obj = db_api.get_voi_instance_template(template_uuid)
        network_info = list()
        net = db_api.get_interface_by_network(template_obj.network_uuid, backup_uuid)
        vif_info = {
            "uuid": net.YzyNetworks.uuid,
            "vlan_id": net.YzyNetworks.vlan_id,
            "interface": net.nic,
            "bridge": constants.BRIDGE_NAME_PREFIX + net.YzyNetworks.uuid[:constants.RESOURCE_ID_LENGTH]
        }
        _d = {
            "fixed_ip": template_obj.bind_ip,
            "mac_addr": template_obj.mac,
            "bridge": vif_info["bridge"],
            "port_id": template_obj.port_uuid,
            "vif_info": vif_info
        }
        if template_obj.subnet_uuid:
            subnet = db_api.get_subnet_by_uuid(template_obj.subnet_uuid)
            _d["netmask"] = subnet.netmask
            _d["gateway"] = subnet.gateway
            if subnet.dns1:
                _d["dns_server"] = [subnet.dns1]
            if subnet.dns2:
                _d["dns_server"].append(subnet.dns2)
        network_info.append(_d)
        return network_info
    except Exception as e:
        logger.exception("%s", str(e), exc_info=True)


def get_voi_ha_domain_info(template_obj, backup_uuid):
    """
    获取定义VOI模板虚拟机所需的信息
    :param template_obj:
    :param backup_uuid:
    :return:
    """
    try:
        info = {
            "xml_file": "/etc/libvirt/qemu/" + constants.VOI_BASE_NAME % template_obj.id + ".xml",
            "instance": {"uuid": template_obj.uuid, "name": template_obj.name},
            "network_info": get_voi_ha_backup_network_info(template_obj, backup_uuid)
        }

        zm = string.ascii_lowercase
        devices = db_api.get_voi_devices_with_all({"instance_uuid": template_obj.uuid})
        kvm_disks = [{"dev": dev.device_name} for dev in devices]
        # 确保添加两个cdrom
        for i in range(len(kvm_disks) + 2):
            for disk in kvm_disks:
                index = zm.index(disk['dev'][-1])
                if index == i:
                    break
            else:
                kvm_disks.append({
                    "bus": "sata",
                    "dev": "sd%s" % zm[i],
                    "type": "cdrom",
                    "path": ""
                })
        info["disk_info"] = kvm_disks
        return info
    except Exception as e:
        logger.exception("%s", str(e), exc_info=True)


def get_template_storage_path(node_uuid):
    """
    获取模板所在节点的存储路径
    :param node_uuid:
    :return:
    """
    try:
        template_sys = db_api.get_template_sys_storage(node_uuid)
        template_data = db_api.get_template_data_storage(node_uuid)
        if not template_sys:
            sys_base = constants.DEFAULT_SYS_PATH
        else:
            sys_base = template_sys.path
        sys_path = os.path.join(sys_base, 'instances')
        if not template_data:
            data_base = constants.DEFAULT_DATA_PATH
        else:
            data_base = template_data.path
        data_path = os.path.join(data_base, 'datas')
        return sys_path, data_path
    except Exception as e:
        logger.exception("%s", str(e), exc_info=True)
        return constants.DEFAULT_SYS_PATH, constants.DEFAULT_DATA_PATH


def get_template_images(template_uuid, master_uuid, sys_base=None, data_base=None, download_base_disk=True, download_torrent=True):
    """
    获取需要同步的VOI模板的磁盘信息
    :param template_uuid:
    :param master_uuid:
    :param sys_base:
    :param data_base:
    :param download_base_disk:
    :param download_torrent:
    :return:
    """
    try:
        logger.debug("template_uuid: %s, master_uuid: %s, sys_base: %s, data_base: %s, download_base_disk: %s, download_torrent: %s",
                     template_uuid, master_uuid, sys_base, data_base, download_base_disk, download_torrent)
        path_list = list()
        if not sys_base or not data_base:
            sys_base, data_base = get_template_storage_path(master_uuid)
        devices = db_api.get_voi_devices_with_all({"instance_uuid": template_uuid})
        operates = db_api.get_voi_operate_with_all({"template_uuid": template_uuid, "exist": True})
        for disk in devices:
            base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
            # base盘
            backing_file = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME,
                                        constants.VOI_BASE_PREFIX % str(0) + disk.uuid)
            image_path_list = [backing_file]
            # 差异盘
            for operate in operates:
                image_path = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME,
                                          constants.VOI_BASE_PREFIX % str(operate.version) + disk.uuid)
                if os.path.exists(image_path):
                    image_path_list.append(image_path)
            # 实际启动盘
            _d = {
                "disk_path": "%s/%s%s" % (base_path, constants.VOI_FILE_PREFIX, disk['uuid']),
                "image_path_list": image_path_list,
                "download_base": download_base_disk
            }
            # 种子文件
            if download_torrent:
                _d["torrent_path_list"] = [path + ".torrent" for path in image_path_list]
            path_list.append(_d)
        logger.debug("path_list: %s", path_list)
        return path_list
    except Exception as e:
        logger.exception("%s", str(e), exc_info=True)
        return []


def notify_backup_sync_voi(master_ip, backup_ip, paths, voi_template_list=None):
    """
    通知备控同步VOI模板的磁盘文件
    :param master_ip:
    :param backup_ip:
    :param paths:
    :param voi_template_list:
    :return:
    """
    try:
        bind = SERVER_CONF.addresses.get_by_default('server_bind', '')
        if bind:
            port = bind.split(':')[-1]
        else:
            port = constants.SERVER_DEFAULT_PORT
        endpoint = "http://%s:%s" % (master_ip, port)
        command_data = {
            "command": "ha_sync_voi",
            "handler": "NodeHandler",
            "data": {
                "url": constants.HA_SYNC_URL,
                "endpoint": endpoint,
                "paths": paths,
                "voi_template_list": voi_template_list
            }
        }
        logger.info("start to sync the file %s to backup node %s", ','.join(paths), backup_ip)
        rep_json = compute_post(backup_ip, command_data, timeout=600)
        if rep_json.get("code", -1) != 0:
            logger.error("sync the file %s to backup node %s failed: %s", ','.join(paths), backup_ip, rep_json["msg"])
        else:
            logger.info("sync the file %s to backup node %s success: %s", ','.join(paths), backup_ip)
    except Exception as e:
        logger.exception("%s", str(e), exc_info=True)


def sync_func_to_ha_backup(func, *args, **kwargs):
    """
    如果启用了HA，在备控上也同步执行对VOI模板的操作，未启用则不同步
    :param func:
    :param args:
    :param kwargs:
    :return:
    """
    try:
        ha_info_obj = db_api.get_ha_info_first()
        if ha_info_obj:
            vip_host_ip, peer_host_ip, peer_uuid = get_host_and_peer_ip(ha_info_obj)
            use_thread = kwargs.pop("use_thread", True)
            logger.info("sync_func: %s, backup node: %s, use_thread: %s, args: %s, kwargs: %s",
                         func, peer_host_ip, use_thread, args, kwargs)
            if use_thread:
                new_args = [peer_host_ip]
                new_args.extend(args)
                task = Thread(target=func, args=new_args, kwargs=kwargs)
                task.start()
            else:
                func(peer_host_ip, *args, **kwargs)
    except Exception as e:
        logger.exception("%s", str(e), exc_info=True)


def sync_compute_post_to_ha_backup_with_network_info(command_data, timeout=120):
    """
    start InstanceHandler 和 create VoiHandler 这两个compute层接口需要提供网络信息。
    当在备控上同步调用这两个接口时，必须将command_data中的network_info替换为备控的网络信息。
    :param command_data:
    :param timeout:
    :return:
    """
    try:
        # 如果启用了HA，在备控上也同步执行对VOI模板的操作，未启用则不同步
        # 其中，network_info必须替换为备控节点的
        ha_info_obj = db_api.get_ha_info_first()
        if ha_info_obj:
            command_data_copy = copy.deepcopy(command_data)
            command_data_copy["data"]["network_info"] = get_voi_ha_backup_network_info(
                None, ha_info_obj.backup_uuid, template_uuid=command_data_copy["data"]["instance"]['uuid'])
            vip_host_ip, peer_host_ip, peer_uuid = get_host_and_peer_ip(ha_info_obj)
            logger.info("sync_func: %s, backup node: %s, use_thread: %s, command_data: %s, timeout: %s",
                         compute_post, peer_host_ip, True, command_data_copy, timeout)
            kwargs = {
                "ipaddr": peer_host_ip,
                "data": command_data_copy,
                "timeout": timeout
            }
            task = Thread(target=compute_post, kwargs=kwargs)
            task.start()
    except Exception as e:
        logger.exception("%s", str(e), exc_info=True)


def sync_voi_file_to_ha_backup_node(template_uuid, sys_base, data_base, download_base_disk, use_thread=True):
    """
    如果启用了HA，把VOI模板磁盘文件同步给备控，未启用则不同步
    :param template_uuid:
    :param sys_base:
    :param data_base:
    :param download_base_disk:
    :param use_thread:
    :return:
    """
    try:
        ha_info_obj = db_api.get_ha_info_first()
        if ha_info_obj:
            voi_template_list = get_template_images(template_uuid, "", sys_base, data_base, download_base_disk, download_torrent=False)
            vip_host_ip, peer_host_ip, peer_uuid = get_host_and_peer_ip(ha_info_obj)
            logger.info("sync_file: %s, backup node: %s, use_thread: %s", voi_template_list, peer_host_ip, use_thread)
            if use_thread:
                task = Thread(target=notify_backup_sync_voi, args=(vip_host_ip, peer_host_ip, [], voi_template_list,))
                task.start()
            else:
                notify_backup_sync_voi(vip_host_ip, peer_host_ip, [], voi_template_list)
    except Exception as e:
        logger.exception("%s", str(e), exc_info=True)


def sync_torrent_to_ha_backup_node(torrent_paths):
    """
    如果启用了HA，把VOI模板的种子文件同步给备控，未启用则不同步
    :param torrent_paths:
    :return:
    """
    try:
        ha_info_obj = db_api.get_ha_info_first()
        if ha_info_obj:
            vip_host_ip, peer_host_ip, peer_uuid = get_host_and_peer_ip(ha_info_obj)
            logger.info("sync_torrent: %s, backup node: %s, use_thread: %s", torrent_paths, peer_host_ip, True)
            task = Thread(target=notify_backup_sync_voi, args=(vip_host_ip, peer_host_ip, torrent_paths,))
            task.start()
    except Exception as e:
        logger.exception("%s", str(e), exc_info=True)


def read_file_md5(path):
    """
    读取文件的md5值
    :param path:
    :return:
    """
    try:
        md5_sum = hashlib.md5()
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(constants.CHUNKSIZE)
                if not chunk:
                    break
                md5_sum.update(chunk)
        return md5_sum.hexdigest()
    except Exception as e:
        logger.exception("read_file_md5 error: %s", str(e), exc_info=True)
        return ""


def ha_sync_file(paths):
    """
    如果启用了HA，把指定文件（例如：ISO库文件，数据库备份文件）同步给备控，未启用则不同步
    :param paths:
    :return:
    """
    try:
        # 如果启用了HA，把指定文件（例如：ISO库文件，数据库备份文件）同步给备控，未启用则不同步
        ha_info_obj = db_api.get_ha_info_first()
        if ha_info_obj:
            vip_host_ip, peer_host_ip, peer_uuid = get_host_and_peer_ip(ha_info_obj)
            logger.info("sync_file: %s, backup node: %s, use_thread: %s", paths, peer_host_ip, False)
            notify_backup_sync_file(vip_host_ip, peer_host_ip, paths)
    except Exception as e:
        logger.exception("%s", str(e), exc_info=True)
        
        
def notify_backup_sync_file(master_ip, backup_ip, paths, check_path=None):
    """
    通知备控同步指定文件
    :param backup_ip: 主控节点ip
    :param backup_ip: 备控节点ip
    :param paths: 需要同步的文件路径列表
    :param check_path: 如果提供此参数，则节点会检查该路径下所有不在'paths'中的文件并删除
    :return:
    """
    bind = SERVER_CONF.addresses.get_by_default('server_bind', '')
    if bind:
        port = bind.split(':')[-1]
    else:
        port = constants.SERVER_DEFAULT_PORT
    endpoint = "http://%s:%s" % (master_ip, port)
    command_data = {
        "command": "ha_sync_file",
        "handler": "NodeHandler",
        "data": {
            "paths": paths,
            "check_path": check_path,
            "endpoint": endpoint,
            "url": constants.HA_SYNC_URL,
        }
    }
    logger.info("start check sync at node %s , check_path: %s, paths: %s", backup_ip, check_path, paths)
    rep_json = compute_post(backup_ip, command_data, timeout=600)
    logger.info("finish check sync at node %s, rep_json: %s, check_path: %s, paths: %s", backup_ip, rep_json, check_path, paths)
    return rep_json