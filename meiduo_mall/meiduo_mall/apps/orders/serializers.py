from rest_framework import serializers

from goods.models import SKU
from .models import OrderInfo


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
        创建并保存订单信息：
        """
        # TODO: 向订单基本信息表中添加一条记录

        # TODO: 遍历向订单商品信息表中添加记录

        # TODO: 清除购物车中对应的记录


class CartSKUSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(label='商品数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    skus = CartSKUSerializer(many=True)
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)