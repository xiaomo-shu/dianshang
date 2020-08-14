# -*- coding: utf-8 -*-


from flask import Blueprint
# from flask_cors import CORS

api_v1 = Blueprint('api_v1', __name__)

# CORS(api_v1)

from yzy_server.apis.v1.views.index import *
from yzy_server.apis.v1.views.resource_pool import *
from yzy_server.apis.v1.views.network import *
from yzy_server.apis.v1.views.node import *
from yzy_server.apis.v1.views.iso import *
from yzy_server.apis.v1.views.desktop import *
from yzy_server.apis.v1.views.template import *
from yzy_server.apis.v1.views.group import *
from yzy_server.apis.v1.views.web import *
from yzy_server.apis.v1.views.system import *
from yzy_server.apis.v1.views.terminal import *
from yzy_server.apis.v1.views.voi_template import *
from yzy_server.apis.v1.views.voi_group import *
from yzy_server.apis.v1.views.voi_desktop import *
from yzy_server.apis.v1.views.voi_terminal import *
from yzy_server.apis.v1.views.monitor import *

