#! /bin/bash
# 设置环境变量
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh

cd ~/Desktop/gz02_code/meiduo/meiduo_mall
workon gz02_django
celery -A celery_tasks.main worker -l info