from yzy_server.database.models import *
from yzy_server.database import model_query


def add_operation_log(values):
    log = YzyOperationLog()
    log.update(values)
    db.session.add(log)
    db.session.flush()


def get_operation_log_all(item):
    logs = model_query(YzyOperationLog).filter_by(**item).all()
    return logs
