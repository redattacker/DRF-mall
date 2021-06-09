from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from django.http import HttpResponse
import random

from mall.libs.captcha.captcha import captcha
from mall.libs.yuntongxun.sms import CCP
from . import constans
from verifications.serializers import ImageCodeCheckSerializer
from celery_tasks.sms import tasks as sms_task

# Create your views here.


'''

参数	类型	是否必须	说明
image_code_id	uuid字符串	是	图片验证码编号
'''


# url('^image_codes/(?P<image_code_id>[\w-]+)/$', views.ImageCodeView.as_view()),
class ImageCodeView(APIView):
    """
    图片验证码
    """

    def get(self, request, image_code_id):
        # 生成图片和验证码
        text, image = captcha.generate_captcha()

        # 保存验证码
        conn = get_redis_connection('verify_code')
        conn.setex('img_%s' % image_code_id, constans.IMAGE_CODE_REDIS_EXPIRES, text)

        # 返回图片验证

        return HttpResponse(image, content_type='images/jpg')


# url('^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),
class SMSCodeView(GenericAPIView):
    """
    短信验证码
    传入参数：
        mobile, image_code_id, text
    """
    serializer_class = ImageCodeCheckSerializer

    def get(self, request, mobile):
        # 验证码验证
        ser = self.get_serializer(data=request.query_params)
        ser.is_valid()
        print(ser.errors)

        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)

        # # 判断短信验证码是否在60s
        # conn=get_redis_connection('verify_code')
        # sms_flag=conn.get('sms_flag_%s'%mobile)
        # if sms_flag:
        #     return Response('操作过于频繁')

        # 保存验证码
        conn = get_redis_connection('verify_code')
        pl = conn.pipeline()  # 使用管道
        pl.setex('sms_%s' % mobile, constans.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('sms_flag_%s' % mobile, constans.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        # 发送短信
        sms_expries = str(constans.SMS_CODE_REDIS_EXPIRES // 60)

        sms_task.send_sms_code.delay(mobile, sms_code, sms_expries)
        return Response({'messages': 'ok'})

