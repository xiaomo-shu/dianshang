from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from django_redis import get_redis_connection

from meiduo_mall.libs.captcha.captcha import captcha

from . import constants
# Create your views here.


#  GET /image_codes/(?P<image_code_id>[\w-]+)/
class ImageCodeView(APIView):
    def get(self, request, image_code_id):
        """
        产生图片验证码:
        """
        # 1. 产生验证码图片captcha
        text, image = captcha.generate_captcha()

        # 2. 在redis中保存图片验证码文本内容
        redis_con = get_redis_connection('verify_codes')
        # redis_con.set('key', 'val', 'expires')
        redis_con.setex('img_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 3. 返回验证码图片
        return HttpResponse(image, content_type='image/jpg')
