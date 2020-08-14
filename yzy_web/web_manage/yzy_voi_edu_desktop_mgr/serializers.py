import json
import psutil
from rest_framework import serializers
from web_manage.common.utils import CustomDateTimeField, DateTimeFieldMix
from web_manage.common import constants
from web_manage.yzy_admin import models as admin_model
from web_manage.yzy_resource_mgr import models as resource_model
from web_manage.common.config import SERVER_CONF
from . import models


class VoiGroupSerializer(DateTimeFieldMix):
    terminal_count = serializers.SerializerMethodField(read_only=True)
    desktop_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyVoiGroup
        fields = ('uuid', 'name', 'desc', 'start_ip', 'end_ip', 'enabled', 'terminal_count', 'desktop_count')

    def get_terminal_count(self, obj):
        return 0

    def get_desktop_count(self, obj):
        count = models.YzyVoiDesktop.objects.filter(group=obj.uuid, deleted=False).count()
        return count


class VoiDesktopSerializer(DateTimeFieldMix):
    group_name = serializers.CharField(source='group.name')
    template_name = serializers.CharField(source='template.name')
    template_status = serializers.CharField(source='template.status')
    owner = serializers.SerializerMethodField(read_only=True)
    inactive_count = serializers.SerializerMethodField(read_only=True)
    active_count = serializers.SerializerMethodField(read_only=True)
    total_count = serializers.SerializerMethodField(read_only=True)
    ip_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyVoiDesktop
        fields = ('uuid', 'name', 'owner', 'template', 'template_name', 'template_status', 'group', 'group_name',
                  'sys_restore', 'data_restore', 'active', 'os_type', 'created_at', 'inactive_count',
                  'active_count', 'default', 'show_info', 'auto_update', 'prefix', 'use_bottom_ip',
                  'ip_detail', 'total_count')

    def get_owner(self, obj):
        user = admin_model.YzyAdminUser.objects.filter(id=obj.owner_id, deleted=False).first()
        if user:
            return user.username
        return ''

    def get_inactive_count(self, obj):
        count = 0
        desktops = models.YzyVoiTerminalToDesktops2.objects.filter(desktop_group_uuid=obj.uuid, deleted=False)
        for desktop in desktops:
            if not desktop.desktop_status:
                count += 1
        return count

    def get_active_count(self, obj):
        count = 0
        desktops = models.YzyVoiTerminalToDesktops2.objects.filter(desktop_group_uuid=obj.uuid, deleted=False)
        for desktop in desktops:
            if desktop.desktop_status:
                count += 1
        return count

    def get_total_count(self, obj):
        count = 0
        return count

    def get_ip_detail(self, obj):
        if obj.ip_detail:
            return json.loads(obj.ip_detail)
        return {}


class VoiTemplateSerializer(DateTimeFieldMix):
    bind_ip = serializers.SerializerMethodField(read_only=True)
    network_uuid = serializers.CharField(source='network.uuid')
    network_name = serializers.CharField(source='network.name')
    subnet_uuid = serializers.SerializerMethodField(read_only=True)
    subnet_name = serializers.SerializerMethodField(read_only=True)
    subnet_start_ip = serializers.SerializerMethodField(read_only=True)
    subnet_end_ip = serializers.SerializerMethodField(read_only=True)
    owner = serializers.SerializerMethodField(read_only=True)
    devices = serializers.SerializerMethodField(read_only=True)
    updated_time = CustomDateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    groups = serializers.SerializerMethodField(read_only=True)
    desktop_count = serializers.SerializerMethodField(read_only=True)
    terminal_count = serializers.SerializerMethodField(read_only=True)
    cpu_count = serializers.SerializerMethodField(read_only=True)
    total_ram = serializers.SerializerMethodField(read_only=True)
    download_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyVoiTemplate
        fields = ('uuid', 'name', 'bind_ip', 'os_type', 'owner', 'updated_time', 'groups', 'vcpu', 'ram',
                  'desc', 'network_uuid', 'network_name', 'version', 'status', 'attach', 'all_group',
                  'desktop_count', 'terminal_count', 'devices', 'cpu_count', 'total_ram', 'subnet_uuid',
                  'subnet_name', 'subnet_start_ip', 'subnet_end_ip', 'download_url')

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

    def get_owner(self, obj):
        user = admin_model.YzyAdminUser.objects.filter(id=obj.owner_id, deleted=False).first()
        if user:
            return user.username
        return ''

    def get_devices(self, obj):
        disks = list()
        origin_devices = models.YzyVoiDeviceInfo.objects.filter(instance_uuid=obj.uuid, deleted=False)
        for device in origin_devices:
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

    def get_groups(self, obj):
        groups = list()
        binds = models.YzyVoiTemplateGroups.objects.filter(template=obj.uuid, deleted=False)
        for bind in binds:
            groups.append({
                "uuid": bind.group.uuid,
                "name": bind.group.name
            })
        return groups

    def get_desktop_count(self, obj):
        count = models.YzyVoiDesktop.objects.filter(template=obj.uuid, deleted=False).count()
        return count

    def get_terminal_count(self, obj):
        return 0

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
        url = '%s/api/v1/voi/template/download?path=%s' % (endpoint, obj.uuid)
        return url


class VoiTemplateOperateSerializer(DateTimeFieldMix):
    updated_at = CustomDateTimeField(format='%Y-%m-%d %H:%M', read_only=True)
    remark = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyVoiTemplateOperate
        fields = ('uuid', 'template', 'remark', 'updated_at', 'exist', 'version', 'op_type', 'created_at')

    def get_remark(self, obj):
        if not obj.remark:
            if 1 == obj.op_type:
                return "更新模板"
            elif 2 == obj.op_type:
                return "版本回退"
        return obj.remark


class VoiTemplateGroupSerializer(DateTimeFieldMix):
    template_name = serializers.CharField(source='template.name')
    tempalte_status = serializers.CharField(source='template.status')
    group_name = serializers.CharField(source='group.name')
    os_type = serializers.CharField(source='template.os_type')
    owner = serializers.SerializerMethodField(read_only=True)
    data_disk = serializers.SerializerMethodField(read_only=True)
    used = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyVoiTemplateGroups
        fields = ('template', 'template_name', 'tempalte_status', 'group', 'group_name', 'os_type', 'owner',
                  'data_disk', 'used')

    def get_owner(self, obj):
        user = admin_model.YzyAdminUser.objects.filter(id=obj.template.owner_id, deleted=False).first()
        if user:
            return user.username
        return ''

    def get_data_disk(self, obj):
        devices = models.YzyVoiDeviceInfo.objects.filter(instance_uuid=obj.template.uuid, deleted=False)
        for device in devices:
            if constants.IMAGE_TYPE_DATA == device.type:
                return True
        return False

    def get_used(self, obj):
        used = models.YzyVoiDesktop.objects.filter(group=obj.group, template=obj.template.uuid, deleted=False)
        if used:
            return True
        return False


class VoiTerminalToDesktopsSerializer(DateTimeFieldMix):
    terminal_ip = serializers.CharField(source='terminal.ip')
    start_datetime = serializers.CharField(source='terminal.register_time')
    desktop_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyVoiTerminalToDesktops
        fields = ('terminal_mac', 'desktop_status', 'desktop_ip', 'terminal_ip', 'start_datetime', 'desktop_name')

    def get_desktop_name(self, obj):
        desktop_name = "{}-{}".format(obj.desktop_group.prefix, obj.terminal.terminal_id)
        return desktop_name

