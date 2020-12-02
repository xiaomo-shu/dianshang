from django.db import models
from web_manage.common.utils import SoftDeletableModel
from web_manage.yzy_resource_mgr import models as resource_model


class YzyOperationLog(SoftDeletableModel):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField(null=True)
    user_name = models.CharField(max_length=200, null=False)
    user_ip = models.GenericIPAddressField(protocol="ipv4", null=True)
    content = models.TextField()
    result = models.TextField()
    module = models.CharField(max_length=255)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_operation_log'
        ordering = ['-created_at', 'id']


class YzyInstanceTemplate(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    os_type = models.CharField(max_length=32)
    desc = models.CharField(max_length=200)
    owner_id = models.CharField(max_length=24)
    pool = models.ForeignKey(to=resource_model.YzyResourcePools, to_field='uuid', on_delete=models.CASCADE,
                             db_column='pool_uuid', null=True)
    # pool_uuid = models.CharField(max_length=64)
    node = models.ForeignKey(to=resource_model.YzyNodes, to_field='uuid', on_delete=models.CASCADE,
                             db_column='host_uuid', null=True)
    # host_uuid = models.CharField(max_length=64)
    network = models.ForeignKey(to=resource_model.YzyNetworks, to_field='uuid', on_delete=models.CASCADE,
                             db_column='network_uuid', null=True)
    # network_uuid = models.CharField(max_length=64)
    # subnet = models.ForeignKey(to=resource_model.YzySubnets, to_field='uuid', on_delete=models.CASCADE,
    #                          db_column='subnet_uuid', null=True)
    subnet_uuid = models.CharField(max_length=64)
    sys_storage = models.CharField(max_length=64)
    data_storage = models.CharField(max_length=64)
    bind_ip = models.CharField(max_length=32)
    vcpu = models.IntegerField(default=2)
    ram = models.FloatField(default=0)
    mac = models.CharField(max_length=64)
    version = models.IntegerField(default=0)
    classify = models.IntegerField(default=1)
    status = models.CharField(max_length=128, default=0)
    attach = models.CharField(max_length=128)
    updated_time = models.DateTimeField(blank=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_template'
        ordering = ['id']


class YzyGroup(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    group_type = models.IntegerField(default=1)
    desc = models.CharField(max_length=32)
    # host_uuid = models.CharField(max_length=64)
    network = models.ForeignKey(to=resource_model.YzyNetworks, to_field='uuid', on_delete=models.CASCADE,
                             db_column='network_uuid', null=True)
    # network_uuid = models.CharField(max_length=64)
    subnet = models.ForeignKey(to=resource_model.YzySubnets, to_field='uuid', on_delete=models.CASCADE,
                             db_column='subnet_uuid', null=True)
    enabled = models.BooleanField(default=True)
    start_ip = models.GenericIPAddressField(protocol="ipv4", null=True)
    end_ip = models.GenericIPAddressField(protocol="ipv4", null=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_group'
        ordering = ['id']


class YzyDesktop(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    owner_id = models.IntegerField(default=0)
    group = models.ForeignKey(to=YzyGroup, to_field='uuid', on_delete=models.CASCADE,
                             db_column='group_uuid', null=True)
    # group_uuid = models.CharField(max_length=64)
    pool = models.ForeignKey(to=resource_model.YzyResourcePools, to_field='uuid', on_delete=models.CASCADE,
                                 db_column='pool_uuid', null=True)
    # pool_uuid = models.CharField(max_length=64)
    template = models.ForeignKey(to=YzyInstanceTemplate, to_field='uuid', on_delete=models.CASCADE,
                             db_column='template_uuid', related_name='desktops', null=True)
    # template_uuid = models.CharField(max_length=64)
    network = models.ForeignKey(to=resource_model.YzyNetworks, to_field='uuid', on_delete=models.CASCADE,
                             db_column='network_uuid', null=True)
    # network_uuid = models.CharField(max_length=64)
    subnet_uuid = models.CharField(max_length=64)
    vcpu = models.IntegerField(default=2)
    ram = models.FloatField(default=0)
    os_type = models.CharField(max_length=64, default='windows')
    instance_num = models.IntegerField(default=1)
    sys_restore = models.IntegerField(default=1)
    data_restore = models.IntegerField(default=1)
    prefix = models.CharField(max_length=128, default='PC')
    postfix = models.IntegerField(default=1)
    postfix_start = models.IntegerField(default=1)
    order_num = models.IntegerField(default=99)
    active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_desktop'
        ordering = ['-active', 'order_num', 'id']


class YzyInstances(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    host = models.ForeignKey(to=resource_model.YzyNodes, to_field='uuid', on_delete=models.CASCADE,
                             db_column='host_uuid', null=True)
    # host_uuid = models.CharField(max_length=64)
    # desktop = models.ForeignKey(to=YzyDesktop, to_field='uuid', on_delete=models.CASCADE,
    #                          db_column='desktop_uuid', related_name='instances', null=True)
    desktop_uuid = models.CharField(max_length=64)
    sys_storage = models.CharField(max_length=64)
    data_storage = models.CharField(max_length=64)
    classify = models.IntegerField(default=1)
    terminal_id = models.IntegerField(null=True)
    terminal_mac = models.CharField(max_length=32, null=True)
    terminal_ip = models.CharField(max_length=32, null=True)
    ipaddr = models.GenericIPAddressField(protocol="ipv4", null=True)
    mac = models.CharField(max_length=64, default='00:00:00:00:00:00')
    status = models.CharField(max_length=64)
    port_uuid = models.CharField(max_length=32)
    allocated = models.BooleanField(default=0)
    user_uuid = models.CharField(max_length=64)
    spice_token = models.CharField(max_length=64)
    spice_port = models.IntegerField()
    spice_link = models.IntegerField(default=0)
    link_time = models.DateTimeField(blank=True)
    message = models.CharField(max_length=255)
    up_time = models.DateTimeField(blank=True, auto_now_add=True)
    # started_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_instances'
        ordering = ['id']


class YzyInstanceDeviceInfo(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    type = models.CharField(max_length=32, null=False, default='data')
    device_name = models.CharField(max_length=32, null=False, default='')
    image_id = models.CharField(max_length=64, null=False)
    # template = models.ForeignKey(to=YzyInstanceTemplate, to_field='uuid', on_delete=models.CASCADE,
    #                          db_column='instance_uuid', related_name='devices', null=True)
    # instance = models.ForeignKey(to=YzyInstances, to_field='uuid', on_delete=models.CASCADE,
    #                          db_column='instance_uuid', related_name='devices', null=True)
    instance_uuid = models.CharField(max_length=64, null=False)
    boot_index = models.IntegerField(null=False, default=-1)
    disk_bus = models.CharField(max_length=32, default='virtio')
    source_type = models.CharField(max_length=32, default='file')
    source_device = models.CharField(max_length=32, default='disk')
    size = models.IntegerField(default=0)
    used = models.FloatField()
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_device_info'
        ordering = ['id']


class YzyDeviceModify(SoftDeletableModel):
    __tablename__ = 'yzy_device_modify'
    uuid = models.CharField(unique=True, max_length=64)
    template_uuid = models.CharField(max_length=64)
    device_name = models.CharField(max_length=32, null=False, default='')
    boot_index = models.IntegerField(null=False, default=-1)
    origin = models.IntegerField()
    size = models.IntegerField(default=0)
    used = models.FloatField()
    state = models.IntegerField(default=0)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_device_modify'
        ordering = ['id']


class YzyCourse(SoftDeletableModel):
    id = models.IntegerField(primary_key=True)
    uuid = models.CharField(max_length=64, unique=True)
    course_template_uuid = models.CharField(max_length=64)
    desktop_uuid = models.CharField(max_length=64)
    weekday = models.IntegerField()
    course_num = models.IntegerField()
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'yzy_course'


class YzyTerm(SoftDeletableModel):
    id = models.IntegerField(primary_key=True)
    uuid = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=32)
    start = models.CharField(max_length=8)
    end = models.CharField(max_length=8)
    duration = models.IntegerField()
    break_time = models.IntegerField()
    morning = models.CharField(max_length=5)
    evening = models.CharField(max_length=5)
    afternoon = models.CharField(max_length=5)
    morning_count = models.IntegerField()
    afternoon_count = models.IntegerField()
    evening_count = models.IntegerField()
    course_num_map = models.TextField()
    weeks_num_map = models.TextField()
    group_status_map = models.TextField()
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'yzy_term'


class YzyCourseTemplate(SoftDeletableModel):
    id = models.IntegerField(primary_key=True)
    uuid = models.CharField(max_length=64, unique=True)
    desktops = models.TextField()
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'yzy_course_template'


class YzyCourseSchedule(SoftDeletableModel):
    id = models.IntegerField(primary_key=True)
    uuid = models.CharField(max_length=64, unique=True)
    term = models.ForeignKey(to=YzyTerm, to_field='uuid', db_column='term_uuid', null=True, on_delete=models.CASCADE,
                              related_name='yzy_course_schedule')
    group = models.ForeignKey(to=YzyGroup, to_field='uuid', db_column='group_uuid', null=True, on_delete=models.CASCADE,
                              related_name='yzy_course_schedule')
    course_template = models.ForeignKey(to=YzyCourseTemplate, to_field='uuid', db_column='course_template_uuid',
                                        null=True, on_delete=models.CASCADE, related_name='yzy_course_schedule')
    week_num = models.IntegerField()
    status = models.IntegerField()
    course_md5 = models.TextField()
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'yzy_course_schedule'

