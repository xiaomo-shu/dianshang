import json
from rest_framework import serializers
from .models import *
from web_manage.common.utils import DateTimeFieldMix
from web_manage.yzy_resource_mgr.models import YzyNodes, YzyResourcePools


class YzyDatabaseBackSerializer(DateTimeFieldMix):

    class Meta:
        model = YzyDatabaseBack
        fields = '__all__'


class YzyCrontabTaskSerializer(DateTimeFieldMix):

    details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyCrontabTask
        fields = ("uuid", "name", "desc", "details", "status")

    def get_details(self, obj):
        if 0 == obj.type:
            result = dict()
            detail = YzyCrontabDetail.objects.filter(task_uuid=obj.uuid, deleted=0).first()
            if detail:
                params = json.loads(detail.params)
                if params:
                    result["count"] = params["count"]
                    result["host_uuid"] = params["node_uuid"]
                if detail.hour:
                    result["hour"] = int(detail.hour)
                if detail.minute:
                    result["minute"] = int(detail.minute)
                if detail.cycle:
                    result["cycle"] = detail.cycle
                if detail.values:
                    result['values'] = [int(item) for item in detail.values.split(',')]
        if obj.type in [1, 2, 3]:
            result = list()
            detail = YzyCrontabDetail.objects.filter(task_uuid=obj.uuid, deleted=0)
            for item in detail:
                info = dict()
                info["uuid"] = item.uuid
                if item.params:
                    params = json.loads(item.params)
                    info["cmd"] = params["cmd"]
                    info['data'] = params['data']
                if item.hour is not None:
                    info["hour"] = int(item.hour)
                if item.minute is not None:
                    info["minute"] = int(item.minute)
                if item.cycle:
                    info["cycle"] = item.cycle
                if item.values:
                    info['values'] = [int(value) for value in item.values.split(',')]
                result.append(info)
        if obj.type == 4:
            result = list()
            detail = YzyCrontabDetail.objects.filter(task_uuid=obj.uuid, deleted=0)
            for item in detail:
                info = dict()
                info["uuid"] = item.uuid
                if item.params:
                    params = json.loads(item.params)
                    info["name"] = params["name"]
                    info['data'] = params['data']
                if item.hour is not None:
                    info["hour"] = int(item.hour)
                if item.minute is not None:
                    info["minute"] = int(item.minute)
                if item.cycle:
                    info["cycle"] = item.cycle
                if item.values:
                    info['values'] = [int(value) for value in item.values.split(',')]
                result.append(info)
        return result


class YzyWarningLogSerializer(DateTimeFieldMix):

    class Meta:
        model = YzyWarningLog
        fields = "__all__"


# class YzyStandbyControlSerializer(DateTimeFieldMix):
#     name = serializers.SerializerMethodField(read_only=True)
#
#     class Meta:
#         model = YzyResourcePools
#         fields = ["name"]
#
#     def get_name(self, obj):
#         nodes = YzyNodes.objects.filter(deleted=False, resource_pool=obj.uuid).exclude(type__in=[1, 3]).all()
#         nodes_name = list()
#         pool_name = dict()
#         if nodes:
#             for node in nodes:
#                 nodes_name.append({"name": node.name, "uuid": node.uuid})
#         pool_name["name"] = obj.name
#         pool_name["node_name"] = nodes_name
#         return pool_name


class YzyWarnSetupSerializer(DateTimeFieldMix):

    class Meta:
        model = YzyWarnSetup
        fields = ["status", "option"]


class YzyCrontabDetailSerializer(DateTimeFieldMix):
    status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyCrontabDetail
        fields = ["uuid", "hour", "minute", "cycle", "values", "status", "task_uuid"]

    def get_status(self, obj):
        status = 0
        task = YzyCrontabTask.objects.filter(uuid=obj.task_uuid).first()
        if task:
            status = task.status
        return status


class YzyAuthSerializer(DateTimeFieldMix):

    class Meta:
        model = YzyAuth
        fields = '__all__'


class YzyTaskSerializer(DateTimeFieldMix):
    # create_time = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyTask
        fields = ['name', 'status', 'created_at']

    # def get_create_time(self, obj):
    #     pass
