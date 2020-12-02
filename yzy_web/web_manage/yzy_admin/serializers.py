from rest_framework import serializers
from .models import *
from web_manage.common.utils import create_uuid
import re
import time


class YzyAdminUserSerializer(serializers.ModelSerializer):
    """
    """
    deleted_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    last_login = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    role_name = serializers.CharField(source='role.role', read_only=True)
    password = serializers.CharField(write_only=True, required=True)
    login_time = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyAdminUser
        fields = ("id", "username", "real_name", "email", "last_login", "login_ip", "is_superuser",
                  "is_active", "desc", "role", "role_name", "created_at", "updated_at", "deleted_at", "password",
                  "login_time")

    # def validate(self, attrs):
    #     return attrs

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     if "password" in data :
    #         data.pop("password")
    #     return data

    def get_login_time(self, obj):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())


class YzyRoleSerializer(serializers.ModelSerializer):
    # TODO 问题：
    # 1、返回主机数量
    # 2、返回状态(1、正常，2、同步数据中，3、异常)
    # 3、添加时uuid自己生成
    # 4、返回的时间格式
    # host_count = serializers.SerializerMethodField(read_only=True)
    # status = serializers.SerializerMethodField(read_only=True)
    user_count = serializers.SerializerMethodField(read_only=True)
    is_super = serializers.SerializerMethodField(read_only=True)

    deleted_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = YzyRole
        fields = '__all__'

    def get_user_count(self, instance):
        return instance.users.count()

    def get_is_super(self, instance):
        is_super = 0
        user = YzyAdminUser.objects.filter(deleted=False, role=instance.id).first()
        if user and user.is_superuser:
            is_super = 1
        return is_super


