from django.db import models
from web_manage.common.utils import SoftDeletableModel
from web_manage.yzy_resource_mgr import models as resource_model
from web_manage.yzy_voi_terminal_mgr.models import YzyVoiTerminal


class YzyVoiTemplate(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=64)
    os_type = models.CharField(max_length=32)
    desc = models.TextField()
    owner_id = models.CharField(max_length=24)
    node = models.ForeignKey(to=resource_model.YzyNodes, to_field='uuid', on_delete=models.CASCADE,
                             db_column='host_uuid', null=True)
    network = models.ForeignKey(to=resource_model.YzyNetworks, to_field='uuid', on_delete=models.CASCADE,
                                db_column='network_uuid', null=True)
    # host_uuid = models.CharField(max_length=64)
    # subnet = models.ForeignKey(to=resource_model.YzySubnets, to_field='uuid', on_delete=models.CASCADE,
    #                          db_column='subnet_uuid', null=True)
    subnet_uuid = models.CharField(max_length=64)
    bind_ip = models.CharField(max_length=32)
    vcpu = models.IntegerField(default=2)
    ram = models.FloatField(default=0)
    mac = models.CharField(max_length=64)
    port_uuid = models.CharField(max_length=64)
    classify = models.IntegerField(default=1)
    version = models.IntegerField(default=0)
    operate_id = models.IntegerField(default=0)
    status = models.CharField(max_length=128, default=0)
    all_group = models.BooleanField(default=False)
    attach = models.CharField(max_length=128)
    updated_time = models.DateTimeField(blank=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_voi_template'
        ordering = ['id']


class YzyVoiTemplateOperate(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    template = models.ForeignKey(to=YzyVoiTemplate, to_field='uuid', on_delete=models.CASCADE,
                                 db_column='template_uuid', null=True)
    op_type = models.IntegerField()
    remark = models.TextField()
    exist = models.BooleanField()
    version = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_voi_template_operate'
        ordering = ['id']


class YzyVoiGroup(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    group_type = models.IntegerField(default=1)
    desc = models.CharField(max_length=200)
    enabled = models.BooleanField(default=True)
    start_ip = models.GenericIPAddressField(protocol="ipv4", null=True)
    end_ip = models.GenericIPAddressField(protocol="ipv4", null=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_voi_group'
        ordering = ['id']


class YzyVoiTemplateGroups(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    template = models.ForeignKey(to=YzyVoiTemplate, to_field='uuid', on_delete=models.CASCADE,
                                 db_column='template_uuid', null=True)
    # template_uuid = models.CharField(unique=True, max_length=64)
    group = models.ForeignKey(to=YzyVoiGroup, to_field='uuid', on_delete=models.CASCADE,
                              db_column='group_uuid', null=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_voi_template_to_groups'
        ordering = ['id']


class YzyVoiTerminalToDesktops2(SoftDeletableModel):
    id = models.BigAutoField(primary_key=True)
    uuid = models.CharField(max_length=64)
    terminal_uuid = models.CharField(max_length=64)
    group_uuid = models.CharField(max_length=64)
    desktop_group_uuid = models.CharField(max_length=64)
    terminal_mac = models.CharField(max_length=20)
    desktop_is_dhcp = models.IntegerField()
    desktop_ip = models.CharField(max_length=16)
    desktop_mask = models.CharField(max_length=16)
    desktop_gateway = models.CharField(max_length=16)
    desktop_dns1 = models.CharField(max_length=16)
    desktop_dns2 = models.CharField(max_length=16, blank=True, null=True)
    desktop_status = models.IntegerField()
    desktop_is_sent = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'yzy_voi_terminal_to_desktops'
        ordering = ['id']


class YzyVoiDesktop(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    owner_id = models.IntegerField(default=0)
    group = models.ForeignKey(to=YzyVoiGroup, to_field='uuid', on_delete=models.CASCADE,
                              db_column='group_uuid', null=True)
    # group_uuid = models.CharField(max_length=64)
    template = models.ForeignKey(to=YzyVoiTemplate, to_field='uuid', on_delete=models.CASCADE,
                                 db_column='template_uuid', related_name='voi_desktops', null=True)
    # template_uuid = models.CharField(max_length=64)
    os_type = models.CharField(max_length=64)
    sys_restore = models.IntegerField(default=1)
    data_restore = models.IntegerField(default=1)
    prefix = models.CharField(max_length=128, default='PC')
    use_bottom_ip = models.BooleanField(default=True)
    ip_detail = models.TextField()
    # postfix = models.IntegerField(default=1)
    # postfix_start = models.IntegerField(default=1)
    # order_num = models.IntegerField(default=0)
    active = models.BooleanField(default=False)
    default = models.BooleanField(default=False)
    show_info = models.BooleanField(default=False)
    auto_update = models.BooleanField(default=False)
    # data_disk = models.BooleanField(default=False)
    # data_disk_size = models.IntegerField()
    # data_disk_type = models.IntegerField(default=1)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_voi_desktop_group'
        ordering = ['-active', 'id']


class YzyVoiTerminalToDesktops(SoftDeletableModel):
    id = models.BigAutoField(primary_key=True)
    uuid = models.CharField(max_length=64)
    # terminal_uuid = models.CharField(max_length=64)
    group_uuid = models.CharField(max_length=64)
    terminal_mac = models.CharField(max_length=20)
    desktop_is_dhcp = models.IntegerField()
    desktop_ip = models.CharField(max_length=16)
    desktop_mask = models.CharField(max_length=16)
    desktop_gateway = models.CharField(max_length=16)
    desktop_dns1 = models.CharField(max_length=16)
    desktop_dns2 = models.CharField(max_length=16, blank=True, null=True)
    desktop_status = models.IntegerField()
    desktop_is_sent = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    terminal = models.ForeignKey(to=YzyVoiTerminal, to_field='uuid', on_delete=models.CASCADE,
                                 db_column='terminal_uuid', null=True)
    desktop_group = models.ForeignKey(to=YzyVoiDesktop, to_field='uuid', on_delete=models.CASCADE,
                                      db_column='desktop_group_uuid', null=True)

    class Meta:
        managed = False
        db_table = 'yzy_voi_terminal_to_desktops'
        ordering = ['id']


class YzyVoiDeviceInfo(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    type = models.CharField(max_length=32, null=False, default='data')
    device_name = models.CharField(max_length=32, null=False, default='')
    image_id = models.CharField(max_length=64, default="")
    instance_uuid = models.CharField(max_length=64, null=False)
    boot_index = models.IntegerField(null=False, default=-1)
    disk_bus = models.CharField(max_length=32, default='virtio')
    source_type = models.CharField(max_length=32, default='file')
    source_device = models.CharField(max_length=32, default='disk')
    size = models.IntegerField(default=0)
    section = models.IntegerField(default=0)
    used = models.FloatField()
    progress = models.IntegerField(default=0)
    upload_path = models.CharField(max_length=255)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_voi_device_info'
        ordering = ['id']


# class YzyVoiDeviceModify(SoftDeletableModel):
#     uuid = models.CharField(unique=True, max_length=64)
#     template_uuid = models.CharField(max_length=64, null=False)
#     device_name = models.CharField(max_length=32)
#     boot_index = models.IntegerField()
#     origin = models.IntegerField(null=False, default='0')
#     size = models.IntegerField(default=0)
#     used = models.FloatField(default=0)
#     state = models.IntegerField(default=0)
#
#     class Meta:
#         db_table = 'yzy_voi_device_modify'
#         ordering = ['id']

# CREATE TABLE `yzy_voi_terminal_share_disk` (
#   `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '终端共享数据盘',
#   `uuid` varchar(64) NOT NULL COMMENT '共享数据盘uuid',
#   `group_uuid` varchar(64) NOT NULL COMMENT '所属分组uuid',
#   `disk_size` int(11) NOT NULL COMMENT '数据盘大小，单位:G',
#   `restore` tinyint(1) NOT NULL DEFAULT 0 COMMENT '数据盘还原与不还原，0-还原，1-还原',
#   `enable` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否启用，0-未启用，1-启用',
#   `deleted` bigint(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
#   `deleted_at` datetime DEFAULT NULL,
#   `updated_at` datetime DEFAULT NULL,
#   `created_at` datetime DEFAULT NULL,
#   PRIMARY KEY (`id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8

class YzyVoiTerminalShareDisk(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    group_uuid = models.CharField(max_length=64, null=False)
    disk_size = models.IntegerField(default=0)
    restore = models.BooleanField(default=0)
    enable = models.BooleanField(default=0, null=False)
    version = models.IntegerField(default=0)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_voi_terminal_share_disk'
        ordering = ['id']

# CREATE TABLE `yzy_voi_share_to_desktops` (
#   `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '共享盘与桌面组的绑定',
#   `uuid` varchar(64) NOT NULL COMMENT 'uuid',
#   `disk_uuid` varchar(64) NOT NULL COMMENT '共享数据盘uuid',
#   `desktop_uuid` varchar(64) NOT NULL COMMENT '桌面组uuid',
#   `desktop_name` varchar(64) NOT NULL COMMENT '桌面组name',
#   `deleted` bigint(11) NOT NULL COMMENT '删除标志',
#   `deleted_at` datetime DEFAULT NULL,
#   `created_at` datetime DEFAULT NULL,
#   `updated_at` datetime DEFAULT NULL,
#   PRIMARY KEY (`id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8;


class YzyVoiShareToDesktops(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    group_uuid = models.CharField(max_length=64, null=False)
    disk_uuid = models.CharField(max_length=64, null=False)
    desktop_uuid = models.CharField(max_length=64)
    desktop_name = models.CharField(max_length=64)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_voi_share_to_desktops'
        ordering = ['id']

