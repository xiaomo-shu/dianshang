from django.conf.urls import url  # noqa
from django.urls import path
from web_manage.yzy_terminal_mgr import views

# from django.contrib import admin
# from django.urls import path, include
# from . import views
#
# urlpatterns = [
#     # path('users/', views.user_list, name='user-list'),
#     path('users/', views.UserList.as_view(), name='user-list'),
#     # path('users/<int:pk>/', views.user_detail, name='user-detail'),
#     path('users/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
#
# ]

urlpatterns = [
    path('terminal_groups/', views.TerminalGroupList.as_view(), name='teriminal-group-list'),
    path('uedu_group/list/', views.UEduGroupList.as_view(), name='teriminal-group-list'),
    path('terminals/', views.TerminalList.as_view(), name='terminal-list'),
    path('terminals/sort/', views.TerminalSortList.as_view(), name='terminal-list-sort'),
    path('terminal_operate/', views.TerminalOperate.as_view(), name='terminal-operate'),
    path('terminal_log/', views.TerminalLog.as_view(), name='terminal-log'),
    path('terminal/upgrade_pag/', views.TerminalUpgradePag.as_view(), name='terminal-upgrade-pag'),
]
