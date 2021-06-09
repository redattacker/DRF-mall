import re
from django.conf import settings
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from user.models import User, Address
from django_redis import get_redis_connection
from celery_tasks.email import tasks as tasks_email
from itsdangerous import TimedJSONWebSignatureSerializer
'''
 username, password, password2, sms_code, mobile, allow
'''


class CreateUserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, )
    sms_code = serializers.CharField(write_only=True)
    allow = serializers.CharField(write_only=True)
    token=serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow','token')

        extra_kwargs = {
            'username': {
                'max_length': 20,
                'min_length': 5,
                'error_messages': {
                    'max_length': '名字太长了',
                    'min_length': '名字太短了',
                }

            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }
    # 手机号格式验证
    def validate_mobile(self, value):

        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')

        return value
    # 协议验证
    def validate_allow(self, value):

        if value != 'true':
            raise serializers.ValidationError('请同意协议')

        return value
     # 密码验证
    def validate(self, attrs):

        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('密码不一致')

        # 手机验证码验证
        conn=get_redis_connection('verify_code')
        real_sms_code=conn.get('sms_%s'%attrs['mobile'])

        if not real_sms_code:
            raise serializers.ValidationError('验证码无效')

        if real_sms_code.decode() != attrs['sms_code']:
            raise serializers.ValidationError('验证码输入错误')

        return attrs

    def create(self, validated_data):

        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        user=super().create(validated_data)

        # 密码加密
        user.set_password(validated_data['password'])
        user.save()
        # 生成用户token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token=token
        return user

class UserDetailSerializer(serializers.ModelSerializer):
    """
    用户详细信息序列化器
    """

    class Meta:
        model=User
        fields=('id', 'username', 'mobile', 'email', 'email_active')

class EmailSerializer(serializers.ModelSerializer):
    """
    邮箱序列化器
    """
    class Meta:
        model = User
        fields = ('id', 'email')
        extra_kwargs = {
            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        instance.email = validated_data['email']
        instance.save()

        ser=TimedJSONWebSignatureSerializer(settings.SECRET_KEY,300)
        data={
            'user_id':instance.id,
            'email':validated_data['email']
        }
        token=ser.dumps(data).decode()

        url='http://www.meiduo.site:8080/success_verify_email.html?token='+token

        # 发送邮件
        tasks_email.send_emailc_code.delay(validated_data['email'],url)

        return instance


class UserAddressSerializer(serializers.ModelSerializer):
    """
    用户地址序列化器
    """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def validate_mobile(self, value):
        """
        验证手机号
        """
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value


    def create(self, validated_data):

        validated_data['user']=self.context['request'].user

        return super().create(validated_data)