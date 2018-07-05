from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response

from .models import User
# Create your views here.


# POST /users/
class UserView(APIView):
    def post(self, request):
        """
        用户注册:
        1. 接收参数并进行参数校验(参数是否完整，密码是否一致，是否同意协议，短信验证码是否正确)
        2. 创建新用户
        3. 返回应答，注册成功
        """
        pass


# url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
class UsernameCountView(APIView):
    """
    用户名数量
    """
    def get(self, request, username):
        """
        获取指定用户名数量
        """
        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }

        return Response(data)


# url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
class MobileCountView(APIView):
    """
    手机号数量
    """
    def get(self, request, mobile):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()

        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)