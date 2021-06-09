import pickle,base64
from django_redis import get_redis_connection

def merge_cart_cookie_to_redis(request,user,response):
    """
    合并请求用户的购物车数据，将未登录保存在cookie里的保存到redis中
    :param request: 用户的请求对象
    :param user: 当前登录的用户
    :param response: 响应对象，用于清楚购物车cookie
    :return:
    """

    # 获取cookies中存储的数据
    cookie_cart=request.COOKIES.get('cart')

    # 判断cookie数据是否存在
    if cookie_cart:

        '''
        {
                sku_id: {
                    "count": xxx,  // 数量
                    "selected": True  // 是否勾选
                },
                sku_id: {
                    "count": xxx,
                    "selected": False
                },
            }
        
        '''

        # 解码
        cookie_cart=pickle.loads(base64.b64decode(cookie_cart.encode()))

        # 建立缓存连接
        conn=get_redis_connection('cart')  #

        # 获取数量数据
        cart_count=conn.hgetall('cart_%s'%user.id)  #{sku_id:10}

        # 获取状态数据
        cart_selected=conn.smembers('cart_selected_%s'%user.id)

        print(cart_count)
        cart={}
        # 对缓存中的数据进行类型转化
        for sku_id,count in cart_count.items():
            cart[int(sku_id)]=int(count)


        # 取出cookies中的数据进行合并

        for sku_id,count_selected_dict in cookie_cart.items():
            # 处理数量关系的合并
            cart[sku_id]=count_selected_dict['count']
            # 处理选中状态的合并
            if count_selected_dict['selected']:
                cart_selected.add(sku_id)


        # 写入到缓存当中
        pl=conn.pipeline()
        pl.hmset('cart_%s'%user.id,cart)
        pl.sadd('cart_selected_%s'%user.id,*cart_selected)#{skuid1,skuid2}
        pl.execute()

        # 删除cookies
        response.delete_cookie('cart')

        return response
    return response



