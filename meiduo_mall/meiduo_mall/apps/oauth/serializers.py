from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from users.models import User
from .utils import OAuthQQ
from .models import OAuthQQUser


class OAuthQQUserSerializer(serializers.ModelSerializer):
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    access_token = serializers.CharField(label='操作凭证', write_only=True)
    token = serializers.CharField(read_only=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')

    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'password', 'sms_code', 'access_token', 'token')
        extra_kwargs = {
            'username': {
                'read_only': True,
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

    def validate(self, attrs):
        # 校验access_token是否有效
        access_token = attrs['access_token']
        openid = OAuthQQ.check_save_user_token(access_token)

        if openid is None:
            raise serializers.ValidationError('openid无效')

        attrs['openid'] = openid

        # 短信验证码是否正确
        mobile = attrs['mobile']
        sms_code = attrs['sms_code']
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % mobile)

        if real_sms_code is None:
            raise serializers.ValidationError('短信验证码无效')

        if real_sms_code.decode() != sms_code:
            raise serializers.ValidationError('短信验证码错误')

        # 根据`mobile`查询是否存在用户
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            user = None
        else:
            # 校验用户的密码是否正确
            password = attrs['password']
            if not user.check_password(password):
                raise serializers.ValidationError('密码错误')

        attrs['user'] = user

        return attrs

    def create(self, validated_data):
        user = validated_data['user']

        if user is None:
            # 2.1 如果用户不存在，先创建一个新的用户
            mobile = validated_data['mobile']
            password = validated_data['password']
            user = User.objects.create_user(username=mobile, mobile=mobile, password=password)

        # 2.2 进行绑定
        openid = validated_data['openid']
        OAuthQQUser.objects.create(user=user, openid=openid)

        # 签发jwt token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        return user



