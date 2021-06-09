from django.conf import settings
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# Create your views here.
from itsdangerous import TimedJSONWebSignatureSerializer as Decipher
#有时候你想向不可信的环境发送一些数据，但如何安全完成这个任务呢？解决的方法就是签名。使用只有你自己知道的密钥，来加密签名你的数据，并把加密后的数据发给别人。当你取回数据时，你就可以确保没人篡改过这份数据。
from rest_framework_jwt.views import ObtainJSONWebToken

from cart.utils import merge_cart_cookie_to_redis
from user.models import User, Address
from user.serializers import CreateUserSerializer, UserDetailSerializer, EmailSerializer, UserAddressSerializer


# url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),



class UsernameCountView(APIView):
    print("wkjsdaja")
    def get(self, request, username):
        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }
        #
        return Response(data)

class RedisStringView(APIView):
    def get(self, request):
        conn = get_redis_connection('verify_code')

        #字符串get,set
        conn.set("tel",188)
        conn.incr("tel")
        data=conn.get("tel")

        # conn.setnx("lizhenhua",35):设置值，只有name不存在时，执行设置操作（添加）
        # mset(k1='v1', k2='v2')=mget({'k1': 'v1', 'k2': 'v2'}):批量设置值
        # mget('ylr', 'wupeiqi') =r.mget(['ylr', 'wupeiqi'])：批量获取值
        # getset(name, value)：设置新值并获取原来的值
        # strlen(name)：返回name对应值的字节长度（一个汉字3个字节）
        # incr(name, amount=1)：# 自增 name对应的值(数字)，当name不存在时，则创建name＝amount，否则，则自增。
        # append(key, value)：# 在redis name对应的值后面追加内容
        # conn.hset('kkk', 'age', 18)
        # data = conn.hget('kkk', 'age')
        return Response(data)

class RedisListView(APIView):
    def get(self, request):
        conn = get_redis_connection('verify_code')
        # lpush(name, values):在name对应的list中添加元素，每个新的元素都添加到列表的最左边
        # rpush(name, values):表示从右向左操作
        # lpushx(name, value):在name对应的list中添加元素，只有name已经存在时，值添加到列表的最左边
        # llen(name):name对应的list元素的个数
        # linsert(name, where, refvalue, value)):在name对应的列表的某一个值前或后插入一个新值
        # lset(name, index, value):对name对应的list中的某一个索引位置重新赋值
        # lrem(name, value, num):# 在name对应的list中删除指定的值
        # lpop(name):在name对应的列表的左侧获取第一个元素并在列表中移除，返回值则是第一个元素
        # lindex(name, index):在name对应的列表中根据索引获取列表元素
        # lrange(name, start, end):# 在name对应的列表分片获取数据
        # ltrim(name, start, end):# 在name对应的列表中移除没有在start-end索引之间的值
        return Response(conn)

class RedisSetView(APIView):
    def get(self, request):
        conn = get_redis_connection('verify_code')
       # #Set操作，Set集合就是不允许重复的列表
       #  #sadd(name, values): name对应的集合中添加元素
       #  #scard(name):获取name对应的集合中元素个数
       #  smove(src, dst, value):# 将某个成员从一个集合中移动到另外一个集合
       #  spop(name):# 从集合的右侧（尾部）移除一个成员，并将其返回
       #  srandmember(name, numbers): 从name对应的集合中随机获取 numbers 个元素
       #  srem(name, values): 在name对应的集合中删除某些值
       #  sunion(keys, *args):# 获取多一个name对应的集合的并集
       #  sunionstore(dest, keys, *args):# 获取多一个name对应的集合的并集，并将结果保存到dest对应的集合中
        return Response(conn)



class RedisZAllView(APIView):
    def get(self, request):
        conn = get_redis_connection('verify_code')
        # expire(name ,time)：为某个redis的某个name设置超时时间
        exists(name):# 检测redis的name是否存在
        delete(*names):根据删除redis中的任意数据类型
        rename(src, dst):对redis的name重命名为
        move(name, db))
        type(name)
        scan(cursor=0, match=None, count=None)
        scan_iter(match=None, count=None)
        同字符串操作，用于增量迭代获取key
        return Response(conn)

