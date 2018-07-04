from celery_tasks.main import celery_app


# 定义任务函数
@celery_app.task(name='my_first_task')
def task_func(a, b):
    print('任务函数被调用...a: %s b: %s' % (a, b))