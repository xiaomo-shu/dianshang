from django.db import models
from web_manage.common.utils import SoftDeletableModel


class YzyNodes2(SoftDeletableModel):

    TYPES = (
        (1, '计算和主控一体'), (2, '计算和备控一体'), (3, '主控'), (4, '备控'), (5, '计算')
    )

    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    hostname = models.CharField(unique=True, max_length=32)
    ip = models.GenericIPAddressField(protocol="ipv4")
    resource_pool_uuid = models.UUIDField(null=True)
    total_mem = models.FloatField(default=0, null=True)
    running_mem = models.FloatField(default=0, null=True)
    mem_utilization = models.FloatField(default=0, null=True)
    cpu_utilization = models.FloatField(default=0, null=True)
    single_reserve_mem = models.IntegerField(default=0, null=True)
    total_vcpus = models.IntegerField(default=0, null=True)
    running_vcpus = models.IntegerField(default=0, null=True)
    server_version_info = models.CharField(max_length=64, null=True)
    gpu_info = models.CharField(max_length=100, null=True)
    cpu_info = models.TextField(null=True)
    mem_info = models.TextField(null=True)
    sys_img_uuid = models.CharField(max_length=64, null=True)
    data_img_uuid = models.CharField(max_length=64, null=True)
    vm_sys_uuid = models.CharField(max_length=64, null=True)
    vm_data_uuid = models.CharField(max_length=64, null=True)
    # 0 - ??? 1 - ??
    status = models.CharField(max_length=64)
    type = models.IntegerField(default=0)
    # deleted = models.IntegerField(default=0)
    # deleted_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_nodes'
        ordering = ['id']


class YzyNodeNetworkInfo2(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    nic = models.CharField(unique=True, max_length=32)
    mac = models.CharField(unique=True, max_length=32)
    node_uuid = models.CharField(unique=True, max_length=32)
    speed = models.IntegerField(null=True)
    type = models.IntegerField(default=0)
    status = models.IntegerField(default=0)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_node_network_info'
        ordering = ['id']


class YzyInterfaceIp2(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=64)
    nic_uuid = models.CharField(unique=True, max_length=64)
    ip = models.CharField(max_length=32)
    netmask = models.CharField(max_length=32)
    gateway = models.CharField(max_length=32)
    dns1 = models.CharField(max_length=32)
    dns2 = models.CharField(max_length=32, default='')
    is_image = models.IntegerField(default=0)
    is_manage = models.IntegerField(default=0)
    deleted = models.IntegerField(default=0)
    deleted_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_interface_ip'
        ordering = ['id']


class YzyVoiTerminalPerformance(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    terminal_uuid = models.CharField(unique=True, max_length=64)
    terminal_mac = models.CharField(unique=True, max_length=32)
    cpu_ratio = models.FloatField(default=0)
    network_ratio = models.FloatField(default=0)
    memory_ratio = models.FloatField(default=0)
    cpu_temperature = models.FloatField(default=0)
    hard_disk = models.FloatField(default=0)
    cpu = models.TextField()
    memory = models.TextField()
    network = models.TextField()
    hard = models.TextField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "yzy_voi_terminal_performance"
        ordering = ['id']


class YzyVoiTerminalHardWare(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    terminal_uuid = models.CharField(unique=True, max_length=64)
    terminal_mac = models.CharField(unique=True, max_length=32)
    content = models.TextField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "yzy_voi_terminal_hard_ware"
        ordering = ['id']