class RedisZsetView(APIView):
    def get(self, request):
        conn = get_redis_connection('verify_code')

        # 有顺序，不能重复,适合做排行榜 排序需要一个分数属性
        # zadd(name, *args, **kwargs):# 在name对应的有序集合中添加元素
        # zcard(name)获取name对应的有序集合元素的数量
        # zcount(name, min, max)
        # zincrby(name, value, amount)
        # zrank(name, value)
        # zrangebylex(name, min, max, start=None, num=None)
        # zrem(name, values)
        # zremrangebyrank(name, min, max): 根据排行范围删除
        # zremrangebyscore(name, min, max):# 根据分数范围删除
        # zremrangebylex(name, min, max):# 根据值返回删除
        # zscore(name, value): 获取name对应有序集合中 value 对应的分数
        # zinterstore(dest, keys, aggregate=None): 获取两个有序集合的交集，如果遇到相同值不同分数，则按照aggregate进行操作
        # zunionstore(dest, keys, aggregate=None)：# 获取两个有序集合的并集，如果遇到相同值不同分数，则按照aggregate进行操作
        # zscan(name, cursor=0, match=None, count=None, score_cast_func=float)
        # zscan_iter(name, match=None, count=None, score_cast_func=float)：同字符串相似，相较于字符串新增score_cast_func，用来对分数进行操作
        # 根据排行范围删除
        return Response(conn)


class RedisHashView(APIView):
    def get(self, request):
        conn = get_redis_connection('verify_code')

        #对HASH的操作
        # hset(name, key, value)：# name对应的hash中设置一个键值对（不存在，则创建；否则，修改）
        #hget(name,key):在name对应的hash中获取根据key获取value
        #hmset(name, mapping):# 在name对应的hash中批量设置键值对
        #hmget(name, keys, *args):在name对应的hash中获取多个key的值
        # hgetall(name):获取name对应hash的所有键值
        # hlen(name):# 获取name对应的hash中键值对的个数
        # hkeys(name):获取name对应的hash中所有的key的值
        # hvals(name): 获取name对应的hash中所有的value的值
        # hexists(name, key):检查name对应的hash是否存在当前传入的key
        # hdel(name, *keys):# 将name对应的hash中指定key的键值对删除
        # hincrby(name, key, amount=1):自增name对应的hash中的指定key的值，不存在则创建key=amount
        conn.hset("li","zhen",3)
        data=conn.hincrby("li","zhen")
        return Response(data)

# url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
class MobileCountView(APIView):
    """
    手机号数量
    """

    def get(self, request, mobile):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()

        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)


# url(r'^users/$', views.UserView.as_view()),
class UserView(CreateAPIView):
    """
    用户注册
    传入参数：
        username, password, password2, sms_code, mobile, allow
    """
    serializer_class = CreateUserSerializer

    # def post(self, request, *args, **kwargs):
    #
    #
    #
    #     return super().post(request, *args, **kwargs)


class UserDetailView(RetrieveAPIView):
    """
    用户详情
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    """
    保存用户邮箱
    """
    permission_classes = [IsAuthenticated]
    serializer_class = EmailSerializer

    def get_object(self, *args, **kwargs):
        return self.request.user


# url(r'^emails/verification/$', views.VerifyEmailView.as_view()),
class VerifyEmailView(APIView):
    """
    邮箱验证
    """

    def get(self, request):

        # 获取token值进行判断
        token = request.query_params.get('token', None)
        if not token:
            return Response({'message': '缺少token'}, status=400)

        # 解码token

        dec = Decipher(settings.SECRET_KEY, 300)

        try:
            data = dec.loads(token)
        except:
            return Response({'message': 'token值无效'}, status=400)

        # 提取数据
        email = data.get('email', None)
        user_id = data.get('user_id', None)

        if email is None or user_id is None:
            return Response({'message': '无效数据'}, status=400)

        # 用户查询
        try:
            user = User.objects.get(id=user_id, email=email)
        except:
            return Response({'message': '查询不到用户'}, status=400)

        user.email_active = True
        user.save()

        return Response({
            'message': 'ok'
        })


class Addresses(ListAPIView, CreateAPIView):
    serializer_class = UserAddressSerializer

    def get_queryset(self):
        return Address.objects.filter(is_deleted=False, user=self.request.user)

    def list(self, request, *args, **kwargs):
        query = self.get_queryset()
        ser = self.get_serializer(query, many=True)

        return Response(
            {
                'user_id': request.user.id,
                'default_address_id': request.user.default_address_id,
                'limit': 5,
                'addresses': ser.data,

            }
        )

class UserAuthorizeView(ObtainJSONWebToken):
    """
    用户认证
    """

    def post(self, request, *args, **kwargs):

        response=super().post(request, *args, **kwargs)

        # 获取一下用户对象
        ser=self.get_serializer(data=request.data)

        if ser.is_valid():
            user=ser.validated_data.get('user')

            # 调用合并方法

            response=merge_cart_cookie_to_redis(request,user,response)


            return response
        return response