import os
import logging
import string
import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from apscheduler.triggers.date import DateTrigger
from threading import Thread
from yzy_server.extensions import db
from datetime import datetime
from yzy_server.database import apis as db_api
from yzy_server.database import models
from yzy_server.crontab_tasks import YzyAPScheduler
from common import constants
from common.errcode import get_error_result
from common.config import SERVER_CONF, FileOp
from common.utils import create_uuid, compute_post, find_ips, get_file_md5, check_node_status, single_lock
from yzy_server.utils import Task
from .desktop_ctl import BaseController, generate_mac, generate_ips


logger = logging.getLogger(__name__)


class TemplateController(BaseController):

    def _check_template_params(self, data):
        if not data:
            return False
        name = data.get('name', '')
        owner = data.get('owner_id', '')
        pool_uuid = data.get('pool_uuid', '')
        network_uuid = data.get('network_uuid', '')
        if not (name and owner and pool_uuid and network_uuid):
            return False
        logger.info("check params ok")
        return True

    def create_template(self, data, disk_generate=True):
        """
        :param data:
            {
                "name": "win7_test",
                "desc": "xxxxx",
                "owner_id": "xxxx",
                "os_type": "win7",
                "classify": 1,
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
        :return:
        """
        # 添加任务信息数据记录
        task_uuid = create_uuid()
        task_data = {
            "uuid": task_uuid,
            "task_uuid": task_uuid,
            "name": constants.NAME_TYPE_MAP[7],
            "status": constants.TASK_RUNNING,
            "type": 7
        }
        db_api.create_task_info(task_data)
        task_obj = db_api.get_task_info_first({"uuid": task_uuid})
        if not self._check_template_params(data):
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("ParamError")

        network = db_api.get_network_by_uuid(data['network_uuid'])
        if not network:
            logger.error("network: %s not exist", data['network_uuid'])
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("NetworkInfoNotExist")

        subnet_uuid = data.get('subnet_uuid', None)
        if subnet_uuid:
            subnet = db_api.get_subnet_by_uuid(data['subnet_uuid'])
            if not subnet:
                logger.error("subnet: %s not exist", data['subnet_uuid'])
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return get_error_result("SubnetNotExist")
        else:
            subnet = None

        template = db_api.get_template_with_all({'name': data['name'], 'classify': data['classify']})
        if template:
            logger.error("template: %s already exist", data['name'])
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("TemplateAlreadyExist", name=data['name'])
        image_id = data['system_disk'].get('image_id')
        if image_id:
            image = db_api.get_image_with_first({"uuid": image_id})
            if not image:
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return get_error_result("TemplateImageNotExist")
        # 如果没有指定节点，则模板默认放在主控节点
        if data.get('host_uuid', None):
            node = db_api.get_node_by_uuid(data['host_uuid'])
        else:
            node = db_api.get_controller_node()
        data['host_uuid'] = node.uuid
        if not data.get('version'):
            version = 0
        else:
            version = data['version']
        data['version'] = version
        data['status'] = "building"
        # network info
        if not subnet:
            # dhcp方式获取IP
            data['bind_ip'] = ''
        else:
            all_ips = find_ips(subnet.start_ip, subnet.end_ip)
            if not data.get('bind_ip', None):
                # 选择子网并且系统分配，模板IP从后往前取值
                all_ip_reverse = all_ips[::-1]
                education_used_ips = self.get_personal_used_ipaddr(subnet_uuid)
                for ipaddr in all_ip_reverse:
                    if ipaddr not in education_used_ips:
                        data['bind_ip'] = ipaddr
                        break
                else:
                    task_obj.update({"status": constants.TASK_ERROR})
                    task_obj.soft_update()
                    return get_error_result("IPNotEnough")
            if data['bind_ip'] not in all_ips:
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return get_error_result("IPNotInRange", ipaddr=data['bind_ip'])
        logger.info("check bind_ip info")
        sys_storage, data_storage = self._get_template_storage(node.uuid)
        if not (sys_storage and data_storage):
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("InstancePathNotExist")

        self.used_macs = self.get_used_macs()
        mac_addr = generate_mac(self.used_macs)
        data['mac'] = mac_addr
        logger.info("allocate mac info")

        port_uuid = create_uuid()
        data['port_uuid'] = port_uuid
        # 获取网络信息，保证网桥等设备存在
        net = db_api.get_interface_by_network(network.uuid, node.uuid)
        if not net:
            logger.error("node %s network info %s error", node.uuid, network.uuid)
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("NodeNetworkInfoError")

        vif_info = {
            "uuid": net.YzyNetworks.uuid,
            "vlan_id": net.YzyNetworks.vlan_id,
            "interface": net.nic,
            "bridge": constants.BRIDGE_NAME_PREFIX + net.YzyNetworks.uuid[:constants.RESOURCE_ID_LENGTH]
        }
        network_info = self.create_network_info(vif_info, port_uuid, mac_addr, subnet, data['bind_ip'])
        logger.info("get instance network info")
        if not data.get('uuid'):
            data['uuid'] = create_uuid()

        # 更新任务数据记录的task_uuid
        task_obj.update({"task_uuid": data['uuid']})
        task_obj.soft_update()

        # disk_info
        if not data['system_disk'].get('uuid'):
            data['system_disk']['uuid'] = create_uuid()
        data['sys_storage'] = sys_storage['uuid']
        data['data_storage'] = data_storage['uuid']
        if image_id:
            image_path = image.path
        else:
            image_path = None
        disk_info = self.create_disk_info(data, sys_storage['path'], data_storage['path'],
                                          image_path, disk_generate=disk_generate)

        # 磁盘记录数据库
        disks = list()
        sys_disk = disk_info[0]
        sys_info = {
            "uuid": sys_disk['uuid'],
            "type": constants.IMAGE_TYPE_SYSTEM,
            "device_name": sys_disk['dev'],
            "image_id": data['system_disk'].get('image_id', ''),
            "instance_uuid": data['uuid'],
            "boot_index": sys_disk['boot_index'],
            "size": int(sys_disk['size'].replace('G', ''))
        }
        disks.append(sys_info)
        for disk in disk_info[1:]:
            if 'cdrom' == disk.get('type'):
                continue
            info = {
                "uuid": disk['uuid'],
                "type": constants.IMAGE_TYPE_DATA,
                "device_name": disk['dev'],
                "image_id": '',
                "instance_uuid": data['uuid'],
                "boot_index": disk['boot_index'],
                "size": int(disk['size'].replace('G', ''))
            }
            disks.append(info)

        template = db_api.create_instance_template(data)
        # db_api.insert_with_many(models.YzyInstanceDeviceInfo, disks)
        logger.info("create template db info, use iso:%s", data.get('iso'))

        # 用于加载ISO的CDROM，加载后的ISO重启需要保存
        disk_info.append({
            "bus": "ide",
            "dev": "hda",
            "type": "cdrom",
            "path": ""
        })
        if not data.get('iso', None):
            disk_info.append({
                "bus": "ide",
                "dev": "hdb",
                "type": "cdrom",
                "path": ""
            })
        else:
            disk_info.append({
                "bus": "ide",
                "dev": "hdb",
                "type": "cdrom",
                "path": data['iso']
            })
            disk_info.append({
                "bus": "ide",
                "dev": "hdc",
                "type": "cdrom",
                "path": constants.VIRTIO_PATH
            })
        # instance info
        data['id'] = template.id
        instance_info = self._get_instance_info(data, template=True)

        try:
            power_on = data.get('power_on', False)
            self._create_instance(node.ip, instance_info, network_info, disk_info, power_on=power_on)
        except Exception as e:
            template.soft_delete()
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("TemplateCreateFail", name=data['name'], data=str(e))
        db_api.insert_with_many(models.YzyInstanceDeviceInfo, disks)
        # 设置是否随节点启动
        if data.get("autostart", False):
            self._autostart(node.ip, instance_info, network_info[0]['vif_info'], data['autostart'])
        if data.get('iso'):
            template.status = constants.STATUS_INSTALL
        elif power_on:
            template.status = constants.STATUS_ACTIVE
        else:
            template.status = constants.STATUS_INACTIVE
        template.soft_update()
        logger.info("create the template success, node:%s", node.ip)
        if 3 != data['classify']:
            # 只保留一个差异盘，创建时直接保存，便于基础镜像的处理
            self._save_template(template.uuid, create=True)
        ret = {
            "uuid": instance_info['uuid'],
            "name": data['name'],
            "version": version
        }
        task_obj.update({"status": constants.TASK_COMPLETE})
        task_obj.soft_update()
        return get_error_result("Success", ret)

    def system_install_complete(self, template_uuid):
        """
        安装系统桌面时，给出标识安装完成了
        """
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("template %s not exist", template_uuid)
            return get_error_result("TemplateNotExist", name='')
        logger.info("start complete template install")
        # 第一步关机
        node = db_api.get_node_by_uuid(template.host_uuid)
        instance_info = {
            "uuid": template.uuid,
            "name": template.name
        }
        try:
            self._stop_instance(node.ip, instance_info, timeout=60)
        except Exception as e:
            logger.error("stop template %s failed:%s", template.uuid, e)
            return get_error_result("TemplateStopError", name=template.name, data=str(e))

        self.detach_cdrom(node.ip, instance_info)
        template.status = constants.STATUS_INACTIVE
        template.updated_time = datetime.utcnow()
        template.soft_update()
        logger.info("the template install completed")
        return get_error_result("Success")

    # def start_template(self, template_uuid):
    #     """
    #     模板开机，这里可以采用两种方式，一种是根据uuid进行开机，一种是跟创建一样拿到所有信息，进行define
    #     注意三点：
    #         1、每次都要新加载IP信息
    #         2、模板属性修改，进行了磁盘增减、扩容、vcpu和ram变化都要能在开机时生效
    #         3、模板挂载的资源重启要保留
    #     """
    #     template = db_api.get_instance_template(template_uuid)
    #     if not template:
    #         logger.error("template %s not exist", template_uuid)
    #         return get_error_result("TemplateNotExist", name='')
    #
    #     node = db_api.get_node_by_uuid(template.host_uuid)
    #     info = {
    #         "uuid": template.uuid,
    #         "name": template.name
    #     }
    #     try:
    #         subnet = db_api.get_subnet_by_uuid(template.subnet_uuid)
    #         net = db_api.get_interface_by_network(template.network_uuid, node.uuid)
    #         if not net:
    #             logger.error("node %s network info %s error", node.uuid, template.network_uuid)
    #             return get_error_result("NodeNetworkInfoError")
    #
    #         vif_info = {
    #             "uuid": net.YzyNetworks.uuid,
    #             "vlan_id": net.YzyNetworks.vlan_id,
    #             "interface": net.nic,
    #             "bridge": constants.BRIDGE_NAME_PREFIX + net.YzyNetworks.uuid[:constants.RESOURCE_ID_LENGTH]
    #         }
    #         network_info = self.create_network_info(vif_info, template.port_uuid, template.mac, subnet,
    #                                                 template.bind_ip)
    #         # 不使用_create_instance方法是因为通过cdrom加载的设备重启后需要保留
    #         rep_json = self._start_instance(node.ip, info, network_info)
    #         logger.info("start instance end, return:%s", rep_json)
    #         if rep_json['code'] == 0:
    #             file_path = os.path.join(constants.TOKEN_PATH, template_uuid)
    #             content = '%s: %s:%s' % (template_uuid, node.ip, rep_json['data']['vnc_port'])
    #             logger.info("write instance token info:%s", template_uuid)
    #             FileOp(file_path, 'w').write_with_endline(content)
    #     except Exception as e:
    #         logger.error("start template failed:%s", e)
    #         template.status = constants.STATUS_ERROR
    #         template.soft_update()
    #         return get_error_result("TemplateStartFail", name=template.name)
    #     if template.status != constants.STATUS_INSTALL:
    #         template.status = constants.STATUS_ACTIVE
    #         template.soft_update()
    #     template.soft_update()
    #     logger.info("start template %s success", info)
    #     return get_error_result("Success", rep_json.get('data'))

    def start_template(self, template_uuid):
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("template %s not exist", template_uuid)
            return get_error_result("TemplateNotExist", name='')
        sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
        if not (sys_base and data_base):
            return get_error_result("InstancePathNotExist")

        node = db_api.get_node_by_uuid(template.host_uuid)
        info = {
            "uuid": template.uuid,
            "name": template.name,
            "ram": template.ram,
            "vcpu": template.vcpu,
            "os_type": template.os_type,
            "id": template.id
        }
        instance_info = self._get_instance_info(info, template=True)
        subnet = db_api.get_subnet_by_uuid(template.subnet_uuid)
        net = db_api.get_interface_by_network(template.network_uuid, node.uuid)
        vif_info = {
            "uuid": net.YzyNetworks.uuid,
            "vlan_id": net.YzyNetworks.vlan_id,
            "interface": net.nic,
            "bridge": constants.BRIDGE_NAME_PREFIX + net.YzyNetworks.uuid[:constants.RESOURCE_ID_LENGTH]
        }
        network_info = self.create_network_info(vif_info, template.port_uuid, template.mac, subnet,
                                                template.bind_ip)
        disk_info = list()
        devices = db_api.get_devices_by_instance(template.uuid)
        modify = db_api.get_devices_modify_with_all({"template_uuid": template.uuid})
        sys_base_dir = os.path.join(sys_base, template_uuid)
        data_base_dir = os.path.join(data_base, template_uuid)
        # 被标记删除的数据盘不记录进来
        for disk in devices:
            flag = True
            for item in modify:
                if constants.DEVICE_NEED_DELETED == item.state and item.uuid == disk.uuid:
                    flag = False
                    break
            if not flag:
                continue
            base_dir = sys_base_dir if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base_dir
            info = {
                "uuid": disk.uuid,
                "dev": disk.device_name,
                "boot_index": disk.boot_index,
                "size": "%dG" % disk.size,
                "disk_file": "%s/%s%s" % (base_dir, constants.DISK_FILE_PREFIX, disk.uuid),
            }
            disk_info.append(info)
            if disk.image_id:
                image = db_api.get_image_with_first({"uuid": disk.image_id})
                if not image:
                    return get_error_result("TemplateImageNotExist")
                info['backing_file'] = image.path
        # 修改的只是数据盘
        for item in modify:
            if constants.DEVICE_NEED_ADDED == item.state:
                info = {
                    "uuid": item.uuid,
                    "dev": item.device_name,
                    "boot_index": item.boot_index,
                    "size": "%dG" % item.size,
                    "disk_file": "%s/%s%s" % (data_base_dir, constants.DISK_FILE_PREFIX, item.uuid),
                }
                disk_info.append(info)
        disk_info.append({
            "bus": "ide",
            "dev": "hda",
            "type": "cdrom",
            "path": ""
        })
        if template.attach:
            iso = db_api.get_iso_with_first({"uuid": template.attach})
        disk_info.append({
                "bus": "ide",
                "dev": "hdb",
                "type": "cdrom",
                "path": iso.path if template.attach else ""
            })
        try:
            rep_json = self._create_instance(node.ip, instance_info, network_info, disk_info, power_on=True)
            logger.info("start template end, return:%s", rep_json)
            if rep_json['code'] == 0:
                file_path = os.path.join(constants.TOKEN_PATH, template_uuid)
                content = '%s: %s:%s' % (template_uuid, node.ip, rep_json['data']['vnc_port'])
                logger.info("write instance token info:%s", template_uuid)
                FileOp(file_path, 'w').write_with_endline(content)
        except Exception as e:
            logger.error("start template failed:%s", e)
            template.status = constants.STATUS_ERROR
            template.soft_update()
            return get_error_result("TemplateStartFail", name=template.name, data=str(e))
        if template.status != constants.STATUS_INSTALL:
            template.status = constants.STATUS_ACTIVE
        template.soft_update()
        logger.info("start template %s success", instance_info)
        return get_error_result("Success", rep_json['msg'])

    def stop_template(self, template_uuid, hard=False):
        """
        模板关机
        :param template_uuid:
        :param hard: 是否强制关机
        :return:
        """
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("template %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")

        node = db_api.get_node_by_uuid(template.host_uuid)
        instance_info = {
            "uuid": template.uuid,
            "name": template.name
        }
        if hard:
            rep_json = self._stop_instance(node.ip, instance_info, timeout=0)
        else:
            rep_json = self._stop_instance(node.ip, instance_info, timeout=180)
        if rep_json.get("code", -1) != 0:
            logger.error("stop template: %s fail:%s", template.uuid, rep_json['msg'])
            return get_error_result("TemplateStopError", name=template.name)
        template.status = constants.STATUS_INACTIVE
        template.soft_update()
        logger.info("stop template %s success", instance_info)
        return get_error_result("Success", rep_json.get('data'))

    def reboot_template(self, template_uuid, reboot_type='soft'):
        """
        模板重启
        """
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("template %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")

        node = db_api.get_node_by_uuid(template.host_uuid)
        instance_info = {
            "uuid": template.uuid,
            "name": template.name
        }
        try:
            rep_json = self._reboot_instance(node.ip, instance_info, reboot_type)
            if rep_json['code'] == 0:
                file_path = os.path.join(constants.TOKEN_PATH, template_uuid)
                content = '%s: %s:%s' % (template_uuid, node.ip, rep_json['data']['vnc_port'])
                logger.info("write instance token info:%s", template_uuid)
                FileOp(file_path, 'w').write_with_endline(content)
        except Exception as e:
            logger.error("reboot template failed:%s", e)
            template.status = constants.STATUS_ERROR
            template.soft_update()
            return get_error_result("TemplateStartFail", name=template.name)
        template.status = constants.STATUS_ACTIVE
        template.soft_update()
        logger.info("reboot template %s success", instance_info)
        return get_error_result("Success", rep_json.get('data'))

    def hard_reboot_template(self, template_uuid):
        """
        模板硬重启
        """
        return self.reboot_template(template_uuid, reboot_type='hard')
        # template = db_api.get_instance_template(template_uuid)
        # if not template:
        #     logger.error("template %s not exist", template_uuid)
        #     return get_error_result("TemplateNotExist")
        #
        # node = db_api.get_node_by_uuid(template.host_uuid)
        # info = {
        #     "uuid": template.uuid,
        #     "name": template.name,
        #     "ram": template.ram,
        #     "vcpu": template.vcpu,
        #     "os_type": template.os_type,
        #     "id": template.id
        # }
        # instance_info = self._get_instance_info(info, template=True)
        # subnet = db_api.get_subnet_by_uuid(template.subnet_uuid)
        # net = db_api.get_interface_by_network(template.network_uuid, node.uuid)
        # vif_info = {
        #     "uuid": net.YzyNetworks.uuid,
        #     "vlan_id": net.YzyNetworks.vlan_id,
        #     "interface": net.nic,
        #     "bridge": constants.BRIDGE_NAME_PREFIX + net.YzyNetworks.uuid[:constants.RESOURCE_ID_LENGTH]
        # }
        # network_info = self.create_network_info(vif_info, template.port_uuid, template.mac, subnet,
        #                                         template.bind_ip)
        # disk_info = list()
        # devices = db_api.get_devices_by_instance(template.uuid)
        # sys_base, data_base = self._get_template_storage_path()
        # for disk in devices:
        #     if constants.IMAGE_TYPE_SYSTEM == disk.type:
        #         base_path = sys_base
        #     else:
        #         base_path = data_base
        #     ins_path = os.path.join(base_path, template.uuid)
        #     disk_path = os.path.join(ins_path, constants.DISK_FILE_PREFIX + disk.uuid)
        #     info = {
        #         "uuid": disk.uuid,
        #         "dev": disk.device_name,
        #         "image_id": disk.uuid if template.version > 0 else disk.image_id,
        #         "image_version": template.version,
        #         "boot_index": disk.boot_index,
        #         "size": "%dG" % disk.size,
        #         "base_path": base_path,
        #         "path": disk_path
        #     }
        #     disk_info.append(info)
        # rep_json = self._hard_reboot_instance(node.ip, instance_info, network_info, disk_info)
        # if rep_json['code'] == 0:
        #     file_path = os.path.join(constants.TOKEN_PATH, template_uuid)
        #     content = '%s: %s:%s' % (template_uuid, node.ip, rep_json['data']['vnc_port'])
        #     logger.info("write instance token info:%s", template_uuid)
        #     FileOp(file_path, 'w').write_with_endline(content)
        # logger.info("hard reboot template %s success", instance_info)
        # return get_error_result("Success", rep_json.get('data'))

    def delete_template(self, template_uuid):
        """
        删除模板，除了删除系统盘和数据盘，还要删除他们的base文件
        :param template_uuid: the uuid of template
        :return:
        """
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("instance template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")
        if constants.SYSTEM_DESKTOP == template.classify and constants.STATUS_ACTIVE == template.status:
            logger.error("the system desktop is active, can not delete")
            return get_error_result("SystemIsActive")
        if constants.EDUCATION_DESKTOP == template.classify:
            desktops = db_api.get_desktop_with_all({'template_uuid': template_uuid})
            if desktops:
                return get_error_result("TemplateInUse", name=template.name)
        if constants.PERSONAL_DEKSTOP == template.classify:
            desktops = db_api.get_personal_desktop_with_all({'template_uuid': template_uuid})
            if desktops:
                return get_error_result("TemplateInUse", name=template.name)
        sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
        if not (sys_base and data_base):
            sys_base = constants.DEFAULT_SYS_PATH
            data_base = constants.DEFAULT_DATA_PATH

        logger.info("delete template:%s", template_uuid)
        images = self._get_deleted_images(template, template.version, sys_base, data_base)
        command_data = {
            "command": "delete",
            "handler": "TemplateHandler",
            "data": {
                "image_version": template.version,
                "instance": {
                    "uuid": template.uuid,
                    "name": template.name,
                    "sys_base": sys_base,
                    "data_base": data_base
                },
                "images": images
            }
        }
        nodes = db_api.get_node_by_pool_uuid(template.pool_uuid)
        # controller = db_api.get_controller_node()
        # for node in nodes:
        #     if node.ip == controller.ip:
        #         break
        # else:
        #     nodes.append(controller)
        for node in nodes:
            logger.info("delete the template begin, node:%s", node.ip)
            rep_json = compute_post(node.ip, command_data)
            if rep_json.get("code", -1) != 0:
                logger.error("delete template: %s fail:%s", template.uuid, rep_json['msg'])
                # return get_error_result("TemplateDeleteFail", name=template.name)
        logger.info("delete the template from db")
        devices = db_api.get_devices_by_instance(template.uuid)
        for disk in devices:
            tasks = db_api.get_task_all({"image_id": disk.uuid})
            for task in tasks:
                task.soft_delete()
            disk.soft_delete()
        devices_modify = db_api.get_devices_modify_with_all({"template_uuid": template.uuid})
        for item in devices_modify:
            tasks = db_api.get_task_all({"image_id": item.uuid})
            for task in tasks:
                task.soft_delete()
            item.soft_delete()
        template.soft_delete()
        try:
            token_file = os.path.join(constants.TOKEN_PATH, template_uuid)
            os.remove(token_file)
        except:
            pass
        return get_error_result("Success")

    def reset_template(self, template_uuid):
        """
        重置模板
        :param template_uuid: the uuid of template
        :return:
        """
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("instance template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")

        logger.info("reset template:%s", template_uuid)
        sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
        if not (sys_base and data_base):
            return get_error_result("InstancePathNotExist")

        images = self._get_sync_images(template, template.version, sys_base, data_base)
        command_data = {
            "command": "reset",
            "handler": "TemplateHandler",
            "data": {
                "instance": {
                    "uuid": template.uuid,
                    "name": template.name
                },
                "images": images
            }
        }
        node = db_api.get_node_with_first({'uuid': template.host_uuid})
        logger.info("reset the template begin, node:%s", node.ip)
        rep_json = compute_post(node.ip, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("reset template: %s fail:%s", template.uuid, rep_json['msg'])
            return get_error_result("TemplateResetError", name=template.name)
        devices_modify = db_api.get_devices_modify_with_all({"template_uuid": template.uuid})
        for device in devices_modify:
            # 如果是添加了盘，需要detach
            if constants.DEVICE_NEED_ADDED == device.state:
                command_data = {
                    "command": "detach_disk",
                    "handler": "TemplateHandler",
                    "data": {
                        "instance": {
                            "uuid": template.uuid,
                            "name": template.name,
                        },
                        "disk_file": os.path.join(data_base, template_uuid, constants.DISK_FILE_PREFIX + device.uuid),
                        "backing_file": os.path.join(data_base, constants.IMAGE_CACHE_DIRECTORY_NAME,
                                                     constants.IMAGE_FILE_PREFIX % str(1) + device.uuid),
                        "delete_base": True
                    }
                }
                rep_json = compute_post(node.ip, command_data)
                if rep_json.get("code", -1) != 0:
                    logger.error("detach disk failed, node:%s, error:%s", node.ip, rep_json.get('data'))
                    return get_error_result("DetachDiskError")
                logger.info("detach disk %s success", device.uuid)

            # 如果是原始盘被删除，需要加回来
            if constants.DEVICE_NEED_DELETED == device.state:
                find = db_api.get_devices_with_first({"uuid": device.uuid})
                if find:
                    command_data = {
                        "command": "attach_disk",
                        "handler": "TemplateHandler",
                        "data": {
                            "instance": {
                                "uuid": template.uuid,
                                "name": template.name
                            },
                            "disk": {
                                'uuid': device.uuid,
                                'dev': device.device_name,
                                'boot_index': device.boot_index,
                                'bus': 'virtio',
                                'type': 'disk',
                                "disk_file": "%s/%s%s" % (os.path.join(data_base, template_uuid),
                                                          constants.DISK_FILE_PREFIX, device.uuid),
                                "backing_file": os.path.join(data_base, constants.IMAGE_CACHE_DIRECTORY_NAME,
                                                             constants.IMAGE_FILE_PREFIX % str(1) + device.uuid)
                            }
                        }
                    }
                    rep_json = compute_post(node.ip, command_data)
                    if rep_json.get("code", -1) != 0:
                        logger.error("attach disk failed, node:%s, error:%s", node.ip, rep_json.get('data'))
                        return get_error_result("TemplateResetError", name=template.name)
                    logger.info("attach disk %s success", device.uuid)
            device.soft_delete()

        template.status = constants.STATUS_INACTIVE
        template.soft_update()
        logger.info("reset the template success")
        return get_error_result("Success")

    def find_add_disk(self, value, template, data_base):
        # 查找新加的磁盘
        template_add_disks = list()
        add_disks = list()
        is_add = False
        for disk in value['devices']:
            if not disk.get('uuid', None):
                add_disks.append(disk)
                is_add = True
        if is_add:
            for disk in add_disks:
                logger.info("template add new disk:%s", disk)
                zm = string.ascii_lowercase
                disk_uuid = create_uuid()
                template_info = {
                    "uuid": disk_uuid,
                    "device_name": "vd%s" % zm[disk['inx'] + 1],
                    "template_uuid": template.uuid,
                    "boot_index": disk['inx'] + 1,
                    "size": disk['size'],
                    "state": constants.DEVICE_NEED_ADDED
                }
                template_add_disks.append(template_info)
                base_path = os.path.join(data_base, constants.IMAGE_CACHE_DIRECTORY_NAME)
                file = os.path.join(base_path, constants.IMAGE_FILE_PREFIX % str(1) + disk_uuid)
                node = db_api.get_node_with_first({'uuid': template.host_uuid})
                rep_json = self.create_file(node.ip, file, disk['size'])
                if rep_json.get("code", -1) != 0:
                    logger.error("create_file failed, node:%s, error:%s", node.ip, rep_json.get('data'))
                    raise Exception("create file failed")
                logger.info("create file %s success", file)
                # 然后新建新加磁盘的差异盘
                command_data = {
                    "command": "attach_disk",
                    "handler": "TemplateHandler",
                    "data": {
                        "instance": {
                            "uuid": template.uuid,
                            "name": template.name
                        },
                        "disk": {
                            'uuid': disk_uuid,
                            'dev': "vd%s" % zm[disk['inx'] + 1],
                            'boot_index': disk['inx'] + 1,
                            'bus': 'virtio',
                            'type': 'disk',
                            "disk_file": "%s/%s%s" % (os.path.join(data_base, template.uuid),
                                                      constants.DISK_FILE_PREFIX, disk_uuid),
                            "backing_file": os.path.join(data_base, constants.IMAGE_CACHE_DIRECTORY_NAME,
                                                         constants.IMAGE_FILE_PREFIX % str(1) + disk_uuid)
                        }
                    }
                }
                node = db_api.get_node_with_first({'uuid': template.host_uuid})
                rep_json = compute_post(node.ip, command_data)
                if rep_json.get("code", -1) != 0:
                    logger.error("attach disk failed, node:%s, error:%s", node.ip, rep_json.get('data'))
                    raise Exception("attach disk file failed")
                logger.info("attach disks success")
        return template_add_disks, is_add

    def find_remove_and_extend_disk(self, template, value, sys_base, data_base, is_add):
        # 查找删除的盘
        images = list()
        origin_devices = db_api.get_devices_with_all({"instance_uuid": template.uuid})
        modify_devices = db_api.get_devices_modify_with_all({"template_uuid": template.uuid,
                                                             "state": constants.DEVICE_NEED_ADDED})
        devices = origin_devices + modify_devices
        node = db_api.get_node_with_first({'uuid': template.host_uuid})
        for device in devices:
            flag = False
            for disk in value['devices']:
                if disk.get('uuid', None) and disk['uuid'] == device.uuid:
                    flag = True
                    # 大小有变化
                    if int(disk['size']) != int(device.size):
                        if int(disk['size']) < int(device.size):
                            return get_error_result("TemplateDiskSizeError")
                        logger.info("disk %s extend size from %s to %s", device.device_name, device.size, disk['size'])
                        base_dir = sys_base if constants.IMAGE_TYPE_SYSTEM == disk['type'] else data_base
                        image = {
                            "disk_file": os.path.join(base_dir, template.uuid, constants.DISK_FILE_PREFIX + device.uuid),
                            "size": int(disk['size']) - int(device.size)
                        }
                        images.append(image)
                        device.size = int(disk['size'])
                        device.soft_update()
                    break
            if not flag and not is_add:
                modified = db_api.get_devices_modify_with_first({"uuid": device.uuid})
                # 被标记删除后进行其他属性修改时，不能再重复标记删除
                if modified and constants.DEVICE_NEED_DELETED == modified.state:
                    continue
                logger.info("delete disk uuid:%s, name:%s", device.uuid, device.device_name)
                command_data = {
                    "command": "detach_disk",
                    "handler": "TemplateHandler",
                    "data": {
                        "instance": {
                            "uuid": template.uuid,
                            "name": template.name,
                        },
                        "disk_file": "%s/%s%s" % (os.path.join(data_base, template.uuid),
                                                  constants.DISK_FILE_PREFIX, device.uuid),
                        "backing_file": os.path.join(data_base, constants.IMAGE_CACHE_DIRECTORY_NAME,
                                                     constants.IMAGE_FILE_PREFIX % str(1) + device.uuid),
                        "delete_base": False if hasattr(device, "instance_uuid") else True
                    }
                }
                rep_json = compute_post(node.ip, command_data)
                if rep_json.get("code", -1) != 0:
                    logger.error("detach disk failed, node:%s, error:%s", node.ip, rep_json.get('data'))
                    return get_error_result("DetachDiskError")
                # 如果是原始盘被删除，则添加一条标记删除记录
                if hasattr(device, "instance_uuid"):
                    change_info = {
                        "uuid": device.uuid,
                        "origin": True,
                        "device_name": device.device_name,
                        "template_uuid": device.instance_uuid,
                        "boot_index": device.boot_index,
                        "size": device.size,
                        "state": constants.DEVICE_NEED_DELETED
                    }
                    db_api.insert_with_many(models.YzyDeviceModify, change_info)
                    logger.info("delete origin disk, insert a record")
                else:
                    device.state = constants.DEVICE_NEED_DELETED
                    device.deleted = True
                    device.soft_update()
        if images:
            command_data = {
                "command": "resize",
                "handler": "TemplateHandler",
                "data": {
                    "uuid": template.uuid,
                    "images": images
                }
            }
            node = db_api.get_node_with_first({'uuid': template.host_uuid})
            rep_json = compute_post(node.ip, command_data)
            if rep_json.get("code", -1) != 0:
                logger.error("resize disk failed, node:%s, error:%s", node.ip, rep_json.get('data'))
                return get_error_result("ImageResizeError")
            logger.info("resize disks success")
        return get_error_result("Success")

    def update_ram_and_vcpu(self, value, template):
        if float(value['ram']) != float(template.ram):
            ram = float(value['ram'])
        else:
            ram = None
        if int(value['vcpu']) != int(template.vcpu):
            vcpu = int(value['vcpu'])
        else:
            vcpu = None
        if ram or vcpu:
            node = db_api.get_node_with_first({'uuid': template.host_uuid})
            command_data = {
                "command": "set_ram_and_vcpu",
                "handler": "InstanceHandler",
                "data": {
                    "instance": {
                        "uuid": template.uuid,
                        "name": template.name,
                    },
                    "vcpu": vcpu,
                    "ram": int(ram * constants.Ki) if ram else None
                }
            }
            rep_json = compute_post(node.ip, command_data)
            if rep_json.get("code", -1) != 0:
                logger.error("set vcpu and ram failed, node:%s, error:%s", node.ip, rep_json.get('data'))
                return get_error_result("SetVcpuMemoryError")
        return get_error_result("Success")

    def update_template(self, data):
        logger.info("update template:%s", data)
        template_uuid = data.get('uuid', '')
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("template %s not exist", template)
            return get_error_result("TemplateNotExist")
        # if template.status == constants.STATUS_ACTIVE:
        #     logger.error("template is active, can not update")
        #     return get_error_result("TemplateActive", name=template.name)
        if data['name'] != data['value']['name']:
            template_check = db_api.get_template_with_all({'name': data['value']['name'], 'classify': template.classify})
            if template_check:
                logger.error("template: %s already exist", data['name'])
                return get_error_result("TemplateAlreadyExist", name=data['name'])
        subnet_uuid = data['value'].get('subnet_uuid', None)
        if subnet_uuid:
            subnet = db_api.get_subnet_by_uuid(data['value']['subnet_uuid'])
            if not subnet:
                logger.error("subnet:%s is not exist", data['value']['subnet_uuid'])
                return get_error_result("SubnetNotExist")
        else:
            subnet = None

        value = data['value']
        if not subnet:
            # dhcp方式获取IP
            value['bind_ip'] = ''
        else:
            education_used_ips = self.get_personal_used_ipaddr(subnet_uuid)
            all_ips = find_ips(subnet.start_ip, subnet.end_ip)
            if not value.get('bind_ip', None):
                # 选择子网并且系统分配，模板IP从后往前取值
                all_ip_reverse = all_ips[::-1]
                for ipaddr in all_ip_reverse:
                    if ipaddr not in education_used_ips:
                        value['bind_ip'] = ipaddr
                        break
                else:
                    return get_error_result("IPNotEnough")
            if value['bind_ip'] not in all_ips:
                return get_error_result("IPNotInRange", ipaddr=value['bind_ip'])
            if template.bind_ip != value['bind_ip'] and value['bind_ip'] in education_used_ips:
                return get_error_result("IPInUse")
        sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
        if not (sys_base and data_base):
            return get_error_result("InstancePathNotExist")
        if template.status == constants.STATUS_ACTIVE:
            ret = self.stop_template(template_uuid)
            if ret.get('code') != 0:
                return ret
        try:
            # cpu和内存的修改
            rep_json = self.update_ram_and_vcpu(value, template)
            if rep_json.get('code') != 0:
                return rep_json
            try:
                template_disks, is_add = self.find_add_disk(value, template, data_base)
            except Exception as e:
                logger.error("get add disk error:%s", e)
                return get_error_result("TemplateUpdateError", name="")
            rep_json = self.find_remove_and_extend_disk(template, value, sys_base, data_base, is_add)
            if rep_json.get('code') != 0:
                return rep_json
            logger.info('update template attr to db')
            template_value = {
                "name": value['name'],
                "desc": value.get('desc', ''),
                "network_uuid": value['network_uuid'],
                "subnet_uuid": value['subnet_uuid'],
                "bind_ip": value.get('bind_ip'),
                "ram": value['ram'],
                "vcpu": value['vcpu']
            }
            template.update(template_value)
            if template_disks:
                db_api.insert_with_many(models.YzyDeviceModify, template_disks)
            # if instance_disks:
            #     db_api.insert_with_many(models.YzyInstanceDeviceInfo, instance_disks)
        except Exception as e:
            logger.error("update template %s failed:%s", template_uuid, e, exc_info=True)
            return get_error_result("TemplateUpdateError", name=template.name)
        logger.info("update template success, uuid:%s, name:%s", template_uuid, template.name)
        return get_error_result("Success")

    def recreate_disk(self, ipaddr, disks):
        """在模板重建差一盘"""
        command_data = {
            "command": "recreate_disk",
            "handler": "TemplateHandler",
            "data": {
                "disks": disks
            }
        }
        rep_json = compute_post(ipaddr, command_data)
        logger.info("recreate the diff disk file, node:%s", ipaddr)
        return rep_json

    def convert(self, ipaddr, backing_file, dest_file, need_convert=True):
        """
        在模板所在节点先合并差异文件生成新的基础镜像
        如果版本为0，则是直接复制镜像
        """
        command_data = {
            "command": "convert",
            "handler": "TemplateHandler",
            "data": {
                "template": {
                    "backing_file": backing_file,
                    "dest_file": dest_file,
                    "need_convert": need_convert
                }
            }
        }
        rep_json = compute_post(ipaddr, command_data, timeout=1200)
        logger.info("convert the disk file finished, node:%s", ipaddr)
        return rep_json

    def write_head(self, ipaddr, image_path, vcpu, ram, disk_size):
        """
        在模板所在节点先合并差异文件生成新的基础镜像
        如果版本为0，则根据image_id进行复制，否则进行合并
        """
        command_data = {
            "command": "write_header",
            "handler": "TemplateHandler",
            "data": {
                "image_path": image_path,
                "vcpu": vcpu,
                "ram": ram,
                "disk_size": disk_size
            }
        }
        rep_json = compute_post(ipaddr, command_data, timeout=1200)
        logger.info("write head to image %s finished, node:%s, return:%s", image_path, ipaddr, rep_json)
        return rep_json

    def detach_cdrom(self, ipaddr, instance_info, configdrive=True):
        """iso安装后删除cdrom"""
        command_data = {
            "command": "detach_cdrom",
            "handler": "TemplateHandler",
            "data": {
                "instance": instance_info,
                "configdrive": configdrive
            }
        }
        rep_json = compute_post(ipaddr, command_data)
        logger.info("detach_cdrom end, instance:%s", instance_info)
        return rep_json

    def copy(self, host, image, task_id=None):
        """
        在节点复制模板的系统盘和数据盘
        """
        command_data = {
            "command": "copy",
            "handler": "TemplateHandler",
            "data": {
                "image": image
            }
        }
        rep_json = compute_post(host['ipaddr'], command_data, timeout=1200)
        rep_json['task_id'] = task_id
        rep_json['host_uuid'] = host['host_uuid']
        rep_json['image_id'] = image['new_image_id']
        rep_json['ipaddr'] = host['ipaddr']
        logger.info("copy the template finished, node:%s", host['ipaddr'])
        return rep_json

    def sync(self, host, server_ip, version, image, task_id=None):
        """节点同步镜像"""
        bind = SERVER_CONF.addresses.get_by_default('server_bind', '')
        if bind:
            port = bind.split(':')[-1]
        else:
            port = constants.SERVER_DEFAULT_PORT
        endpoint = "http://%s:%s" % (server_ip, port)
        command_data = {
            "command": "sync",
            "handler": "TemplateHandler",
            "data": {
                "image_version": version,
                "task_id": task_id,
                "endpoint": endpoint,
                "url": constants.IMAGE_SYNC_URL,
                "image": image
            }
        }
        rep_json = compute_post(host['ipaddr'], command_data, timeout=1800)
        logger.info("sync the image file end, image:%s, host:%s,rep_json:%s", image, host['ipaddr'], rep_json)
        rep_json['task_id'] = task_id
        rep_json['host_uuid'] = host['host_uuid']
        rep_json['image_id'] = image['image_id']
        rep_json['ipaddr'] = host['ipaddr']
        return rep_json

    def create_file(self, ipaddr, file, size):
        command_data = {
            "command": "create_file",
            "handler": "TemplateHandler",
            "data": {
                "file": file,
                "size": "%sG" % size
            }
        }
        rep_json = compute_post(ipaddr, command_data)
        logger.info("create disk file:%s, host:%s", file, ipaddr)
        rep_json['ipaddr'] = ipaddr
        return rep_json

    def _attach_source(self, ipaddr, instance_info, path):
        command_data = {
            "command": "attach_source",
            "handler": "TemplateHandler",
            "data": {
                "instance": instance_info,
                "path": path
            }
        }
        logger.info("attach %s device in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("attach %s device failed, node:%s, error:%s", instance_info['uuid'], ipaddr, rep_json.get('data'))
        return rep_json

    def _detach_source(self, ipaddr, instance_info):
        command_data = {
            "command": "detach_source",
            "handler": "TemplateHandler",
            "data": {
                "instance": instance_info
            }
        }
        logger.info("detach %s device in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("detach %s device failed, node:%s, error:%s", instance_info['uuid'], ipaddr, rep_json.get('data'))
        return rep_json

    def _send_key(self, ipaddr, instance_info):
        command_data = {
            "command": "send_key",
            "handler": "TemplateHandler",
            "data": {
                "instance": instance_info
            }
        }
        logger.info("teamplate send key in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("teamplate send key failed, node:%s, error:%s", instance_info['uuid'], ipaddr, rep_json.get('data'))
        return rep_json

    def _get_disk_and_backing_file(self, template, sys_base, data_base):
        disks = list()
        devices = db_api.get_devices_by_instance(template.uuid)
        for disk in devices:
            base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
            template_dir = os.path.join(base_path, template.uuid)
            file_name = constants.DISK_FILE_PREFIX + disk.uuid
            disk_path = os.path.join(template_dir, file_name)
            backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
            backing_file_name = constants.IMAGE_FILE_PREFIX % str(1) + disk.uuid
            backing_file = os.path.join(backing_dir, backing_file_name)
            info = {
                "disk_file": disk_path,
                "backing_file": backing_file
            }
            disks.append(info)
        devices = db_api.get_devices_modify_with_all({"template_uuid": template.uuid})
        for disk in devices:
            if constants.DEVICE_NEED_ADDED == disk.state:
                base_path = data_base
                template_dir = os.path.join(base_path, template.uuid)
                file_name = constants.DISK_FILE_PREFIX + disk.uuid
                disk_path = os.path.join(template_dir, file_name)
                backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
                backing_file_name = constants.IMAGE_FILE_PREFIX % str(1) + disk.uuid
                backing_file = os.path.join(backing_dir, backing_file_name)
                info = {
                    "disk_file": disk_path,
                    "backing_file": backing_file
                }
                disks.append(info)
        return disks

    def _get_sync_images(self, template, version, sys_base, data_base, md5=False, update=False):
        """
        :param template: the template db object
        :param version: the template version
        :param sys_base: the dir of the template sys image
        :param data_base: the dir of the tepmlate data image
        :param md5: Is it necessary to calculate the image file md5 sum
        :param update: if the add data disk need sync
        :return:
            {
                "image_id": "",             # 主要用于同步任务情况的记录
                "disk_file": "",            # 虚拟机实际的磁盘文件
                "backing_file": "",         # 虚拟机磁盘文件的base文件
                "dest_path": "",            # 同步时的目的地址
                "md5_sum": ""               # 虚拟机磁盘文件的md5值
            }
        """
        images = list()
        devices = db_api.get_devices_by_instance(template.uuid)
        modify_devices = db_api.get_devices_modify_with_all({"template_uuid": template.uuid})
        for disk in devices:
            # 如果原始盘被标记删除，则不需要同步
            if update:
                flag = False
                for device in modify_devices:
                    if disk.uuid == device.uuid and constants.DEVICE_NEED_DELETED == device.state:
                        flag = True
                        break
                if flag:
                    continue

            if constants.IMAGE_TYPE_SYSTEM == disk.type and version < 1:
                image_id = disk.image_id
                backing_file_name = image_id
                dest_file_name = image_id
            else:
                image_id = disk.uuid
                backing_file_name = constants.IMAGE_FILE_PREFIX % str(1) + image_id
                dest_file_name = constants.IMAGE_FILE_PREFIX % str(version) + image_id
            base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
            backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
            template_dir = os.path.join(base_path, template.uuid)
            file_name = constants.DISK_FILE_PREFIX + disk.uuid
            image_path = os.path.join(template_dir, file_name)
            info = {
                "image_id": image_id,
                "disk_file": image_path,
                "backing_file": os.path.join(backing_dir, backing_file_name),
                "dest_path": os.path.join(backing_dir, dest_file_name)
            }
            if md5:
                logger.info("calculate the image file %s md5 sum", image_path)
                info['md5_sum'] = get_file_md5(image_path)
            images.append(info)
        if update:
            # 这边的都是数据盘
            devices = db_api.get_devices_modify_with_all({"template_uuid": template.uuid})
            for device in devices:
                if constants.DEVICE_NEED_ADDED == device.state:
                    template_dir = os.path.join(data_base, template.uuid)
                    file_name = constants.DISK_FILE_PREFIX + device.uuid
                    image_path = os.path.join(template_dir, file_name)
                    backing_dir = os.path.join(data_base, constants.IMAGE_CACHE_DIRECTORY_NAME)
                    backing_file_name = constants.IMAGE_FILE_PREFIX % str(1) + device.uuid
                    dest_file_name = constants.IMAGE_FILE_PREFIX % str(version) + device.uuid
                    info = {
                        "image_id": device.uuid,
                        "disk_file": image_path,
                        "backing_file": os.path.join(backing_dir, backing_file_name),
                        "dest_path": os.path.join(backing_dir, dest_file_name)
                    }
                    if md5:
                        logger.info("calculate the image file %s md5 sum", image_path)
                        info['md5_sum'] = get_file_md5(image_path)
                    images.append(info)
        logger.info("get template image info:%s", images)
        return images

    def _get_deleted_images(self, template, version, sys_base, data_base):
        """
        :param template: the template db object
        :param version: the template version
        :param sys_base: the dir of the template sys image
        :param data_base: the dir of the tepmlate data image
        :return:
        """
        images = list()
        devices = db_api.get_devices_by_instance(template.uuid)
        for disk in devices:
            if constants.IMAGE_TYPE_SYSTEM == disk.type and version < 1:
                image_id = disk.image_id
            else:
                image_id = disk.uuid
            base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
            backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
            if version > 0:
                backing_file_name = constants.IMAGE_FILE_PREFIX % str(1) + image_id
            else:
                backing_file_name = image_id
            image_path = os.path.join(backing_dir, backing_file_name)
            info = {
                "backing_file": image_path
            }
            images.append(info)
        # 这边的都是数据盘
        devices = db_api.get_devices_modify_with_all({"template_uuid": template.uuid})
        for device in devices:
            if constants.DEVICE_NEED_ADDED == device.state:
                backing_dir = os.path.join(data_base, constants.IMAGE_CACHE_DIRECTORY_NAME)
                if version > 0:
                    backing_file_name = constants.IMAGE_FILE_PREFIX % str(1) + device.uuid
                else:
                    backing_file_name = device.uuid
                image_path = os.path.join(backing_dir, backing_file_name)
                info = {
                    "backing_file": image_path
                }
                images.append(info)
        logger.info("get template image info:%s", images)
        return images

    def _get_copy_images(self, template, new_uuid, sys_base, data_base, dest_sys_base, dest_data_base):
        disks = list()
        images = list()
        add_disks = list()
        devices = db_api.get_devices_by_instance(template.uuid)
        for disk in devices:
            base_dir = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
            dest_base_dir = dest_sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else dest_data_base
            disk_uuid = create_uuid()
            info = {
                "image_id": disk.uuid,
                "new_image_id": disk_uuid,
                "backing_file": os.path.join(base_dir, constants.IMAGE_CACHE_DIRECTORY_NAME,
                                             constants.IMAGE_FILE_PREFIX % str(1) + disk.uuid),
                "dest_file": os.path.join(dest_base_dir, constants.IMAGE_CACHE_DIRECTORY_NAME,
                                          constants.IMAGE_FILE_PREFIX % str(1) + disk_uuid),
            }
            disks.append({
                "uuid": disk_uuid,
                "dev": disk.device_name,
                "boot_index": disk.boot_index,
                "size": "%dG" % disk.size,
                "disk_file": os.path.join(dest_base_dir, new_uuid, constants.DISK_FILE_PREFIX + disk_uuid),
                "backing_file": os.path.join(dest_base_dir, constants.IMAGE_CACHE_DIRECTORY_NAME,
                                             constants.IMAGE_FILE_PREFIX % str(1) + disk_uuid),
            })
            add_disks.append({
                "uuid": disk_uuid,
                "type": disk.type,
                "device_name": disk.device_name,
                "image_id": disk.image_id,
                "instance_uuid": new_uuid,
                "boot_index": disk.boot_index,
                "size": disk.size
            })
            images.append(info)
        logger.info("get template copy image info:%s", images)
        return images, disks, add_disks

    # def _get_template_storage_path(self):
    #     template_sys = db_api.get_template_sys_storage()
    #     template_data = db_api.get_template_data_storage()
    #     if not template_sys:
    #         sys_base = constants.DEFAULT_SYS_PATH
    #     else:
    #         sys_base = template_sys.path
    #     sys_path = os.path.join(sys_base, 'instances')
    #     if not template_data:
    #         data_base = constants.DEFAULT_DATA_PATH
    #     else:
    #         data_base = template_data.path
    #     data_path = os.path.join(data_base, 'datas')
    #     return sys_path, data_path

    def _get_template_storage(self, node_uuid=None):
        if not node_uuid:
            node = db_api.get_controller_node()
            node_uuid = node.uuid
        template_sys = db_api.get_template_sys_storage(node_uuid)
        template_data = db_api.get_template_data_storage(node_uuid)
        if not (template_sys and template_data):
            return None, None
        sys_path = os.path.join(template_sys.path, 'instances')
        data_path = os.path.join(template_data.path, 'datas')
        return {"path": sys_path, "uuid": template_sys.uuid, 'free': template_sys.free}, \
               {"path": data_path, "uuid": template_data.uuid, 'free': template_data.free}

    def node_sync_image(self, pool_uuid, ipaddr, host_uuid):
        try:
            controller = db_api.get_controller_image()
            sys_base, data_base = self._get_template_storage()
            if not (sys_base and sys_base):
                return get_error_result("InstancePathNotExist")
            templates = db_api.get_template_with_all({"pool_uuid": pool_uuid})
            base_images = db_api.get_images_with_all({"pool_uuid": pool_uuid})
            # 同步基础镜像
            host = {
                'ipaddr': ipaddr,
                'host_uuid': host_uuid
            }
            all_task = list()
            with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
                for image in base_images:
                    info = {
                        "image_id": image['uuid'],
                        "disk_file": image['path'],
                        "backing_file": image['path'],
                        "dest_path": image['path'],
                        "md5_sum": image['md5_sum']
                    }
                    task = Task(image_id=image['uuid'], host_uuid=host_uuid, version=0)
                    task_id = create_uuid()
                    task.begin(task_id, "start sync the image to host:%s" % ipaddr)
                    logger.info("sync image %s to host %s, task_id:%s", image['uuid'], ipaddr, task_id)
                    future = executor.submit(self.sync, host, controller.ip, 0, info, task_id)
                    all_task.append(future)
                for future in as_completed(all_task):
                    rep_json = future.result()
                    task = Task(image_id=rep_json['image_id'], host_uuid=rep_json['host_uuid'], version=0)
                    if rep_json.get('code') != 0:
                        logger.info("sync the image %s to host:%s failed:%s", rep_json['image_id'],
                                    rep_json['ipaddr'], rep_json.get('data'))
                        task.error(task_id, "sync the image to host:%s failed:%s" % (rep_json['ipaddr'], rep_json.get('data')))
                    else:
                        logger.info("sync the image %s to host:%s success", rep_json['image_id'], rep_json['ipaddr'])
                        task.end(task_id, "sync the image to host:%s success" % rep_json['ipaddr'])
            logger.info("start sync template diff image")

            for template in templates:
                if template.version > 0:
                    image_diff = self._get_sync_images(template, 1, sys_base['path'], data_base['path'])
                    # 这里只是同步base文件，因此源文件和md5都要更新
                    for image in image_diff:
                        image['disk_file'] = image['backing_file']
                        image['md5_sum'] = get_file_md5(image['backing_file'])
                    logger.info("the image need to sync:%s", image_diff)
                    with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
                        for image in image_diff:
                            task = Task(image_id=image['image_id'], host_uuid=host_uuid, version=template.version)
                            task_id = create_uuid()
                            task.begin(task_id, "start sync the image to host:%s" % ipaddr)
                            logger.info("sync image %s to host %s, task_id:%s", image['image_id'], ipaddr, task_id)
                            future = executor.submit(self.sync, host, controller.ip, 1, image, task_id)
                            all_task.append(future)
                        for future in as_completed(all_task):
                            rep_json = future.result()
                            task = Task(image_id=rep_json['image_id'], host_uuid=rep_json['host_uuid'],
                                        version=template.version)
                            if rep_json.get('code') != 0:
                                logger.info("sync the image %s to host:%s failed:%s", rep_json['image_id'],
                                            rep_json['ipaddr'], rep_json.get('data'))
                                task.error(task_id, "sync the image to host:%s failed:%s" %
                                           (rep_json['ipaddr'], rep_json.get('data')))
                            else:
                                logger.info("sync the image %s to host:%s success", rep_json['image_id'],
                                            rep_json['ipaddr'])
                                task.end(task_id, "sync the image to host:%s success" % rep_json['ipaddr'])
                    logger.info("sync the diff image to new node. template:%s", template.name)
        except Exception as e:
            logger.exception("sys images failed:%s", e)

    def delete_instance_only(self, ipaddr, info):
        try:
            self._delete_instance(ipaddr, info)
        except:
            return False
        return True

    def check_need_resync(self, template):
        """
        检查该模板是否有节点需要重传，如果有并且节点在线，则需要先重传才能更新
        :return:
        """
        devices = db_api.get_devices_by_instance(template.uuid)
        nodes = db_api.get_node_with_all({'resource_pool_uuid': template.pool_uuid})
        for device in devices:
            for node in nodes:
                task = db_api.get_image_task_state_first({"image_id": device.uuid, "host_uuid": node.uuid})
                if task and task.status == "error":
                    ret = check_node_status(node.ip)
                    if ret.get('code') == 0:
                        return node.ip

    def add_scheduler_task(self, app):
        # 模板定时更新的任务
        with app.app_context():
            scheduler_path = constants.TEMPLATE_SCHEDULER_PATH
            if os.path.exists(scheduler_path):
                for file in os.listdir(scheduler_path):
                    filepath = os.path.join(scheduler_path, file)
                    try:
                        content = FileOp(filepath).read()
                        info = content.split("_")
                        template_uuid = info[0]
                        job_id = info[1]
                        run_date = info[2]
                        trigger = DateTrigger(run_date=run_date)
                        YzyAPScheduler().add_job(jobid=job_id, func=self._save_template,
                                                 args=(template_uuid, ), trigger=trigger)
                    except Exception as e:
                        logger.error("add template scheduler task error:%s", e)

    # @single_lock
    # def save_template_with_lock(self, template_uuid):
    #     time.sleep(2)
    #     self._save_template(template_uuid)
    #     # 如果是定时任务，则需要删除记录定时任务的文件
    #     try:
    #         filepath = os.path.join(constants.TEMPLATE_SCHEDULER_PATH, template_uuid)
    #         if os.path.exists(filepath):
    #             logger.info("delete scheduler file:%s", filepath)
    #             os.remove(filepath)
    #     except:
    #         pass

    def upgrade_template(self, template_uuid, upgrade_time=None):
        if upgrade_time:
            return self.save_template_with_time(template_uuid, upgrade_time)
        else:
            return self.upgrade(template_uuid)

    def upgrade(self, template_uuid):
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("instance template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")
        if constants.STATUS_COPING == template.status:
            logger.error("instance template is copying", template_uuid)
            return get_error_result("TemplateCopying")
        if constants.STATUS_DOWNLOADING == template.status:
            logger.error("instance template is downloading", template_uuid)
            return get_error_result("TemplateDownloading")
        result = self.check_need_resync(template)
        if result:
            return get_error_result("TemplateNeedResync", node=result)
        task = Thread(target=self._save_template, args=(template_uuid, ))
        task.start()
        return get_error_result("Success")

    def save_template_with_time(self, template_uuid, upgrade_time):
        """
        问题：
        1、时区问题，保存的默认是本地时间，如果服务器时区变化，会有问题
        """
        run_date = datetime.strptime(upgrade_time, "%Y-%m-%d %H:%M:%S")
        logger.info("save template run_date:%s", run_date)
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("instance template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")
        result = self.check_need_resync(template)
        if result:
            return get_error_result("TemplateNeedResync", node=result)
        if datetime.now() > run_date:
            logger.info("the upgrade time is less than now, skip")
            return get_error_result("UpdateTimeError")
        filepath = os.path.join(constants.TEMPLATE_SCHEDULER_PATH, template_uuid)
        file_read = FileOp(filepath)
        if file_read.exist_file():
            content = file_read.read()
            job_id = content.split('_')[1]
            logger.info("the template task already exists, remove")
            YzyAPScheduler().remove_job(job_id)
        job_id = create_uuid()
        trigger = DateTrigger(run_date=run_date)
        YzyAPScheduler().add_job(jobid=job_id, func=self._save_template,
                                 args=(template_uuid, ), trigger=trigger)
        content = template_uuid + "_" + job_id + "_" + upgrade_time
        FileOp(filepath, 'w').write_with_endline(content)
        logger.info("add template scheduler task, template_uuid:%s, run_date:%s", template_uuid, run_date)
        return get_error_result("Success")

    def _save_template(self, template_uuid, create=False):
        """
        保存模板
        :param template_uuid: the uuid of template
        :return:
        """
        logger.info("begin save template:%s", template_uuid)
        # 添加任务信息数据记录
        task_data = {
            "uuid": create_uuid(),
            "task_uuid": template_uuid,
            "name": constants.NAME_TYPE_MAP[13],
            "status": constants.TASK_RUNNING,
            "type": 13
        }
        db_api.create_task_info(task_data)
        task_obj = db_api.get_task_info_first({"uuid": task_data['uuid']})

        template = db_api.get_instance_template(template_uuid)
        sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
        if not (sys_base and data_base):
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("InstancePathNotExist")
        try:
            if not create:
                pre_status = template.status
                template.status = constants.STATUS_UPDATING
                template.soft_update()
                try:
                    instance_info = {
                        "uuid": template.uuid,
                        "name": template.name
                    }
                    node = db_api.get_node_with_first({'uuid': template.host_uuid})
                    self._stop_instance(node.ip, instance_info, timeout=120)
                except Exception as e:
                    template.status = pre_status
                    template.soft_update()
                    logger.error("stop template %s failed:%s", template.uuid, e)
                    task_obj.update({"status": constants.TASK_ERROR})
                    task_obj.soft_update()
                    return get_error_result("TemplateStopError", name=template.name, data=str(e))
            controller_image = db_api.get_controller_image()
            controller = db_api.get_controller_node()
            # 如果是定时任务，则需要删除记录定时任务的文件
            try:
                filepath = os.path.join(constants.TEMPLATE_SCHEDULER_PATH, template_uuid)
                if os.path.exists(filepath):
                    logger.info("delete scheduler file:%s", filepath)
                    os.remove(filepath)
            except:
                pass
            personal_maintenance_uuid = []
            desktop_active_uuid = []
            if constants.EDUCATION_DESKTOP == template.classify:
                desktops = db_api.get_desktop_with_all({'template_uuid': template_uuid})
                for desktop in desktops:
                    if desktop.active:
                        desktop_active_uuid.append(desktop.uuid)
                    desktop.active = False
                    desktop.soft_update()
            elif constants.PERSONAL_DEKSTOP == template.classify:
                desktops = db_api.get_personal_desktop_with_all({'template_uuid': template_uuid})
                for desktop in desktops:
                    if not desktop.maintenance:
                        personal_maintenance_uuid.append(desktop.uuid)
                    desktop.maintenance = True
                    desktop.soft_update()
            else:
                desktops = []

            # 第二步，合并差异磁盘前，要关闭所有链接的桌面
            all_task = list()
            failed_num = 0
            success_num = 0
            for desktop in desktops:
                logger.info("recreate all instance in desktop:%s", desktop.name)
                instances = db_api.get_instance_by_desktop(desktop.uuid)
                with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
                    for instance in instances:
                        logger.info("delete instance %s thread", instance.uuid)
                        ins_sys, ins_data = self._get_storage_path_with_uuid(instance.sys_storage,
                                                                               instance.data_storage)
                        info = {
                            "uuid": instance.uuid,
                            "name": instance.name,
                            "sys_base": ins_sys,
                            "data_base": ins_data
                        }
                        node = db_api.get_node_by_uuid(instance.host_uuid)
                        future = executor.submit(self.delete_instance_only, node.ip, info)
                        all_task.append(future)
                    for future in as_completed(all_task):
                        result = future.result()
                        if not result:
                            failed_num += 1
                        else:
                            success_num += 1

            new_version = template.version + 1
            images = self._get_sync_images(template, new_version, sys_base, data_base, md5=True, update=True)
            logger.info("sync the diff disk file to compute nodes")
            nodes = db_api.get_node_by_pool_uuid(template.pool_uuid)
            hosts = list()
            compute_tasks = list()
            controller_tasks = list()
            # 第三步其他节点同步镜像
            for item in nodes:
                if item.ip != controller.ip:
                    hosts.append({
                        'ipaddr': item.ip,
                        'host_uuid': item.uuid
                    })
            with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
                for host in hosts:
                    ipaddr = host['ipaddr']
                    for image in images:
                        task = Task(image_id=image['image_id'], host_uuid=host['host_uuid'], version=new_version)
                        task_id = create_uuid()
                        task.begin(task_id, "start sync the image to host:%s" % ipaddr)
                        logger.info("sync image %s to host %s, task_id:%s", image['image_id'], ipaddr, task_id)
                        future = executor.submit(self.sync, host, controller_image.ip, new_version, image, task_id)
                        compute_tasks.append(future)
                for future in as_completed(compute_tasks):
                    rep_json = future.result()
                    task = Task(image_id=rep_json['image_id'], host_uuid=rep_json['host_uuid'], version=new_version)
                    if rep_json.get('code') != 0:
                        logger.info("sync the image %s to host:%s failed:%s", rep_json['image_id'],
                                    rep_json['ipaddr'], rep_json.get('data'))
                        task.error(rep_json['task_id'], "sync the image to host:%s failed:%s" %
                                   (rep_json['ipaddr'], rep_json.get('data')))
                    else:
                        logger.info("sync the image %s to host:%s success", rep_json['image_id'], rep_json['ipaddr'])
                        task.end(rep_json['task_id'], "sync the image to host:%s success" % rep_json['ipaddr'])

            # 第四步是本节点同步差异磁盘并合并
            logger.info("merge the diff disk file in local")
            host = {
                'ipaddr': controller.ip,
                'host_uuid': controller.uuid
            }
            with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
                for image in images:
                    task = Task(image_id=image['image_id'], host_uuid=controller.uuid, version=new_version)
                    task_id = create_uuid()
                    task.begin(task_id, "start sync the image to host:%s" % controller.ip)
                    logger.info("sync image %s to host %s, task_id:%s", image['image_id'], controller.ip, task_id)
                    future = executor.submit(self.sync, host, controller_image.ip, new_version, image, task_id)
                    controller_tasks.append(future)
                for future in as_completed(controller_tasks):
                    rep_json = future.result()
                    task = Task(image_id=rep_json['image_id'], host_uuid=rep_json['host_uuid'], version=new_version)
                    if rep_json.get('code') != 0:
                        logger.info("sync the image %s to host:%s failed:%s", rep_json['image_id'],
                                    rep_json['ipaddr'], rep_json.get('data'))
                        task.error(rep_json['task_id'], "sync the image to host:%s failed:%s" %
                                   (rep_json['ipaddr'], rep_json.get('data')))
                        template.status = constants.STATUS_ERROR
                        template.updated_time = datetime.utcnow()
                        template.soft_update()
                        task_obj.update({"status": constants.TASK_ERROR})
                        task_obj.soft_update()
                        return get_error_result("TemplateUpdateError", name=template.name)
                    else:
                        logger.info("sync the image %s to host:%s success", rep_json['image_id'], rep_json['ipaddr'])
                        task.end(rep_json['task_id'], "sync the image to host:%s success" % rep_json['ipaddr'])
            # 第四步是删除并重建模板的差异磁盘
            disks = self._get_disk_and_backing_file(template, sys_base, data_base)
            rep_json = self.recreate_disk(controller.ip, disks)
            if rep_json.get("code", -1) != 0:
                logger.error("instance template: %s recreate fail:%s", template_uuid, rep_json['msg'])
                template.status = constants.STATUS_ERROR
                template.updated_time = datetime.utcnow()
                template.soft_update()
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return get_error_result("TemplateRecreateFail", name=template.name)

            # 第四步是新建所有桌面，并且处于关机状态
            failed_num = 0
            success_num = 0
            devices = db_api.get_devices_modify_with_all({"template_uuid": template.uuid})
            for device in devices:
                # 模板添加了磁盘，更新时要将引用的桌面都添加磁盘
                if constants.DEVICE_NEED_ADDED == device.state:
                    logger.info("device %s state is need add", device.device_name)
                    instance_add_disks = list()
                    template_add_disks = list()
                    template_add_disks.append({
                        "uuid": device.uuid,
                        "type": constants.IMAGE_TYPE_DATA,
                        "device_name": device.device_name,
                        "image_id": "",
                        "instance_uuid": device.template_uuid,
                        "boot_index": device.boot_index,
                        "disk_bus": "virtio",
                        "source_type": "file",
                        "source_device": "disk",
                        "size": device.size,
                        "used": device.used
                    })
                    for desktop in desktops:
                        instances = db_api.get_instance_with_all({'desktop_uuid': desktop.uuid})
                        for instance in instances:
                            info = {
                                "uuid": create_uuid(),
                                "type": constants.IMAGE_TYPE_DATA,
                                "device_name": device.device_name,
                                "image_id": device.uuid,
                                "instance_uuid": instance.uuid,
                                "boot_index": device.boot_index,
                                "size": device.size
                            }
                            logger.info("instance %s add disk", instance.uuid)
                            instance_add_disks.append(info)
                    db_api.insert_with_many(models.YzyInstanceDeviceInfo, template_add_disks)
                    if instance_add_disks:
                        db_api.insert_with_many(models.YzyInstanceDeviceInfo, instance_add_disks)
                    device.deleted = True
                # 模板删除了磁盘，更新时需要将引用的桌面已有磁盘都删除
                elif constants.DEVICE_NEED_DELETED == device.state:
                    backing_dir = os.path.join(data_base, constants.IMAGE_CACHE_DIRECTORY_NAME)
                    backing_file_name = constants.IMAGE_FILE_PREFIX % str(1) + device.uuid
                    backing_file = os.path.join(backing_dir, backing_file_name)
                    logger.info("device %s state is need delete", device.device_name)
                    origin_device = db_api.get_devices_with_first({"uuid": device.uuid})
                    for desktop in desktops:
                        instances = db_api.get_instance_with_all({'desktop_uuid': desktop.uuid})
                        for instance in instances:
                            items = db_api.get_devices_with_all({"instance_uuid": instance.uuid, "image_id": origin_device.uuid})
                            for item in items:
                                logger.info("instance %s delete disk: %s", instance.uuid, item.uuid)
                                item.soft_delete()
                    command_data = {
                        "command": "delete_base",
                        "handler": "TemplateHandler",
                        "data": {
                            "image": {
                                "disk_file": backing_file
                            }
                        }
                    }
                    # 删除各个节点上的base文件
                    for node in nodes:
                        node_ip = node.ip
                        logger.info("delete base file %s in node %s", device.uuid, node.ip)
                        rep_json = compute_post(node_ip, command_data)
                        if rep_json.get("code", -1) != 0:
                            logger.error("delete base image fail: node %s image %s delete error", node.ip, device.uuid)
                    try:
                        template_dir = os.path.join(data_base, template.uuid)
                        disk_file = os.path.join(template_dir, constants.DISK_FILE_PREFIX + device.uuid)
                        logger.info("delete file %s", disk_file)
                        os.remove(disk_file)
                    except:
                        pass
                    device.deleted = True
                    origin_device.soft_delete()
                else:
                    pass
                device.soft_update()
                logger.info("template device %s update end", device.device_name)

            desktop_tasks = list()
            for desktop in desktops:
                logger.info("recreate all instance in desktop:%s", desktop.name)
                subnet = db_api.get_subnet_by_uuid(desktop.subnet_uuid)
                instances = db_api.get_instance_by_desktop(desktop.uuid)
                with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
                    for instance in instances:
                        logger.info("recreate instance %s thread", instance.uuid)
                        ins_sys, ins_data = self._get_storage_path_with_uuid(instance.sys_storage,
                                                                             instance.data_storage)
                        future = executor.submit(self.create_instance, desktop, subnet, instance,
                                                 ins_sys, ins_data, power_on=False)
                        desktop_tasks.append(future)
                    for future in as_completed(desktop_tasks):
                        result = future.result()
                        if result.get('code') != 0:
                            failed_num += 1
                        else:
                            success_num += 1
                if constants.EDUCATION_DESKTOP == template.classify:
                    if desktop.uuid in desktop_active_uuid:
                        desktop.active = True
                        desktop.soft_update()
                elif constants.PERSONAL_DEKSTOP == template.classify:
                    if desktop.uuid in personal_maintenance_uuid:
                        desktop.maintenance = False
                        desktop.soft_update()
                db.session.flush()

            # 保存成功
            template.version = new_version
            template.status = constants.STATUS_INACTIVE
            template.updated_time = datetime.utcnow()
            template.soft_update()
        except Exception as e:
            logger.exception("save template error:%s", e, exc_info=True)
            template.status = constants.STATUS_ERROR
            template.updated_time = datetime.utcnow()
            template.soft_update()
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
        task_obj.update({"status": constants.TASK_COMPLETE})
        task_obj.soft_update()
        return get_error_result("Success")

    def copy_template(self, data):
        """
        复制模板：原理就是复制模板的系统盘和数据盘，进行重命名作为基础差异盘
        :param data:
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
        :return:
        """
        uuid = create_uuid()
        # 添加任务信息数据记录
        task_uuid = create_uuid()
        task_data = {
            "uuid": task_uuid,
            "task_uuid": uuid,
            "name": constants.NAME_TYPE_MAP[8],
            "status": constants.TASK_RUNNING,
            "type": 8
        }
        db_api.create_task_info(task_data)
        task_obj = db_api.get_task_info_first({"uuid": task_uuid})
        template = db_api.get_template_with_all({'name': data['name']})
        if template:
            logger.error("template: %s already exist", data['name'])
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("TemplateAlreadyExist", name=data['name'])

        template_uuid = data['template_uuid']
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("instance template: %s not exist", template_uuid)
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("TemplateNotExist")

        network = db_api.get_network_by_uuid(data['network_uuid'])
        if not network:
            logger.error("network: %s not exist", data['network_uuid'])
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("NetworkInfoNotExist")
        # IP分配检测
        subnet_uuid = data.get('subnet_uuid', None)
        if subnet_uuid:
            subnet = db_api.get_subnet_by_uuid(data['subnet_uuid'])
            if not subnet:
                logger.error("subnet: %s not exist", data['subnet_uuid'])
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return get_error_result("SubnetNotExist")
            subnet = subnet.dict()
        else:
            subnet = {}
        if not subnet and not data.get('bind_ip', None):
            # dhcp方式获取IP
            data['bind_ip'] = ''
        else:
            all_ips = find_ips(subnet['start_ip'], subnet['end_ip'])
            education_used_ips = self.get_personal_used_ipaddr(subnet_uuid)
            if not data.get('bind_ip', None):
                # 选择子网并且系统分配，模板IP从后往前取值
                all_ip_reverse = all_ips[::-1]
                for ipaddr in all_ip_reverse:
                    if ipaddr not in education_used_ips:
                        data['bind_ip'] = ipaddr
                        break
                else:
                    task_obj.update({"status": constants.TASK_ERROR})
                    task_obj.soft_update()
                    return get_error_result("IPNotEnough")
            else:
                # 选择子网并且固定IP，检查该IP是否已被占用
                logger.info('education_used_ips: %s, bind_ip: %s' % (education_used_ips, data['bind_ip']))
                if data['bind_ip'] in education_used_ips:
                    task_obj.update({"status": constants.TASK_ERROR})
                    task_obj.soft_update()
                    return get_error_result("IPInUse")

            if data['bind_ip'] not in all_ips:
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return get_error_result("IPNotInRange", ipaddr=data['bind_ip'])
            if template.bind_ip != data['bind_ip'] and data['bind_ip'] in education_used_ips:
                task_obj.update({"status": constants.TASK_ERROR})
                task_obj.soft_update()
                return get_error_result("IPInUse")
        logger.info("check bind_ip info")
        sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
        if not (sys_base and data_base):
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("InstancePathNotExist")
        cur_sys, cur_data = self._get_template_storage()
        if not (sys_base and sys_base):
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("InstancePathNotExist")

        # 如果被复制的模板有节点异常，先要重传
        result = self.check_need_resync(template)
        if result:
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("TemplateNeedResync", node=result)
        # mac和port分配
        self.used_macs = self.get_used_macs()
        mac_addr = generate_mac(self.used_macs)
        logger.info("allocate mac info")
        port_uuid = create_uuid()
        # 模板所在节点判断
        if data.get('host_uuid', None):
            node = db_api.get_node_by_uuid(data['host_uuid'])
        else:
            node = db_api.get_controller_node()
        values = {
            "uuid": uuid,
            "name": data['name'],
            "desc": data.get('desc'),
            "owner_id": data['owner_id'],
            "pool_uuid": data['pool_uuid'],
            "host_uuid": node.uuid,
            "network_uuid": data['network_uuid'],
            "subnet_uuid": data.get('subnet_uuid', None),
            "sys_storage": cur_sys['uuid'],
            "data_storage": cur_data['uuid'],
            "version": 1,
            "bind_ip": data.get('bind_ip'),
            "os_type": template.os_type,
            "classify": template.classify,
            "vcpu": template.vcpu,
            "ram": template.ram,
            "mac": mac_addr,
            "port_uuid": port_uuid,
            "status": constants.STATUS_C_CREATING
        }
        # 磁盘记录数据库
        new_template = db_api.create_instance_template(values)
        values['id'] = new_template['id']
        pre_status = template.status
        template.status = constants.STATUS_COPING
        template.soft_update()
        logger.info("create template db info")
        node_info = {
            "uuid": node.uuid,
            "ipaddr": node.ip
        }
        images, kvm_disks, add_disks = self._get_copy_images(template, new_template.uuid,
                                                             sys_base, data_base, cur_sys['path'], cur_data['path'])
        db_api.insert_with_many(models.YzyInstanceDeviceInfo, add_disks)
        # 注意线程后台运行，不能传输数据库对象，会有session绑定问题
        task = Thread(target=self.create_template_thread, args=(node_info, values, subnet, template_uuid, pre_status,
                                                                images, kvm_disks, ))
        task.start()
        ret = {
            "uuid": new_template.uuid,
            "name": data['name'],
            "version": 1
        }
        task_obj.update({"status": constants.TASK_COMPLETE})
        task_obj.soft_update()
        return get_error_result("Success", ret)

    def create_template_thread(self, node_info, data, subnet, origin, pre_status, images, kvm_disks, power_on=False):
        origin_template = db_api.get_instance_template(origin)
        new_template = db_api.get_instance_template(data['uuid'])
        nodes = db_api.get_node_with_all({'resource_pool_uuid': new_template.pool_uuid})
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for node in nodes:
                host = {
                    "ipaddr": node.ip,
                    "host_uuid": node.uuid
                }
                for image in images:
                    task = Task(image_id=image['new_image_id'], host_uuid=host['host_uuid'], version=1)
                    task_id = create_uuid()
                    task.begin(task_id, "start copy the image %s to %s in host:%s" %
                               (image['image_id'], image['new_image_id'], host['ipaddr']))
                    logger.info("copy image %s to %s in host %s, task_id:%s", image['image_id'],
                                image['new_image_id'], host['ipaddr'], task_id)
                    future = executor.submit(self.copy, host, image, task_id)
                    all_task.append(future)
            for future in as_completed(all_task):
                rep_json = future.result()
                task = Task(image_id=rep_json['image_id'], host_uuid=rep_json['host_uuid'], version=1)
                if rep_json.get('code') != 0:
                    task.error(rep_json['task_id'], "copy the image in host:%s failed:%s" %
                               (rep_json['ipaddr'], rep_json.get('data')))
                    logger.info("copy the image %s in host:%s failed:%s", rep_json['image_id'],
                                rep_json['ipaddr'], rep_json.get('data'))
                else:
                    task.end(rep_json['task_id'], "copy the image in host:%s success" % rep_json['ipaddr'])
                    logger.info("copy the image %s in host:%s success", rep_json['image_id'], rep_json['ipaddr'])

        try:
            # 获取网络信息，保证网桥等设备存在
            net = db_api.get_interface_by_network(data['network_uuid'], node_info['uuid'])
            if not net:
                logger.error("node %s network info %s error", node_info['uuid'], data['network_uuid'])
                return get_error_result("NodeNetworkInfoError")

            vif_info = {
                "uuid": net.YzyNetworks.uuid,
                "vlan_id": net.YzyNetworks.vlan_id,
                "interface": net.nic,
                "bridge": constants.BRIDGE_NAME_PREFIX + net.YzyNetworks.uuid[:constants.RESOURCE_ID_LENGTH]
            }
            network_info = self.create_network_info(vif_info, data['port_uuid'], data['mac'], subnet, data['bind_ip'])
            logger.info("get instance network info")
            # 用于加载ISO的CDROM，加载后的ISO重启需要保存
            kvm_disks.append({
                "bus": "ide",
                "dev": "hdb",
                "type": "cdrom",
                "path": ""
            })

            # instance info
            instance_info = self._get_instance_info(data, template=True)
            self._create_instance(node_info['ipaddr'], instance_info, network_info, kvm_disks, power_on=power_on)
        except Exception as e:
            logger.exception("create template failed:%s", e)
            devices = db_api.get_devices_with_all({"instance_uuid": new_template.uuid})
            for device in devices:
                device.soft_delete()
            new_template.soft_delete()
            origin_template.status = pre_status
            origin_template.soft_update()
            return get_error_result("TemplateCreateFail", name=data['name'], data=str(e))

        if power_on:
            new_template.status = constants.STATUS_ACTIVE
        else:
            new_template.status = constants.STATUS_INACTIVE
        new_template.soft_update()
        origin_template.status = pre_status
        origin_template.soft_update()
        logger.info("copy the template success, node:%s", node_info['ipaddr'])
        return get_error_result("Success")

    def edit_template(self, template_uuid):
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("instance template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")

        # # 模板的启动状态
        # if template.status != "active":
        # 启动模板
        ret_json = self.start_template(template_uuid)
        if ret_json['code'] != 0:
            # 启动失败
            logger.error("edit template: %s, start template fail" % template_uuid)
            return get_error_result("TemplateStartFail", name=template.name)

        # 返回对应的token链接
        node = db_api.get_controller_node()
        websockify_url = "ws://%s:%s/websockify/?token=%s" % (node.ip, constants.WEBSOCKIFY_PORT, template_uuid)
        logger.info("start edit success,websockify_url: %s, attach:%s", websockify_url, template.attach)
        return get_error_result("Success", {'websockify_url': websockify_url, 'attach': template.attach})

    def get_downloading_path(self, template_uuid):
        template = db_api.get_instance_template(template_uuid)
        sys_base, data_base = self._get_template_storage()
        if not (sys_base and sys_base):
            return get_error_result("InstancePathNotExist")
        sys_info = db_api.get_devices_with_first({'instance_uuid': template.uuid, 'type': constants.IMAGE_TYPE_SYSTEM})
        backing_path = os.path.join(sys_base['path'], constants.IMAGE_CACHE_DIRECTORY_NAME)
        file_name = "%s_c%s_r%s_d%s" % ((template['name'] + '_' + template['uuid']),
                                        template['vcpu'], template['ram'], sys_info['size'])
        dest_path = os.path.join(backing_path, file_name)
        return dest_path

    def get_template_sys_space(self, node_uuid):
        storages = db_api.get_node_storage_all({'node_uuid': node_uuid})
        for storage in storages:
            if str(constants.TEMPLATE_SYS) in storage.role:
                free = round(storage.free/1024/1024/1024, 2)
                return free

    def download_template(self, template_uuid):
        # 添加任务信息记录
        task_data = {
            "uuid": create_uuid(),
            "task_uuid": template_uuid,
            "name": constants.NAME_TYPE_MAP[9],
            "status": constants.TASK_RUNNING,
            "type": 9,
        }
        db_api.create_task_info(task_data)
        task_obj = db_api.get_task_info_first({"uuid": task_data['uuid']})
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("instance template: %s not exist", template_uuid)
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("TemplateNotExist")
        if constants.STATUS_DOWNLOADING == template.status:
            logger.error("template is already in downloading")
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("Success")
        # 下载时，将convert生产的目标文件放到当前存储路径下
        cur_sys_base, cur_data_base = self._get_template_storage()
        if not (cur_sys_base and cur_data_base):
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("InstancePathNotExist")
        sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
        node = db_api.get_node_with_first({'uuid': template['host_uuid']})
        sys_info = db_api.get_devices_with_first(
            {'instance_uuid': template['uuid'], 'type': constants.IMAGE_TYPE_SYSTEM})
        image_info = {
            "need_convert": True if template.version > 0 else False,
            "disk_uuid": sys_info.uuid,
            "size": sys_info.size
        }
        # 下载合成后还需要写头部信息，因此需要两倍空间
        free = round(cur_sys_base['free']/1024/1024/1024, 2)
        total_size = 0
        # 获取当前磁盘的上层backing_file
        backing_dir = os.path.join(sys_base, constants.IMAGE_CACHE_DIRECTORY_NAME)
        backing_file = os.path.join(backing_dir, constants.IMAGE_FILE_PREFIX % str(1) + sys_info.uuid)
        image_info['backing_file'] = backing_file
        total_size += round(os.path.getsize(backing_file) / 1024 / 1024 / 1024, 2)
        if sys_info.image_id:
            image = db_api.get_image_with_first({'uuid': sys_info.image_id})
            total_size += image.size
        if total_size * 2 > free:
            logger.exception("the disk size in not enough, return")
            task_obj.update({"status": constants.TASK_ERROR})
            task_obj.soft_update()
            return get_error_result("SpaceNotEnough")

        # convert后的目的地址
        cur_backing_dir = os.path.join(cur_sys_base['path'], constants.IMAGE_CACHE_DIRECTORY_NAME)
        new_uuid = template.name + '_' + template.uuid
        dest_file = os.path.join(cur_backing_dir, new_uuid)
        image_info['dest_file'] = dest_file
        pre_status = template['status']
        template.status = constants.STATUS_DOWNLOADING
        template.soft_update()
        logger.info("start downloading thread")
        task = Thread(target=self.download_thread, args=(node.ip, template_uuid, pre_status, image_info, ))
        task.start()
        task_obj.update({"status": constants.TASK_COMPLETE})
        task_obj.soft_update()
        return get_error_result("Success")

    def download_thread(self, ipaddr, template_uuid, pre_status, image_info):
        template = db_api.get_instance_template(template_uuid)
        logger.info("start download template:%s", template.name)
        new_uuid = template.name + '_' + template.uuid
        convert = self.convert(ipaddr, image_info['backing_file'], image_info['dest_file'], image_info['need_convert'])
        if convert.get("code", -1) != 0:
            logger.error("convert template: %s failed:%s", template_uuid, convert['msg'])
            template.status = pre_status
            template.soft_update()
            return get_error_result("TemplateDownloadFail", name=template.name)
        logger.info("convert end, start write head to image")
        rep_json = self.write_head(ipaddr, convert['data']['path'], template.vcpu, template.ram, image_info['size'])
        if rep_json.get("code", -1) != 0:
            logger.error("write head to image: %s failed:%s", convert['data']['path'], rep_json.get('data'))
            template.status = pre_status
            template.soft_update()
            return get_error_result("TemplateDownloadFail", name=template.name)
        logger.info("convert template success")
        template.status = pre_status
        template.soft_update()
        return get_error_result("Success")

    def attach_source(self, data):
        """
        :param data:
            {
                "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                "name": "template1"
                "iso_uuid": ""
            }
        :return:
        """
        template_uuid = data.get('uuid')
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("instance template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")
        iso = db_api.get_iso_with_first({"uuid": data['iso_uuid']})
        if not iso:
            logger.error("the iso in not exists")
            return get_error_result("ISOFileNotExistError")
        instance = {
            "uuid": data['uuid'],
            "name": data['name']
        }
        node = db_api.get_node_with_first({"uuid": template.host_uuid})
        rep_json = self._attach_source(node.ip, instance, iso.path)
        if rep_json.get("code", -1) != 0:
            logger.error("attach template:%s device failed:%s", data['uuid'], rep_json['msg'])
            return get_error_result("TemplateLoadIsoFail", name=data['name'])
        template.attach = iso.uuid
        template.soft_update()
        return get_error_result("Success")

    def detach_source(self, data):
        """
        :param data:
            {
                "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                "name": "template1"
            }
        :return:
        """
        template_uuid = data.get('uuid')
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("instance template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")
        instance = {
            "uuid": data['uuid'],
            "name": data['name']
        }
        node = db_api.get_node_with_first({"uuid": template.host_uuid})
        rep_json = self._detach_source(node.ip, instance)
        if rep_json.get("code", -1) != 0:
            logger.error("detach template:%s device failed:%s", data['uuid'], rep_json['msg'])
            return get_error_result("TemplateLoadIsoFail", name=data['name'])
        template.attach = ''
        template.soft_update()
        return get_error_result("Success")

    def send_key(self, data):
        """
        :param data:
            {
                "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                "name": "template1"
            }
        :return:
        """
        template_uuid = data.get('uuid')
        template = db_api.get_instance_template(template_uuid)
        if not template:
            logger.error("instance template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")
        instance = {
            "uuid": data['uuid'],
            "name": data['name']
        }
        node = db_api.get_node_with_first({"uuid": template.host_uuid})
        rep_json = self._send_key(node.ip, instance)
        if rep_json.get("code", -1) != 0:
            logger.error("template send key failed:%s", data['uuid'], rep_json['msg'])
            return get_error_result("TemplateSendKeyFail", name=data['name'])
        return get_error_result("Success")

    def retransmit(self, data):
        device = db_api.get_devices_with_first({"uuid": data['image_id']})
        template = db_api.get_instance_template(device.instance_uuid)
        if not template:
            return get_error_result("TemplateNotExist")
        sys_base, data_base = self._get_storage_path_with_uuid(template.sys_storage, template.data_storage)
        if not (sys_base and data_base):
            return get_error_result("InstancePathNotExist")
        if constants.TEMPLATE_SYS == data['role']:
            base_path = sys_base
        elif constants.TEMPLATE_DATA == data['role']:
            base_path = data_base
        else:
            return get_error_result("ParamError")

        backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
        backing_file_name = constants.IMAGE_FILE_PREFIX % str(1) + data['image_id']
        image_path = os.path.join(backing_dir, backing_file_name)
        logger.info("get the image path:%s", image_path)
        if not os.path.exists(image_path):
            return get_error_result("TemplateImageNotExist")

        node = db_api.get_node_with_first({'ip': data['ipaddr']})
        if not node:
            return get_error_result("NodeNotExist")
        logger.info("delete the task info before restransmit, image:%s", data['image_id'])
        tasks = db_api.get_task_all({'image_id': data['image_id'], 'host_uuid': node.uuid})
        for task in tasks:
            task.soft_delete()

        controller_image = db_api.get_controller_image()
        image = {
            "image_id": data['image_id'],
            "disk_file": image_path,
            "backing_file": image_path,
            "dest_path": image_path,
            "md5_sum": get_file_md5(image_path)
        }
        task = Task(image_id=image['image_id'], host_uuid=node.uuid, version=data['version'])
        task_id = create_uuid()
        task.begin(task_id, "start sync the image to host:%s" % data['ipaddr'])
        logger.info("sync image %s to host %s, task_id:%s", image['image_id'], data['ipaddr'], task_id)
        host = {
            "ipaddr": data['ipaddr'],
            "host_uuid": node.uuid
        }
        # 重传的永远是合并后的基础镜像，所以重传后不需要再commit，所以版本号不会大于1
        res = self.sync(host, controller_image.ip, 1, image, task_id)
        if res.get('code') != 0:
            task.error(task_id, "sync the image to host:%s failed:%s" %
                       (data['ipaddr'], res['data']))
            return get_error_result("TemplateResyncError")
        else:
            logger.info("sync the image %s to host:%s success", image['image_id'], data['ipaddr'])
            task.end(task_id, "sync the image to host:%s success" % data['ipaddr'])
        return get_error_result("Success")

    def check_ip(self, data):
        try:
            subnet = db_api.get_subnet_by_uuid(data['subnet_uuid'])
            if not subnet:
                logger.error("check ip error subnet:%s is not exist", data['subnet_uuid'])
                return get_error_result("SubnetNotExist")
            template = db_api.get_template_by_uuid_first({"uuid": data['uuid']})
            if not template:
                logger.error("template %s not exist", template)
                return get_error_result("TemplateNotExist")
            all_ips = find_ips(subnet.start_ip, subnet.end_ip)
            if data['ip'] not in all_ips:
                return get_error_result("IPNotInRange", ipaddr=data['ip'])
            used_ips = self.get_personal_used_ipaddr(data['subnet_uuid'])
            if template.bind_ip != data['ip'] and data['ip'] in used_ips:
                return get_error_result("IPInUse")
        except Exception as e:
            return get_error_result("OtherError")
        return get_error_result("Success")
