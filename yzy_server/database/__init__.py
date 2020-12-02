from ..extensions import db


def model_query(*args, **kwargs):
    read_deleted = kwargs.get('read_deleted') or 'no'
    query = db.session.query(*args)

    if read_deleted == 'no':
        query = query.filter_by(deleted=False)
    elif read_deleted == 'yes':
        pass  # omit the filter to include deleted and active
    elif read_deleted == 'only':
        query = query.filter_by(deleted=True)
    else:
        raise Exception(
            "Unrecognized read_deleted value '%s'") % read_deleted

    return query


def many_update(value_dict, *args, **kwargs):
    """
    使用where语句批量更新
    :param value_dict: 更新内容字典
    :param args: 库表model
    :param kwargs: 对哪些记录进行批量更新的过滤条件
    :return: 批量更新成功的数量
    """
    return db.session.query(*args).filter_by(deleted=False).filter_by(**kwargs).update(value_dict)


def many_update_by_in(value_dict, model, field_obj, in_list):
    """
    使用in语句批量更新
    :param value_dict: 更新内容字典
    :param model: 库表model
    :param field_obj: in语句筛选字段obj
    :param in_list: in语句筛选值列表
    :return: 批量更新成功的数量
    """
    return db.session.query(model).filter_by(deleted=False).filter(field_obj.in_(in_list)).update(value_dict, synchronize_session=False)
