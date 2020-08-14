import os
import traceback
from yzy_monitor.log import logger
from flask import current_app
from yzy_monitor.timer_tasks.resource_task import ResourceTask
from yzy_monitor.timer_tasks.service_task import ServiceTask
from yzy_monitor.timer_tasks.statistic_task import StatisticTask


def setup_and_start(app):
    # tasks = []
    try:
        # path = os.path.dirname(os.path.abspath(__file__))
        # task_dir, task_package = os.path.split(path)
        # tasks_files = os.listdir(path)
        # for file_name in tasks_files:
        #     if file_name.endswith('.py') and file_name not in ('__init__.py', 'base_task.py'):
        #         full_file_name = file_name.split('.')[0]
        #         package = '%s' % task_package + "." + full_file_name
        #         module = __import__(package, fromlist=['.'])
        #         names = full_file_name.split('_')
        #         class_name = list()
        #         for name in names:
        #             class_name.append(name.title())
        #         cls = getattr(module, ''.join(class_name))
        #         tasks.append(cls(app))
        tasks = [
            ResourceTask(app),
            ServiceTask(app),
            StatisticTask(app)
        ]
        return tasks
    except Exception as err:
        print('err {}'.format(err))
        logger.error('err {}'.format(err))
        logger.error(''.join(traceback.format_exc()))
        current_app.logger.error(err)
        raise Exception("load task error")


