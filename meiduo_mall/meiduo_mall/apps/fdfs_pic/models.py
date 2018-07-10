from django.db import models

# Create your models here.


class GoodsPic(models.Model):
    """测试上传图片模型类"""
    image = models.ImageField(verbose_name='图片')

    class Meta:
        db_table = 'tb_fdfs_pic'
        verbose_name = '测试图片上传应用'
        verbose_name_plural = verbose_name