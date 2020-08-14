import time
import os
import psutil
from rest_framework import serializers
from web_manage.common.utils import CustomDateTimeField, DateTimeFieldMix
from web_manage.common import constants
from web_manage.yzy_resource_mgr import models as resource_model
from web_manage.yzy_user_desktop_mgr import models as personal_model
from web_manage.common.config import SERVER_CONF
from . import models


class InstanceDevicesSerializer(DateTimeFieldMix):

    class Meta:
        model = models.YzyInstanceDeviceInfo
        fields = ('uuid', 'type', 'device_name', 'instance_uuid', 'boot_index', 'size')


class GroupSerializer(DateTimeFieldMix):
    network_name = serializers.CharField(source='network.name')
    subnet_name = serializers.CharField(source='subnet.name')
    subnet_start_ip = serializers.CharField(source='subnet.start_ip')
    subnet_end_ip = serializers.CharField(source='subnet.end_ip')
    terminal_count = serializers.SerializerMethodField(read_only=True)
    desktop_count = serializers.SerializerMethodField(read_only=True)
    instance_count = serializers.SerializerMethodField(read_only=True)
    has_desktop = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyGroup
        fields = ('uuid', 'name', 'desc', 'network', 'network_name', 'subnet', 'subnet_name', 'subnet_start_ip',
                  'subnet_end_ip', 'start_ip', 'end_ip', 'terminal_count', 'instance_count', 'has_desktop',
                  'desktop_count')

    def get_desktop_count(self, obj):
        return models.YzyDesktop.objects.filter(group=obj.uuid, deleted=False).count()

    def get_instance_count(self, obj):
        instance_count = 0
        desktops = models.YzyDesktop.objects.filter(group=obj.uuid, deleted=False)
        for desktop in desktops:
            instance_count += desktop.instance_num
        return instance_count

    def get_terminal_count(self, obj):
        return 0

    def get_has_desktop(self, obj):
        if 1 == obj.group_type:
            desktop = models.YzyDesktop.objects.filter(group=obj.uuid, deleted=False).first()
            if desktop:
                return 1
        return 0


class InstanceSerializer(DateTimeFieldMix):
    up_time = serializers.SerializerMethodField(read_only=True)
    host_name = serializers.CharField(source='host.name')
    user_name = serializers.SerializerMethodField(read_only=True)
    ipaddr = serializers.SerializerMethodField(read_only=True)
    active_time = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyInstances
        fields = ('uuid', 'name', 'ipaddr', 'host_name', 'status', 'up_time', 'active_time', 'message', 'user_name')

    def get_ipaddr(self, obj):
        if not obj.ipaddr:
            return "DHCP"
        return obj.ipaddr

    def get_active_time(self, obj):
        if obj.status == constants.STATUS_ACTIVE:
            now = int(time.time())
            start_time = obj.up_time.timestamp()
            gap = now - start_time
        else:
            gap = 0
        return gap

    def get_user_name(self, obj):
        user_name = ''
        if obj.status == constants.STATUS_ACTIVE:
            desktop = personal_model.YzyUserRandomInstance.objects.filter(instance=obj.uuid, deleted=False).first()
            if desktop:
                user = personal_model.YzyGroupUser.objects.filter(uuid=desktop.user_uuid, deleted=False).first()
            else:
                user = personal_model.YzyGroupUser.objects.filter(uuid=obj.user_uuid, deleted=False).first()
            if user:
                user_name = user.user_name
        return user_name

    def get_up_time(self, obj):
        up_time = ''
        if obj.status == constants.STATUS_ACTIVE:
            up_time = obj.up_time.strftime("%Y-%m-%d %H:%M:%S")

        return up_time


