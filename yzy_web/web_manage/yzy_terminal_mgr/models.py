# from django.db import models

# Create your models here.

from django.db import models
from web_manage.common.utils import SoftDeletableModel

# CREATE TABLE `yzy_terminal` (
#   `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '记录的唯一编号',
#   `terminal_id` int(11) NOT NULL COMMENT '终端序号,不同组可以重复',
#   `mac` char(25) NOT NULL COMMENT '终端MAC地址',
#   `ip` varchar(15) NOT NULL COMMENT '终端IP地址',
#   `mask` varchar(15) NOT NULL COMMENT '子网掩码',
#   `gateway` varchar(15) NOT NULL COMMENT '网关地址',
#   `dns1` varchar(15) NOT NULL,
#   `dns2` varchar(15) DEFAULT NULL,
#   `is_dhcp` char(1) NOT NULL DEFAULT '1' COMMENT 'dhcp: 1-自动 0-静态',
#   `name` varchar(256) NOT NULL COMMENT '终端名称',
#   `platform` varchar(20) NOT NULL COMMENT '终端CPU架构: arm/x86',
#   `soft_version` varchar(50) NOT NULL COMMENT '终端程序版本号: 16.3.8.0',
#   `status` char(1) NOT NULL DEFAULT '0' COMMENT '终端状态: 0-离线 1-在线',
#   `register_time` datetime DEFAULT NULL,
#   `conf_version` varchar(20) NOT NULL COMMENT '终端配置版本号',
#   `setup_info` varchar(1024) DEFAULT NULL COMMENT '终端设置信息:模式、个性化、windows窗口',
#   `group_uuid` char(64) DEFAULT NULL COMMENT '组UUID，默认NULL表示未分组',
#   `reserve1` varchar(512) DEFAULT NULL,
#   `reserve2` varchar(512) DEFAULT NULL,
#   `reserve3` varchar(512) DEFAULT NULL,
#   PRIMARY KEY (`id`) USING BTREE,
#   UNIQUE KEY `mac_index` (`mac`) USING BTREE,
#   KEY `terminal_id_ip_index` (`terminal_id`,`ip`) USING BTREE
# ) ENGINE=InnoDB AUTO_INCREMENT=58 DEFAULT CHARSET=utf8


class YzyTerminal(SoftDeletableModel):
    terminal_id = models.IntegerField()
    mac = models.CharField(unique=True, max_length=25)
    ip = models.CharField(max_length=15)
    mask = models.CharField(max_length=15)
    gateway = models.CharField(max_length=15)
    dns1 = models.CharField(max_length=15)
    dns2 = models.CharField(max_length=15)
    is_dhcp = models.IntegerField(default=0)
    name = models.CharField(max_length=64)
    platform = models.CharField(max_length=20)
    soft_version = models.CharField(max_length=50)
    status = models.IntegerField(default=0)
    register_time = models.DateTimeField(blank=True, auto_now_add=True)
    conf_version = models.CharField(max_length=20)
    setup_info = models.CharField(max_length=1024)
    group_uuid = models.CharField(max_length=64)
    reserve1 = models.CharField(max_length=512)
    reserve2 = models.CharField(max_length=512)
    reserve3 = models.CharField(max_length=512)

    class Meta:
        # managed = False
        db_table = 'yzy_terminal'
        ordering = ['id']


class YzyTerminalUpgrade(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(max_length=32)
    platform = models.CharField(max_length=32)
    os = models.CharField(max_length=32)
    version = models.CharField(max_length=32)
    size = models.FloatField()
    path = models.CharField(max_length=200)
    upload_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_terminal_upgrade'
        ordering = ['id']


# CREATE TABLE `yzy_terminal_instance` (
#   `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '终端跟桌面的关系',
#   `uuid` varchar(64) NOT NULL COMMENT '关系uuid',
#   `mac` varchar(32) NOT NULL COMMENT '终端mac',
#   `instance_uuid` varchar(64) NOT NULL COMMENT '桌面uuid',
#   `instance_name` varchar(64) NOT NULL COMMENT '桌面名称',
#   `deleted` bigint(11) NOT NULL COMMENT '删除标志',
#   `deleted_at` datetime DEFAULT NULL,
#   `created_at` datetime NOT NULL,
#   `updated_at` datetime DEFAULT NULL,
#   PRIMARY KEY (`id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8


class YzyTerminalInstance(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    # mac = models.CharField(max_length=32)
    terminal = models.ForeignKey(to=YzyTerminal, to_field='mac', on_delete=models.CASCADE,
                               related_name='terminal_of_instance', db_column='mac', null=True)
    instance_uuid = models.CharField(max_length=64)
    instance_name = models.CharField(max_length=64)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_terminal_instance'
        ordering = ['id']