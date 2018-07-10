import re

from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer

from .models import User, Address
from . import constants
from goods.models import SKU

# from users.models import User
class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """
    添加用户浏览历史序列化器
    """
    sku_id = serializers.IntegerField(label="商品SKU编号", min_value=1)

    def validate_sku_id(self, value):
        """
        检验sku_id是否存在
        """
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('该商品不存在')
        return value

    def create(self, validated_data):
        # 在redis中保存用户的历史浏览记录
        sku_id = validated_data['sku_id']
        redis_conn = get_redis_connection('histories')

        # 拼接list key
        user_id = self.context['request'].user.id
        history_key = 'history_%s' % user_id

        # 去重
        pipeline = redis_conn.pipeline()
        pipeline.lrem(history_key, 0, sku_id)
        # 左侧加入(保持浏览顺序)
        pipeline.lpush(history_key, sku_id)
        # 截取前几个
        pipeline.ltrim(history_key, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)
        pipeline.execute()

        return validated_data

class UserAddressSerializer(serializers.ModelSerializer):
    """
    用户地址序列化器
    """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def validate_mobile(self, value):
        """
        验证手机号
        """
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def create(self, validated_data):
        """
        保存
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址标题
    """
    class Meta:
        model = Address
        fields = ('title',)


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email')

    def update(self, instance, validated_data):
        email = validated_data['email']
        # 2. 设置用户的邮箱email
        instance.email = email
        instance.save()

        # 3. 给用户的`email`发送验证邮件
        # 生成一个激活链接: http://www.meiduo.site:8080/success_verify_email.html?token=<token>
        verify_url = instance.generate_verify_email_url()

        # 发出发送邮件任务(邮件正文包含激活链接)
        from celery_tasks.email.tasks import send_verify_email
        send_verify_email.delay(email, verify_url)

        return instance


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'email_active')


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

    def validate_username(self, value):
        """用户名不能全为数字"""
        if re.match(r'^\d+$', value):
            return serializers.ValidationError('用户名不能全为数字')
        return value

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
