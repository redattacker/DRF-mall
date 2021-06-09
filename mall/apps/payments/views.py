from alipay import AliPay
from django.conf import settings
from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
import os
# GET /orders/(?P<order_id>\d+)/payment/
from order.models import OrderInfo
from rest_framework.response import Response

from payments.models import Payment


class PaymentView(APIView):
    """
    支付
    """

    def get(self,request,order_id):

        # 订单查询
        try:
            order=OrderInfo.objects.get(order_id=order_id,user=request.user,pay_method=2,status=2)
        except:
            return Response({'message':'订单不存在'},status=404)

        # 构建跳转页面

        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url="http://www.meiduo.site:8080/pay_success.html",
        )

        url='https://openapi.alipaydev.com/gateway.do?'+order_string

        return Response({'alipay_url': url})


#  PUT /payment/status/?支付宝参数
class PaymentStatusView(APIView):
    """
    支付结果
    """

    def put(self,request):

        # 获取查询字符串参数
        print(request.query_params)
        data=request.query_params.dict() # 转化为Python字典形式
        signature = data.pop("sign") # 相当于解密的key

        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        sucess=alipay.verify(data,signature)

        if sucess:

            # 获取传递过去的商品order_id

            order_id=data.get('out_trade_no')

            # 支付编号

            pay_id=data.get('trade_no')

            Payment.objects.create(
                order_id=order_id,
                trade_id=pay_id
            )

            order=OrderInfo.objects.filter(order_id=order_id)
            order.status=1
            order.save()
            return Response({'message':'ok'})

        else:
            return Response({'message':'订单有错误'})