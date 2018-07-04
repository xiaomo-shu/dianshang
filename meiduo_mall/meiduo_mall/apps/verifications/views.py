import random

import logging
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection

from meiduo_mall.libs.captcha.captcha import captcha

from . import constants
from .serializers import CheckImageCodeSerializer
from .libs.yuntongxun.sms import CCP
# Create your views here.

# 获取日志器
logger = logging.getLogger('django')


# GET /sms_codes/(?P<mobile>1[3-9]\d{9})/?image_code_id=xxx&text=xxx
class SMSCodeView(APIView):
    def get(self, request, mobile):
        """
        发送短信验证码:
        1. 接收参数并进行参数校验(参数合法性校验，图片验证码对比)
        2. 使用云通讯发送短信验证码
        3. 返回应答，发送成功
        """
        # 1. 接收参数并进行参数校验(参数合法性校验，图片验证码对比)
        serializer = CheckImageCodeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 2. 发送短信验证码
        # 2.1 随机生成6位的短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info('短信验证码为: %s' % sms_code)

        # 2.2 在redis中保存短信验证码内容
        redis_con = get_redis_connection('verify_codes')
        redis_con.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)

        # 2.3 使用云通讯发送短信验证码
        # try:
        #     expires = constants.SMS_CODE_REDIS_EXPIRES // 60
        #     res = CCP().send_template_sms(mobile, [sms_code, expires], constants.SMS_CODE_TEMP_ID)
        # except Exception as e:
        #     logger.error(e)
        #     return Response({'message': '发送短信异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        # else:
        #     if res != 0:
        #         # 发送短信失败
        #         logger.error('发送短信失败')
        #         return Response({'message': '发送短信失败'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 3. 返回应答，发送成功
        return Response({'message': '发送短信成功'})


#  GET /image_codes/(?P<image_code_id>[\w-]+)/
class ImageCodeView(APIView):
    def get(self, request, image_code_id):
        """
        产生图片验证码:
        1. 产生验证码图片captcha
        2. 在redis中保存图片验证码文本内容
        3. 返回验证码图片
        """
        # 1. 产生验证码图片captcha
        text, image = captcha.generate_captcha()
        logger.info('图片验证码为: %s' % text)

        # 2. 在redis中保存图片验证码文本内容
        redis_con = get_redis_connection('verify_codes')
        # redis_con.set('key', 'val', 'expires')
        redis_con.setex('img_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 3. 返回验证码图片
        return HttpResponse(image, content_type='image/jpg')
