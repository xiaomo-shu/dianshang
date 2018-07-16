import os
from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from orders.models import OrderInfo
from .models import Payment

from alipay import AliPay
# Create your views here.

# PUT /payment/status/?支付宝参数
# charset=utf-8&
# out_trade_no=20180716102810000000002&  # 订单编号
# method=alipay.trade.page.pay.return&
# total_amount=3798.00&
# sign=JDw49xZjSiuDfZ8WWudSiRF3g4MhjTvum%2F7%2Bzov9t9Evi0bkfQgkIYGa4dkUGVy5ONUT6JegWXEzBNHgsNrl1VgwGvtfUgueuP0VFg6L41yCGQPXj51CmJFran%2B1hszzyvTq5GvdUX9T896YGCd7QBBWcdSQxk%2FfGfxK2MPjHsRK%2FCcCY75y9T46t%2FyUx3N8nlYtmKLgPc0%2F5HqxKbVxv%2FNTF0kzS0PIfWPGqV7u5ImawjqFY0emI0ZtqPbNhZFBFv9Af1GJ8vqTDIGcWkrICtwR83oL3EMlm24NfwBliATxIuM9FRkl2bMrt22v6G8TxWvwQ1JDINdIs%2BUvZNezjw%3D%3D&
# trade_no=2018071621001004920200604858 # 支付宝交易号
# &auth_app_id=2016090800464054&
# version=1.0&app_id=2016090800464054&
# sign_type=RSA2&seller_id=2088102174694091&
# timestamp=2018-07-16+10%3A33%3A11


class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        """
        保存支付结果:
        """
        req_dict = request.query_params.dict() # QueryDict->dict
        signature = req_dict.pop('sign')

        # 初始化
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,  # 支付宝应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        # 校验签名
        success = alipay.verify(req_dict, signature)

        if not success:
            return Response({'message': '非法请求'}, status=status.HTTP_403_FORBIDDEN)

        # 修改订单支付状态，保存支付信息
        order_id = req_dict.get('out_trade_no')

        # 校验订单id(order_id)
        try:
            order = OrderInfo.objects.get(
                order_id=order_id,
                user=request.user,
                status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],
                pay_method=OrderInfo.PAY_METHODS_ENUM['ALIPAY']
            )
        except OrderInfo.DoesNotExist:
            return Response({'message': '无效的订单信息'}, status=status.HTTP_400_BAD_REQUEST)

        # 修改订单支付状态
        order.status = OrderInfo.ORDER_STATUS_ENUM['UNSEND'] # 待发货
        order.save()

        # 保存支付信息
        trade_id = req_dict.get('trade_no')
        Payment.objects.create(
            order_id=order_id,
            trade_id=trade_id
        )

        return Response({'trade_id': trade_id})



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

