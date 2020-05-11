#! /usr/bin/env python
import os
import django
import sys

sys.path.insert(0, '../')

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

# 让Django进行一次初始化操作
django.setup()

from contents.crons import generate_static_index_html

if __name__ == "__main__":
    # 重新生成静态首页
    generate_static_index_html()