from rest_framework.generics import ListAPIView, RetrieveAPIView
# Create your views here.
from rest_framework_extensions.cache.decorators import cache_response
from areas.models import Area
from areas.serializers import AreaSerializer,SubAreaSerializer



class AreasViews(ListAPIView):
    serializer_class = AreaSerializer

    def get_queryset(self):
        return Area.objects.filter(parent_id=None)

    @cache_response()
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AreasView(RetrieveAPIView):
    serializer_class = SubAreaSerializer
    queryset = Area.objects.all()

    @cache_response(key_func='calculate_cache_key')
    # @cache_response()
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def calculate_cache_key(self, view_instance, view_method,
                            request, args, kwargs):
        pk = self.kwargs['pk']
        pk_list = []
        pk_list.append(pk)

        return '.'.join(pk_list)
