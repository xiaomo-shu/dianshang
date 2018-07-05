import re

from django_redis import get_redis_connection
from rest_framework import serializers

from .models import User


class CreateUserSerializer(serializers.ModelSerializer):
    # (参数是否完整，密码是否一致，手机号格式是否正确，是否同意协议，短信验证码是否正确)
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'mobile', 'password2', 'sms_code', 'allow')
        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate_allow(self, value):
        """是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError('请同意协议')


    def validate_mobile(self, value):
        """手机号格式是否正确"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')

    def validate(self, attrs):
        # 密码是否一致
        password = attrs['password']
        password2 = attrs['password2']

        if password != password2:
            raise serializers.ValidationError('两次密码不一致')

        # 短信验证码是否正确
        sms_code = attrs['sms_code']
        mobile = attrs['mobile']
        redis_con = get_redis_connection('verify_codes')
        real_sms_code = redis_con.get('sms_%s' % mobile)

        if not real_sms_code:
            raise serializers.ValidationError('短信验证码无效')

        if sms_code != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return attrs
