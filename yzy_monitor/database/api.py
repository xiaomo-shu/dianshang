# -*- coding: utf-8 -*-
from yzy_monitor.extensions import db
from .models import *


def list_ImageTemparyInstance():
    result = db.session.query(VecImageTemparyInstance).filter_by(deleted=0).all()
    return result

