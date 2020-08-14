from yzy_server.database.models import *
from yzy_server.database import model_query


def get_resource_pool_list():
    result = model_query(YzyResourcePool).all()
    return result


def add_resource_pool(values):
    resource_pool = YzyResourcePool()
    resource_pool.update(values)
    db.session.add(resource_pool)
    db.session.flush()
    return


def add_task_info(values):
    task = YzyTaskInfo()
    task.update(values)
    db.session.add(task)
    db.session.flush()


def get_resource_pool_by_key(key, val):
    _query = model_query(YzyResourcePool)
    if key == "name":
        _query = _query.filter_by(name=val)
    elif key == "id":
        _query = _query.filter_by(id=val)
    else:
        _query = _query.filter_by(uuid=val)
    res_pool = _query.first()
    return res_pool


def get_task_step(task_id):
    try:
        result = model_query(YzyTaskInfo).filter_by(task_id=task_id).order_by(YzyTaskInfo.step.desc()).first()
        return result.step
    except Exception:
        return 0


def get_task_first(item):
    result = model_query(YzyTaskInfo).filter_by(**item).first()
    return result


def get_task_first_with_progress_desc(item):
    result = model_query(YzyTaskInfo).filter_by(**item).\
        order_by(YzyTaskInfo.progress.desc()). \
        order_by(YzyTaskInfo.id.desc()).first()
    return result


def get_image_task_state_first(item):
    result = model_query(YzyTaskInfo).filter_by(**item).\
        order_by(YzyTaskInfo.progress.desc()).\
        order_by(YzyTaskInfo.id.desc()).first()
    return result


def get_task_all(item):
    result = model_query(YzyTaskInfo).filter_by(**item).all()
    return result


def get_images_with_all(item):
    images = model_query(YzyBaseImage).filter_by(**item).all()
    return images


def get_image_with_first(item):
    image = model_query(YzyBaseImage).filter_by(**item).first()
    return image


def get_iso_with_first(item):
    iso = model_query(YzyIso).filter_by(**item).first()
    return iso
