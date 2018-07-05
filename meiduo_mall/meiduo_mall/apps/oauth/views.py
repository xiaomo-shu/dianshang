import logging
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from .utils import OAuthQQ
from .exceptions import QQAPIError
from .models import OAuthQQUser


# Create your views here.

logger = logging.getLogger('django')


# GET /oauth/qq/user/?code=xxx
class QQAuthUserView(APIView):
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