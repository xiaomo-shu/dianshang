import json
import datetime
import pytz
from rest_framework import serializers
from web_manage.common.utils import DateTimeFieldMix, CustomDateTimeField
from . import models


class YzyVoiTerminalSerializer(DateTimeFieldMix):
    """
        {
              "id": 1,
              "name": "yzy-01",
              "terminal_id": 1,
              "mac":"52:54:00:e1:58:14",
              "ip":"172.16.1.54",
              "mask":"255.255.255.0",
              "platform":"ARM",
              "soft_version":"2.2.2.0",
              "disk_residue": 5.03,
              "status": 0,
              "desktop_group_cnt": 2,
              "download_status": 1,
              "download_percent": 23,
        },
    """
    desktop_group_cnt = serializers.SerializerMethodField(read_only=True)
    download_status = serializers.SerializerMethodField(read_only=True)
    download_percent = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyVoiTerminal
        fields = ('id', 'name', 'terminal_id', 'mac', 'ip', 'mask', 'platform',
                  'soft_version', 'disk_residue', 'status', 'desktop_group_cnt', 'download_status', 'download_percent')

    def get_desktop_group_cnt(self, obj):
        count = models.YzyVoiDesktop2.objects.filter(group_uuid=obj.group_uuid, deleted=False).count()
        return count

    def get_download_status(self, obj):
        task = models.YzyVoiTorrentTask.objects.filter(terminal_mac=obj.mac, status=1, deleted=False).first()
        download_status = 0  # 0-no 1-downloading
        if task:
            download_status = 1  # 0-no 1-downloading
        return download_status

    def get_download_percent(self, obj):
        task = models.YzyVoiTorrentTask.objects.filter(terminal_mac=obj.mac, status=1, deleted=False).first()
        download_percent = 0
        if task:
            download_percent = task.process
        return download_percent
