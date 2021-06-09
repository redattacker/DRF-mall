from django.conf import settings
from django.shortcuts import render

# Create your views here.
# /oauth/qq/authorization/?state=xxx
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from itsdangerous import TimedJSONWebSignatureSerializer
from rest_framework.generics import GenericAPIView

from mall.apps.cart.utils import merge_cart_cookie_to_redis
from .utils import OAuthQQ
#  url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
from rest_framework.views import APIView
from oauth.models import OAuthQQUser
from oauth.serializers import OAuthQQUserSerializer


class QQAuthURLView(APIView):
    """
    获取QQ登录的url
    """

    def get(self, request):
        state = request.query_params.get('state')

        # 生成qq对象调用方法
        qq = OAuthQQ(state=state)

        # 获取qq登录url

        url = qq.get_url()

        return Response({'login_url': url})


# /oauth/qq/user/?code=
class QQAuthUserView(GenericAPIView):
    """
    QQ登录的用户
    """
    serializer_class = OAuthQQUserSerializer

    def get(self, request):

        code = request.query_params.get('code', None)
        if not code:
            return Response({'message': '请传递code'})

        qq = OAuthQQ()
        try:
            # 掉用qq辅助类里定义的方法获取access_token和openid
            access_token = qq.get_access_token(code)
            openid = qq.get_openid(access_token)
            print(openid)
        except Exception as e:
            print(e)
            return Response({'message': e}, status=400)

        # 查询openid判断用户绑定过没有

        try:
            qq_user = OAuthQQUser.objects.get(openid=openid)
        except:
            # 捕获到异常说明没绑定过
            ser = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 300)
            data = {
                'openid': openid
            }
            token = ser.dumps(data).decode()
            return Response({'access_token': token})

        else:
            user = qq_user.user

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            response=Response(
                {
                    "token": token,
                    "username": user.username,
                    "user_id": user.id
                }
            )
            response=merge_cart_cookie_to_redis(request,user,response)
            return response

    def post(self, request):

        ser = self.get_serializer(data=request.data)
        ser.is_valid()
        print(ser.errors)

        user = ser.save()

        # 生成JWTToken

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        response=Response(
            {
                'token': token,
                'username': user.username,
                'user_id': user.id
            }
        )

        response = merge_cart_cookie_to_redis(request, user, response)
        return response
