from rest_framework import serializers
from django_redis import get_redis_connection

'''
mobile	str	是	手机号
image_code_id	uuid字符串	是	图片验证码编号
text	str	是	用户输入的图片验证码

'''

class ImageCodeCheckSerializer(serializers.Serializer):

    # 指定验证字段
    image_code_id=serializers.UUIDField()
    text=serializers.CharField(max_length=4,min_length=4)

    def validate(self, attrs):

        # 获取缓存中的验证码
        conn=get_redis_connection('verify_code')
        real_text=conn.get('img_%s'%attrs['image_code_id'])
        if not real_text:
            raise serializers.ValidationError('无效验证码')

        # 删除验证码
        conn.delete('img_%s',attrs['image_code_id'])

        # 对比验证码
        if real_text.decode().lower() != attrs['text'].lower():
            raise serializers.ValidationError('验证码错误')


        # 判断短信验证码是否在60s
        mobile=self.context['view'].kwargs['mobile']
        conn=get_redis_connection('verify_code')
        sms_flag=conn.get('sms_flag_%s'%mobile)
        if sms_flag:
            raise serializers.ValidationError('操作过于频繁')

        return attrs

