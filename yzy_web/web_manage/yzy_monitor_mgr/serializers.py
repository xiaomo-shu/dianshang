import time
from web_manage.common.utils import DateTimeFieldMix, CustomDateTimeField
from rest_framework import serializers
from .models import *
from web_manage.yzy_resource_mgr.serializers import YzyNodeStorageSerializer
from web_manage.common import constants
from web_manage.common.http import server_post, monitor_post
from web_manage.yzy_edu_desktop_mgr.models import YzyInstances
from web_manage.yzy_resource_mgr.models import YzyNodes
from web_manage.yzy_edu_desktop_mgr.models import YzyDesktop


class YzyNodesSerializer2(DateTimeFieldMix):

    class Meta:
        model = YzyNodes2
        # fields = '__all__'
        fields = ('name', 'uuid', 'hostname', 'ip', 'status', 'type', 'created_at')


class YzyWarningInfoSerializer(DateTimeFieldMix):

    class Meta:
        model = YzyNodes
        fields = ["name", "uuid", "ip", "total_mem", "running_mem", "cpu_utilization", "mem_utilization", "cpu_info", "mem_info"]

    def to_representation(self, instance):
        # role_map = {'1': 'template_sys', '2': 'template_data', '3': 'instance_sys', '4': 'instance_data'}
        representation = super(YzyWarningInfoSerializer, self).to_representation(instance)
        representation['cpu_info'] = representation['cpu_info'].split(',')
        representation['mem_info'] = representation['mem_info'].split(',')
        storages = YzyNodeStorageSerializer(instance.yzy_node_storages, many=True).data
        storages = [storage for storage in storages if storage['path'] != '/boot/efi']
        representation['storages'] = storages

        sys_used = 0
        sys_free = 0
        sys_total = 0
        data_used = 0
        data_free = 0
        data_total = 0
        usage_mem = 0
        usage_vcpu = 0
        total_vm = 0
        running_vm = 0
        sys_usage = 0
        data_usage = 0
        sys_path = list()
        data_path = list()
        for storage in storages:
            roles = storage['role']
            for role in roles.split(','):
                # if role in role_map:
                #     representation[role_map[role]] = storage
                if role in [str(constants.TEMPLATE_SYS), str(constants.INSTANCE_SYS)]:
                    if storage['path'] not in sys_path:
                        sys_path.append(storage['path'])
                        sys_used += storage['used']
                        sys_free += storage['available']
                        sys_total += storage['total']
                else:
                    if storage['path'] not in data_path:
                        data_path.append(storage['path'])
                        data_used += storage['used']
                        data_free += storage['available']
                        data_total += storage['total']
        if sys_total:
            sys_usage = "%.2f" % ((sys_total - sys_free) / sys_total * 100)
        if data_total:
            data_usage = "%.2f" % ((data_total - data_free) / data_total * 100)

        instances = YzyInstances.objects.filter(deleted=False, host=instance).all()
        power_instance = instances.filter(status=constants.STATUS_ACTIVE).count()
        error_instance = instances.exclude(message='').count()
        representation['instance_total'] = len(instances)
        representation['power_instance'] = power_instance
        representation['error_instance'] = error_instance
        representation['shutdown_instance'] = len(instances) - power_instance
        representation['system_run_time'] = self.get_system_run_time(instance.uuid)
        bytes_send, bytes_recv = self.get_networkio(instance.ip, instance.uuid)
        representation['bytes_send'] = bytes_send
        representation['bytes_recv'] = bytes_recv
        representation['usage_sys'] = sys_usage
        representation['usage_data'] = data_usage
        representation['total_sys'] = sys_total
        representation['used_sys'] = sys_used
        return representation

    def get_system_run_time(self, node_uuid):
        data = {
            "node_uuid": node_uuid
        }
        url = "/api/v1/controller/get_system_time"
        ret = server_post(url, data=data)
        return ret['data']['run_time']

    def get_networkio(self, node_ip, node_uuid):
        url = "/api/v1/monitor/networkio"
        request_data = {
            "handler": "ServiceHandler",
            "command": "get_networkio_info",
        }
        old_ret = monitor_post(node_ip, url, request_data)
        manage_network_name = None
        networks = YzyNodeNetworkInfo2.objects.filter(deleted=False, node_uuid=node_uuid).all()
        for network in networks:
            interface = YzyInterfaceIp2.objects.filter(deleted=False, nic_uuid=network.uuid).first()
            if interface and interface.is_manage:
                manage_network_name = interface.name

        time.sleep(0.8)
        ret = monitor_post(node_ip, url, request_data)
        if manage_network_name and manage_network_name in ret["data"].keys():
            bytes_send = ret["data"][manage_network_name]["bytes_send"] - old_ret["data"][manage_network_name]["bytes_send"]
            bytes_recv = ret["data"][manage_network_name]["bytes_recv"] - old_ret["data"][manage_network_name]["bytes_recv"]
            return bytes_send, bytes_recv


class YzyWarningInfoDesktopSerializer(DateTimeFieldMix):
    up_time = CustomDateTimeField(read_only=True)
    ipaddr = serializers.SerializerMethodField(read_only=True)
    host_name = serializers.CharField(source='host.name')
    system_type = serializers.SerializerMethodField(read_only=True)
    active_time = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyInstances
        fields = ["name", "status", "ipaddr", "message", "up_time", "classify", "active_time", "system_type", "host_name"]

    def get_ipaddr(self, obj):
        if not obj.ipaddr:
            return "DHCP"
        return obj.ipaddr

    def get_active_time(self, obj):
        if obj.status == constants.STATUS_ACTIVE:
            now = int(time.time())
            start_time = obj.up_time.timestamp()
            gap = now - start_time
        else:
            gap = 0
        return gap

    def get_system_type(self, obj):
        desktop = YzyDesktop.objects.filter(deleted=False, uuid=obj.desktop_uuid).first()
        if desktop:
            return desktop.os_type
        return ''


class TerminalMonitorSerializer(DateTimeFieldMix):

    class Meta:
        model = YzyVoiTerminalPerformance
        fields = ["uuid", "terminal_uuid", "cpu_ratio", "network_ratio", "memory_ratio", "cpu_temperature", "hard_disk"]