class DesktopSerializer(DateTimeFieldMix):
    group_name = serializers.CharField(source='group.name')
    template_name = serializers.CharField(source='template.name')
    template_status = serializers.CharField(source='template.status')
    pool_name = serializers.CharField(source='pool.name')
    network_name = serializers.CharField(source='network.name')
    # os_type = serializers.SerializerMethodField(read_only=True)
    inactive_count = serializers.SerializerMethodField(read_only=True)
    active_count = serializers.SerializerMethodField(read_only=True)
    user_count = serializers.SerializerMethodField(read_only=True)
    owner = serializers.SerializerMethodField(read_only=True)
    devices = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyDesktop
        fields = ('uuid', 'name', 'template', 'template_name', 'pool', 'pool_name', 'sys_restore', 'data_restore',
                  'instance_num', 'inactive_count', 'active', 'group', 'group_name', 'vcpu', 'ram', 'os_type',
                  'created_at', 'active_count', 'owner', 'network', 'network_name', 'order_num', 'devices',
                  'prefix', 'postfix', 'template_status', 'user_count')
        # fields = '__all__'

    def get_user_count(self, obj):
        count = 0
        instances = models.YzyInstances.objects.filter(desktop_uuid=obj.uuid, deleted=False)
        for instance in instances:
            if instance.spice_link:
                count += 1
        return count

    def get_inactive_count(self, obj):
        count = 0
        instances = models.YzyInstances.objects.filter(desktop_uuid=obj.uuid, deleted=False)
        for instance in instances:
            if instance.status != 'active':
                count += 1
        return count

    def get_active_count(self, obj):
        count = 0
        instances = models.YzyInstances.objects.filter(desktop_uuid=obj.uuid, deleted=False)
        for instance in instances:
            if instance.status == 'active':
                count += 1
        return count

    def get_owner(self, obj):
        return 'admin'

    def get_devices(self, obj):
        disks = list()
        devices = models.YzyInstanceDeviceInfo.objects.filter(instance_uuid=obj.template.uuid, deleted=False)
        for device in devices:
            info = {
                'type': device.type,
                'boot_index': device.boot_index,
                'size': device.size
            }
            disks.append(info)
        return disks


