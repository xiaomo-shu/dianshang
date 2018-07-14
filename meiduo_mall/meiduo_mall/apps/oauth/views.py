import logging
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework_jwt.settings import api_settings

from .utils import OAuthQQ
from .exceptions import QQAPIError
from .models import OAuthQQUser
from .serializers import OAuthQQUserSerializer

from cart.utils import merge_cart_cookie_to_redis

# Create your views here.

logger = logging.getLogger('django')


# GET /oauth/qq/user/?code=xxx
class QQAuthUserView(CreateAPIView):
    serializer_class = OAuthQQUserSerializer

    def post(self, request, *args, **kwargs):
        # 先调用父类的post方法
        response = super().post(request, *args, **kwargs)

        # 合并cookie中的购物车记录到redis中
        merge_cart_cookie_to_redis(request, self.user, response)

        return response

    # def post(self, request):
    #     """
    #     绑定QQ用户:
    #     """
    #     # 1. 接收数据并将校验(短信验证是否正确，校验access_token是否有效)
    #     serializer = OAuthQQUserSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #
    #     # 2. 根据`mobile`查询是否存在用户信息
    #     # 2.1 如果用户不存在，先创建一个新的用户，再进行绑定
    #     # 2.2 如果用户存在，直接进行绑定
    #     user = serializer.save()
    #
    #     # 3. 签发JWT token，进行返回
    #     serializer = OAuthQQUserSerializer(user)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        # 1.获取code
        code = request.query_params.get('code')
        if not code:
            return Response({'message': 'code不能为空'})

        oauth = OAuthQQ()
        try:
            # 2.凭借code向QQ服务器获取access_token
            access_token = oauth.get_access_token(code)
            # 3. 凭借access_token向QQ服务器获取绑定用户的openid
            openid = oauth.get_openid(access_token)
        except QQAPIError as e:
            logger.error(e)
            return Response({'message': 'QQ服务异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 4. 根据openid判断qq是否绑定过网站用户
        try:
            qq_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 4.2 如果未绑定，返回openid(加密成token)
            token = OAuthQQ.generate_save_user_token(openid)
            return Response({'access_token': token})
        else:
            # 4.1 如果绑定过，直接签发JWT token
            # 补充生成记录登录状态的token
            user = qq_user.user
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            response = Response({
                'token': token,
                'user_id': user.id,
                'username': user.username
            })

            # 合并cookie中的购物车记录到redis中
            merge_cart_cookie_to_redis(request, user, response)

            return response


# GET /oauth/qq/authorization/?next=xxx
class QQAuthURLView(APIView):
    """
    QQ登录的网址:
    """
    def get(self, request):
        next = request.query_params.get('next', '/')

        # 获取QQ登录地址
        oauth = OAuthQQ(state=next)
        login_url = oauth.get_login_url()

        # 返回QQ登录地址
        return Response({'login_url': login_url})