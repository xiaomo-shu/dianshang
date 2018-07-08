from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from .serializers import AreasSerializer, SubAreasSerializer
from .models import Area


# Create your views here.
# class AreasViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
class AreasViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    # 关闭分页
    pagination_class = None

    def get_serializer_class(self):
        if self.action == 'list':
            return AreasSerializer
        else:
            return SubAreasSerializer

    def get_queryset(self):
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()


# GET /areas/
# class AreasView(ListModelMixin, GenericAPIView):
# class AreasView(ListAPIView):
#     """
#     获取所有省级地址的信息:
#     """
#     serializer_class = AreasSerializer
#     queryset = Area.objects.filter(parent=None)
#
#     # def get(self, request):
#     #     # # 1. 获取所有省级地区信息
#     #     # # areas = Area.objects.filter(parent=None)
#     #     # areas = self.get_queryset()
#     #     #
#     #     # # 2. 将所有省级地区的信息进行序列化并返回
#     #     # # serializer = AreasSerializer(areas, many=True)
#     #     # serializer = self.get_serializer(areas, many=True)
#     #     # return Response(serializer.data)
#     #     return self.list(request)

# GET /areas/(?P<pk>\d+)/
# class SubAreasView(RetrieveModelMixin, GenericAPIView):
# class SubAreasView(RetrieveAPIView):
#     """
#     根据父级地址id获取子级地区的信息:
#     """
#     serializer_class = SubAreasSerializer
#     queryset = Area.objects.all()
#
#     # def get(self, request, pk):
#     #     # # 1. 根据`pk`获取地区的信息
#     #     # # area = Area.objects.get(pk=pk)
#     #     # area = self.get_object()
#     #     #
#     #     # # sub_areas = area.subs.all()
#     #     # # 2. 对父级地区进行序列化(包含关联数据)
#     #     # # serializer = SubAreasSerializer(area)
#     #     # serializer = self.get_serializer(area)
#     #     # return Response(serializer.data)
#     #
#     #     return self.retrieve(request, pk)
