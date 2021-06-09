from rest_framework import serializers
from goods.models import SKU

'''
sku_id	int	是	商品sku id
count	int	是	数量
selected	bool	否	是否勾选，默认勾选

'''

class CartSerializer(serializers.Serializer):


    sku_id=serializers.IntegerField(min_value=1)
    count=serializers.IntegerField(min_value=1)
    selected=serializers.BooleanField(default=True)

    def validate(self, attrs):

        try:
            sku=SKU.objects.get(id=attrs['sku_id'])
        except:
            raise serializers.ValidationError('商品不存在')

        if attrs['count'] > sku.stock:
            raise serializers.ValidationError('商品库存不足')

        return attrs

class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField()
    selected = serializers.BooleanField()

    class Meta:
        model=SKU
        fields=('id', 'count', 'name', 'default_image_url', 'price', 'selected')

class CartDeleteSerializer(serializers.Serializer):
    """
    删除购物车数据序列化器
    """
    sku_id = serializers.IntegerField(min_value=1)


    def validate_sku_id(self, value):

        try:
            sku = SKU.objects.get(id=value)
        except:
            raise serializers.ValidationError('商品不存在')

        return value

class CartSelectAllSerializer(serializers.Serializer):
    """
    购物车全选
    """
    selected = serializers.BooleanField(label='全选')