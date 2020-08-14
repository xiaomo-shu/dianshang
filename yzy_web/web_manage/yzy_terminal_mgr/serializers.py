import json
import datetime
import pytz
from rest_framework import serializers
from .models import *
from web_manage.yzy_edu_desktop_mgr.models import YzyInstances, YzyDesktop
from web_manage.yzy_user_desktop_mgr.models import YzyGroupUser
from web_manage.common.utils import DateTimeFieldMix, CustomDateTimeField
from web_manage.common import constants


class YzyTerminalSerializer(DateTimeFieldMix):
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
              "instance": "PC101",
              "status": 0,
              "connect_time": "2020-04-08 13:51:00",
              "connect_length":"1小时20分钟",
              "resolution": "1920*1680"
        },
    """
    instance = serializers.SerializerMethodField(read_only=True)
    user_name = serializers.SerializerMethodField(read_only=True)
    resolution = serializers.SerializerMethodField(read_only=True)
    connect_time = serializers.SerializerMethodField(read_only=True)
    connect_length = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyTerminal
        fields = ('id', 'name', 'terminal_id', 'mac', 'ip', 'mask', 'platform',
                  'soft_version', 'instance', 'user_name', 'status', 'connect_time', 'connect_length', 'resolution')

    def get_instance(self, instance):
        instance_name = ""
        if instance.status == constants.STATUS_INACTIVE:
            return instance_name

        terminal_mac = instance.mac
        desktops = YzyInstances.objects.filter(terminal_mac=terminal_mac, spice_link=True,
                                                        status=constants.STATUS_ACTIVE).all()
        # desktops = instance.terminal_of_instance.all()
        instances = []
        for desktop in desktops:
            if desktop.spice_link: instances.append(desktop.name)
        if instances:
            return ";".join(instances)
        return instance_name

    def get_resolution(self, instance):
        try:
            setup_info = json.loads(instance.setup_info)
            width = setup_info.get("program", {}).get("current_screen_info", {}).get("width", "")
            height = setup_info.get("program", {}).get("current_screen_info", {}).get("height", "")
            return "%s*%s"% (width, height)
        except Exception as e:
            return ""

    def get_connect_time(self, instance):
        connect_time_str = ""
        if instance.status == constants.TERMINAL_OFFLINE:
            # 关机状态
            return connect_time_str
        # desktops = instance.terminal_of_instance.all()
        terminal_mac = instance.mac
        desktops = YzyInstances.objects.filter(terminal_mac=terminal_mac, spice_link=True,
                                               status=constants.STATUS_ACTIVE).all()
        # datetime.datetime.now()
        connect_time = []
        for desktop in desktops:
            if desktop.link_time: connect_time.append(desktop.link_time.strftime("%Y-%m-%d %H:%M:%S"))
        if connect_time:
            return ";".join(connect_time)
        return connect_time_str

    def get_connect_length(self, instance):
        connect_length_str = ""
        if instance.status == constants.TERMINAL_OFFLINE:
            # 关机状态
            return connect_length_str

        # desktops = instance.terminal_of_instance.all()
        terminal_mac = instance.mac
        desktops = YzyInstances.objects.filter(terminal_mac=terminal_mac, spice_link=True,
                                               status=constants.STATUS_ACTIVE).all()
        connect_lengths = []
        for desktop in desktops:
            if not desktop.link_time:
                continue
            connect_time = desktop.link_time.replace(tzinfo=None)
            delta_days = (datetime.datetime.now() - connect_time).days
            delta_seconds = (datetime.datetime.now() - connect_time).seconds
            hours = delta_seconds // (60 * 60)
            minutes = (delta_seconds - hours * (60 * 60)) // 60
            secondes = (delta_seconds - hours * (60 * 60) - minutes * 60)
            connect_length = ""
            if delta_days:
                hours = int(delta_days * 24) + hours
            if hours:
                connect_length += "%s小时"% hours
            if minutes:
                connect_length += "%s分钟"% minutes
            if secondes:
                connect_length += "%s秒"% secondes
            connect_lengths.append(connect_length)
        if connect_lengths:
            return ";".join(connect_lengths)
        return connect_length_str

    def get_user_name(self, instance):
        user_name = ""
        if instance.status == constants.TERMINAL_OFFLINE:
            return user_name
        terminal_mac = instance.mac
        desktops = YzyInstances.objects.filter(terminal_mac=terminal_mac, spice_link=True).all()
        user = YzyGroupUser.objects.filter(mac=terminal_mac).first()
        if desktops and user:
            user_name = user.user_name
        return user_name


class YzyTerminalUpgradeSerializer(DateTimeFieldMix):
    """
    终端升级包
    """
    count = serializers.SerializerMethodField(read_only=True)
    terminal_count = serializers.SerializerMethodField(read_only=True)
    upload_at = CustomDateTimeField(read_only=True)

    class Meta:
        model = YzyTerminalUpgrade
        fields = '__all__'

    def get_count(self, instance):
        uuid = self.context['request'].GET.get('uuid')
        terminals = YzyTerminal.objects.filter(deleted=False, group_uuid=uuid,
                                               soft_version=instance.version, platform=instance.platform).all()
        return len(terminals)

    def get_terminal_count(self, instance):
        uuid = self.context['request'].GET.get('uuid')
        terminals = YzyTerminal.objects.filter(deleted=False, group_uuid=uuid, platform=instance.platform).all()
        return len(terminals)

