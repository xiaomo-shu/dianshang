

class BaseTableCtrl:
    def __init__(self, db):
        self.db = db

    def model_query(self, *args, **kwargs):
        query = self.db.session.query(*args)
        return query

