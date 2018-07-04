from django_redis import get_redis_connection
from rest_framework import serializers


class CheckImageCodeSerializer(serializers.Serializer):
    """图片验证码序列化器类"""
    image_code_id = serializers.UUIDField(label='图片验证码uuid')
    text = serializers.CharField(label='图片验证码', max_length=4, min_length=4)

    def validate(self, attrs):
        # 获取图片验证码标识和用户输入的图片验证码内容
        image_code_id = attrs['image_code_id']
        text = attrs['text']

        # 判断60s内是否给手机发送过短信
        mobile = self.context['view'].kwargs['mobile']
        redis_con = get_redis_connection('verify_codes')
        send_flag = redis_con.get('send_flag_%s' % mobile)

        if send_flag:
            raise serializers.ValidationError('发送短信过于频繁')

        # 根据`image_code_id`从redis中获取真实的图片验证码文本
        real_image_code = redis_con.get('img_%s' % image_code_id)

        # 删除图片验证码
        try:
            redis_con.delete('img_%s' % image_code_id)
        except Exception:
            pass

        if not real_image_code:
            raise serializers.ValidationError('图片验证码无效')

        # 对比图片验证码
        if text.lower() != real_image_code.decode().lower():
            raise serializers.ValidationError('图片验证码错误')

        return attrs