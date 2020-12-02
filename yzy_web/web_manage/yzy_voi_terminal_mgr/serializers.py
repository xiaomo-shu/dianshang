import json
import datetime
import pytz
from rest_framework import serializers
from web_manage.common.utils import DateTimeFieldMix, CustomDateTimeField, size_to_M
from web_manage.common import constants
from . import models
from web_manage.yzy_voi_edu_desktop_mgr.models import YzyVoiTerminalToDesktops
from ..yzy_terminal_mgr.models import YzyTerminalUpgrade


class YzyVoiSerializer(DateTimeFieldMix):

    class Meta:
        model = YzyTerminalUpgrade
        # fields = '__all__'
        fields = ('id', 'uuid', 'name', 'platform', 'os', 'version', 'path', 'size',
                  'upload_at', 'deleted', 'deleted_at', 'created_at', 'updated_at')


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
    # desktop_group_cnt = serializers.SerializerMethodField(read_only=True)
    # download_status = serializers.SerializerMethodField(read_only=True)
    # download_percent = serializers.SerializerMethodField(read_only=True)
    # disk_residue = serializers.SerializerMethodField(read_only=True)
    # platform = serializers.SerializerMethodField(read_only=True)
    # desktop_group_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.YzyVoiTerminal
        fields = ('id', 'name', 'terminal_id', 'mac', 'ip', 'mask', 'platform',
                  'soft_version', 'disk_residue', 'status')

    def to_representation(self, instance):
        # pass
        representation = super(YzyVoiTerminalSerializer, self).to_representation(instance)
        count = YzyVoiTerminalToDesktops.objects.filter(
            group_uuid=instance.group_uuid, terminal_mac=instance.mac, desktop_is_sent=1, deleted=False).count()
        representation['desktop_group_cnt'] = count
        representation['download_status'] = self._get_download_status(instance)
        representation['disk_residue'] = self._get_disk_residue(instance)
        representation['platform'] = ""
        tasks = models.YzyVoiTorrentTask.objects.filter(terminal_mac=instance.mac, status__in = [0,1,2],
                                                       deleted=False).all()
        representation['download_percent'] = self._get_download_percent(tasks)
        representation['desktop_group_name'] = self._get_desktop_group_name(tasks)
        representation.update(self._get_transfer_rate(tasks))
        return representation

    # def get_desktop_group_cnt(self, obj):
    #     count = YzyVoiTerminalToDesktops.objects.filter(
    #         group_uuid=obj.group_uuid, terminal_mac=obj.mac, desktop_is_sent=1, deleted=False).count()
    #     return count

    def _get_transfer_rate(self, tasks):
        download_rate = 0
        upload_rate = 0
        for task in tasks:
            if task.status == 1:
                # if task.type == constants.BT_UPLOAD_TASK:
                upload_rate = size_to_M(int(task.upload_rate))
                download_rate = size_to_M(int(task.download_rate))
                break
        return {"download_rate": download_rate, "upload_rate": upload_rate}



    def _get_download_status(self, obj):
        task = models.YzyVoiTorrentTask.objects.filter(terminal_mac=obj.mac, status=1,
                                                       deleted=False).order_by("-id").first()
        download_status = 0  # 0-no 1-downloading
        if task:
            if task.state == "checking":
                download_status = 2  # 0-no 1-downloading, 2- checking
            elif task.state == "finished":
                download_status = 0
            else:
                download_status = 1
        return download_status

    def _get_download_percent(self, tasks):
        complete = 0
        total = 0
        for task in tasks:
            total += task.disk_size
            complete += task.disk_size * task.process
            # torrent_name = task.torrent_name
        download_percent = 0
        if total:
            download_percent = round(complete / total, 2)
        return download_percent

    def _get_disk_residue(self, obj):
        section_num = obj.disk_residue
        return round(section_num / 2 / 1024 / 1024, 2)

    # def get_platform(self, obj):
    #     return ""

    def _get_desktop_group_name(self, tasks):
        # tasks = models.YzyVoiTorrentTask.objects.filter(terminal_mac=obj.mac, status__in=[0, 1, 2],
        #                                                 deleted=False).all()
        desktop_group_name = ""
        for task in tasks:
            if task.status == 1:
                desktop_group_name = task.desktop_name
        return desktop_group_name

