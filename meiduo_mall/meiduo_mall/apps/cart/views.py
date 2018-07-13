import base64
import pickle

from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# Create your views here.

from .serializers import CartSerializer, CartSKUSerializer
from . import constants

from goods.models import SKU


# POST /cart/
class CartView(APIView):
    # permission_classes = [IsAuthenticated]

    def perform_authentication(self, request):
        pass

    def put(self, request):
        """
        修改用户购物车记录:
        """
        # 接收参数并进行校验
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data['sku_id']
        count = serializer.validated_data['count']
        selected = serializer.validated_data['selected']

        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            user = None

        if user and user.is_authenticated:
            # 如果登录，修改redis中的购物车记录
            redis_conn = get_redis_connection('cart')
            pipeline = redis_conn.pipeline()

            # 修改redis中对应商品的数量
            cart_key = 'cart_%s' % user.id
            pipeline.hset(cart_key, sku_id, count)

            # 修改redis中对应商品的选中状态
            cart_selected_key = 'cart_selected_%s' % user.id

            if selected:
                # 勾选
                pipeline.sadd(cart_selected_key, sku_id)
            else:
                # 未勾选
                pipeline.srem(cart_selected_key, sku_id)

            pipeline.execute()

            return Response(serializer.data)
        else:
            # 如果未登录，修改cookie中的购物车记录
            cookie_cart = request.COOKIES.get('cart')

            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}

            # 修改cookie中对应商品的数量和选中状态
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            cookie_cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

            response = Response(serializer.data)

            # 设置cookie
            response.set_cookie('cart', cookie_cart_data, constants.CART_COOKIE_EXPIRES)

            return response

    def get(self, request):
        """
        获取用户的购物车记录:
        """
        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            user = None

        if user and user.is_authenticated:
            # 如果用户登录，从redis中获取购物车记录
            redis_conn = get_redis_connection('cart')

            # 获取用户的购物车中商品id和对应的数量count
            cart_key = 'cart_%s' % user.id

            # cart_redis_dict = {
            #     '<sku_id>': '<count>', # bytes类型
            #     '<sku_id>': '<count>', # bytes类型
            #     ...
            # }
            cart_redis_dict = redis_conn.hgetall(cart_key)

            # 获取用户的购物车勾选的商品id
            cart_selected_key = 'cart_selected_%s' % user.id

            # cart_selected_set = (sku_id, sku_id, ...)
            cart_selected_set = redis_conn.smembers(cart_selected_key)

            # 处理数据
            # cart_dict = {
            #     '<sku_id>': {
            #         'count': '<count>',
            #         'selected': '<selected>'
            #     },
            #     '<sku_id>': {
            #         'count': '<count>',
            #         'selected': '<selected>'
            #     }
            # }
            cart_dict = {}

            for sku_id, count in cart_redis_dict.items():
                res_dict = {
                    'count': int(count),
                    'selected': sku_id in cart_selected_set
                }

                cart_dict[int(sku_id)] = res_dict
                # cart_dict[int(sku_id)]['count'] = int(count)
                # cart_dict[int(sku_id)]['selected'] = sku_id in cart_selected_set
        else:
            # 如果用户未登录，从cookie中获取购物车记录
            cookie_cart = request.COOKIES.get('cart')

            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}

        # 根据sku_ids获取对应商品的信息，序列化返回
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)

        for sku in skus:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        serializer = CartSKUSerializer(skus, many=True)

        return Response(serializer.data)

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

        if user and user.is_authenticated:
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



