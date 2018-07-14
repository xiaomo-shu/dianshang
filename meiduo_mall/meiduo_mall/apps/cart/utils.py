import pickle
import base64


from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """
    合并cookie中的购物车数据到redis中：
    """
    # 获取cookie中的购物车数据
    cookie_cart = request.COOKIES.get('cart')

    if cookie_cart:
        cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
    else:
        cart_dict = {}

    if not cart_dict:
        # cookie中没有购物车数据，直接返回
        return

    # 将cookei中购物车数据合并的redis中
    # 如果cookie中的数据和redis中的数据存在冲突，以cookie中的数据为准
    redis_conn = get_redis_connection('cart')
    pipeline = redis_conn.pipeline()
    cart_key = 'cart_%s' % user.id

    # cookie中的数据格式如下:
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

    # 处理cookie中的数据为如下格式:
    # cart = {
    #     '<sku_id>': '<count>',
    #     '<sku_id>': '<count>',
    #     ...
    # }
    cart = {}

    # 保存应该向redis中添加勾选的商品的sku_id
    redis_selected_add = []

    # 保存应该从redis中移除勾选的商品的sku_id
    redis_selected_remove = []

    for sku_id, item in cart_dict.items():
        cart[sku_id] = item['count']

        if item['selected']:
            redis_selected_add.append(sku_id)
        else:
            redis_selected_remove.append(sku_id)

    # 设置redis中购物车商品的sku_id和对应的数量count
    pipeline.hmset(cart_key, cart)

    # 设置redis中购物车商品的选中状态
    cart_selected_key = 'cart_selected_%s' % user.id

    if redis_selected_add:
        # 从redis中对应set集合中添加应该被勾选的商品的sku_id
        pipeline.sadd(cart_selected_key, *redis_selected_add)

    if redis_selected_remove:
        # 从redis中对应set集合中移除不被勾选的商品的sku_id
        pipeline.srem(cart_selected_key, *redis_selected_remove)

    pipeline.execute()

    # 清除cookie
    response.delete_cookie('cart')











