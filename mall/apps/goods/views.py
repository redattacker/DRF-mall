# Create your views here.
from rest_framework.generics import ListAPIView,CreateAPIView
from rest_framework.permissions import IsAuthenticated
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
# from drf_haystack.viewsets import HaystackViewSet
from goods.serializer import SKUSerializer,AddUserBrowsingHistorySerializer
from goods.models import SKU


#GET /categories/(?P<category_id>\d+)/hotskus/
class HotSKUListView(ListAPIView):
    """
    热销商品, 使用缓存扩展
    """
    serializer_class =SKUSerializer
    pagination_class = None

    # def get(self,request,category_id):

    def get_queryset(self):

        # 获取月分类id
        category_id=self.kwargs['category_id']
        return SKU.objects.filter(category_id=category_id,is_launched=True).order_by('-sales')[:4]

# POST /browse_histories/ # 保存历史记录
# GET /browse_histories/  # 获取历史记录

class UserBrowsingHistoryView(CreateAPIView):
    """
    用户浏览历史记录
    """

    serializer_class = AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get(self,request):


        # 或去用户id
        user_id=request.user.id
        # 建立缓存连接
        conn=get_redis_connection('history')

        history=conn.lrange('history_%s'%user_id,0,4)

        # 根据sku——id查询出商品对象
        skus=[]
        for sku_id in history:
            skus.append(SKU.objects.get(id=sku_id,is_launched=True))


        ser=SKUSerializer(skus,many=True)

        return Response(ser.data)

# /categories/(?P<category_id>\d+)/skus?page=xxx&page_size=xxx&ordering=xxx
class SKUListView(ListAPIView):
    """
    sku列表数据
    """
    serializer_class = SKUSerializer
    filter_backends = (OrderingFilter,)
    ordering_fields=('create_time','price','sales')

    def get_queryset(self):
        category_id=self.kwargs['category_id']

        return SKU.objects.filter(category_id=category_id,is_launched=True)

#
#
# class SKUSearchViewSet(HaystackViewSet):
#     """
#     SKU搜索
#     """
#     index_models = [SKU]
#
#     serializer_class = SKUIndexSerializer