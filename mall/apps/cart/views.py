from django.shortcuts import render

from rest_framework.generics import GenericAPIView
from django_redis import get_redis_connection
# Create your views here.
from rest_framework.response import Response
import pickle, base64
from rest_framework.views import APIView

from cart.seializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer, CartSelectAllSerializer
from goods.models import SKU
from rest_framework import status


class CartView(GenericAPIView):
    """
    购物车
    """

    def perform_authentication(self, request):
        pass

    # serializer_class =CartSerializer
    def get_serializer_class(self):
        if self.request.method == 'DELETE':
            return CartDeleteSerializer
        else:
            return CartSerializer

    def post(self, request):
        # 进行数据验证
        ser = self.get_serializer(data=request.data)
        ser.is_valid()

        # 获取数据
        sku_id = ser.validated_data['sku_id']
        count = ser.validated_data['count']
        selected = ser.validated_data['selected']

        try:
            user = request.user

        except:
            user = None

        if user is not None:
            # 用户已经登录
            # 建立连接
            conn = get_redis_connection('cart')
            pl = conn.pipeline()
            # 先写数量关系  哈希类型
            pl.hincrby('cart_%s' % user.id, sku_id, count)

            # 写入是否选中状态
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)

            pl.execute()

            return Response(ser.data)
        else:
            # 先判断有没有写入过cookies数据

            cart = request.COOKIES.get('cart')
            if cart:
                # 说明以前写入过
                # 解密
                cart = pickle.loads(base64.b64decode(cart.encode()))
            else:
                cart = {}

            # 判断当前sku是否写入过
            '''
             sku_id: {
                    "count": xxx,  // 数量
                    "selected": True  // 是否勾选
                },


            '''
            sku = cart.get(sku_id, None)
            if sku:
                count += int(sku['count'])
            # 组建新的数据字典
            cart[sku_id] = {
                "count": count,
                "selected": selected
            }

            # 反回数据
            # 加密
            cookies_cart = base64.b64encode(pickle.dumps(cart)).decode()

            response = Response(ser.data)

            response.set_cookie('cart', cookies_cart, 60 * 60 * 24)

            return response

    def get(self, request):
        # 获取用户
        try:
            user = request.user

        except:
            user = None

        if user is not None:
            # 用户已经登录
            # 建立连接
            conn = get_redis_connection('cart')

            # 先去数量关系数据
            count_cart = conn.hgetall('cart_%s' % user.id)  # {sku_id:10}

            # 获取选中状态
            selected_cart = conn.smembers('cart_selected_%s' % user.id)  # (sku_id,)
            cart = {}
            print(count_cart)
            for sku_id, count in count_cart.items():
                cart[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected_cart
                }


        else:

            cart = request.COOKIES.get('cart')
            if cart:
                # 说明以前写入过
                # 解密
                cart = pickle.loads(base64.b64decode(cart.encode()))
            else:
                cart = {}

        # 查询数据或sku数据对象

        skus = SKU.objects.filter(id__in=cart.keys())

        # 还需要对数据对象额外负值

        for sku in skus:
            sku.count = cart[sku.id]['count']
            sku.selected = cart[sku.id]['selected']

        # 序列化返回

        ser = CartSKUSerializer(skus, many=True)

        return Response(ser.data)

    def put(self, request):
        # 进行数据验证
        ser = self.get_serializer(data=request.data)
        ser.is_valid()

        # 获取数据
        sku_id = ser.validated_data['sku_id']
        count = ser.validated_data['count']
        selected = ser.validated_data['selected']

        try:
            user = request.user

        except:
            user = None

        if user is not None:
            # 用户已经登录
            # 建立连接
            conn = get_redis_connection('cart')
            pl = conn.pipeline()
            # 先写数量关系  哈希类型
            pl.hset('cart_%s' % user.id, sku_id, count)

            # 写入是否选中状态
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            else:
                pl.srem('cart_selected_%s' % user.id, sku_id)

            pl.execute()

            return Response(ser.data)

        else:
            cart = request.COOKIES.get('cart')
            if cart:
                # 说明以前写入过
                # 解密
                cart = pickle.loads(base64.b64decode(cart.encode()))
            else:
                cart = {}

            # 构建新的数据字典
            cart[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 反回数据
            # 加密
            cookies_cart = base64.b64encode(pickle.dumps(cart)).decode()

            response = Response(ser.data)

            response.set_cookie('cart', cookies_cart, 60 * 60 * 24)

            return response

    def delete(self, request):

        # 数据验证
        ser = self.get_serializer(data=request.data)
        ser.is_valid()
        sku_id = ser.validated_data['sku_id']

        # 用户判断

        try:
            user = request.user

        except:
            user = None

        if user is not None:
            # 用户已经登录
            # 建立连接
            conn = get_redis_connection('cart')
            pl = conn.pipeline()

            # 对数量数据进行删除
            pl.hdel('cart_%s' % user.id, sku_id)
            # 对于状态进行删除
            pl.srem('cart_%s' % user.id, sku_id)

            pl.execute()

            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            cart = request.COOKIES.get('cart')
            if cart:
                # 说明以前写入过
                # 解密
                cart = pickle.loads(base64.b64decode(cart.encode()))

                '''                    
                sku_id: {
                       "count": xxx,  // 数量
                       "selected": True  // 是否勾选
                   },
                 '''
                if sku_id in cart:
                    del cart[sku_id]

                    # 反回数据
                    # 加密
                    cookies_cart = base64.b64encode(pickle.dumps(cart)).decode()

                    response = Response(status=status.HTTP_204_NO_CONTENT)

                    response.set_cookie('cart', cookies_cart, 60 * 60 * 24)

                    return response

        return Response(status=status.HTTP_204_NO_CONTENT)


class CartSelectAllView(APIView):
    """
    购物车全选
    """

    def put(self, request):
        ser = CartSelectAllSerializer(data=request.data)

        selected = ser.validated_data['selected']

        # 用户判断

        try:
            user = request.user

        except:
            user = None

        if user is not None:
            # 用户已经登录
            # 建立连接
            conn = get_redis_connection('cart')
            pl = conn.pipeline()

            # 获取sku_id值
            count_cart = pl.hgetall('cart_%s' % user.id)  # ({skuid:10}{skuid2:10})

            for sku_id, count in count_cart.items():

                if selected:
                    pl.sadd('cart_selected_%s' % user.id, sku_id)
                else:
                    pl.srem('cart_selected_%s' % user.id, sku_id)

            pl.execute()
            return Response({'message': 'ok'})

        else:

            cart = request.COOKIES.get('cart')
            if cart:
                # 说明以前写入过
                # 解密
                cart = pickle.loads(base64.b64decode(cart.encode()))
                '''
                 sku_id: {
                       "count": xxx,  // 数量
                       "selected": True  // 是否勾选
                   },

                '''
                # 所有撞塌进行修改
                for sku_id in cart.keys():
                    cart[sku_id]['selected'] = selected

                cookies_cart = base64.b64encode(pickle.dumps(cart)).decode()

                response = Response({'message': 'ok'})

                response.set_cookie('cart', cookies_cart, 60 * 60 * 24)

                return response

            return Response({'message': 'ok'})
