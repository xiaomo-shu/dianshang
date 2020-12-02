from yzy_server.database.models import *
from yzy_server.database import model_query
from common import constants


def create_database_back(values):
    database_back = YzyDatabaseBack()
    database_back.update(values)
    db.session.add(database_back)
    db.session.flush()


def get_crontab_tasks(item={}):
    tasks = model_query(YzyCrontabTask).filter_by(**item).all()
    return tasks


def create_crontab_task(values):
    task = YzyCrontabTask()
    task.update(values)
    db.session.add(task)
    db.session.flush()


def create_crontab_detail(values):
    task = YzyCrontabDetail()
    task.update(values)
    db.session.add(task)
    db.session.flush()


def create_warn_setup(values):
    record = YzyWarnSetup()
    record.update(values)
    db.session.add(record)
    db.session.flush()


def create_task_info(values):
    task = YzyTask()
    task.update(values)
    db.session.add(task)
    db.session.flush()


def get_database_backup_first(item):
    backup = model_query(YzyDatabaseBack).filter_by(**item).first()
    return backup


def get_database_backup_all(item):
    backups = model_query(YzyDatabaseBack).filter_by(**item).all()
    return backups


def get_crontab_first(item):
    crontab = model_query(YzyCrontabTask).filter_by(**item).first()
    return crontab


def get_crontab_detail_first(item):
    crontab = model_query(YzyCrontabDetail).filter_by(**item).first()
    return crontab


def get_crontab_detail_all(item):
    crontab = model_query(YzyCrontabDetail).filter_by(**item).all()
    return crontab


def get_admin_user_first(item):
    user = model_query(YzyAdminUser).filter_by(**item).first()
    return user


def get_warning_log_all(item):
    warning_logs = model_query(YzyWarningLog).filter(YzyWarningLog.created_at < item)
    return warning_logs


def get_operation_log_all(item):
    operation_logs = model_query(YzyOperationLog).filter(YzyOperationLog.created_at < item)
    return operation_logs


def get_warn_setup_first(item):
    warn_setup = model_query(YzyWarnSetup).filter_by(**item).first()
    return warn_setup


def get_task_info_first(item):
    task = model_query(YzyTask).filter_by(**item).first()
    return task


def get_task_with_type_all(item):
    tasks = model_query(YzyTask).filter(YzyTask.type.in_(item)).all()
    return tasks
