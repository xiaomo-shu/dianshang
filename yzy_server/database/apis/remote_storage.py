from yzy_server.database.models import *
from yzy_server.database import model_query


def add_remote_storage(values):
    rs = YzyRemoteStorage()
    rs.update(values)
    db.session.add(rs)
    db.session.flush()


def get_remote_storage_by_key(key, val):
    _query = model_query(YzyRemoteStorage)
    if key == "name":
        _query = _query.filter_by(name=val)
    elif key == "server":
        _query = _query.filter_by(server=val)
    else:
        _query = _query.filter_by(uuid=val)
    res_rs = _query.first()
    return res_rs


def update_remote_storage(rs, values):
    rs.update(values)
    db.session.flush()