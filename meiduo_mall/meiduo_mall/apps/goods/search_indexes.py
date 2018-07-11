from haystack import indexes

from .models import SKU


class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    # 索引字段
    # use_template=True说明会在一个文件中直接索引字段的内容
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        """返回索引类对应的模型类"""
        return SKU

    def index_queryset(self, using=None):
        """返回要建立索引数据的查询集"""
        return self.get_model().objects.filter(is_launched=True)