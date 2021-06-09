from rest_framework import serializers
from django_redis import get_redis_connection
# from drf_haystack.serializers import HaystackSerializer
from goods.models import SKU

# from mall.apps.goods.search_indexes import SKUIndex
'''

返回值	类型	是否必须	说明
id	int	是	商品sku 编号
name	str	是	商品名称
price	decimal	是	单价
default_image_url	str	是	默认图片
comments
'''

class SKUSerializer(serializers.ModelSerializer):
    """
        商品数据序列化器
    """

    class Meta:
        model=SKU
        fields=('id','name','price','default_image_url','comments')



class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """
    添加用户浏览历史序列化器
    """

    sku_id=serializers.IntegerField(min_value=1)


    def validate_sku_id(self, value):

        # 判断sku_id所对应的数据是否存在
        try:
            SKU.objects.get(id=value)
        except:
            raise serializers.ValidationError('商品数据不存在')

        return value

    def create(self, validated_data):

        # 获取用户id商品id
        user_id=self.context['request'].user.id
        sku_id=validated_data['sku_id']

        # 建立缓存连接
        conn=get_redis_connection('history')

        # 先要删除重复数
        pl=conn.pipeline()
        pl.lrem('history_%s'%user_id,0,sku_id)

        # 写入新数据
        pl.lpush('history_%s'%user_id,sku_id)

        # 控制数量
        pl.ltrim('history_%s'%user_id,0,4)

        pl.execute()

        return validated_data



# class SKUIndexSerializer(HaystackSerializer):
#     """
#     SKU索引结果数据序列化器
#     """
#     class Meta:
#         index_classes = [SKUIndex]
#         fields = ('text', 'id', 'name', 'price', 'default_image_url', 'comments')