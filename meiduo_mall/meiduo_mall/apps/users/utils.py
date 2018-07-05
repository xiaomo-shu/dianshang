import re


def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义jwt认证成功返回数据
    """
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }

from django.contrib.auth.backends import ModelBackend
from .models import User


def get_user_by_account(account):
    """
    根据手机号或者用户名查询用户信息:
    account: 用户名或者是手机号
    """
    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            # 根据手机号查询用户信息
            user = User.objects.get(mobile=account)
        else:
            # 根据用户名查询用户信息
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        user = None

    return user


class UsernameMobileAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 根据手机号或者用户名查询账户信息
        user = get_user_by_account(username)

        if user is not None and user.check_password(password):
            return user
