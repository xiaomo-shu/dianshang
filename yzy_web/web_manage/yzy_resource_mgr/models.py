# from django.db import models

# Create your models here.

from django.db import models
from web_manage.common.utils import SoftDeletableModel


# # Create your models here.
# class User(models.Model):
#
#
#     GENDERS = (
#         (1, '男'), (2, "女")
#     )
#     name = models.CharField(max_length=10, verbose_name='名字')
#     phone = models.CharField(max_length=11, verbose_name='手机号')
#     gender = models.IntegerField(choices=GENDERS, verbose_name='性别')
#     pwd = models.CharField(verbose_name='密码', max_length=64)


# class YzyResourcePools(models.Model):
class YzyResourcePools(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=64)
    desc = models.CharField(max_length=500, blank=True, null=True)
    default = models.IntegerField(default=0)
    # deleted = models.IntegerField(default=0)
    # deleted_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_resource_pools'
        ordering = ['id']


class YzyNodes(SoftDeletableModel):

    TYPES = (
        (1, '计算和主控一体'), (2, '计算和备控一体'), (3, '主控'), (4, '备控'), (5, '计算')
    )

    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    hostname = models.CharField(unique=True, max_length=32)
    ip = models.GenericIPAddressField(protocol="ipv4")
    # resource_pool_uuid = models.UUIDField(null=True)
    resource_pool = models.ForeignKey(to=YzyResourcePools, to_field='uuid', on_delete=models.CASCADE,
                                      related_name='yzy_nodes', db_column='resource_pool_uuid', null=True)
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
    # 0 - 正常， 1 - 异常
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


