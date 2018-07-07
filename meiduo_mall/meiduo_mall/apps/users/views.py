from django.shortcuts import render
from django.contrib.auth.backends import ModelBackend
from rest_framework import status

from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import User
from .serializers import CreateUserSerializer, UserDetailSerializer, EmailSerializer
# Create your views here.


# PUT /email/
# class EmailView(UpdateModelMixin, GenericAPIView):
class EmailView(UpdateAPIView):
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]

    # def put(self, request):
    #     """
    #     设置用户邮箱并发送验证邮件:
    #     """
    #     # # user = request.user
    #     # user = self.get_object()
    #     # # 1. 获取email并进行校验
    #     # serializer = self.get_serializer(user, data=request.data)
    #     # serializer.is_valid(raise_exception=True)
    #     #
    #     # # 2. 设置用户的邮箱email
    #     # # 3. 给用户的`email`发送验证邮件
    #     # serializer.save()
    #     #
    #     # # 4. 返回应答
    #     # serializer = self.get_serializer(user)
    #     # return Response(serializer.data)
    #
    #     return self.update(request)

    def get_object(self):
        """返回登录的用户"""
        return self.request.user


# GET /user/
# class UserDetailView(GenericAPIView):
class UserDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer

    # def get(self, request):
    #     """
    #     获取用户的基本信息:
    #     """
    #     # 1. 获取当前登录的用户user
    #     # user = request.user
    #     user = self.get_object()
    #
    #     # 2. 将用户数据进行序列化返回
    #     # serializer = UserDetailSerializer(user)
    #     serializer = self.get_serializer(user)
    #     return Response(serializer.data)

    def get_object(self):
        """返回登录的用户"""
        return self.request.user



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