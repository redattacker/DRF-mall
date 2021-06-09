from django.shortcuts import render

# Create your views here.
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from django_redis import get_redis_connection

#GET /orders/settlement/
from rest_framework.response import Response
from rest_framework.views import APIView
from decimal import Decimal
from goods.models import SKU
from order.serializers import OrderSettlementSerializer, SaveOrderSerializer


class OrderSettlementView(APIView):
    """
    订单结算
    """
    permission_classes = [IsAuthenticated]

    def get(self,request):

        # 从缓存中获取商品数据
        conn=get_redis_connection('cart')

        # 获取数量数据
        cart_count=conn.hgetall('cart_%s'%request.user.id)
        # 获取选中状态
        cart_selected=conn.smembers('cart_selected_%s'%request.user.id)

        # 组建数据

        cart={}

        for sku_id in cart_selected:
            cart[int(sku_id)]=int(cart_count[sku_id])


        # 通过id值查询数据对象

        skus=SKU.objects.filter(id__in=cart.keys())
        # 取出count值
        for sku in skus:
            sku.count=cart[sku.id]

        freight= Decimal(10)  # 指定运费

        ser=OrderSettlementSerializer({'freight':freight,'skus':skus})

        return Response(ser.data)


class SaveOrderView(CreateAPIView):
    """
    保存订单
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SaveOrderSerializer

    # def post(self, request, *args, **kwargs):
    #
    #     ser=self.get_serializer(data=request.data)
    #     ser.is_valid()
    #     print(ser.errors)
    #     ser.save()
    #
    #     return super().post(request, *args, **kwargs)

