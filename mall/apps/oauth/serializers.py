import re
from django.conf import settings
from django_redis import get_redis_connection
from rest_framework import serializers
from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from user.models import User
from oauth.models import OAuthQQUser
'''
mobile	str	是	手机号
password	str	是	密码
sms_code	str	是	短信验证码
access_token	str	是	凭据 （包含openid)
'''

class OAuthQQUserSerializer(serializers.Serializer):
    """
    QQ登录创建用户序列化器
    """

    mobile=serializers.CharField(max_length=11,min_length=11)
    password=serializers.CharField(max_length=20,min_length=8)
    sms_code=serializers.CharField(max_length=6,min_length=6)
    access_token=serializers.CharField()

    # 手机号格式验证
    def validate_mobile(self, value):
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')

        return value

    def validate(self, attrs):
        # 获取access_token
        access_token=attrs['access_token']
        # 解析access_token
        ser=TimedJSONWebSignatureSerializer(settings.SECRET_KEY,300)
        try:
            data=ser.loads(access_token)
        except BadData:
            raise serializers.ValidationError('access_token错误')
        # 提取openid
        openid=data.get('openid',None)
        if  not openid:
            raise serializers.ValidationError('openid错误')
        # 在attrs中额外添加一个openid
        attrs['openid']=openid

        # 手机验证码验证
        conn = get_redis_connection('verify_code')
        real_sms_code = conn.get('sms_%s' % attrs['mobile'])

        if not real_sms_code:
            raise serializers.ValidationError('验证码无效')

        if real_sms_code.decode() != attrs['sms_code']:
            raise serializers.ValidationError('验证码输入错误')


        # 判断用户是否存在
        try:
            user=User.objects.get(mobile=attrs['mobile'])
        except:
            #捕获到异常说明用户不存
            pass
        else:
            if user.check_password(attrs['password']):
                attrs['user']=user

        return attrs

    def create(self, validated_data):
        user=validated_data.get('user',None)
        if not user:
            user=User.objects.create(
                username=validated_data['mobile'],
                mobile=validated_data['mobile'],
                password=validated_data['password']
            )
            user.set_password(validated_data['password'])
            user.save()

        # user用户和openid绑定
        qq_user=OAuthQQUser()
        qq_user.user=user
        qq_user.openid=validated_data['openid']
        qq_user.save()

        return user
