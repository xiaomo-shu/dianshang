# from django.db import models

# Create your models here.

from django.db import models
from web_manage.common.utils import SoftDeletableModel


class YzyDatabaseBack(SoftDeletableModel):
    name = models.CharField(unique=True, max_length=64)
    node_uuid = models.CharField(max_length=64)
    path = models.CharField(max_length=200)
    size = models.FloatField(default=0)
    type = models.IntegerField(default=0)
    status = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'yzy_database_back'
        ordering = ['id']


# CREATE TABLE `yzy_crontab_task` (
#   `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '定时任务id',
#   `uuid` varchar(64) NOT NULL COMMENT 'uuid',
#   `name` varchar(32) NOT NULL COMMENT '定时任务名称',
#   `desc` varchar(200) NOT NULL COMMENT '描述',
#   `type` tinyint(1) NOT NULL COMMENT '类型(0-数据库自动备份，1-桌面定时开机，2-桌面定时关机，3-主机定时关机，4-终端定时关机)',
#   `exec_time` varchar(10) NOT NULL COMMENT '执行时间 xx:xx:00 (时:分)',
#   `cycle` varchar(10) NOT NULL COMMENT '周期，day/week/month',
#   `values` varchar(32) DEFAULT '' COMMENT '记录周 如：1,2,3,4,5',
#   `cron` varchar(20) NOT NULL COMMENT 'cron表达式',
#   `params` text COMMENT '执行参数',
#   `status` tinyint(1) NOT NULL DEFAULT '0' COMMENT '状态 0 -未启用，1-启用',
#   `deleted` bigint(11) NOT NULL DEFAULT '0',
#   `deleted_at` datetime DEFAULT NULL,
#   `created_at` datetime DEFAULT NULL,
#   `updated_at` datetime DEFAULT NULL,
#   PRIMARY KEY (`id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='定时任务表';

class YzyCrontabTask(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(max_length=64)
    desc = models.CharField(max_length=200)
    type = models.IntegerField(default=0)
    status = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_crontab_task'
        ordering = ['id']


class YzyCrontabDetail(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    task_uuid = models.CharField(max_length=64)
    hour = models.IntegerField()
    minute = models.IntegerField()
    cycle = models.CharField(max_length=32)
    values = models.CharField(max_length=32)
    func = models.CharField(max_length=255)
    params = models.TextField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_crontab_detail'
        ordering = ['id']


class YzyWarningLog(SoftDeletableModel):
    WARNING_ITEMS = (
        (1, 'CPU利用率'), (2, '内存利用率'), (3, '磁盘使用空间'), (4, '磁盘IO利用率'), (5, '网络上下行速度'), (6, '云桌面运行时间'), (7, '系统授权过期剩余日期')
    )
    number_id = models.PositiveIntegerField(unique=True, auto_created=True)
    option = models.IntegerField()
    ip = models.CharField(max_length=32)
    content = models.CharField(max_length=64)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'yzy_warning_log'
        ordering = ['number_id', 'id']


class YzyWarnSetup(SoftDeletableModel):
    status = models.IntegerField(default=0)
    option = models.CharField(max_length=1024)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'yzy_warn_setup'
