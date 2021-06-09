from time import timezone
from datetime import datetime
from rest_framework import serializers

from goods.models import SKU
from order.models import OrderInfo, OrderGoods
from django.db import transaction
from decimal import Decimal
from django_redis import get_redis_connection

class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')
    # freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')

# [{skuid:10,freight:10,count:1,name:iphon},{skuid:9,freight:10,count:1,name:iphon}]


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)

# {freight:10,skus:{{skuid1:10,count:1,name:iphon},{skuid2=9,count:2,name:ipad}}

class SaveOrderSerializer(serializers.ModelSerializer):
    """
    下单数据序列化器
    """
    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')
        read_only_fields = ('order_id',)
        extra_kwargs = {
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
        """保存订单"""
        # 获取用户对象
        user=self.context['request'].user

        # 获取地址和支付方式
        address=validated_data['address']
        pay_method=validated_data['pay_method']
        # 生成订单编号
        order_id=datetime.now().strftime('%Y%m%d%H%M%S')+'%09d'%user.id

        with transaction.atomic():

            # 创建保存点
            save_point=transaction.savepoint()

            try:

                # 写入orderinfo表数据
                order=OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal(10),
                    freight=Decimal(10),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if OrderInfo.PAY_METHODS_ENUM["CASH"] else OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                    # status=2 if OrderInfo.PAY_METHODS_ENUM["CASH"] else 1
                )
                # 查询缓存商品数据
                conn=get_redis_connection('cart')

                # 获取商品数量
                redis_cart_count=conn.hgetall('cart_%s'%user.id)

                # 获取商品选中状态
                redis_cart_selected=conn.smembers('cart_selected_%s'%user.id)

                # 转为Python类型

                cart={}
                for sku_id in redis_cart_selected:
                    cart[int(sku_id)]=int(redis_cart_count[sku_id])


                # 查询所有已选中的商品数据
                # 获取商品信息
                # skus=SKU.objects.filter(id__in=cart.keys())
                skuid_list=cart.keys()
                for sku_id in skuid_list:
                    while True:
                        sku=SKU.objects.get(id=sku_id)
                        # 判断库存
                        redis_count=cart[sku.id]

                        if redis_count > sku.stock:
                            raise serializers.ValidationError('商品库存不足')

                        # 更新商品库存和销量
                        # 原始的库存和销量
                        old_stock=sku.stock  # 第一次 10 第二次 8
                        old_sales=sku.sales

                        new_stock=old_stock-redis_count
                        new_sales = old_sales+redis_count

                        # sku.stock=new_stock
                        # sku.sales=new_sales
                        # sku.save()

                        #线程资源被抢占    修改stock 8

                        ret=SKU.objects.filter(id=sku.id,stock=old_stock).update(stock=new_stock,sales=new_sales)
                        if ret==0:
                            continue

                        # 更新spu表中的销量
                        sku.goods.sales+=redis_count
                        sku.goods.save()

                        # 更新oredrifo表中的商品价格和数量
                        order.total_count+=redis_count
                        order.total_amount+=(redis_count*sku.price)

                        # 保存商品订单表
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=redis_count,
                            price=sku.price,
                        )

                        break
                # 循环结束后,所有商品的总额也计算完成,最终需要总价加上运费
                order.total_amount+=order.freight
                order.save()
            except:
                transaction.savepoint_rollback(save_point)

            else:
                transaction.savepoint_commit(save_point)
                # 清空缓存中的商品数据

                pl=conn.pipeline()
                pl.hdel('cart_%s'%user.id,*redis_cart_selected)
                pl.srem('cart_selected_%s' % user.id, *redis_cart_selected)
                pl.execute()

                return order