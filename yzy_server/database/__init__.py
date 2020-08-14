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


