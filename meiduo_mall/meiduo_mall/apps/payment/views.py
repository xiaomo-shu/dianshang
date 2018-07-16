import os
from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from orders.models import OrderInfo

from alipay import AliPay
# Create your views here.


# GET /orders/(?P<order_id>\d+)/payment/
class PaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """
        返回支付宝支付的网址和参数:
        """
        # 获取登录用户user
        user = request.user

        # 校验订单id(order_id)
        try:
            order = OrderInfo.objects.get(
                order_id=order_id,
                user=user,
                status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],
                pay_method=OrderInfo.PAY_METHODS_ENUM['ALIPAY']
            )
        except OrderInfo.DoesNotExist:
            return Response({'message': '无效的订单信息'}, status=status.HTTP_400_BAD_REQUEST)

        # 组织支付宝支付的网址和参数
        # 初始化
        alipay = AliPay(
            appid=settings.ALIPAY_APPID, # 支付宝应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        total_pay = order.total_amount + order.freight # Decimal

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay), # 订单总金额
            subject="美多商城%s" % order_id, # 订单标题
            return_url="http://www.meiduo.site:8080/pay_success.html",
        )

        # 返回支付地址
        pay_url = settings.ALIPAY_URL + '?' + order_string

        return Response({'alipay_url': pay_url})

