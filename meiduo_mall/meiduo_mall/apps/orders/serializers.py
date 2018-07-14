from rest_framework import serializers

from goods.models import SKU


class CartSKUSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(label='商品数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    skus = CartSKUSerializer(many=True)
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)