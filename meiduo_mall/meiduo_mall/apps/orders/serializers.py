from django.db import transaction
from django_redis import get_redis_connection
from rest_framework import serializers
from datetime import datetime
from decimal import Decimal
from goods.models import SKU
from .models import OrderInfo, OrderGoods


class SaveOrderSerializer(serializers.ModelSerializer):
    """
    下单数据序列化器
    """
    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')

        # 只读字段声明
        read_only_fields = ('order_id',)

        extra_kwargs = {
            # 'order_id': {
            #     'read_only': True
            # },
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        """
        创建并保存订单信息：(乐观锁)
        """
        # 获取收货地址和支付方式
        address = validated_data['address']
        pay_method = validated_data['pay_method']

        # 组织参数
        # 获取登录用户
        user = self.context['request'].user

        # 订单id (格式: 年月日时分秒+用户id)
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id

        # 订单商品总数目和总金额
        total_count = 0
        total_amount = Decimal(0.00)

        # 运费: 10.00
        freight = Decimal(10.00)

        # 从redis中获取用户所要购买的商品的sku_id和对应数量count
        redis_conn = get_redis_connection('cart')
        pipeline = redis_conn.pipeline()
        cart_key = 'cart_%s' % user.id

        # 获取用户购物车中所有商品的sku_id和对应数量count
        # cart_dict = {
        #     '<sku_id>': '<count>', # bytes
        #     ...
        # }
        cart_dict = redis_conn.hgetall(cart_key)

        # 获取用户所有购买的购物车中对应商品的sku_id
        cart_selected_key = 'cart_selected_%s' % user.id
        # set(sku_id) # bytes
        # set(11, 15)
        cart_selected_set = redis_conn.smembers(cart_selected_key)

        if not cart_selected_set:
            raise serializers.ValidationError('订单数据为空')

        with transaction.atomic():
            # with语句中的涉及到数据库操作的语句会放在同一个事务中
            # 设置一个事务的保存点
            sid = transaction.savepoint()

            try:
                # TODO: 向订单基本信息表中添加一条记录
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=total_count,
                    total_amount=total_amount,
                    freight=freight,
                    pay_method=pay_method
                )

                # TODO: 遍历向订单商品信息表中添加记录
                for sku_id in cart_selected_set:
                    # 获取要购买的商品的数量
                    count = cart_dict[sku_id]
                    count = int(count)

                    for i in range(3):
                        try:
                            # select * from tb_sku where id=<sku_id>;
                            sku = SKU.objects.get(id=sku_id)
                        except SKU.DoesNotExist:
                            # 回滚到sid保存点
                            transaction.savepoint_rollback(sid)
                            raise serializers.ValidationError('商品不存在')

                        # 校验商品的库存
                        if count > sku.stock:
                            # 回滚到sid保存点
                            transaction.savepoint_rollback(sid)
                            raise serializers.ValidationError('商品库存不足')

                        # 保存商品的原始库存
                        origin_stock = sku.stock
                        new_stock = origin_stock - count
                        new_sales = sku.sales + count

                        # 模拟订单并发问题
                        # print('user: %d' % user.id)
                        print('user: %s times: %s stock: %s' % (user.id, i, origin_stock))
                        # import time
                        # time.sleep(10)

                        # 减少对应商品的库存，增加销量
                        # update tb_sku set stock=<new_stock>, sales=<new_sales>
                        # where id=<sku_id>;
                        # sku.stock -= count
                        # sku.sales += count
                        # sku.save()

                        # update tb_sku set stock=<new_stock>, sales=<new_sales>
                        # where id=<sku_id> and stock=<origin_stock>;
                        # 更新的行数
                        res = SKU.objects.filter(id=sku_id, stock=origin_stock).\
                            update(stock=new_stock, sales=new_sales)

                        if res == 0:
                            # 尝试了3次，仍然失败，下单失败
                            if i == 2:
                                # 回滚到sid保存点
                                transaction.savepoint_rollback(sid)
                                raise serializers.ValidationError('下单失败2')
                            # 更新失败，应该重新进行尝试
                            continue

                        # 向订单商品信息表中添加一条记录
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            # order_id=order.id,
                            # sku_id=sku.id,
                            count=count,
                            price=sku.price,
                        )

                        # 累加计算订单中商品的总数量和总金额
                        total_count += count
                        total_amount += sku.price * count

                        # 更新成功，跳转循环
                        break

                # 更新订单基本信息表中订单商品的总数量和总金额
                order.total_count = total_count
                order.total_amount = total_amount
                order.save()
            except serializers.ValidationError:
                # 继续向外抛异常
                raise
            except Exception as e:
                # 回滚到sid保存点
                transaction.savepoint_rollback(sid)
                raise serializers.ValidationError('下单失败1')

        # TODO: 清除购物车中对应的记录
        pipeline.hdel(cart_key, *cart_selected_set)
        pipeline.delete(cart_selected_key)
        pipeline.execute()

        return order

    def create_1(self, validated_data):
        """
        创建并保存订单信息：(悲观锁)
        """
        # 获取收货地址和支付方式
        address = validated_data['address']
        pay_method = validated_data['pay_method']

        # 组织参数
        # 获取登录用户
        user = self.context['request'].user

        # 订单id (格式: 年月日时分秒+用户id)
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id

        # 订单商品总数目和总金额
        total_count = 0
        total_amount = Decimal(0.00)

        # 运费: 10.00
        freight = Decimal(10.00)

        # 从redis中获取用户所要购买的商品的sku_id和对应数量count
        redis_conn = get_redis_connection('cart')
        pipeline = redis_conn.pipeline()
        cart_key = 'cart_%s' % user.id

        # 获取用户购物车中所有商品的sku_id和对应数量count
        # cart_dict = {
        #     '<sku_id>': '<count>', # bytes
        #     ...
        # }
        cart_dict = redis_conn.hgetall(cart_key)

        # 获取用户所有购买的购物车中对应商品的sku_id
        cart_selected_key = 'cart_selected_%s' % user.id
        # set(sku_id) # bytes
        # set(11, 15)
        cart_selected_set = redis_conn.smembers(cart_selected_key)

        if not cart_selected_set:
            raise serializers.ValidationError('订单数据为空')

        with transaction.atomic():
            # with语句中的涉及到数据库操作的语句会放在同一个事务中
            # 设置一个事务的保存点
            sid = transaction.savepoint()

            try:
                # TODO: 向订单基本信息表中添加一条记录
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=total_count,
                    total_amount=total_amount,
                    freight=freight,
                    pay_method=pay_method
                )

                # TODO: 遍历向订单商品信息表中添加记录
                for sku_id in cart_selected_set:
                    # 获取要购买的商品的数量
                    count = cart_dict[sku_id]
                    count = int(count)

                    try:
                        # select * from tb_sku where id=<sku_id>;
                        # sku = SKU.objects.get(id=sku_id)

                        # select * from tb_sku where id=<sku_id> for update;
                        print('user: %s try get lock' % user.id)
                        sku = SKU.objects.select_for_update().get(id=sku_id)
                        print('user: %s get locked' % user.id)
                    except SKU.DoesNotExist:
                        # 回滚到sid保存点
                        transaction.savepoint_rollback(sid)
                        raise serializers.ValidationError('商品不存在')

                    # 校验商品的库存
                    if count > sku.stock:
                        # 回滚到sid保存点
                        transaction.savepoint_rollback(sid)
                        raise serializers.ValidationError('商品库存不足')

                    # 模拟订单并发问题
                    # print('user: %d' % user.id)
                    import time
                    time.sleep(10)


                    # 减少对应商品的库存，增加销量
                    sku.stock -= count
                    sku.sales += count
                    sku.save()

                    # 向订单商品信息表中添加一条记录
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=count,
                        price=sku.price,
                    )

                    # 累加计算订单中商品的总数量和总金额
                    total_count += count
                    total_amount += sku.price * count

                # 更新订单基本信息表中订单商品的总数量和总金额
                order.total_count = total_count
                order.total_amount = total_amount
                order.save()
            except serializers.ValidationError:
                # 继续向外抛异常
                raise
            except Exception as e:
                # 回滚到sid保存点
                transaction.savepoint_rollback(sid)
                raise serializers.ValidationError('下单失败1')

        # TODO: 清除购物车中对应的记录
        pipeline.hdel(cart_key, *cart_selected_set)
        pipeline.delete(cart_selected_key)
        pipeline.execute()

        return order


class CartSKUSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(label='商品数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    skus = CartSKUSerializer(many=True)
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)