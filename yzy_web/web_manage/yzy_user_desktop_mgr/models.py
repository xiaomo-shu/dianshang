from django.db import models
from web_manage.yzy_edu_desktop_mgr import models as education_model
from web_manage.yzy_resource_mgr import models as resource_model
from web_manage.common.utils import SoftDeletableModel


class YzyGroupUser(SoftDeletableModel):
    uuid = models.CharField(max_length=64, unique=True)
    # group_uuid = models.CharField(max_length=64)
    group = models.ForeignKey(to=education_model.YzyGroup, to_field='uuid', on_delete=models.CASCADE,
                              related_name='user_of_group', db_column='group_uuid', null=True)
    user_name = models.CharField(max_length=128, null=False)
    passwd = models.CharField(max_length=128, null=False)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    email = models.CharField(max_length=128)
    enabled = models.BooleanField(default=1)
    online = models.BooleanField(default=0)
    mac = models.CharField(max_length=32, null=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_group_user'
        ordering = ['id']


class YzyPersonalDesktop(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    owner_id = models.IntegerField(default=0)
    # group_uuid = models.CharField(max_length=64)
    pool = models.ForeignKey(to=resource_model.YzyResourcePools, to_field='uuid',
                             on_delete=models.CASCADE, db_column='pool_uuid', null=True)
    # pool_uuid = models.CharField(max_length=64)
    template = models.ForeignKey(to=education_model.YzyInstanceTemplate, to_field='uuid', on_delete=models.CASCADE,
                                 db_column='template_uuid', related_name='personal_desktops', null=True)
    # template_uuid = models.CharField(max_length=64)
    network = models.ForeignKey(to=resource_model.YzyNetworks, to_field='uuid',
                                on_delete=models.CASCADE, db_column='network_uuid', null=True)
    # network_uuid = models.CharField(max_length=64)
    subnet_uuid = models.CharField(max_length=64)
    # 1-系统分配 2-固定分配
    allocate_type = models.IntegerField(default=1)
    allocate_start = models.GenericIPAddressField(protocol="ipv4", null=True)
    vcpu = models.IntegerField(default=2)
    ram = models.FloatField(default=0)
    os_type = models.CharField(max_length=64, default='windows')
    instance_num = models.IntegerField(default=1)
    sys_restore = models.IntegerField(default=1)
    data_restore = models.IntegerField(default=1)
    prefix = models.CharField(max_length=128, default='PC')
    postfix = models.IntegerField(default=1)
    postfix_start = models.IntegerField(default=1)
    # 1-随机桌面 2-静态桌面
    desktop_type = models.IntegerField(default=1)
    group_uuid = models.CharField(max_length=64, null=True)
    order_num = models.IntegerField(default=99)
    maintenance = models.IntegerField(default=1)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_personal_desktop'
        ordering = ['order_num', 'id']


# class YzyStaticDesktop(SoftDeletableModel):
#     uuid = models.CharField(unique=True, max_length=64)
#     desktop = models.ForeignKey(to=YzyPersonalDesktop, to_field='uuid', on_delete=models.CASCADE,
#                                 db_column='desktop_uuid', null=True)
#     # desktop_uuid = models.CharField(max_length=64)
#     instance = models.ForeignKey(to=education_model.YzyInstances, to_field='uuid', on_delete=models.CASCADE,
#                                  db_column='instance_uuid', null=True)
#     # instance_uuid = models.CharField(max_length=64)
#     user = models.ForeignKey(to=YzyGroupUser, to_field='uuid', on_delete=models.CASCADE,
#                              db_column='user_uuid', null=True)
#     # user_uuid = models.CharField(max_length=64)
#     updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
#     created_at = models.DateTimeField(blank=True, auto_now_add=True)
#
#     class Meta:
#         db_table = 'yzy_static_desktop'
#         ordering = ['id']


class YzyRandomDesktop(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    desktop = models.ForeignKey(to=YzyPersonalDesktop, to_field='uuid', on_delete=models.CASCADE,
                                db_column='desktop_uuid', null=True)
    # desktop_uuid = models.CharField(max_length=64)
    group = models.ForeignKey(to=education_model.YzyGroup, to_field='uuid', on_delete=models.CASCADE,
                              db_column='group_uuid', null=True)
    # group_uuid = models.CharField(max_length=64)

    class Meta:
        db_table = 'yzy_random_desktop'
        ordering = ['id']


class YzyUserRandomInstance(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    desktop = models.ForeignKey(to=YzyPersonalDesktop, to_field='uuid', on_delete=models.CASCADE,
                                db_column='desktop_uuid', null=True)
    user_uuid = models.CharField(unique=True, max_length=64)
    instance = models.ForeignKey(to=education_model.YzyInstances, to_field='uuid', on_delete=models.CASCADE,
                              db_column='instance_uuid', null=True)

    class Meta:
        db_table = 'yzy_user_random_instance'
        ordering = ['id']