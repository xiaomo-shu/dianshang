from django.shortcuts import render
from django.contrib.auth.backends import ModelBackend
from rest_framework import status

from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, CreateAPIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response

from .models import User
from .serializers import CreateUserSerializer
# Create your views here.


# POST /users/
# class UserView(CreateModelMixin, GenericAPIView):
class UserView(CreateAPIView):
    serializer_class = CreateUserSerializer

    # def post(self, request):
    #     """
    #     用户注册:
    #     1. 接收参数并进行参数校验(参数是否完整，密码是否一致，是否同意协议，短信验证码是否正确)
    #     2. 创建新用户
    #     3. 返回应答，注册成功
    #     """
    #     # 1. 接收参数并进行参数校验(参数是否完整，密码是否一致，是否同意协议，短信验证码是否正确)
    #     # serializer = CreateUserSerializer(data=request.data)
    #     # serializer = self.get_serializer(data=request.data)
    #     # serializer.is_valid(raise_exception=True)
    #
    #     # 2. 创建新用户
    #     # user = serializer.save()
    #
    #     # 3. 返回应答，注册成功
    #     # serializer = CreateUserSerializer(user)
    #     # serializer = self.get_serializer(user)
    #     # return Response(serializer.data, status=status.HTTP_201_CREATED)
    #
    #     return self.create(request)


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