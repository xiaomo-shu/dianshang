import datetime

from yzy_monitor.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class commonColumnMixin(object):
    deleted_at = db.Column(db.DateTime)
    deleted = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    updated_at = db.Column(db.DateTime, onupdate=datetime.datetime.utcnow())


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    locale = db.Column(db.String(20))
    # items = database.relationship('Item', back_populates='author', cascade='all')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_json(self):
        return {
            "id": self.id,
            "username": self.username,
            "password_hash": self.password_hash,
            "locale": self.locale
        }


class VecImageTemparyInstance(db.Model, commonColumnMixin):
    __tablename__ = 'vec_images_tempary_instances'

    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.String(64))
    flavor_id = db.Column(db.String(64))
    file_name = db.Column(db.String(512))
    proc_id = db.Column(db.Integer)
    vncport = db.Column(db.Integer)
    monitor_port = db.Column(db.Integer)
    last_connect_time = db.Column(db.Integer)
    status = db.Column(db.String(50))