class TemplateSerializer(DateTimeFieldMix):
    bind_ip = serializers.SerializerMethodField(read_only=True)
    host_name = serializers.CharField(source='node.name')
    host_ip = serializers.CharField(source='node.ip')
    network_uuid = serializers.CharField(source='network.uuid')
    network_name = serializers.CharField(source='network.name')
    subnet_uuid = serializers.SerializerMethodField(read_only=True)
    subnet_name = serializers.SerializerMethodField(read_only=True)
    pool_uuid = serializers.CharField(source='pool.uuid')
    pool_name = serializers.CharField(source='pool.name')
    subnet_start_ip = serializers.SerializerMethodField(read_only=True)
    subnet_end_ip = serializers.SerializerMethodField(read_only=True)
    updated_time = CustomDateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    # os_type = serializers.SerializerMethodField(read_only=True)
    owner = serializers.SerializerMethodField(read_only=True)
    devices = serializers.SerializerMethodField(read_only=True)
    desktop_count = serializers.SerializerMethodField(read_only=True)
    instance_count = serializers.SerializerMethodField(read_only=True)
    os_type_simple = serializers.SerializerMethodField(read_only=True)
    cpu_count = serializers.SerializerMethodField(read_only=True)
    total_ram = serializers.SerializerMethodField(read_only=True)
    download_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyInstanceTemplate
        fields = ('uuid', 'name', 'desc', 'host_ip', 'host_name', 'network_name', 'subnet_name', 'bind_ip',
                  'vcpu', 'ram', 'os_type', 'subnet_start_ip', 'subnet_end_ip', 'devices', 'owner',
                  'desktop_count', 'instance_count', 'updated_time', 'status', 'os_type_simple', 'created_at',
                  'pool_uuid', 'pool_name', 'network_uuid', 'subnet_uuid', 'attach', 'cpu_count', 'total_ram',
                  'download_url')

    def get_bind_ip(self, obj):
        if not obj.bind_ip:
            return "DHCP分配"
        return obj.bind_ip

    def get_subnet_uuid(self, obj):
        if obj.subnet_uuid:
            subnet = resource_model.YzySubnets.objects.filter(uuid=obj.subnet_uuid, deleted=False).first()
            return subnet.uuid
        return ""

    def get_subnet_name(self, obj):
        if obj.subnet_uuid:
            subnet = resource_model.YzySubnets.objects.filter(uuid=obj.subnet_uuid, deleted=False).first()
            return subnet.name
        return ""

    def get_subnet_start_ip(self, obj):
        if obj.subnet_uuid:
            subnet = resource_model.YzySubnets.objects.filter(uuid=obj.subnet_uuid, deleted=False).first()
            return subnet.start_ip
        return ""

    def get_subnet_end_ip(self, obj):
        if obj.subnet_uuid:
            subnet = resource_model.YzySubnets.objects.filter(uuid=obj.subnet_uuid, deleted=False).first()
            return subnet.end_ip
        return ""
    # def get_os_type(self, obj):
    #     os_type = constants.IMAGE_TYPE_REVERT.get(obj.os_type)
    #     if os_type:
    #         return os_type

    def get_os_type_simple(self, obj):
        simple = constants.IMAGE_TYPE.get(obj.os_type)
        if simple:
            return simple
        return obj.os_type

    def get_desktop_count(self, obj):
        """
        obj.desktops里面的'desktops'对应'YzyDesktop'表的外键定义中的'related_name'
        """
        if constants.EDUCATION_TYPE == obj.classify:
            return obj.desktops.filter(deleted=False).count()
        else:
            return obj.personal_desktops.filter(deleted=False).count()

    def get_instance_count(self, obj):
        instance_count = 0
        if constants.EDUCATION_TYPE == obj.classify:
            desktops = obj.desktops.filter(deleted=False)
        else:
            desktops = obj.personal_desktops.filter(deleted=False)
        for desktop in desktops:
            instance_count += desktop.instance_num
        return instance_count

    def get_devices(self, obj):
        state = self.context['request'].GET.get('state', 1)
        disks = list()
        # 模板磁盘的展示需要考虑他的磁盘修改情况
        if 1 == int(state):
            origin_devices = models.YzyInstanceDeviceInfo.objects.filter(instance_uuid=obj.uuid, deleted=False)
            modify_devices = models.YzyDeviceModify.objects.filter(template_uuid=obj.uuid, deleted=False)
            for device in origin_devices:
                # 如果原始盘被标记为删除了，则不显示
                flag = False
                for disk in modify_devices:
                    if device.uuid == disk.uuid and 1 == disk.state:
                        flag = True
                        break
                if flag:
                    continue
                info = {
                    'uuid': device.uuid,
                    'type': device.type,
                    'device_name': device.device_name,
                    'boot_index': device.boot_index,
                    'size': device.size,
                    'used': device.used
                }
                disks.append(info)
            for device in modify_devices:
                # 修改记录里只有被标记为添加的盘才显示
                if 2 == device.state:
                    info = {
                        'uuid': device.uuid,
                        'type': constants.IMAGE_TYPE_DATA,
                        'device_name': device.device_name,
                        'boot_index': device.boot_index,
                        'size': device.size,
                        'used': device.used
                    }
                    disks.append(info)
        else:
            # 桌面组中模板磁盘的展示只展示模板的原始盘
            devices = models.YzyInstanceDeviceInfo.objects.filter(instance_uuid=obj.uuid, deleted=False)
            for device in devices:
                info = {
                    'uuid': device.uuid,
                    'type': device.type,
                    'device_name': device.device_name,
                    'boot_index': device.boot_index,
                    'size': device.size,
                    'used': device.used
                }
                disks.append(info)
        return disks

    def get_owner(self, obj):
        return 'admin'

    def get_cpu_count(self, obj):
        return psutil.cpu_count()

    def get_total_ram(self, obj):
        return round(psutil.virtual_memory().total/1024/1024/1024, 1)

    def get_download_url(self, obj):
        bind = SERVER_CONF.addresses.get_by_default('server_bind', '')
        if bind:
            port = bind.split(':')[-1]
        else:
            port = constants.SERVER_DEFAULT_PORT
        endpoint = 'http://%s:%s' % (obj.node.ip, port)
        url = '%s/api/v1/template/download?path=%s' % (endpoint, obj.uuid)
        return url


