from django.shortcuts import render
from decimal import Decimal

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated

from django_redis import get_redis_connection

from goods.models import SKU
from .serializers import CartSKUSerializer, OrderSettlementSerializer
from .serializers import SaveOrderSerializer
# Create your views here.


#  POST /orders/
class OrdersView(CreateAPIView):
    serializer_class = SaveOrderSerializer

    permission_classes = [IsAuthenticated]

    # def post(self, request):
    #     """
    #     保存订单信息:
    #     """
    #     # 获取参数并进行参数校验
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #
    #     # 创建并保存订单信息
    #     serializer.save()
    #
    #     # 返回应答
    #     return Response(serializer.data)


#  GET /orders/settlement/
class OrderSettlementView(APIView):
    """
    订单结算：
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 获取登录用户user
        user = request.user

        # 从redis中获取用户所要购买的商品的sku_id和数量count
        redis_conn = get_redis_connection('cart')
        cart_key = 'cart_%s' % user.id

        # 获取用户购物车所要商品的sku_id和数量count
        # cart_dict = {
        #     '<sku_id>': '<count>', # bytes
        #     ....
        # }
        cart_dict = redis_conn.hgetall(cart_key)

        cart = {}
        for sku_id, count in cart_dict.items():
            cart[int(sku_id)] = int(count)

        # 获取用户购物车选中商品的sku_id
        cart_selected_key = 'cart_selected_%s' % user.id
        cart_selected_set = redis_conn.smembers(cart_selected_key)

        # 根据商品的sku_id获取用户所要购买的商品的信息
        skus = SKU.objects.filter(id__in=cart_selected_set)

        for sku in skus:
            # 遍历获取用户所要购买的商品的数量
            sku.count = cart[sku.id]

        # 运费
        freight = Decimal(10.00)

        # serializer = CartSKUSerializer(skus, many=True)
        # return Response({'freight': freight, 'skus': serializer.data})

        serializer = OrderSettlementSerializer({'freight': freight, 'skus': skus})
        return Response(serializer.data)


