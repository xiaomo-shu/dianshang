from django.db import models
from web_manage.common.utils import SoftDeletableModel


class YzyVoiTerminal(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
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
    disk_residue = models.FloatField(default=0)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta:
        # managed = False
        db_table = 'yzy_voi_terminal'
        ordering = ['terminal_id']


class YzyVoiTorrentTask(SoftDeletableModel):
    id = models.BigAutoField(primary_key=True)
    uuid = models.CharField(max_length=64)
    torrent_id = models.CharField(max_length=64)
    torrent_name = models.CharField(max_length=64)
    torrent_path = models.CharField(max_length=200)
    torrent_size = models.IntegerField()
    template_uuid = models.CharField(max_length=64)
    disk_uuid = models.CharField(max_length=64)
    disk_name = models.CharField(max_length=64)
    terminal_mac = models.CharField(max_length=32)
    terminal_ip = models.CharField(max_length=32)
    type = models.IntegerField()
    status = models.IntegerField()
    process = models.IntegerField()
    download_rate = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'yzy_voi_torrent_task'


class YzyVoiDesktop2(SoftDeletableModel):
    uuid = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=32)
    owner_id = models.IntegerField(default=0)
    group_uuid = models.CharField(max_length=64)
    template_uuid = models.CharField(max_length=64)
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