class TemplateImageSerializer(DateTimeFieldMix):

    storages = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = resource_model.YzyNodes
        fields = ('name', 'uuid', 'ip', 'storages')

    def get_storages(self, obj):
        result = []
        template_uuid = self.context['request'].GET.get('template_uuid', None)
        if template_uuid:
            template = models.YzyInstanceTemplate.objects.filter(uuid=template_uuid, deleted=False).first()
            parts = resource_model.YzyNodeStorages.objects.filter(node=obj.uuid, deleted=False)
            devices = models.YzyInstanceDeviceInfo.objects.filter(instance_uuid=template_uuid, deleted=False)
            for part in parts:
                if str(constants.TEMPLATE_SYS) in part.role:
                    for device in devices:
                        if constants.IMAGE_TYPE_SYSTEM == device.type:
                            storage = dict()
                            storage['role'] = constants.TEMPLATE_SYS
                            storage['path'] = part.path
                            storage['image_id'] = device.uuid
                            storage['version'] = template.version
                            exists = models.YzyInstanceDeviceInfo.objects.filter(image_id=device.uuid,
                                                                                 deleted=False).first()
                            if exists:
                                storage['bind_desktop'] = True
                            else:
                                storage['bind_desktop'] = False
                            task = resource_model.YzyTaskInfo.objects.filter(image_id=device.uuid, host_uuid=obj.uuid,
                                                                             deleted=False). \
                                order_by('-progress').order_by('-id').first()
                            if not task or task.status == 'end':
                                status = 0
                            elif task.status == 'error':
                                status = 2
                            else:
                                status = 1
                            storage['status'] = status
                            result.append(storage)
                            break
                if str(constants.TEMPLATE_DATA) in part.role:
                    for device in devices:
                        if constants.IMAGE_TYPE_DATA == device.type:
                            storage = dict()
                            storage['role'] = constants.TEMPLATE_DATA
                            storage['path'] = part.path
                            storage['image_id'] = device.uuid
                            storage['version'] = template.version
                            exists = models.YzyInstanceDeviceInfo.objects.filter(image_id=device.uuid,
                                                                                 deleted=False).first()
                            if exists:
                                storage['bind_desktop'] = True
                            else:
                                storage['bind_desktop'] = False
                            task = resource_model.YzyTaskInfo.objects.filter(image_id=device.uuid, host_uuid=obj.uuid,
                                                                             deleted=False). \
                                order_by('-progress').order_by('-id').first()
                            if not task or task.status == 'end':
                                status = 0
                            elif task.status == 'error':
                                status = 2
                            else:
                                status = 1
                            storage['status'] = status
                            result.append(storage)
        return result


class NodeTemplateSerializer(DateTimeFieldMix):

    storages = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyInstanceTemplate
        fields = ('name', 'uuid', 'storages')

    def get_storages(self, obj):
        node_uuid = self.context['request'].GET.get('node_uuid')
        if not node_uuid:
            node_uuid = obj.node.uuid
        result = list()
        parts = resource_model.YzyNodeStorages.objects.filter(node=node_uuid, deleted=False)
        devices = models.YzyInstanceDeviceInfo.objects.filter(instance_uuid=obj.uuid, deleted=False)
        for part in parts:
            if str(constants.TEMPLATE_SYS) in part.role:
                for device in devices:
                    if constants.IMAGE_TYPE_SYSTEM == device.type:
                        storage = dict()
                        storage['role'] = constants.TEMPLATE_SYS
                        storage['path'] = part.path
                        storage['image_id'] = device.uuid
                        storage['version'] = obj.version
                        task = resource_model.YzyTaskInfo.objects.filter(image_id=device.uuid, host_uuid=node_uuid,
                                                                         deleted=False). \
                            order_by('-progress').order_by('-id').first()
                        if not task or task.status == 'end':
                            status = 0
                        elif task.status == 'error':
                            status = 2
                        else:
                            status = 1
                        storage['status'] = status
                        result.append(storage)
                        break
            if str(constants.TEMPLATE_DATA) in part.role:
                for device in devices:
                    if constants.IMAGE_TYPE_DATA == device.type:
                        storage = dict()
                        storage['role'] = constants.TEMPLATE_DATA
                        storage['path'] = part.path
                        storage['image_id'] = device.uuid
                        storage['version'] = obj.version
                        task = resource_model.YzyTaskInfo.objects.filter(image_id=device.uuid, host_uuid=node_uuid,
                                                                         deleted=False). \
                            order_by('-progress').order_by('-id').first()
                        if not task or task.status == 'end':
                            status = 0
                        elif task.status == 'error':
                            status = 2
                        else:
                            status = 1
                        storage['status'] = status
                        result.append(storage)
        return result


class OperationLogSerializer(DateTimeFieldMix):

    class Meta:
        model = models.YzyOperationLog
        fields = "__all__"
