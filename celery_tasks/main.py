from celery import Celery

# 创建一个Celery对象
# celery_app = Celery('celery_tasks', broker='中间人地址')
celery_app = Celery('celery_tasks')

# 加载配置
celery_app.config_from_object('celery_tasks.config')


# 让celery自动发现任务
celery_app.autodiscover_tasks(['celery_tasks.sms'])