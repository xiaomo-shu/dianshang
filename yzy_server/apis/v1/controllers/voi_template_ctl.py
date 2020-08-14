import os
import logging
import string
import re
import json
from threading import  Thread
from datetime import datetime
from yzy_server.database import apis as db_api
from yzy_server.database import models
from yzy_server.crontab_tasks import YzyAPScheduler
from common import constants
from common import cmdutils
from common.errcode import get_error_result
from common.config import SERVER_CONF, FileOp
from common.utils import create_uuid, compute_post, find_ips, check_node_status, single_lock,\
                        size_to_G, voi_terminal_post, gi_to_section, bytes_to_section, section_to_G
from .desktop_ctl import BaseController, generate_mac


logger = logging.getLogger(__name__)


class VoiTemplateController(BaseController):

    def __init__(self):
        super().__init__()
        self.system_type_dict = {
            "windows_7_x64": 1,
            "windows_7": 2,
            "windows_10_x64": 3,
            "Other": 0,
        }
        self.disk_type_dict = {
            constants.IMAGE_TYPE_SYSTEM: 0,
            constants.IMAGE_TYPE_DATA: 1
        }

    def get_qcow2_section(self, qcow2_file, default):
        """ 获取扇区大小
            qcow2_file: qcow2文件的路径
            default:  默认size 单位：G
        """
        try:
            stdout, stderror = cmdutils.execute('qemu-img info %s' % qcow2_file,
                                                shell=True, timeout=20, run_as_root=True)
            logger.info("qemu-img info execute end, stdout:%s, stderror:%s", stdout, stderror)
            result = re.search(r"virtual size: \d+G \((\d+) bytes\)", stdout).group(1)
            logger.info("qemu-img info execute end, stdout:%s,  stderror:%s, result: %s", stdout, stderror, result)
            return int(result) / 512
            # logger.info(result)
        except Exception as e:
            logger.error("", exc_info=True)
            section = int(default) * 1024 * 1024 * 2
            return section

    def _check_template_params(self, data):
        if not data:
            return False
        name = data.get('name', '')
        network_uuid = data.get('network_uuid', '')
        vcpu = data.get('vcpu', '')
        ram = data.get('ram', '')
        if not (name and network_uuid and vcpu and ram):
            return False
        logger.info("check params ok")
        return True

    def _create_template(self, ipaddr, instance_info, network_info, disk_info, power_on=True, iso=False, configdrive=True):
        command_data = {
            "command": "create",
            "handler": "VoiHandler",
            "data": {
                "instance": instance_info,
                "network_info": network_info,
                "disk_info": disk_info,
                "power_on": power_on,
                "iso": iso,
                "configdrive": configdrive
            }
        }
        logger.info("create instance %s in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data, timeout=600)
        if rep_json.get("code", -1) != 0:
            logger.error("create instance:%s failed, node:%s, error:%s", instance_info['name'], ipaddr, rep_json.get('data'))
            message = rep_json['data'] if rep_json.get('data', None) else rep_json['msg']
            raise Exception(message)
        return rep_json

    def create_disk_info(self, data, version, sys_base, data_base, disk_generate=True):
        """
        生成模板的磁盘信息
        :return:
            [
                {
                    "uuid": "dfcd91e8-30ed-11ea-9764-000c2902e179",
                    "dev": "vda",
                    "boot_index": 0,
                    "image_id": "196df26e-2b92-11ea-a62d-000c29b3ddb9",
                    "image_version": 0,
                    "base_path": "/opt/ssd/instances"
                },
                {
                    "uuid": "f613f8ac-30ed-11ea-9764-000c2902e179",
                    "dev": "vdb",
                    "boot_index": -1,
                    "size": "50G",
                    "base_path": "/opt/ssd/datas"
                },
                ...
            ]
        """
        _disk_list = []
        if not disk_generate:
            _disk_list.append(data['system_disk'])
            for disk in data['data_disks']:
                _disk_list.append(disk)
            return _disk_list
        system_disk_dict = {
            "uuid": data['system_disk']['uuid'],
            "bus": data['system_disk'].get("bus", "sata"),
            "dev": "sda",
            "boot_index": 0,
            "size": "%dG" % int(data['system_disk']['size']),
            "image_id": data['system_disk'].get('image_id', ''),
            "image_version": version,
            "base_path": sys_base
        }
        _disk_list.append(system_disk_dict)

        zm = string.ascii_lowercase

        for disk in data.get('data_disks', []):
            _d = dict()
            inx = int(disk["inx"])
            size = int(disk["size"])
            _d["uuid"] = create_uuid()
            _d["bus"] = disk.get('bus', 'sata')
            _d["boot_index"] = inx + 1
            _d["size"] = "%dG" % size
            _d["dev"] = "sd%s" % zm[inx + 1]
            _d['base_path'] = data_base
            _disk_list.append(_d)
        # if data.get('iso', None):
        #     _disk_list.append({
        #         "bus": "ide",
        #         "dev": "hdb",
        #         "type": "cdrom",
        #         "path": data['iso']
        #     })
        #     _disk_list.append({
        #         "bus": "ide",
        #         "dev": "hdc",
        #         "type": "cdrom",
        #         "path": constants.VIRTIO_PATH
        #     })
        logger.debug("get disk info %s", _disk_list)
        return _disk_list

    def get_template_sys_space(self, node_uuid):
        storages = db_api.get_node_storage_all({'node_uuid': node_uuid})
        for storage in storages:
            if str(constants.TEMPLATE_SYS) in storage.role:
                free = round(storage.free/1024/1024/1024, 2)
                return free

    def create_template(self, data, disk_generate=True):
        """
        :param data:
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
        :return:
        """
        if not self._check_template_params(data):
            return get_error_result("ParamError")

        network = db_api.get_network_by_uuid(data['network_uuid'])
        if not network:
            logger.error("network: %s not exist", data['network_uuid'])
            return get_error_result("NetworkInfoNotExist")

        subnet_uuid = data.get('subnet_uuid', None)
        if subnet_uuid:
            subnet = db_api.get_subnet_by_uuid(data['subnet_uuid'])
            if not subnet:
                logger.error("subnet: %s not exist", data['subnet_uuid'])
                return get_error_result("SubnetNotExist")
        else:
            subnet = None

        template_exist = db_api.get_item_with_first(models.YzyVoiTemplate,
                                                    {'name': data['name'], 'classify': data['classify']})
        if template_exist:
            logger.error("template: %s already exist", data['name'])
            return get_error_result("TemplateAlreadyExist", name=data['name'])

        # 如果没有指定节点，则模板默认放在主控节点
        if data.get('host_uuid', None):
            node = db_api.get_node_by_uuid(data['host_uuid'])
        else:
            node = db_api.get_controller_node()
        # 检查磁盘空间是否足够
        image_id = data['system_disk'].get('image_id', None)
        if image_id:
            image = db_api.get_image_with_first({'uuid': image_id})
            free = self.get_template_sys_space(node.uuid)
            if free and image.size > free:
                logger.exception("the disk size in not enough, return")
                return get_error_result("SpaceNotEnough")

        if not data.get('version'):
            version = 0
        else:
            version = data['version']
        data['host_uuid'] = node.uuid
        data['version'] = version
        # network info
        if not subnet:
            # dhcp方式获取IP
            data['bind_ip'] = ''
        else:
            all_ips = find_ips(subnet.start_ip, subnet.end_ip)
            if not data.get('bind_ip', None):
                # 选择子网并且系统分配，模板IP从后往前取值
                all_ip_reverse = all_ips[::-1]
                used_ips = self.get_personal_used_ipaddr(subnet_uuid)
                for ipaddr in all_ip_reverse:
                    if ipaddr not in used_ips:
                        data['bind_ip'] = ipaddr
                        break
                else:
                    return get_error_result("IPNotEnough")
            if data['bind_ip'] not in all_ips:
                return get_error_result("IPNotInRange", ipaddr=data['bind_ip'])
        logger.info("check bind_ip info")

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

        # disk_info
        if not data['system_disk'].get('uuid'):
            data['system_disk']['uuid'] = create_uuid()
        sys_base, data_base = self._get_template_storage_path()
        disk_info = self.create_disk_info(data, version, sys_base, data_base, disk_generate=disk_generate)

        # 磁盘记录数据库
        disks = list()
        sys_disk = disk_info[0]
        file_name = constants.VOI_BASE_PREFIX % str(0) + sys_disk["uuid"]
        backing_file = os.path.join(os.path.join(sys_base, constants.IMAGE_CACHE_DIRECTORY_NAME), file_name)
        # self.get_qcow2_section(backing_file, int(sys_disk['size'].replace("G","")))
        sys_info = {
            "uuid": sys_disk['uuid'],
            "type": constants.IMAGE_TYPE_SYSTEM,
            "device_name": sys_disk['dev'],
            "image_id": sys_disk['image_id'],
            "instance_uuid": data['uuid'],
            "boot_index": sys_disk['boot_index'],
            "size": int(sys_disk['size'].replace('G', '')),
            # "section": os.path.join(os.path.join(sys_base, constants.IMAGE_CACHE_DIRECTORY_NAME), file_name)
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
        # 和分组绑定关系
        binds = list()
        data['all_group'] = False if data.get('groups', []) else True
        if not data.get('groups', []):
            result = db_api.get_item_with_all(models.YzyVoiGroup, {})
            groups = [item.uuid for item in result]
        else:
            groups = data['groups']
        for group_uuid in groups:
            binds.append({
                "uuid": create_uuid(),
                "template_uuid": data['uuid'],
                "group_uuid": group_uuid
            })
        data["status"] = constants.STATUS_INSTALL if data.get('iso', None) else constants.STATUS_CREATING
        template = db_api.create_voi_template(data)
        logger.info("create template db info")

        zm = string.ascii_lowercase
        index = zm.index(disk_info[-1]['dev'][-1])
        # 需要添加configdrive，uefi启动cdrom只支持sata和scsi，不支持ide格式
        configdrive = True
        if configdrive:
            disk_info.append({
                "bus": "sata",
                "dev": "sd%s" % zm[index + 1],
                "type": "cdrom",
                "path": ""
            })
        if not data.get('iso', None):
            disk_info.append({
                "bus": "sata",
                "dev": "sd%s" % (zm[index + 2] if configdrive else zm[index + 1]),
                "type": "cdrom",
                "path": ""
            })
        else:
            disk_info.append({
                "bus": "sata",
                "dev": "sd%s" % (zm[index + 2] if configdrive else zm[index + 1]),
                "type": "cdrom",
                "path": data['iso']
            })
            disk_info.append({
                "bus": "sata",
                "dev": "sd%s" % (zm[index + 3] if configdrive else zm[index + 2]),
                "type": "cdrom",
                "path": constants.VIRTIO_PATH
            })
        # instance info
        data['id'] = template.id
        instance_info = self._get_instance_info(data, voi=True)
        db_api.insert_with_many(models.YzyVoiDeviceInfo, disks)
        if binds:
            db_api.insert_with_many(models.YzyVoiTemplateGroups, binds)
        logger.info("create the voi template success, node:%s", node.ip)

        ret = {
            "uuid": instance_info['uuid'],
            "name": data['name'],
            "version": version
        }
        if not data.get('iso', None):
            task = Thread(target=self.create_thread,
                          args=(node.ip, template.uuid, instance_info, network_info, disk_info, False, False, configdrive))
            task.start()
        else:
            result = self.create_thread(node.ip, template.uuid, instance_info,
                                        network_info, disk_info, iso=True, configdrive=configdrive)
            if not result:
                template.soft_delete()
                return get_error_result("TemplateCreateFail", name=template.name)

        return get_error_result("Success", ret)

    def create_thread(self, ipaddr, template_uuid, instance_info, network_info, disk_info,
                      power_on=False, iso=False, configdrive=True):
        try:
            logger.info("start create template thread")
            template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
            self._create_template(ipaddr, instance_info, network_info, disk_info,
                                  power_on=power_on, iso=iso, configdrive=configdrive)
        except Exception as e:
            logger.exception("create template error:%s", e)
            template.status = constants.STATUS_ERROR
            template.soft_update()
            return False
        # iso安装时，如果没有保存，状态一直是installing
        if not iso:
            if power_on:
                template.status = constants.STATUS_ACTIVE
            else:
                template.status = constants.STATUS_INACTIVE
        logger.info("update template status to %s", template.status)
        template.soft_update()
        # # 更新磁盘的扇区
        # devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
        # for dev in devices:
        #     if dev.type == constants.IMAGE_TYPE_SYSTEM
        # 生成种子文件
        task = Thread(target=self.create_torrent_disks, args=(template_uuid,))
        task.start()
        logger.info("create template thread end")
        return True

    def allocate_ipaddr(self, network_uuid):
        ipaddr = ""
        subnets = db_api.get_subnet_by_network(network_uuid)
        for subnet in subnets:
            all_ips = find_ips(subnet.start_ip, subnet.end_ip)
            # 选择子网并且系统分配，模板IP从后往前取值
            all_ip_reverse = all_ips[::-1]
            used_ips = self.get_personal_used_ipaddr(subnet.uuid)
            for ip in all_ip_reverse:
                if ip not in used_ips:
                    ipaddr = ip
                    return ipaddr, subnet.uuid
        return ipaddr, None

    def upload_start(self, data):
        template_exist = db_api.get_item_with_first(models.YzyVoiTemplate,
                                                    {'name': data['name'], 'classify': data['classify']})
        if template_exist:
            logger.error("template: %s already exist", data['name'])
            return get_error_result("TemplateAlreadyExist", name=data['name'])
        # 1、默认网络从后往前分配 2、无可用网络则设置为未分配
        networks = db_api.get_network_all({"default": 1})
        network_uuid = networks[0].uuid
        subnet_uuid = None
        ipaddr = ""
        # 有默认网络，则从默认网络分配，子网段中从后向前分配
        if networks:
            ipaddr, sub = self.allocate_ipaddr(networks[0].uuid)
        if ipaddr:
            network_uuid = networks[0].uuid
            subnet_uuid = sub
        else:
            networks = db_api.get_network_all({})
            for network in networks:
                ipaddr, sub = self.allocate_ipaddr(network.uuid)
                if ipaddr:
                    network_uuid = network.uuid
                    subnet_uuid = sub
                    break
        logger.info("the network info, network_uuid:%s, subnet_uuid:%s, ipaddr:%s", network_uuid, subnet_uuid, ipaddr)

        # 如果没有指定节点，则模板默认放在主控节点
        if data.get('host_uuid', None):
            node = db_api.get_node_by_uuid(data['host_uuid'])
        else:
            node = db_api.get_controller_node()

        # 保证上传存放的资源池存在
        pool_name = data.get('pool_name', 'template-voi')
        template_sys = db_api.get_template_sys_storage()
        if not template_sys:
            sys_base = constants.DEFAULT_SYS_PATH
        else:
            sys_base = template_sys.path
        pool_path = os.path.join(sys_base, constants.VOI_POOL_DIR_NAME)
        self._create_pool(node.ip, pool_name, pool_path)
        # 检查磁盘空间是否足够
        # free = self.get_template_sys_space(node.uuid)
        # size = 0
        # size += data['system_disk']['real_size']
        # for item in data['data_disks']:
        #     size += item['real_size']
        # if free and size > free:
        #     logger.exception("the disk size in not enough, return")
        #     return get_error_result("SpaceNotEnough")

        self.used_macs = self.get_used_macs()
        mac_addr = generate_mac(self.used_macs)
        port_uuid = create_uuid()
        logger.info("allocate mac and port info")

        # 磁盘记录数据库
        template_uuid = create_uuid()
        disks_db = list()
        sys_uuid = create_uuid()
        disks_db.append(
            {
                "uuid": sys_uuid,
                "type": constants.IMAGE_TYPE_SYSTEM,
                "disk_bus": "sata",
                "device_name": "sda",
                "instance_uuid": template_uuid,
                "boot_index": 0,
                "size": section_to_G(int(data['system_disk']['size']))
            }
        )
        ret = {
            "system_disk": {
                "uuid": sys_uuid
            },
            "data_disks": []
        }
        zm = string.ascii_lowercase
        for index, disk in enumerate(data.get('data_disks', [])):
            disk_uuid = create_uuid()
            info = {
                "uuid": disk_uuid,
                "type": constants.IMAGE_TYPE_DATA,
                "disk_bus": "sata",
                "device_name": "sd%s" % zm[index+1],
                "instance_uuid": template_uuid,
                "boot_index": index+1,
                "size": section_to_G(int(disk['size']))
            }
            disks_db.append(info)
            ret['data_disks'].append({
                "uuid": disk_uuid
            })
        # 终端样机上传默认绑定所有教学分组
        binds = list()
        result = db_api.get_item_with_all(models.YzyVoiGroup, {})
        groups = [item.uuid for item in result]
        for group_uuid in groups:
            binds.append({
                "uuid": create_uuid(),
                "template_uuid": template_uuid,
                "group_uuid": group_uuid
            })
        os_type = data.get('os_type', 'windows_7_x64')
        values = {
            "uuid": template_uuid,
            "name": data['name'],
            "desc": data.get("desc", ""),
            "os_type": os_type,
            "owner_id": 1,
            "host_uuid": node.uuid,
            "network_uuid": network_uuid,
            "subnet_uuid": subnet_uuid,
            "bind_ip": ipaddr,
            "vcpu": 2 if os_type.startswith("windows_7") else 4,
            "ram": 2 if os_type.startswith("windows_7") else 4,
            "classify": data['classify'],
            "version": 0,
            "operate_id": 0,
            "status": constants.STATUS_UPLOADING,
            "mac": mac_addr,
            "port_uuid": port_uuid,
            "all_group": True
        }
        db_api.create_voi_template(values)
        logger.info("create template db info")
        db_api.insert_with_many(models.YzyVoiDeviceInfo, disks_db)
        if binds:
            db_api.insert_with_many(models.YzyVoiTemplateGroups, binds)
        logger.info("create the voi template success, node:%s", node.ip)
        return get_error_result("Success", ret)

    def upload_end(self, data):
        disk_uuid = data.get('uuid', "")
        device = db_api.get_item_with_first(models.YzyVoiDeviceInfo, {"uuid": disk_uuid})
        if not device:
            return get_error_result("DiskNotExist")
        if not data.get('status', False):
            logger.error("template upload error, delete")
            self.delete_template(device.instance_uuid)
            return get_error_result()

        template_sys = db_api.get_template_sys_storage()
        if not template_sys:
            sys_base = constants.DEFAULT_SYS_PATH
        else:
            sys_base = template_sys.path
        pool_path = os.path.join(sys_base, constants.VOI_POOL_DIR_NAME)
        upload_path = os.path.join(pool_path, disk_uuid)
        device.progress = data['progress']
        device.upload_path = upload_path
        device.soft_update()
        logger.info("update device info:%s", disk_uuid)
        if data.get('os_type'):
            template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": device.instance_uuid})
            if template:
                logger.info("update template os_type to %s", data['os_type'])
                template.os_type = data['os_type']
                template.soft_update()
        devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": device.instance_uuid})
        finished = True
        for item in devices:
            if 100 != item.progress:
                finished = False
                break
        if finished:
            logger.info("finish file upload, create the template")
            return self.template_upload_end(device.instance_uuid)
        return get_error_result()

    def template_upload_end(self, template_uuid):
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
        if not template:
            return get_error_result("TemplateNotExist", name="")
        subnet = None
        if template.subnet_uuid:
            subnet = db_api.get_subnet_by_uuid(template.subnet_uuid)
            if not subnet:
                return get_error_result("SubnetNotExist")
        node = db_api.get_node_by_uuid(template.host_uuid)
        if not node:
            return get_error_result("NodeNotExist")
        net = db_api.get_interface_by_network(template.network_uuid, template.host_uuid)
        if not net:
            logger.error("node %s network info %s error", node.uuid, template.network_uuid)
            return get_error_result("NodeNetworkInfoError")
        vif_info = {
            "uuid": net.YzyNetworks.uuid,
            "vlan_id": net.YzyNetworks.vlan_id,
            "interface": net.nic,
            "bridge": constants.BRIDGE_NAME_PREFIX + net.YzyNetworks.uuid[:constants.RESOURCE_ID_LENGTH]
        }
        network_info = self.create_network_info(vif_info, template.port_uuid, template.mac, subnet, template.bind_ip)
        logger.info("get instance network info")

        # disk_info
        disk_info = list()
        sys_base, data_base = self._get_template_storage_path()
        devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
        for device in devices:
            disk_info.append({
                "upload": device.upload_path + '-sda',
                "uuid": device.uuid,
                "bus": device.disk_bus,
                "dev": device.device_name,
                "boot_index": device.boot_index,
                "size": "%dG" % int(device.size),
                "base_path": sys_base if device.type == constants.IMAGE_TYPE_SYSTEM else data_base
            })
        logger.info("get disk info:%s", disk_info)
        # instance info
        value = {
            "name": template.name,
            "uuid": template.uuid,
            "id": template.id,
            "os_type": template.os_type,
            "ram": template.ram,
            "vcpu": template.vcpu
        }
        instance_info = self._get_instance_info(value, voi=True)
        zm = string.ascii_lowercase
        index = len(devices) - 1
        configdrive = True
        if configdrive:
            disk_info.append({
                "bus": "sata",
                "dev": "sd%s" % zm[index + 1],
                "type": "cdrom",
                "path": ""
            })
        disk_info.append({
            "bus": "sata",
            "dev": "sd%s" % (zm[index + 2] if configdrive else zm[index + 1]),
            "type": "cdrom",
            "path": ""
        })
        result = self.create_thread(node.ip, template.uuid, instance_info, network_info, disk_info, configdrive=configdrive)
        if not result:
            self.delete_template(template_uuid)
            return get_error_result("TemplateCreateFail", name=template.name)
        # todo 生成种子文件
        # disks = list()
        # for device in devices:
        #     voi_device_name = "voi_0_%s" % device.uuid
        #     base_path = sys_base if device.type == constants.IMAGE_TYPE_SYSTEM else data_base
        #     disk_path = os.path.join(base_path, voi_device_name)
        #     if os.path.exists(disk_path):
        #         disks.append(disk_path)
        task = Thread(target=self.create_torrent_disks, args=(template_uuid,))
        task.start()
        logger.info("template upload end success !!!!")
        return get_error_result()

    def create_torrent_disks(self, template_uuid):
        """
        :param disks:
        :return:
        """
        logger.info("threading create disk torrent: %s"% template_uuid)
        try:
            template = db_api.get_voi_instance_template(template_uuid)
            sys_base, data_base = self._get_template_storage_path()

            devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
            operates = db_api.get_item_with_all(models.YzyVoiTemplateOperate,
                                                {"template_uuid": template.uuid, "exist": True})
            disks = list()
            for disk in devices:
                base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
                backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
                backing_file = os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(0) + disk.uuid)
                torrent_path = backing_file + ".torrent"
                if not os.path.exists(torrent_path):
                    disks.append({"file_path": backing_file, "torrent_path": torrent_path})

                for operate in operates:
                    file_path = os.path.join(backing_dir,
                                             constants.VOI_BASE_PREFIX % str(operate.version) + disk.uuid)
                    torrent_path = file_path + ".torrent"
                    if os.path.exists(file_path):
                        disks.append({"file_path": file_path, "torrent_path": torrent_path})
                section = self.get_qcow2_section(backing_file, disk.size)
                disk.section = section
                disk.soft_update()

            data = {
                "command": "create_torrent",
                "data": {
                    "torrents": disks
                }
            }
            ret = voi_terminal_post("/api/v1/voi/terminal/command/", data, 180)
            if ret.get("code", -1) != 0:
                logger.error("threading create disk torrent :%s", ret)
                return ret
            logger.info("threading create disk torrents success")
            return get_error_result("Success")
        except Exception as e:
            logger.error("%s" % e, exc_info=True)
            return get_error_result("OtherError")

    def upload_cancel(self, data):
        template_uuid = data.get('uuid', "")
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
        if not template:
            return get_error_result("TemplateNotExist", name=data.get('name', ""))
        self.delete_template(template_uuid)
        return get_error_result()

    def start_template(self, template_uuid):
        """
        模板开机，这里可以采用两种方式，一种是根据uuid进行开机，一种是跟创建一样拿到所有信息，进行define
        注意三点：
            1、每次都要新加载IP信息
            2、模板属性修改，进行了磁盘增减、扩容、vcpu和ram变化都要能在开机时生效
            3、模板挂载的资源重启要保留
        """
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
        if not template:
            logger.error("template %s not exist", template_uuid)
            return get_error_result("TemplateNotExist", name='')

        node = db_api.get_node_by_uuid(template.host_uuid)
        info = {
            "uuid": template.uuid,
            "name": template.name
        }
        try:
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
            # 不使用_create_instance方法是因为通过cdrom加载的设备重启后需要保留
            rep_json = self._start_instance(node.ip, info, network_info)
            logger.info("start voi template end, return:%s", rep_json)
            if rep_json['code'] == 0:
                file_path = os.path.join(constants.TOKEN_PATH, template_uuid)
                content = '%s: %s:%s' % (template_uuid, node.ip, rep_json['data']['vnc_port'])
                logger.info("write instance token info:%s", template_uuid)
                FileOp(file_path, 'w').write_with_endline(content)
        except Exception as e:
            logger.error("start voi template failed:%s", e)
            template.status = constants.STATUS_ERROR
            template.soft_update()
            return get_error_result("TemplateStartFail", name=template.name)
        if template.status != constants.STATUS_INSTALL:
            template.status = constants.STATUS_ACTIVE
            template.soft_update()
        logger.info("start voi template %s success", info)
        return get_error_result("Success", rep_json.get('data'))

    def stop_template(self, template_uuid, hard=False):
        """
        模板关机
        :param template_uuid:
        :param hard: 是否强制关机
        :return:
        """
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
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
        logger.info("stop voi template %s success", instance_info)
        return get_error_result("Success", rep_json.get('data'))

    def reboot_template(self, template_uuid, reboot_type='soft'):
        """
        模板重启
        """
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
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
            logger.error("reboot voi template failed:%s", e)
            template.status = constants.STATUS_ERROR
            template.soft_update()
            return get_error_result("TemplateStartFail", name=template.name)
        template.status = constants.STATUS_ACTIVE
        template.soft_update()
        logger.info("reboot voi template %s success", instance_info)
        return get_error_result("Success", rep_json.get('data'))

    def hard_reboot_template(self, template_uuid):
        """
        模板硬重启
        """
        return self.reboot_template(template_uuid, reboot_type='hard')

    def _get_deleted_images(self, template, sys_base, data_base):
        """
        :param template: the template db object
        :param version: the template version
        :param sys_base: the dir of the template sys image
        :param data_base: the dir of the tepmlate data image
        :return:
        """
        images = list()
        devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
        operates = db_api.get_item_with_all(models.YzyVoiTemplateOperate,
                                            {"template_uuid": template.uuid, "exist": True})
        for disk in devices:
            base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
            file_name = constants.VOI_FILE_PREFIX + disk.uuid
            images.append({
                "image_path": os.path.join(base_path, file_name)
            })
            backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
            info = {
                "image_path": os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(0) + disk.uuid),
            }
            images.append(info)
            for operate in operates:
                images.append(
                    {
                        "image_path": os.path.join(backing_dir,
                                                   constants.VOI_BASE_PREFIX % str(operate.version) + disk.uuid)
                    }
                )
        logger.info("get voi template delete image info:%s", images)
        return images

    def delete_template(self, template_uuid):
        """
        删除模板，除了删除系统盘和数据盘，还要删除他们的base文件
        :param template_uuid: the uuid of template
        :return:
        """
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
        if not template:
            logger.error("instance template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")

        if constants.EDUCATION_DESKTOP == template.classify:
            desktops = db_api.get_item_with_first(models.YzyVoiDesktop, {'template_uuid': template_uuid})
            if desktops:
                return get_error_result("TemplateInUse", name=template.name)

        logger.info("delete voi template, uuid:%s, name:%s", template_uuid, template.name)
        sys_base, data_base = self._get_template_storage_path()
        images = self._get_deleted_images(template, sys_base, data_base)
        command_data = {
            "command": "delete",
            "handler": "VoiHandler",
            "data": {
                "instance": {
                    "uuid": template.uuid,
                    "name": template.name
                },
                "images": images
            }
        }
        node = db_api.get_controller_node()
        logger.info("delete the template begin, node:%s", node.ip)
        rep_json = compute_post(node.ip, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("delete template: %s fail:%s", template.uuid, rep_json['msg'])
            return get_error_result("TemplateDeleteFail", name=template.name)
        logger.info("delete the template from db")
        devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
        for disk in devices:
            tasks = db_api.get_task_all({"image_id": disk.uuid})
            for task in tasks:
                task.soft_delete()
            disk.soft_delete()
        binds = db_api.get_item_with_all(models.YzyVoiTemplateGroups, {"template_uuid": template.uuid})
        for bind in binds:
            bind.soft_delete()
        operates = db_api.get_item_with_all(models.YzyVoiTemplateOperate, {"template_uuid": template.uuid})
        for operate in operates:
            operate.soft_delete()
        template.soft_delete()
        return get_error_result("Success")

    def reset_template(self, template_uuid):
        """
        重置模板，除了删除系统盘和数据盘，还要删除他们的base文件
        :param template_uuid: the uuid of template
        :return:
        """
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
        if not template:
            logger.error("voi template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")

        logger.info("reset voi template:%s", template_uuid)
        sys_base, data_base = self._get_template_storage_path()
        images = self._get_sync_images(template, sys_base, data_base)
        command_data = {
            "command": "reset",
            "handler": "VoiHandler",
            "data": {
                "instance": {
                    "uuid": template.uuid,
                    "name": template.name
                },
                "images": images
            }
        }
        node = db_api.get_node_with_first({'uuid': template.host_uuid})
        logger.info("reset the voi template begin, node:%s", node.ip)
        rep_json = compute_post(node.ip, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("reset voi template: %s fail:%s", template.uuid, rep_json['msg'])
            return get_error_result("TemplateResetError", name=template.name)

        template.status = constants.STATUS_INACTIVE
        template.attach = ""
        template.soft_update()
        logger.info("reset the template success")
        return get_error_result("Success")

    def find_add_disk(self, value, template, data_base):
        # 查找新加的磁盘
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
                index = disk['inx'] + 3
                device_info = {
                    "uuid": disk_uuid,
                    "type": constants.IMAGE_TYPE_DATA,
                    "device_name": "sd%s" % zm[index],
                    "disk_bus": "sata",
                    "instance_uuid": template.uuid,
                    "boot_index": index,
                    "size": disk['size'],
                }
                node = db_api.get_node_with_first({'uuid': template.host_uuid})
                instance_info = {
                    "uuid": template.uuid,
                    "name": template.name
                }
                disk_info = {
                    'uuid': disk_uuid,
                    'dev': "sd%s" % zm[index],
                    'image_id': disk_uuid,
                    'boot_index': index,
                    'bus': 'sata',
                    'type': 'disk',
                    'size': '%sG' % disk['size'],
                    'base_path': data_base
                }
                rep_json = self.create_and_attach_file(node.ip, instance_info, disk_info, template.version)
                if rep_json.get("code", -1) != 0:
                    logger.error("create_file failed, node:%s, error:%s", node.ip, rep_json.get('data'))
                    return get_error_result("AttachDiskError")
                logger.info("create data file success, version:%s", template.version)
                db_api.create_voi_device(device_info)
            desktops = db_api.get_item_with_all(models.YzyVoiDesktop, {'template_uuid': template.uuid})
            for desktop in desktops:
                desktop.data_restore = desktop.sys_restore
                desktop.soft_update()
        return get_error_result("Success")

    def find_extend_disk(self, template, value, sys_base, data_base):
        # 查找删除的盘
        images = list()
        devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
        node = db_api.get_node_with_first({'uuid': template.host_uuid})
        for device in devices:
            for disk in value['devices']:
                if disk.get('uuid', None) and disk['uuid'] == device.uuid:
                    # 大小有变化
                    if int(disk['size']) != int(device.size):
                        if int(disk['size']) < int(device.size):
                            return get_error_result("TemplateDiskSizeError")
                        logger.info("disk %s extend size from %s to %s", device.device_name, device.size, disk['size'])
                        image = {
                            "image_id": disk['uuid'],
                            "base_path": sys_base if constants.IMAGE_TYPE_SYSTEM == disk['type'] else data_base,
                            "size": int(disk['size']) - int(device.size)
                        }
                        images.append(image)
                        device.size = int(disk['size'])
                        device.soft_update()
                    break
        if images:
            command_data = {
                "command": "resize",
                "handler": "VoiHandler",
                "data": {
                    "images": images
                }
            }
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
                "handler": "VoiHandler",
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
        """只允许添加数据盘，并且只能添加一个"""
        logger.info("update voi template:%s", data)
        template_uuid = data.get('uuid', '')
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {'uuid': template_uuid})
        if not template:
            logger.error("voi template %s not exist", template)
            return get_error_result("TemplateNotExist")
        # if template.status == constants.STATUS_ACTIVE:
        #     logger.error("template is active, can not update")
        #     return get_error_result("TemplateActive", name=template.name)
        if data['name'] != data['value']['name']:
            template_check = db_api.get_item_with_all(models.YzyVoiTemplate,
                                                      {'name': data['value']['name'], 'classify': template.classify})
            if template_check:
                logger.error("template: %s already exist", data['value']['name'])
                return get_error_result("TemplateAlreadyExist", name=data['value']['name'])
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
            all_ips = find_ips(subnet.start_ip, subnet.end_ip)
            education_used_ips = self.get_personal_used_ipaddr(subnet_uuid)
            if not value.get('bind_ip', None):
                # 选择子网并且系统分配，模板IP从后往前取值
                all_ip_reverse = all_ips[::-1]
                education_used_ips = self.get_personal_used_ipaddr(subnet_uuid)
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
        if template.status == constants.STATUS_ACTIVE:
            ret = self.stop_template(template_uuid)
            if ret.get('code') != 0:
                return ret
        try:
            # cpu和内存的修改
            rep_json = self.update_ram_and_vcpu(value, template)
            if rep_json.get('code') != 0:
                return rep_json

            sys_base, data_base = self._get_template_storage_path()
            rep_json = self.find_add_disk(value, template, data_base)
            if rep_json.get('code') != 0:
                return rep_json
            rep_json = self.find_extend_disk(template, value, sys_base, data_base)
            if rep_json.get('code') != 0:
                return rep_json
            logger.info('update template attr to db')
            template_value = {
                "name": value['name'],
                "desc": value.get('desc', ''),
                "network_uuid": value['network_uuid'],
                "subnet_uuid": value.get('subnet_uuid', ''),
                "bind_ip": value.get('bind_ip', ''),
                "ram": value['ram'],
                "vcpu": value['vcpu'],
                "all_group": False if value.get('groups', None) else True
            }
            # 桌面组绑定的处理
            binds = list()
            if not value.get('groups', []):
                result = db_api.get_item_with_all(models.YzyVoiGroup, {})
                groups = [item.uuid for item in result]
            else:
                groups = value['groups']
            origin_binds = db_api.get_item_with_all(models.YzyVoiTemplateGroups, {"template_uuid": template.uuid})
            for group_uuid in groups:
                for bind in origin_binds:
                    if bind.group_uuid == group_uuid:
                        break
                else:
                    binds.append({
                        "uuid": create_uuid(),
                        "template_uuid": template_uuid,
                        "group_uuid": group_uuid
                    })
            for bind in origin_binds:
                for group_uuid in groups:
                    if bind.group_uuid == group_uuid:
                        break
                else:
                    logger.info("delete the bind group:%s", bind.group_uuid)
                    bind.soft_delete()
            template.update(template_value)
            if binds:
                db_api.insert_with_many(models.YzyVoiTemplateGroups, binds)
        except Exception as e:
            logger.error("update voi template %s failed:%s", template_uuid, e, exc_info=True)
            return get_error_result("TemplateUpdateError", name=template.name)
        _task = Thread(target=self.create_torrent_disks, args=(template_uuid,))
        _task.start()
        logger.info("update voi template success, uuid:%s, name:%s", template_uuid, template.name)
        return get_error_result("Success")

    def convert(self, ipaddr, image):
        """
        在模板所在节点先合并差异文件生成新的基础镜像
        如果版本为0，则进行复制，否则进行合并
        """
        command_data = {
            "command": "convert",
            "handler": "VoiHandler",
            "data": {
                "template": image
            }
        }
        rep_json = compute_post(ipaddr, command_data, timeout=600)
        logger.info("convert the disk file finished, node:%s", ipaddr)
        return rep_json

    def write_head(self, ipaddr, image_path, vcpu, ram, disk_size):
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
        rep_json = compute_post(ipaddr, command_data, timeout=600)
        logger.info("write head to image %s finished, node:%s, return:%s", image_path, ipaddr, rep_json)
        return rep_json

    def copy(self, ipaddr, version, images):
        """
        在节点复制模板的系统盘和数据盘
        """
        command_data = {
            "command": "copy",
            "handler": "VoiHandler",
            "data": {
                "version": version,
                "images": images
            }
        }
        rep_json = compute_post(ipaddr, command_data, timeout=600)
        logger.info("copy the template finished, node:%s", ipaddr)
        return rep_json

    def save(self, ipaddr, version, images):
        """模板更新"""
        command_data = {
            "command": "save",
            "handler": "VoiHandler",
            "data": {
                "version": version,
                "images": images
            }
        }
        rep_json = compute_post(ipaddr, command_data, timeout=600)
        logger.info("save the image end, version:%s, images:%s", version, images)
        return rep_json

    def detach_cdrom(self, ipaddr, instance_info, configdrive=True):
        """iso安装后删除cdrom"""
        command_data = {
            "command": "detach_cdrom",
            "handler": "VoiHandler",
            "data": {
                "instance": instance_info,
                "configdrive": configdrive
            }
        }
        rep_json = compute_post(ipaddr, command_data)
        logger.info("detach_cdrom end, instance:%s", instance_info)
        return rep_json

    def rollback(self, ipaddr, rollback_version, cur_version, images):
        """模板回滚"""
        command_data = {
            "command": "rollback",
            "handler": "VoiHandler",
            "data": {
                "rollback_version": rollback_version,
                "cur_version": cur_version,
                "images": images
            }
        }
        rep_json = compute_post(ipaddr, command_data)
        logger.info("save the image end, rollback_version:%s, cur_version, images:%s",
                    rollback_version, cur_version, images)
        return rep_json

    def create_and_attach_file(self, ipaddr, instance_info, disk_info, version):
        command_data = {
            "command": "create_file",
            "handler": "VoiHandler",
            "data": {
                "instance": instance_info,
                "disk_info": disk_info,
                "version": version
            }
        }
        rep_json = compute_post(ipaddr, command_data, timeout=600)
        logger.info("create disk file:%s, host:%s", disk_info, ipaddr)
        rep_json['ipaddr'] = ipaddr
        return rep_json

    def create_and_share_disk(self, ipaddr, instance_info, disk_info, version):
        command_data = {
            "command": "create_share",
            "handler": "VoiHandler",
            "data": {
                "instance": instance_info,
                "disk_info": disk_info,
                "version": version
            }
        }
        rep_json = compute_post(ipaddr, command_data, timeout=600)
        logger.info("create disk file:%s, host:%s", disk_info, ipaddr)
        rep_json['ipaddr'] = ipaddr
        return rep_json

    def _attach_source(self, ipaddr, instance_info, path):
        command_data = {
            "command": "attach_source",
            "handler": "VoiHandler",
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
            "handler": "VoiHandler",
            "data": {
                "instance": instance_info
            }
        }
        logger.info("detach %s device in node %s", instance_info['uuid'], ipaddr)
        rep_json = compute_post(ipaddr, command_data)
        if rep_json.get("code", -1) != 0:
            logger.error("detach %s device failed, node:%s, error:%s", instance_info['uuid'], ipaddr, rep_json.get('data'))
        return rep_json

    def _create_pool(self, ipaddr, pool_name, pool_path):
        """
        创建storage pool
        """
        command_data = {
            "command": "create_pool",
            "handler": "VoiHandler",
            "data": {
                "pool_name": pool_name,
                "path": pool_path
            }
        }
        rep_json = compute_post(ipaddr, command_data)
        logger.info("create the storage pool finished, node:%s", ipaddr)
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
                "disk_path": disk_path,
                "backing_file": backing_file
            }
            disks.append(info)
        return disks

    def _get_sync_images(self, template, sys_base, data_base):
        """
        :param template: the template db object
        :param sys_base: the dir of the template sys image
        :param data_base: the dir of the tepmlate data image
        :return:
        """
        images = list()
        devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
        for disk in devices:
            base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
            backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
            file_name = constants.VOI_FILE_PREFIX + disk.uuid
            images.append({
                "image_path": os.path.join(base_path, file_name),
                "backing_path": os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(template.version) + disk.uuid)
            })
        logger.info("get template image info:%s", images)
        return images

    def _get_copy_images(self, template, new_uuid, sys_base, data_base):
        disks = list()
        images = list()
        add_disks = list()
        devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
        operates = db_api.get_item_with_all(models.YzyVoiTemplateOperate, {"template_uuid": template.uuid, "exist": True})
        for disk in devices:
            disk_uuid = create_uuid()
            base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
            backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
            backing_file = os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(0) + disk.uuid)
            info = {
                "image_path": backing_file,
                "dest_path": os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(0) + disk_uuid),
            }
            images.append(info)
            for operate in operates:
                images.append(
                    {
                        "image_path": os.path.join(backing_dir,
                                                   constants.VOI_BASE_PREFIX % str(operate.version) + disk.uuid),
                        "dest_path": os.path.join(backing_dir,
                                                  constants.VOI_BASE_PREFIX % str(operate.version) + disk_uuid)
                    }
                )
            disks.append({
                "uuid": disk_uuid,
                "dev": disk.device_name,
                "boot_index": disk.boot_index,
                "image_version": template.version,
                "image_id": "",
                "bus": "sata",
                "size": "%dG" % disk.size,
                "base_path": sys_base
            })
            add_disks.append({
                "uuid": disk_uuid,
                "type": disk.type,
                "device_name": disk.device_name,
                "instance_uuid": new_uuid,
                "boot_index": disk.boot_index,
                "size": disk.size,
                "used": disk.used
            })
            # if constants.IMAGE_TYPE_SYSTEM == disk.type:
            #     sys_disk = {
            #         "uuid": disk_uuid,
            #         "dev": disk.device_name,
            #         "boot_index": disk.boot_index,
            #         "size": "%dG" % disk.size,
            #         "base_path": sys_base
            #     }
            # if constants.IMAGE_TYPE_DATA == disk.type:
            #     disk_info = {
            #         "uuid": disk_uuid,
            #         "dev": disk.device_name,
            #         "boot_index": disk.boot_index,
            #         "size": "%dG" % disk.size,
            #         "base_path": data_base
            #     }
            #     data_disks.append(disk_info)
        logger.info("get template copy image info:%s", images)
        return images, disks, add_disks

    def _get_template_storage_path(self):
        template_sys = db_api.get_template_sys_storage()
        template_data = db_api.get_template_data_storage()
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

    def delete_instance_only(self, ipaddr, info):
        try:
            self._delete_instance(ipaddr, info)
        except:
            return False
        return True

    def upgrade_template(self, template_uuid, desc):
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {'uuid': template_uuid})
        # template = db_api.get_voi_instance_template(template_uuid)
        if not template:
            logger.error("voi instance template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")
        if constants.STATUS_COPING == template.status:
            logger.error("instance template is copying", template_uuid)
            return get_error_result("TemplateCopying")
        if constants.STATUS_DOWNLOADING == template.status:
            logger.error("instance template is downloading", template_uuid)
            return get_error_result("TemplateDownloading")
        task = Thread(target=self._save_template, args=(template_uuid, desc, ))
        task.start()
        return get_error_result("Success")

    def _save_template(self, template_uuid, desc=""):
        """
        保存模板
        :param template_uuid: the uuid of template
        :return:
        """
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
        if not template:
            logger.error("voi template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")
        try:
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
                logger.error("stop template %s failed:%s", template.uuid, e)
                return get_error_result("TemplateStopError", name=template.name, data=str(e))

            node = db_api.get_node_with_first({"uuid": template.host_uuid})
            new_version = template.version + 1
            images = list()
            sys_base, data_base = self._get_template_storage_path()
            operates = db_api.get_item_with_all(models.YzyVoiTemplateOperate, {'template_uuid': template.uuid, 'exist': True})
            devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template_uuid})
            for device in devices:
                images.append({
                    "image_id": device.uuid,
                    "base_path": sys_base if constants.IMAGE_TYPE_SYSTEM == device.type else data_base,
                    "need_commit": True if len(operates) >= constants.IMAGE_COMMIT_VERSION else False
                })
            self.save(node.ip, new_version, images)
            operate = {
                "uuid": create_uuid(),
                "template_uuid": template_uuid,
                "remark": desc,
                "op_type": 1,
                "exist": True,
                "version": new_version
            }
            db_api.create_template_operate(operate)
            if new_version > constants.IMAGE_COMMIT_VERSION:
                if len(operates) >= constants.IMAGE_COMMIT_VERSION:
                    operates[0].exist = False
                    operates[0].soft_update()
            # 保存成功
            template.version = new_version
            template.operate_id = template.operate_id + 1
            template.status = constants.STATUS_INACTIVE
            template.updated_time = datetime.utcnow()
            template.soft_update()
        except Exception as e:
            logger.error("save voi template error:%s", e)
            template.status = constants.STATUS_ERROR
            template.updated_time = datetime.utcnow()
            template.soft_update()
        # 创建模板种子
        _task = Thread(target=self.create_torrent_disks, args=(template_uuid,))
        _task.start()
        return get_error_result("Success")

    def save_iso_template(self, template_uuid):
        """
        ISO全新安装时，需要进行保存才能跟基础镜像安装完时状态一致
        """
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
        if not template:
            logger.error("voi template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")
        template.status = constants.STATUS_SAVING
        template.soft_update()
        task = Thread(target=self.save_iso_template_thread, args=(template_uuid, ))
        task.start()
        return get_error_result("Success")

    def save_iso_template_thread(self, template_uuid):
        logger.info("start save iso template")
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
        # 第一步关机
        node = db_api.get_node_with_first({"uuid": template.host_uuid})
        instance_info = {
            "uuid": template.uuid,
            "name": template.name
        }
        try:
            self._stop_instance(node.ip, instance_info, timeout=60)
        except Exception as e:
            logger.error("stop voi template %s failed:%s", template.uuid, e)
            return get_error_result("TemplateStopError", name=template.name, data=str(e))

        images = list()
        sys_base, data_base = self._get_template_storage_path()
        devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template_uuid})
        for device in devices:
            images.append({
                "image_id": device.uuid,
                "base_path": sys_base if constants.IMAGE_TYPE_SYSTEM == device.type else data_base
            })
        configdrive = True if template.bind_ip else False
        self.save(node.ip, 0, images)
        self.detach_cdrom(node.ip, instance_info, configdrive=configdrive)
        template.status = constants.STATUS_INACTIVE
        template.updated_time = datetime.utcnow()
        template.soft_update()
        logger.info("save iso template thread end")
        return get_error_result("Success")

    def copy_template(self, data):
        """
        复制模板：原理就是复制模板的系统盘和数据盘(base和差异盘一起复制)
        :param data:
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
        :return:
        """
        logger.info("copy data, data:%s", data)
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": data['name']})
        if template:
            logger.error("template: %s already exist", data['name'])
            return get_error_result("TemplateAlreadyExist", name=data['name'])

        template_uuid = data['template_uuid']
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
        if not template:
            logger.error("template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")

        network = db_api.get_network_by_uuid(data['network_uuid'])
        if not network:
            logger.error("network: %s not exist", data['network_uuid'])
            return get_error_result("NetworkInfoNotExist")
        # IP分配检测
        subnet_uuid = data.get('subnet_uuid', None)
        if subnet_uuid:
            subnet = db_api.get_subnet_by_uuid(data['subnet_uuid'])
            if not subnet:
                logger.error("subnet: %s not exist", data['subnet_uuid'])
                return get_error_result("SubnetNotExist")
            subnet = subnet.dict()
        else:
            subnet = {}
        if not subnet and not data.get('bind_ip', None):
            # dhcp方式获取IP
            data['bind_ip'] = ''
        else:
            all_ips = find_ips(subnet['start_ip'], subnet['end_ip'])
            if not data.get('bind_ip', None):
                # 选择子网并且系统分配，模板IP从后往前取值
                all_ip_reverse = all_ips[::-1]
                education_used_ips = self.get_personal_used_ipaddr(subnet_uuid)
                for ipaddr in all_ip_reverse:
                    if ipaddr not in education_used_ips:
                        data['bind_ip'] = ipaddr
                        break
                else:
                    return get_error_result("IPNotEnough")
            if data['bind_ip'] not in all_ips:
                return get_error_result("IPNotInRange", ipaddr=data['bind_ip'])

        # 模板所在节点判断
        if data.get('host_uuid', None):
            node = db_api.get_node_by_uuid(data['host_uuid'])
        else:
            node = db_api.get_controller_node()
        new_uuid = create_uuid()
        sys_base, data_base = self._get_template_storage_path()
        images, kvm_disks, add_disks = self._get_copy_images(template, new_uuid, sys_base, data_base)
        free = self.get_template_sys_space(node.uuid)
        total_size = 0
        for image in images:
            if os.path.exists(image['image_path']):
                total_size += round(os.path.getsize(image['image_path'])/1024/1024/1024, 2)
        if total_size > free:
            logger.exception("the disk size in not enough, return")
            return get_error_result("SpaceNotEnough")
        # mac和port分配
        self.used_macs = self.get_used_macs()
        mac_addr = generate_mac(self.used_macs)
        logger.info("allocate mac info")
        port_uuid = create_uuid()
        # 与教学分组绑定关系
        binds = list()
        all_group = False if data.get('groups', []) else True
        if not data.get('groups', []):
            result = db_api.get_item_with_all(models.YzyVoiGroup, {})
            groups = [item.uuid for item in result]
        else:
            groups = data['groups']
        for group_uuid in groups:
            binds.append({
                "uuid": create_uuid(),
                "template_uuid": new_uuid,
                "group_uuid": group_uuid
            })
        ops = list()
        # 操作记录
        operates = db_api.get_item_with_all(models.YzyVoiTemplateOperate, {"template_uuid": template.uuid})
        for operate in operates:
            ops.append({
                "uuid": create_uuid(),
                "template_uuid": new_uuid,
                "remark": operate['remark'],
                "op_type": operate['op_type'],
                "exist": operate['exist'],
                "version": operate['version']
            })
        values = {
            "uuid": new_uuid,
            "name": data['name'],
            "desc": data.get('desc'),
            "owner_id": data['owner_id'],
            "version": template.version,
            "operate_id": template.operate_id,
            "host_uuid": node.uuid,
            "network_uuid": data['network_uuid'],
            "subnet_uuid": data.get('subnet_uuid', None),
            "bind_ip": data.get('bind_ip', ''),
            "os_type": template.os_type,
            "classify": template.classify,
            "vcpu": template.vcpu,
            "ram": template.ram,
            "mac": mac_addr,
            "port_uuid": port_uuid,
            "status": constants.STATUS_CREATING,
            "all_group": all_group
        }
        new_template = db_api.create_voi_template(values)
        db_api.insert_with_many(models.YzyVoiDeviceInfo, add_disks)
        if binds:
            db_api.insert_with_many(models.YzyVoiTemplateGroups, binds)
        if ops:
            db_api.insert_with_many(models.YzyVoiTemplateOperate, ops)
        values['id'] = new_template['id']
        pre_status = template.status
        template.status = constants.STATUS_COPING
        template.soft_update()
        logger.info("create template db info")
        node_info = {
            "uuid": node.uuid,
            "ipaddr": node.ip
        }
        task = Thread(target=self.create_template_thread,
                      args=(node_info, values, subnet, template_uuid, pre_status, images, kvm_disks, ))
        task.start()
        _task = Thread(target=self.create_torrent_disks, args=(new_uuid,))
        _task.start()
        ret = {
            "uuid": new_template.uuid,
            "name": data['name'],
            "version": 1
        }
        return get_error_result("Success", ret)

    def create_template_thread(self, node_info, data, subnet, origin, pre_status, images, kvm_disks, power_on=False):
        origin_template = db_api.get_item_with_first(models.YzyVoiTemplate, {'uuid': origin})
        new_template = db_api.get_item_with_first(models.YzyVoiTemplate, {'uuid': data['uuid']})
        try:
            rep_json = self.copy(node_info['ipaddr'], origin_template.version, images)
            if rep_json.get('code', -1) != 0:
                raise Exception("copy image failed")
            configdrive = True
            zm = string.ascii_lowercase
            if configdrive:
                for i in range(4):
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
            # instance info
            instance_info = self._get_instance_info(data, voi=True)
            self._create_template(node_info['ipaddr'], instance_info, network_info, kvm_disks, power_on=power_on)
        except Exception as e:
            logger.exception("copy voi template failed:%s", e)
            self.delete_template(new_template.uuid)
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
        logger.info("copy the voi template success, node:%s", node_info['ipaddr'])
        return get_error_result("Success")

    def edit_template(self, template_uuid):
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
        if not template:
            logger.error("instance template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")

        # 启动模板
        ret_json = self.start_template(template_uuid)
        if ret_json['code'] != 0:
            # 启动失败
            logger.error("edit template: %s, start template fail" % template_uuid)
            return get_error_result("TemplateStartFail", name=template.name)

        # 返回对应的token链接
        node = db_api.get_controller_node()
        websockify_url = "ws://%s:%s/websockify/?token=%s" % (node.ip, constants.WEBSOCKIFY_PORT, template_uuid)
        logger.info("start edit success, websockify_url: %s, attach:%s", websockify_url, template.attach)
        return get_error_result("Success", {'websockify_url': websockify_url, 'attach': template.attach})

    def get_downloading_path(self, template_uuid):
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {'uuid': template_uuid})
        sys_base, data_base = self._get_template_storage_path()
        sys_info = db_api.get_item_with_first(models.YzyVoiDeviceInfo,
                                              {'instance_uuid': template.uuid, 'type': constants.IMAGE_TYPE_SYSTEM})
        backing_path = os.path.join(sys_base, constants.IMAGE_CACHE_DIRECTORY_NAME)
        file_name = "%s_c%s_r%s_d%s" % ((template.name + '_' + template.uuid),
                                        template.vcpu, template.ram, sys_info.size)
        dest_path = os.path.join(backing_path, file_name)
        return dest_path

    def download_template(self, template_uuid):
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
        if not template:
            logger.error("voi template: %s not exist", template_uuid)
            return get_error_result("TemplateNotExist")
        if constants.STATUS_DOWNLOADING == template.status:
            logger.error("template is already in downloading")
            return get_error_result("Success")

        node = db_api.get_node_with_first({'uuid': template.host_uuid})
        sys_base, data_base = self._get_template_storage_path()
        free = self.get_template_sys_space(node.uuid)
        backing_dir = os.path.join(sys_base, constants.IMAGE_CACHE_DIRECTORY_NAME)
        sys_info = db_api.get_item_with_first(models.YzyVoiDeviceInfo, {'type': constants.IMAGE_TYPE_SYSTEM})
        operates = db_api.get_item_with_all(models.YzyVoiTemplateOperate,
                                            {'template_uuid': template.uuid, 'exist': True})
        # 下载合成后还需要写头部信息，因此需要两倍空间
        total_size = 0
        file_path = os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(0) + sys_info.uuid)
        total_size += round(os.path.getsize(file_path)/1024/1024/1024, 2)
        for operate in operates:
            file_path = os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(operate.version) + sys_info.uuid)
            if os.path.exists(file_path):
                total_size += round(os.path.getsize(file_path)/1024/1024/1024, 2)
        if total_size*2 > free:
            logger.exception("the disk size in not enough, return")
            return get_error_result("SpaceNotEnough")
        # 获取需要convert的差异文件名
        new_uuid = template.name + '_' + template.uuid
        if not operates:
            image = {
                "need_convert": False,
                "image_path": os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(0) + sys_info.uuid),
                "new_path": os.path.join(backing_dir, new_uuid),
                "size": sys_info.size
            }
        else:
            image = {
                "need_convert": True,
                "image_path": os.path.join(backing_dir,
                                           constants.VOI_BASE_PREFIX % str(operates[-1].version) + sys_info.uuid),
                "new_path": os.path.join(backing_dir, new_uuid),
                "size": sys_info.size
            }
        # 在模板所在节点合并差异文件生成新的基础镜像（只有系统盘）
        pre_status = template['status']
        template.status = constants.STATUS_DOWNLOADING
        template.soft_update()
        logger.info("start download template thread:%s", template['name'])
        task = Thread(target=self.download_thread, args=(node.ip, template_uuid, pre_status, image, ))
        task.start()
        return get_error_result("Success")

    def download_thread(self, ipaddr, template_uuid, pre_status, image):
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {'uuid': template_uuid})
        try:
            logger.info("start download template:%s", template['name'])
            convert = self.convert(ipaddr, image)
            if convert.get("code", -1) != 0:
                logger.error("convert template: %s failed:%s", template_uuid, convert['msg'])
                template.status = pre_status
                template.soft_update()
                raise Exception("convert template failed")
            rep_json = self.write_head(ipaddr, convert['data']['path'], template.vcpu, template.ram, image['size'])
            if rep_json.get("code", -1) != 0:
                logger.error("write head to image: %s failed:%s", convert['data']['path'], rep_json.get('data'))
                template.status = pre_status
                template.soft_update()
                raise Exception("write head to image failed")
        except Exception as e:
            logger.error("download voi template thread error:%s", e)
            template.status = pre_status
            template.soft_update()
            return get_error_result("TemplateDownloadFail", name=template.name)
        logger.info("convert voi template success")
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
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
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
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
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
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
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

    def rollback_template(self, data):
        """
        :param data:
            {
                "rollback_version": 4,
                "cur_version": 5,
                "name": "",
                "uuid": ""
            }
        :return:
        """
        detail = db_api.get_item_with_first(models.YzyVoiTemplateOperate, {'version': data['cur_version']})
        if not detail:
            return get_error_result("TemplateVersionNotExist")
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {'uuid': data['uuid']})
        if not template:
            logger.error("voi template: %s not exist", data['uuid'])
            return get_error_result("TemplateNotExist")
        self.stop_template(template.uuid, hard=True)
        # if constants.STATUS_ACTIVE == template.status:
        #     return get_error_result("TemplateIsActive", name=template.name)
        images = list()
        template.status = constants.STATUS_ROLLBACK
        template.soft_update()
        sys_base, data_base = self._get_template_storage_path()
        devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": data['uuid']})
        for device in devices:
            images.append({
                "image_id": device.uuid,
                "base_path": sys_base if constants.IMAGE_TYPE_SYSTEM == device.type else data_base
            })
        node = db_api.get_node_with_first({'uuid': template.host_uuid})
        rep_json = self.rollback(node.ip, data['rollback_version'], data['cur_version'], images)
        if rep_json.get("code", -1) != 0:
            logger.error("template rollback failed:%s", rep_json)
            return get_error_result("TemplateRollbackError")
        operate = db_api.get_item_with_first(
            models.YzyVoiTemplateOperate, {'template_uuid': data['uuid'], 'version': data['cur_version'], 'exist': True})
        if operate:
            logger.info("delete the template version:%s", operate.version)
            operate.exist = False
            operate.soft_update()
        value = {
            "uuid": create_uuid(),
            "template_uuid": template.uuid,
            "remark": "",
            "op_type": 2,
            "exist": False
        }
        db_api.create_template_operate(value)
        template.status = constants.STATUS_INACTIVE
        template.version = data['rollback_version']
        template.operate_id = template.operate_id + 1
        template.soft_update()
        logger.info("rollback template success")
        return get_error_result("Success")

    def get_console(self, data):
        uuid = data.get("uuid", '')
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": uuid})
        if not template:
            return get_error_result("TemplateNotExist", name='')

        host = db_api.get_node_with_first({"uuid": template.host_uuid})
        info = {
            "uuid": template.uuid,
            "name": template.name
        }
        rep_json = self._get_instance_status(host.ip, info)
        if rep_json.get('code') != 0:
            return get_error_result("InstancePowerOff", name=template.name)
        if rep_json['data'].get('state') != constants.DOMAIN_STATE['running']:
            return get_error_result("InstancePowerOff", name=template.name)
        node = db_api.get_controller_node()
        websockify_url = "ws://%s:%s/websockify/?token=%s" % (node.ip, constants.WEBSOCKIFY_PORT, template.uuid)
        logger.debug("get console success, websockify_url: %s", websockify_url)
        return get_error_result("Success", {'websockify_url': websockify_url})

    def get_template_disk_list(self, data):
        """{
                "terminal_id": qry.terminal_id,
                "terminal_ip": qry.ip,
                "group_uuid": qry.group_uuid
        }
        :param data:
        :return:
        """
        terminal_id = data.get("terminal_id")
        terminal_uuid = data.get("terminal_uuid")
        group_uuid = data.get("group_uuid")
        desktops = db_api.get_item_with_all(models.YzyVoiDesktop, {"group_uuid": group_uuid})

        desktop_group_list = list()
        template_uuids = list()
        for desktop in desktops:
            # get desktop ip info
            use_bottom_ip = desktop.use_bottom_ip
            desktop_is_dhcp = 1
            desktop_ip = ""
            desktop_mask = ""
            desktop_gateway = ""
            desktop_dns1 = ""
            desktop_dns2 = ""
            if not use_bottom_ip:
                qry_temminal_desktops = db_api.get_item_with_first(models.YzyVoiTerminalToDesktops, {
                    "desktop_group_uuid": desktop.uuid,
                    "terminal_uuid": terminal_uuid
                })
                if qry_temminal_desktops:
                    desktop_is_dhcp = qry_temminal_desktops.desktop_is_dhcp
                    if not desktop_is_dhcp:
                        desktop_ip = qry_temminal_desktops.desktop_ip
                        desktop_mask = qry_temminal_desktops.desktop_mask
                        desktop_gateway = qry_temminal_desktops.desktop_gateway
                        desktop_dns1 = qry_temminal_desktops.desktop_dns1
                        desktop_dns2 = qry_temminal_desktops.desktop_dns2

            template_uuid = desktop.template_uuid
            template_updated_time = desktop.template.updated_time.strftime('%Y-%m-%d %H:%M:%S')
            if template_uuid not in template_uuids:
                template_uuids.append(template_uuid)
                desktop_group_list.append({"desktop_group_name": desktop.name, "desktop_group_uuid": desktop.uuid,
                                           "desktop_group_status": int(desktop.active),
                                           "desktop_group_restore": desktop.sys_restore,
                                           "show_desktop_info": int(desktop.show_info),
                                           "auto_update_desktop": int(desktop.auto_update),
                                           "default_desktop_group": True if desktop.default else False,
                                           "os_sys_type": self.system_type_dict[desktop.os_type.lower()],
                                           "desktop_name": "%s-%s"%(desktop.prefix,terminal_id),
                                           "template_uuid": template_uuid,
                                           "template_name": desktop.template.name,
                                           "template_updated_time": template_updated_time,
                                           "desktop_enable_bottom_ip": desktop.use_bottom_ip,
                                           "desktop_is_dhcp": desktop_is_dhcp,
                                           "desktop_ip": desktop_ip,
                                           "desktop_mask": desktop_mask,
                                           "desktop_gateway": desktop_gateway,
                                           "desktop_dns1": desktop_dns1,
                                           "desktop_dns2": desktop_dns2
                                           })

        sys_base, data_base = self._get_template_storage_path()
        templates = db_api.get_voi_template_by_uuids(template_uuids)

        for template in templates:
            _d = dict()
            template_name = template.name
            template_uuid = template.uuid
            _d["template_name"] = template_name
            _d["template_uuid"] = template_uuid
            devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
            operates = db_api.get_item_with_all(models.YzyVoiTemplateOperate,
                                                {"template_uuid": template.uuid, "exist": True})
            disks = list()
            for disk in devices:
                _tmp_disk = list()
                base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
                # file_name = constants.VOI_BASE_PREFIX + disk.uuid
                backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
                backing_file = os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(0) + disk.uuid)
                if not os.path.exists(backing_file):
                    logger.error("disk info error: %s disk file not exist" % backing_file)
                    return get_error_result("DiskNotExist")
                # reserve_size = str(bytes_to_section(os.path.getsize(backing_file)))
                reserve_size = str(gi_to_section(100))
                real_size  = str(disk.section) if disk.section else str(gi_to_section(disk.size))
                _tmp_disk.append(
                    {"uuid": disk.uuid, "type": self.disk_type_dict[disk.type], "dif_level": 0, "prefix": "voi",
                     "real_size": real_size, "reserve_size": reserve_size, "max_dif": template.version})
                for operate in operates:
                    file_path = os.path.join(backing_dir,
                                             constants.VOI_BASE_PREFIX % str(operate.version) + disk.uuid)
                    if os.path.exists(file_path):
                        # reserve_size = str(bytes_to_section(os.path.getsize(file_path)) + gi_to_section(50)) # 加5G
                        reserve_size = str(gi_to_section(100)) # 加5G

                        _tmp_disk.append(
                            {"uuid": disk.uuid, "type": self.disk_type_dict[disk.type], "dif_level": operate.version,
                             "prefix": "voi", "real_size": real_size,
                             "reserve_size": reserve_size, "max_dif": template.version })
                _tmp_disk.sort(key=lambda x:x["dif_level"])
                # import pdb; pdb.set_trace()
                # disks.append(_tmp_disk[-1])
                disks.extend(_tmp_disk)

                # # todo 共享盘
                # share_disk_bind = db_api.get_item_with_first(models.YzyVoiShareToDesktops,
                #                                              {"desktop_uuid": desktop.uuid})
                # if share_disk_bind:
                #     share_disk = self.get_object_by_uuid(YzyVoiTerminalShareDisk, share_disk_bind.disk_uuid)
                #     if share_disk and share_disk.enable:
                #         base_name = "voi_0_%s" % share_disk.uuid
                #         base_file = os.path.join(sys_base, base_name)
                #         reserve_size = str(bytes_to_section(os.path.getsize(base_file)))
                #         disks.append({
                #             "uuid": share_disk.uuid, "type": 2, "prefix": "voi", "dif_level": 0,
                #             "reserve_size": reserve_size, "real_size": str(gi_to_section(share_disk.disk_size)),
                #             "torrent_file": base_file + ".torrent", "restore_flag": share_disk.restore
                #         })
            # 共享盘
            share_disks = db_api.get_item_with_all(models.YzyVoiTerminalShareDisk, {"group_uuid": group_uuid})
            share_disks_dict = dict()
            for share_disk in share_disks:
                backing_dir = os.path.join(sys_base, constants.IMAGE_CACHE_DIRECTORY_NAME)
                base_name = (constants.VOI_SHARE_BASE_PREFIX % share_disk.version) + share_disk.uuid
                base_file = os.path.join(backing_dir, base_name)
                reserve_size = str(bytes_to_section(os.path.getsize(base_file)))
                share_disk_uuid = share_disk.uuid
                share_disks_dict[share_disk_uuid] = {
                                "uuid": share_disk.uuid, "type": 2, "prefix": "voi", "dif_level": share_disk.version,
                                "reserve_size": reserve_size, "real_size": str(gi_to_section(share_disk.disk_size)),
                                "torrent_file": base_file + ".torrent", "restore_flag": share_disk.restore,
                                "max_dif": share_disk.version
                            }

            share_disks_binds = db_api.get_item_with_all(models.YzyVoiShareToDesktops, {"group_uuid": group_uuid})
            desktop_share_disk = dict()
            for bind in share_disks_binds:
                # 绑定关系
                disk_uuid = bind.disk_uuid
                desktop_uuid = bind.desktop_uuid
                desktop_share_disk[desktop_uuid] = share_disks_dict.get(disk_uuid)

            for desktop_dict in desktop_group_list:
                if desktop_dict["template_uuid"] == template_uuid:
                    desktop_dict["disks"] = disks
                    desktop_dict["desktop_group_desc"] = template.desc
                    # # voi 共享盘
                    desktop_uuid = desktop_dict["desktop_group_uuid"]
                    share_disk = desktop_share_disk.get(desktop_uuid)
                    if share_disk:
                        desktop_dict["disks"].append(share_disk)

        for desktop_dict in desktop_group_list:
            desktop_dict.pop("template_uuid")
        return get_error_result("Success", {"desktop_group_list": desktop_group_list})

    def sync_template_disk_info(self, data):
        logger.info("desktop sync upload info: %s"% data)
        # desktop_data = data.get("desktop", {})
        template_uuid = data.get("uuid")
        template = db_api.get_voi_instance_template(template_uuid)
        if not template:
            logger.error("desktop sync info error: %s not exist"% template_uuid)
            return get_error_result("TerminalDesktopNotExist")

        sys_base, data_base = self._get_template_storage_path()
        template_name = template.name
        template_uuid = template.uuid
        desktop_info = dict()
        desktop_info["name"] = template_name
        desktop_info["uuid"] = template_uuid
        desktop_info["sys_type"] = self.system_type_dict[template.os_type]
        desktop_info["desc"] = template.desc

        devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
        operates = db_api.get_item_with_all(models.YzyVoiTemplateOperate,
                                            {"template_uuid": template.uuid, "exist": True})
        disks = list()
        for disk in devices:
            base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
            # file_name = constants.VOI_BASE_PREFIX + disk.uuid
            backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
            backing_file = os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(0) + disk.uuid)
            if not os.path.exists(backing_file):
                logger.error("desktop info compare error: %s backing file not exist"% disk.uuid)
                return get_error_result("OtherError")
            reserve_size = str(bytes_to_section(os.path.getsize(backing_file)))
            real_size = str(disk.section) if disk.section else str(gi_to_section(disk.size))
            disks.append({"uuid": disk.uuid, "type": self.disk_type_dict[disk.type], "dif_level": 0, "prefix": "voi",
                          "real_size": real_size,
                          "file_path": backing_file, "reserve_size": reserve_size})
            for operate in operates:
                file_path = os.path.join(backing_dir,
                                constants.VOI_BASE_PREFIX % str(operate.version) + disk.uuid)

                if os.path.exists(file_path):
                    reserve_size = str(bytes_to_section(os.path.getsize(file_path)))
                    # _size =
                    disks.append(
                        {"uuid": disk.uuid, "type": self.disk_type_dict[disk.type], "dif_level": operate.version,
                         "prefix": "voi", "real_size": real_size, "file_path": file_path,
                         "reserve_size": reserve_size})
        desktop_info["disks"] = disks
        logger.info("current desktop info compare info:%s", desktop_info)
        # 对比
        download_disks = list()
        upload_disks = list()
        client_disks = data.get("disks", [])
        for dk in client_disks:
            if dk not in disks:
                # 需要上传
                if "file_path" in dk: dk.pop("file_path")
                dk.update({"prefix": "voi"})
                upload_disks.append(dk)
        desktop_info["upload_disks"] = upload_disks
        for dk in disks:
            if dk not in client_disks:
                # 需要下载
                # todo 添加种子文件信息
                file_path = None
                if "file_path" in dk: file_path = dk.pop("file_path")
                if file_path :
                    torrent_file = file_path + ".torrent"
                    dk["torrent_file"] = torrent_file
                download_disks.append(dk)
        desktop_info["download_disks"] = download_disks
        # 调用终端管理，发送上传下载命令
        req_data = {
            "cmd": "sync_client_disk",
            "data": desktop_info
        }
        # ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        logger.info("sync desktop disk terminal agent cmd: %s "% (req_data))
        return get_error_result("Success", data={"desktop": desktop_info})

    # def get_info_by_system_disk(self, data):
    #     """
    #     根据系统启动盘查找桌面的信息
    #     {
    #         "boot_disk": "voi_0_92f9d1ba-cb4a-41ba-971a-618f9e306571",
    #         # 还需桌面分组信息
    #     }
    #     {
    #         "desktop": {
    #             "uuid": "f15a1759-789e-4e17-a3e1-e723121e9314",
    #             "name": "",
    #             "desc": "",
    #             "sys_type":1,
    #             "disks": [
    #                 {
    #                     "uuid":"91f9d1ba-cb4a-41ba-971a-618f9e306571",
    #                     "type":1,
    #                     "dif_level":1,
    #                     "prefix": "voi",
    #                     "real_size":8888888888
    #                 },
    #                 {
    #                     "uuid":"92f9d1ba-cb4a-41ba-971a-618f9e306571",
    #                     "type":1,
    #                     "dif_level":1,
    #                     "prefix": "voi",
    #                    "real_size":8888888888
    #                 }
    #             ]
    #         }
    #     }
    #         :param data:
    #     :return:
    #     """
    #     system_type_dict = {
    #         "windows_7_x64" : 1,
    #         "Other": 0,
    #     }
    #     disk_type_dict = {
    #         constants.IMAGE_TYPE_SYSTEM : 0,
    #         constants.IMAGE_TYPE_DATA: 1
    #     }
    #     sys_base, data_base = self._get_template_storage_path()
    #     sys_disk_dir = os.path.join(sys_base, "_base")
    #     data_disk_dir = os.path.join(data_base, "_base")
    #
    #     # system_disk = data.get("uuid", "")
    #     system_disk_uuid = data.get("uuid", "")
    #     device = db_api.get_item_with_first(models.YzyVoiDeviceInfo,
    #                           {"uuid": system_disk_uuid, "type": constants.IMAGE_TYPE_SYSTEM})
    #     if not device:
    #         logger.error("voi query desktop by boot disk error: %s not exist"% system_disk_uuid)
    #         return get_error_result("TemplateNotExist")
    #
    #     template = db_api.get_voi_instance_template(device.instance_uuid)
    #     if not template:
    #         logger.error("voi query template not exist: %s"% system_disk_uuid)
    #         return get_error_result("TemplateNotExist")
    #
    #     desktop = {
    #         "uuid": template.uuid,
    #         "name": template.name,
    #         "desc": template.desc,
    #         "sys_type": system_type_dict.get(template.os_type, "Other"),
    #         "disks" : list()
    #     }
    #     version = template.version
    #     template_devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo,
    #                                         {"instance_uuid": template.uuid})
    #     for device in template_devices:
    #         disk_uuid = device.uuid
    #         if device.type == constants.IMAGE_TYPE_SYSTEM:
    #             for i in range(version + 1):
    #                 _disk = dict()
    #                 name = "voi_%d_%s" % (i, disk_uuid)
    #                 file_path = os.path.join(sys_disk_dir, name)
    #                 if not os.path.exists(file_path):
    #                     continue
    #                 real_size = os.path.getsize(file_path)
    #                 _disk["uuid"] = disk_uuid
    #                 _disk["real_size"] = real_size
    #                 _disk["dif_level"] = i
    #                 _disk["type"] = self.disk_type_dict[device.type]
    #                 desktop["disks"].append(_disk)
    #         else:
    #             # import pdb
    #             # pdb.set_trace()
    #             for i in range(version + 1):
    #                 _disk = dict()
    #                 name = "voi_%d_%s" % (i, disk_uuid)
    #                 file_path = os.path.join(data_disk_dir, name)
    #                 if not os.path.exists(file_path):
    #                     continue
    #                 real_size = os.path.getsize(file_path)
    #                 _disk["uuid"] = disk_uuid
    #                 _disk["real_size"] = real_size
    #                 _disk["dif_level"] = i
    #                 _disk["type"] = disk_type_dict[device.type]
    #                 desktop["disks"].append(_disk)
    #     # pass
    #     logger.info("voi terminal get desktop info: %s"% (desktop))
    #     return get_error_result("Success", {"desktop": desktop})

    def get_info_by_system_disk(self, data):
        """
        根据系统启动盘查找桌面的信息
        {
            "boot_disk": "voi_0_92f9d1ba-cb4a-41ba-971a-618f9e306571",
            # 还需桌面分组信息
        }
        {
            "desktop": {
                "uuid": "f15a1759-789e-4e17-a3e1-e723121e9314",
                "name": "",
                "desc": "",
                "sys_type":1,
                "disks": [
                    {
                        "uuid":"91f9d1ba-cb4a-41ba-971a-618f9e306571",
                        "type":1,
                        "dif_level":1,
                        "prefix": "voi",
                        "real_size":8888888888
                    },
                    {
                        "uuid":"92f9d1ba-cb4a-41ba-971a-618f9e306571",
                        "type":1,
                        "dif_level":1,
                        "prefix": "voi",
                       "real_size":8888888888
                    }
                ]
            }
        }
            :param data:
        :return:
        """
        # system_disk = data.get("uuid", "")
        system_disk_uuid = data.get("uuid", "")
        device = db_api.get_item_with_first(models.YzyVoiDeviceInfo,
                              {"uuid": system_disk_uuid, "type": constants.IMAGE_TYPE_SYSTEM})
        if not device:
            logger.error("voi query desktop by boot disk error: %s not exist"% system_disk_uuid)
            return get_error_result("TemplateNotExist")

        template = db_api.get_voi_instance_template(device.instance_uuid)
        if not template:
            logger.error("voi query template not exist: %s"% system_disk_uuid)
            return get_error_result("TemplateNotExist")
        desktop_group = db_api.get_item_with_first(models.YzyVoiDesktop,
                              {"template_uuid": template.uuid})
        desktop = {
            "uuid": template.uuid,
            "name": template.name,
            "desktop_group_name": desktop_group.name,
            "last_update_time": str(template.updated_time)
        }

        logger.info("voi terminal get desktop info: %s"% (desktop))
        return get_error_result("Success", desktop)

    def download_template_diff_disk(self, data):
        """
        {
            "desktop_group_uuid": "92f9d1ba-cb4a-41ba-971a-2222222222",
            "diff_disk_uuid": "92f9d1ba-cb4a-41ba-971a-618f9e306571",
            "diff_level": 3
        }
        {
            "template_uuid": "f15a1759-789e-4e17-a3e1-e723121e9314",
            "torrent_file": "/opt/slow/_base/xxxx.torrent",
            "os_sys_type":1,
            "diff_disk_type":1,
            "real_size":8888888888,
            "reserve_size": 2222222222
        }
        """
        desktop_group_uuid = data.get("desktop_group_uuid", "")
        diff_disk_uuid = data.get("diff_disk_uuid", "")
        diff_level = data.get("diff_level", "")
        desktop_group = db_api.get_item_with_first(models.YzyVoiDesktop, {"uuid": desktop_group_uuid})
        if desktop_group:
            template_uuid = desktop_group.template_uuid
            os_type = desktop_group.os_type
            disk = db_api.get_item_with_first(models.YzyVoiDeviceInfo,
                                            {"instance_uuid": template_uuid, "uuid": diff_disk_uuid})
            if not disk:
                logger.error('template_uuid: {}, diff_disk_uuid: {}'.format(template_uuid, diff_disk_uuid))
                return get_error_result("DiskNotExist")
            if diff_level:
                operate_version = db_api.get_item_with_all(models.YzyVoiTemplateOperate,
                                                    {"template_uuid": template_uuid,
                                                     "version": diff_level,
                                                     "exist": True})
                if not operate_version:
                    return get_error_result("TemplateVersionNotExist")

            sys_base, data_base = self._get_template_storage_path()
            base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
            backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
            backing_file = os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(diff_level) + disk.uuid)
            torrent_file = backing_file + ".torrent"
            if not os.path.exists(backing_file):
                logger.error("%s backing file not exist" % backing_file)
                return get_error_result("OtherError")
            if not os.path.exists(torrent_file):
                logger.error("%s torrent file not exist" % torrent_file)
                return get_error_result("OtherError")
            # reserve_size = str(bytes_to_section(os.path.getsize(backing_file)) + gi_to_section(50))  # 加5G
            reserve_size = str(gi_to_section(100))                                                      # 加5G

            real_size = str(disk.section) if disk.section else str(gi_to_section(disk.size))
            ret_data = {
                "template_uuid": template_uuid,
                "diff_disk_type": self.disk_type_dict[disk.type],
                "os_sys_type": self.system_type_dict[desktop_group.os_type.lower()],
                "real_size": real_size,
                "reserve_size": reserve_size,
                "torrent_file": torrent_file
            }
            logger.debug('return: {}'.format(ret_data))
            return get_error_result("Success", ret_data)
        else:
            logger.error('desktop_group not exists: {}'.format(desktop_group_uuid))
            return get_error_result("DesktopNotExist", name="")

    def init_template_disk_info(self, data):
        logger.info("init desktop info: %s" % data)
        templates = db_api.get_voi_template_with_all({})
        # if not templates:
        #     logger.error("init desktop info error: %s not exist" % )
        #     return get_error_result("TerminalDesktopNotExist")
        sys_base, data_base = self._get_template_storage_path()
        desktops = list()
        for template in templates:
            template_name = template.name
            template_uuid = template.uuid
            desktop_info = dict()
            desktop_info["name"] = template_name
            desktop_info["uuid"] = template_uuid
            desktop_info["sys_type"] = template.os_type
            desktop_info["desc"] = template.desc

            devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
            operates = db_api.get_item_with_all(models.YzyVoiTemplateOperate,
                                                {"template_uuid": template.uuid, "exist": True})
            disks = list()
            for disk in devices:
                base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
                # file_name = constants.VOI_BASE_PREFIX + disk.uuid
                backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
                backing_file = os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(0) + disk.uuid)
                if not os.path.exists(backing_file):
                    logger.error("desktop info compare error: %s backing file not exist" % disk.uuid)
                    return get_error_result("OtherError")
                _size = os.path.getsize(backing_file)
                backing_torrent_file = backing_file + ".torrent"
                disk_info = {"uuid": disk.uuid, "type": disk.type, "dif_level": 0, "prefix": "voi", "real_size": _size}
                if os.path.exists(backing_torrent_file):
                    disk_info.update({"torrent_file": backing_torrent_file})
                disks.append(disk_info)
                for operate in operates:
                    file_path = os.path.join(backing_dir,
                                             constants.VOI_BASE_PREFIX % str(operate.version) + disk.uuid)
                    if os.path.exists(file_path):
                        _size = os.path.getsize(file_path)
                        _disk_info = {"uuid": disk.uuid, "type": disk.type, "dif_level": operate.version,
                             "prefix": "voi", "real_size": _size}
                        torrent_file = file_path + ".torrent"
                        if os.path.exists(torrent_file):
                            _disk_info.update({"torrent_file": torrent_file})
                        disks.append(_disk_info)
            desktop_info["disks"] = disks
            desktops.append(desktop_info)

        logger.info("init desktop info:%s", desktops)
        return get_error_result("Success", data={"desktops": desktops})

    def send_template_disk_info(self, data):
        """ 下发桌面 """
        logger.info("send desktop info: %s" % data)
        mac = data.get("mac", "")
        templates = db_api.get_voi_template_with_all({})
        # if not templates:
        #     logger.error("init desktop info error: %s not exist" % )
        #     return get_error_result("TerminalDesktopNotExist")
        sys_base, data_base = self._get_template_storage_path()
        desktops = list()
        for template in templates:
            template_name = template.name
            template_uuid = template.uuid
            desktop_info = dict()
            desktop_info["name"] = template_name
            desktop_info["uuid"] = template_uuid
            desktop_info["sys_type"] = self.system_type_dict[template.os_type]
            desktop_info["desc"] = template.desc

            devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
            operates = db_api.get_item_with_all(models.YzyVoiTemplateOperate,
                                                {"template_uuid": template.uuid, "exist": True})
            disks = list()
            for disk in devices:
                base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
                # file_name = constants.VOI_BASE_PREFIX + disk.uuid
                backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
                backing_file = os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(0) + disk.uuid)
                if not os.path.exists(backing_file):
                    logger.error("desktop info compare error: %s backing file not exist" % disk.uuid)
                    return get_error_result("OtherError")
                _size = os.path.getsize(backing_file)
                backing_torrent_file = backing_file + ".torrent"
                disk_info = {"uuid": disk.uuid, "type": self.disk_type_dict[disk.type], "dif_level": 0,
                             "prefix": "voi", "real_size": disk.size, "reserve_size": int(size_to_G(_size)) + 1}
                if os.path.exists(backing_torrent_file):
                    disk_info.update({"torrent_file": backing_torrent_file})
                disks.append(disk_info)
                for operate in operates:
                    file_path = os.path.join(backing_dir,
                            constants.VOI_BASE_PREFIX % str(operate.version) + disk.uuid)
                    if os.path.exists(file_path):
                        # _size = os.path.getsize(file_path)
                        _disk_info = {"uuid": disk.uuid, "type": self.disk_type_dict[disk.type], "dif_level": operate.version,
                                      "prefix": "voi", "real_size": disk.size, "reserve_size": 50}
                        torrent_file = file_path + ".torrent"
                        if os.path.exists(torrent_file):
                            _disk_info.update({"torrent_file": torrent_file})
                        disks.append(_disk_info)
            desktop_info["disks"] = disks
            desktops.append(desktop_info)
        # 通知VOI终端管理服下发桌面通知
        req_data = {
            "cmd": "send_desktop",
            "data": {
                "mac": mac,
                "desktops": desktops
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        if ret.get("code", -1) == 0:
            logger.info("init desktop info:%s", desktops)
            return get_error_result("Success", data={"desktops": desktops})
        logger.error("send desktop info fail: %s"% ret)
        return ret

    def send_template_disk_info_single(self, data):
        """ 下发桌面 单个桌面"""
        logger.info("send desktop info single: %s" % data)
        mac_list_str = data.get("mac_list", "")
        template_uuid = data.get("desktop_uuid", "")
        template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
        sys_base, data_base = self._get_template_storage_path()
        desktops = list()
        template_name = template.name
        template_uuid = template.uuid
        desktop_info = dict()
        desktop_info["name"] = template_name
        desktop_info["uuid"] = template_uuid
        desktop_info["sys_type"] = self.system_type_dict[template.os_type]
        desktop_info["desc"] = template.desc

        devices = db_api.get_item_with_all(models.YzyVoiDeviceInfo, {"instance_uuid": template.uuid})
        operates = db_api.get_item_with_all(models.YzyVoiTemplateOperate,
                                            {"template_uuid": template.uuid, "exist": True})
        disks = list()
        for disk in devices:
            base_path = sys_base if constants.IMAGE_TYPE_SYSTEM == disk.type else data_base
            # file_name = constants.VOI_BASE_PREFIX + disk.uuid
            backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
            backing_file = os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(0) + disk.uuid)
            if not os.path.exists(backing_file):
                logger.error("desktop info compare error: %s backing file not exist" % disk.uuid)
                return get_error_result("OtherError")
            _size = os.path.getsize(backing_file)
            backing_torrent_file = backing_file + ".torrent"
            disk_info = {"uuid": disk.uuid, "type": self.disk_type_dict[disk.type], "dif_level": 0,
                         "prefix": "voi", "real_size": disk.size, "reserve_size": int(size_to_G(_size)) + 1}
            if os.path.exists(backing_torrent_file):
                disk_info.update({"torrent_file": backing_torrent_file})
            disks.append(disk_info)
            for operate in operates:
                file_path = os.path.join(backing_dir,
                        constants.VOI_BASE_PREFIX % str(operate.version) + disk.uuid)
                if os.path.exists(file_path):
                    # _size = os.path.getsize(file_path)
                    _disk_info = {"uuid": disk.uuid, "type": self.disk_type_dict[disk.type], "dif_level": operate.version,
                                  "prefix": "voi", "real_size": disk.size, "reserve_size": 50}
                    torrent_file = file_path + ".torrent"
                    if os.path.exists(torrent_file):
                        _disk_info.update({"torrent_file": torrent_file})
                    disks.append(_disk_info)
        desktop_info["disks"] = disks
        desktops.append(desktop_info)
        # 通知VOI终端管理服下发桌面通知
        req_data = {
            "cmd": "send_desktop",
            "data": {
                "mac": mac,
                "desktops": desktops
            }
        }
        ret = voi_terminal_post("/api/v1/voi/terminal/command/", req_data)
        if ret.get("code", -1) == 0:
            logger.info("init desktop info:%s", desktops)
            return get_error_result("Success", data={"desktops": desktops})
        logger.error("send desktop info fail: %s"% ret)
        return ret

    def upload_template_diff_disk(self, data):
        """ 上传差分盘
        1、判断桌面组是否存在
        2、判断差分是否可以正常上传，更改模板状态
        3、创建下载任务
        4、上传完后链接
        """
        # pass
        desktop_group_uuid = data.get("desktop_group_uuid", "")
        desktop = db_api.get_item_with_first(models.YzyVoiDesktop, {"uuid": desktop_group_uuid})
        if not desktop:
            logger.error("terminal upload diff disk error: %s desktop not exist" % desktop_group_uuid)
            return get_error_result("DesktopNotExist", name="")
        # todo 判断差分盘的层级
        diff_level = data.get("diff_level")
        resp = get_error_result("Success")
        logger.info("terminal upload diff disk success!!! %s"% data)
        return resp

    def check_upload_state(self, data):
        """
            "desktop_group_uuid": "1234"
        """
        desktop_group_uuid = data.get("desktop_group_uuid", "")
        desktop = db_api.get_item_with_first(models.YzyVoiDesktop, {"uuid": desktop_group_uuid})
        resp = get_error_result("Success", data={"can_update": 0})
        if not desktop:
            logger.error("terminal desktop group error: %s desktop not exist" % desktop_group_uuid)
        else:
            template_uuid = desktop.template_uuid
            template = db_api.get_item_with_first(models.YzyVoiTemplate, {"uuid": template_uuid})
            if template and template.status == "inactive":
                resp = get_error_result("Success", data={"can_update": 1})
        return resp

