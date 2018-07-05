from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from .utils import OAuthQQ
# Create your views here.


# GET /oauth/qq/authorization/?next=xxx
class QQAuthURLView(APIView):
    """
    QQ登录的网址:
    """
    def get(self, request):
        next = request.query_params.get('next', '/')

        # 获取QQ登录地址
        oauth = OAuthQQ()
        login_url = oauth.get_login_url()

        # 返回QQ登录地址
        return Response({'login_url': login_url})