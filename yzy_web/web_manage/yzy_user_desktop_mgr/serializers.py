from rest_framework import serializers
from web_manage.yzy_edu_desktop_mgr import models as education_model
from web_manage.yzy_user_desktop_mgr import models as personal_model
from web_manage.common import constants
from . import models
from web_manage.yzy_admin.models import YzyAdminUser


class DateTimeFieldMix(serializers.ModelSerializer):

    deleted_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    updated_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)


class UserGroupSerializer(DateTimeFieldMix):
    user_num = serializers.SerializerMethodField()
    enable_num = serializers.SerializerMethodField()
    disable_num = serializers.SerializerMethodField()
    name_with_num = serializers.SerializerMethodField()

    class Meta:
        model = education_model.YzyGroup
        fields = ('uuid', 'name', 'desc', 'user_num', 'enable_num', 'disable_num', 'name_with_num')

    def to_representation(self, obj):
        representation = super(UserGroupSerializer, self).to_representation(obj)
        representation['users'] = GroupUserSerializer(obj.user_of_group, many=True).data
        return representation

    def get_user_num(self, obj):
        return obj.user_of_group.count()

    def get_enable_num(self, obj):
        user_num = models.YzyGroupUser.objects.filter(group=obj.uuid, enabled=True, deleted=False).count()
        return user_num

    def get_disable_num(self, obj):
        user_num = models.YzyGroupUser.objects.filter(group=obj.uuid, enabled=False, deleted=False).count()
        return user_num

    def get_name_with_num(self, obj):
        name_with_num = '%s（总：%s，禁用%s个）' % (obj.name , self.get_user_num(obj), self.get_disable_num(obj))
        return name_with_num


class GroupUserSerializer(DateTimeFieldMix):

    class Meta:
        model = models.YzyGroupUser
        # fields = '__all__'
        fields = ('uuid', 'user_name', 'passwd', 'name', 'phone', 'email', 'enabled', 'group')


class PersonalDesktopSerializer(DateTimeFieldMix):
    network_name = serializers.CharField(source='network.name')
    template_name = serializers.CharField(source='template.name')
    template_status = serializers.CharField(source='template.status')
    pool_name = serializers.CharField(source='pool.name')
    # os_type = serializers.SerializerMethodField(read_only=True)
    inactive_count = serializers.SerializerMethodField(read_only=True)
    active_count = serializers.SerializerMethodField(read_only=True)
    user_count = serializers.SerializerMethodField(read_only=True)
    owner = serializers.SerializerMethodField(read_only=True)
    devices = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyPersonalDesktop
        fields = ('uuid', 'name', 'template', 'template_name', 'pool', 'pool_name', 'sys_restore', 'data_restore',
                  'instance_num', 'inactive_count', 'vcpu', 'ram', 'os_type', 'active_count', 'network_name', 'network',
                  'created_at', 'owner', 'order_num', 'maintenance', 'devices', 'prefix', 'postfix', 'desktop_type',
                  'group_uuid', 'template_status', 'user_count')
        # fields = '__all__'

    def get_user_count(self, obj):
        count = 0
        instances = education_model.YzyInstances.objects.filter(desktop_uuid=obj.uuid, deleted=False)
        for instance in instances:
            if instance.spice_link:
                count += 1
        return count

    def get_inactive_count(self, obj):
        count = 0
        instances = education_model.YzyInstances.objects.filter(desktop_uuid=obj.uuid, deleted=False)
        for instance in instances:
            if instance.status != 'active':
                count += 1
        return count

    def get_active_count(self, obj):
        count = 0
        instances = education_model.YzyInstances.objects.filter(desktop_uuid=obj.uuid, deleted=False)
        for instance in instances:
            if instance.status == 'active':
                count += 1
        return count

    def get_owner(self, obj):
        user = YzyAdminUser.objects.get(id=obj.owner_id)
        return user.username

    def get_devices(self, obj):
        disks = list()
        devices = education_model.YzyInstanceDeviceInfo.objects.filter(instance_uuid=obj.template.uuid, deleted=False)
        for device in devices:
            info = {
                'type': device.type,
                'boot_index': device.boot_index,
                'size': device.size
            }
            disks.append(info)
        return disks


class DesktopRandomSerializer(DateTimeFieldMix):
    group_uuid = serializers.CharField(source='group.uuid')
    group_name = serializers.CharField(source='group.name')
    user_num = serializers.SerializerMethodField(read_only=True)
    disable_num = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyRandomDesktop
        fields = ('uuid', 'group_uuid', 'group_name', 'user_num', 'disable_num')

    def get_user_num(self, obj):
        return obj.group.user_of_group.count()

    def get_disable_num(self, obj):
        count = 0
        for user in obj.group.user_of_group.all():
            if not user.enabled:
                count += 1
        return count


class DesktopStaticSerializer(DateTimeFieldMix):
    instance_uuid = serializers.CharField(source='uuid')
    instance_name = serializers.CharField(source='name')
    user_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = education_model.YzyInstances
        fields = ('user_uuid', 'user_name', 'instance_uuid', 'instance_name')

    def get_user_name(self, obj):
        user = personal_model.YzyGroupUser.objects.filter(uuid=obj.user_uuid, deleted=False).first()
        if user:
            return user.user_name
        return ''