class YzyBaseImages(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=150)
    path = models.CharField(unique=True, max_length=200)
    md5_sum = models.CharField(max_length=64)
    os_type = models.CharField(max_length=64)
    os_bit = models.CharField(max_length=10)
    vcpu = models.IntegerField(default=2)
    ram = models.FloatField(default=0)
    disk = models.IntegerField()
    resource_pool = models.ForeignKey(to=YzyResourcePools, to_field='uuid', on_delete=models.CASCADE,
                                      related_name='yzy_base_images', db_column='pool_uuid', null=True)

    size = models.FloatField(default=0)
    status = models.IntegerField(default=0)
    # count = models.IntegerField(default=0)
    # publish = models.IntegerField(default=0)
    updated_at = models.DateTimeField(blank=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_base_images'
        ordering = ['id']


class YzyTaskInfo(SoftDeletableModel):
    task_id = models.CharField(max_length=64)
    image_id = models.CharField(max_length=64)
    version = models.IntegerField(default=0)
    host_uuid = models.CharField(max_length=64)
    context = models.TextField()
    progress = models.IntegerField(default=0)
    status = models.CharField(max_length=255)
    step = models.IntegerField(default=0)
    updated_at = models.DateTimeField(blank=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_task_info'
        ordering = ['id']


class YzyVirtualSwitchs(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    desc = models.CharField(max_length=64, null=True)
    type = models.CharField(max_length=10)
    default = models.IntegerField(default=0)
    # deleted = models.IntegerField(default=0)
    # deleted_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_virtual_switch'
        ordering = ['id']


class YzyNetworks(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    switch = models.ForeignKey(to=YzyVirtualSwitchs, to_field='uuid', on_delete=models.CASCADE,
                                      related_name='yzy_vs_networks', db_column='switch_uuid', null=True)
    switch_name = models.CharField(max_length=64)
    vlan_id = models.IntegerField(default=200, null=True)
    switch_type = models.CharField(max_length=10, default='')
    default = models.IntegerField(default=0)
    # deleted = models.IntegerField(default=0)
    # deleted_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_networks'
        ordering = ['id']


class YzyNodeNetworkInfo(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    nic = models.CharField(unique=True, max_length=32)
    mac = models.CharField(unique=True, max_length=32)
    node = models.ForeignKey(to=YzyNodes, to_field='uuid',on_delete=models.CASCADE,
                                      related_name='yzy_node_interfaces', db_column='node_uuid', null=True)
    speed = models.IntegerField(null=True)
    type = models.IntegerField(default=0)
    status = models.IntegerField(default=0)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_node_network_info'
        ordering = ['id']


class YzyNodeStorages(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    node = models.ForeignKey(to=YzyNodes, to_field='uuid',on_delete=models.CASCADE,
                                      related_name='yzy_node_storages', db_column='node_uuid', null=True)
    path = models.CharField(max_length=64)
    role = models.CharField(max_length=64, default='')
    used = models.BigIntegerField()
    free = models.BigIntegerField()
    total = models.BigIntegerField()
    type = models.IntegerField(default=2)

    class Meta:
        # managed = False
        db_table = 'yzy_node_storages'
        ordering = ['id']

class YzyNodeServices(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    node = models.ForeignKey(to=YzyNodes, to_field='uuid',on_delete=models.CASCADE,
                                      related_name='yzy_node_services', db_column='node_uuid', null=True)
    name = models.CharField(max_length=64)
    status = models.CharField(max_length=64, default='not found')

    class Meta:
        # managed = False
        db_table = 'yzy_node_services'
        ordering = ['id']

class YzyInterfaceIp(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=64)
    interface = models.ForeignKey(to=YzyNodeNetworkInfo, to_field='uuid',on_delete=models.CASCADE,
                                      related_name='yzy_interface_ips', db_column='nic_uuid', null=True)
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


class YzyVirtualSwitchUplink(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    virtual_switch = models.ForeignKey(to=YzyVirtualSwitchs, to_field='uuid',on_delete=models.CASCADE,
                                      related_name='yzy_virtual_switch_uplinks', db_column='vs_uuid', null=True)
    network_interface = models.ForeignKey(to=YzyNodeNetworkInfo, to_field='uuid',on_delete=models.CASCADE,
                                      related_name='yzy_network_interface_uplinks', db_column='nic_uuid', null=True)
    node_uuid = models.CharField(max_length=64)
    deleted = models.IntegerField(default=0)
    deleted_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_vswitch_uplink'
        ordering = ['id']


class YzySubnets(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    network = models.ForeignKey(to=YzyNetworks, to_field='uuid', on_delete=models.CASCADE,
                                          related_name='yzy_network_subnets', db_column='network_uuid', null=True)
    netmask = models.CharField(max_length=64)
    gateway = models.CharField(max_length=64)
    cidr = models.CharField(max_length=64, null=True)
    # start_ip = models.GenericIPAddressField(protocol="ipv4")
    start_ip = models.CharField(max_length=64, null=True)
    # end_ip = models.GenericIPAddressField(protocol="ipv4")
    end_ip = models.CharField(max_length=64, null=True)
    enable_dhcp = models.IntegerField(default=0)
    dns1 = models.CharField(max_length=64, null=True)
    dns2 = models.CharField(max_length=64, null=True)
    deleted = models.IntegerField(default=0)
    deleted_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_subnets'
        ordering = ['id']


# class YzyISO(models.Model):
class YzyISO(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=150)
    md5_sum = models.CharField(max_length=64)
    desc = models.CharField(max_length=64, null=True)
    path = models.CharField(max_length=200)
    type = models.IntegerField(default=1)
    os_type = models.CharField(max_length=64, default='other')
    size = models.FloatField(default=0)
    status = models.IntegerField(default=0)
    deleted = models.IntegerField(default=0)
    deleted_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_iso'
        ordering = ['id']


class YzyBondNics(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    mode = models.IntegerField()
    master_uuid = models.CharField(max_length=64)
    # master = models.ForeignKey(to=YzyNodeNetworkInfo, to_field='uuid',on_delete=models.CASCADE,
    #                                   related_name='yzy_node_network_info', db_column='master_uuid', null=True)
    master_name = models.CharField(null=True, max_length=32)
    slave_uuid = models.CharField(max_length=64)
    # slave = models.ForeignKey(to=YzyNodeNetworkInfo, to_field='uuid',on_delete=models.CASCADE,
    #                                   related_name='yzy_node_network_info', db_column='slave_uuid', null=True)
    slave_name = models.CharField(null=True, max_length=32)
    # vs_uplink_uuid = models.CharField(max_length=64, default=None)
    node_uuid = models.CharField(max_length=64)
    # node = models.ForeignKey(to=YzyNodes, to_field='uuid',on_delete=models.CASCADE,
    #                                   related_name='yzy_node_bond_nics', db_column='node_uuid', null=True)
    deleted = models.IntegerField(default=0)
    deleted_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_bond_nics'
        ordering = ['id']