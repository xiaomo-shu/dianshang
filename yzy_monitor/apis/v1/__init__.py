# -*- coding: utf-8 -*-


from flask import Blueprint
# from flask_cors import CORS

api_v1 = Blueprint('api_v1', __name__)

# CORS(api_v1)

from yzy_monitor.apis.v1.views.index import *
from yzy_monitor.apis.v1.views.resource_monitor import *