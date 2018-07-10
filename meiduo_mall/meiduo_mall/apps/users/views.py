from django.shortcuts import render
from django.contrib.auth.backends import ModelBackend
from rest_framework import status
from rest_framework.decorators import action

from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet
from rest_framework.generics import GenericAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView, ListAPIView
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import User
from .serializers import CreateUserSerializer, UserDetailSerializer, EmailSerializer
from .serializers import UserAddressSerializer, AddressTitleSerializer
from . import constants


# Create your views here.
class AddressViewSet(CreateModelMixin, UpdateModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    # GET /addresses/
    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    # POST /addresses/
    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    # delete /addresses/<pk>/
    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # put /addresses/pk/status/
    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    # put /addresses/pk/title/
    # 需要请求体参数 title
    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# GET /emails/verification/?token=xxx
class VerifyEmailView(APIView):
    def get(self, request):
        """
        验证用户的邮箱:
        """
        # 1. 获取token并进行校验(参数是否传递，是否有效)
        token = request.query_params.get('token')

        if not token:
            return Response({'message': '缺少token信息'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.check_verify_email_token(token)

        if user is None:
            return Response({'message': '无效的token'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. 根据`user_id`和`email`获取对应的用户，设置邮箱激活状态
        user.email_active = True
        user.save()

        # 3. 返回结果
        return Response({'message': '邮箱验证已通过'})


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
