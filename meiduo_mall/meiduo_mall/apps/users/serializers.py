import re

from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .models import User


class CreateUserSerializer(serializers.ModelSerializer):
    # (参数是否完整，密码是否一致，手机号格式是否正确，是否同意协议，短信验证码是否正确)
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    token = serializers.CharField(label='登录状态token', read_only=True)  # 增加token字段

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'mobile', 'password2', 'sms_code', 'allow', 'token')
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
        return value

    def validate_mobile(self, value):
        """手机号格式是否正确"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')
        return value

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

    def create(self, validated_data):
        """创建新用户"""
        # 清除无用数据
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        # 调用父类的方法
        user = super().create(validated_data)

        # 加密用户的密码
        password = validated_data['password']
        user.set_password(password)
        user.save()

        # 签发(生成)JWT token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        # 动态给user对象增加一个属性token
        user.token = token

        return user

