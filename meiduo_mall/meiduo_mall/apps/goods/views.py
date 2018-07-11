from django.shortcuts import render
from rest_framework.generics import ListAPIView

from .serializers import SKUSerializer
from .models import SKU
# Create your views here.


# GET /categories/(?P<category_id>\d+)/skus/?page=xxx&page_size=xxx&ordering=xxx
class SKUListView(ListAPIView):
    serializer_class = SKUSerializer

    def get_queryset(self):
        # 获取分类id
        category_id = self.kwargs['category_id']

        return SKU.objects.filter(category_id=category_id, is_launched=True)