# from django.db import models

# Create your models here.

from django.db import models
from web_manage.common.utils import SoftDeletableModel, create_md5


# CREATE TABLE `yzy_admin_user` (
#   `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '管理员用户id',
#   `user` varchar(32) NOT NULL COMMENT '账号',
#   `password` varchar(64) NOT NULL COMMENT '密码',
#   `last_login` datetime NOT NULL COMMENT '上次登录时间',
#   `real_name` varchar(64) NOT NULL COMMENT '真实姓名',
#   `role_id` bigint(11) NOT NULL COMMENT '角色id',
#   `email` varchar(100) NOT NULL COMMENT 'email',
#   `is_superuser` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否为超级管理员，0-否，1-是',
#   `is_active` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否激活，0-否，1-是',
#   `deleted` bigint(20) NOT NULL DEFAULT '0' COMMENT '删除标志',
#   `deleted_at` datetime DEFAULT NULL,
#   `updated_at` datetime DEFAULT NULL,
#   `created_at` datetime DEFAULT NULL,
#   PRIMARY KEY (`id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8
#

class YzyRole(SoftDeletableModel):
    role = models.CharField(unique=True, max_length=64)

    menus = models.ManyToManyField('YzyMenuPermission', through='YzyRolePermission')
    enable = models.IntegerField(default=0)
    default = models.IntegerField(default=0)
    desc = models.CharField(blank=True, max_length=200)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_role'
        ordering = ['id']


class YzyAdminUser(SoftDeletableModel):
    username = models.CharField(unique=True, max_length=32)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    login_ip = models.CharField(max_length=20, default='', blank=True)
    real_name = models.CharField(max_length=32, default='', null=True, blank=True)
    role = models.ForeignKey(YzyRole, on_delete=models.CASCADE,
                             db_column='role_id', related_name='users', null=True)
    email = models.CharField(max_length=128, default='', null=True, blank=True)
    is_superuser = models.IntegerField(default=0)
    is_active = models.IntegerField(default=1)
    desc = models.CharField(blank=True, max_length=200)
    # deleted = models.IntegerField(default=0)
    # deleted_at = models.DateTimeField(blank=True, null=True)

    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_admin_user'
        ordering = ['id']

    def validate_password(self, _password):
        # print(create_md5(_password))
        return self.password == create_md5(_password)

    def set_password(self, password):
        self.password = create_md5(password)

# CREATE TABLE `yzy_role` (
#   `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '角色id',
#   `role` varchar(64) NOT NULL COMMENT '角色名称',
#   `deleted` bigint(11) NOT NULL DEFAULT '0' COMMENT '删除标志',
#   `deleted_at` datetime DEFAULT NULL,
#   `updated_at` datetime DEFAULT NULL,
#   `created_at` datetime DEFAULT NULL,
#   PRIMARY KEY (`id`)
# ) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8


class YzyMenuPermission(SoftDeletableModel):
    pid = models.BigIntegerField()
    type = models.IntegerField()
    title = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    component = models.CharField(max_length=255)
    bread_num = models.IntegerField()
    menu_sort = models.IntegerField()
    icon_show = models.CharField(max_length=255)
    icon_click = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    redirect = models.CharField(max_length=255)
    login = models.IntegerField(default=1)
    hidden = models.IntegerField(default=0)
    permission = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'yzy_menu_permission'


class YzyRolePermission(models.Model):
    role = models.ForeignKey(YzyRole, on_delete=models.CASCADE)
    menu = models.ForeignKey(YzyMenuPermission, on_delete=models.CASCADE)

    class Meta:
        db_table = 'yzy_role_permission'
    objects = models.Manager

# class YzyRolePermission(models.Model):
#     role = models.ForeignKey('YzyRole', on_delete=models.CASCADE)
#     menu = models.ForeignKey('YzyMenu', on_delete=models.CASCADE)
#
#     # 创建联合唯一索引
#     class Meta:
#         db_table = 'yzy_role_permission'
#         unique_together = [
#             ('role','menu'),
#

