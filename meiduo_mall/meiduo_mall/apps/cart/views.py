import base64
import pickle

from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# Create your views here.

from .serializers import CartSerializer
from . import constants


# POST /cart/
class CartView(APIView):
    # permission_classes = [IsAuthenticated]

    def perform_authentication(self, request):
        pass

    def post(self, request):
        """
        购物车记录的添加
        """
        # 1. 获取参数并进行操作验证
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data['sku_id']
        count = serializer.validated_data['count']
        selected = serializer.validated_data['selected']

        try:
            user = request.user
        except Exception:
            user = None

        if user:
            # 用户已登录
            # 2. 向redis中添加购物车记录
            redis_conn = get_redis_connection('cart')
            pipeline = redis_conn.pipeline()
            cart_key = 'cart_%s' % user.id

            # 用户购车中商品数目进行计算(如果不存在，加一条新数据，如果已经存在，在原来的数目上进行累加)
            pipeline.hincrby(cart_key, sku_id, count)

            # 判断购车记录是否被选中
            if selected:
                cart_selected_key = 'cart_selected_%s' % user.id
                pipeline.sadd(cart_selected_key, sku_id)

            pipeline.execute()

            # 3. 返回应答
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)
        else:
            # 用户未登录
            cookie_cart = request.COOKIES.get('cart')

            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}

            # 判断用户的购物车中是否添加过该商品
            if sku_id in cart_dict:
                # 购物车中商品的数量进行累加
                count += cart_dict[sku_id]['count']

            # 设置用户购物车中商品的记录
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            cookie_cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = Response(serializer.validated_data, status=status.HTTP_201_CREATED)

            # 设置cookie
            response.set_cookie('cart', cookie_cart_data, constants.CART_COOKIE_EXPIRES)

            return response



