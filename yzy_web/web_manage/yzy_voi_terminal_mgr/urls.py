from django.urls import path
from web_manage.yzy_voi_terminal_mgr import views


urlpatterns = [
    path('terminal_groups/', views.TerminalGroupList.as_view(), name='voi-teriminal-group-list'),
    path('group/list/', views.GroupList.as_view(), name='voi-teriminal-group-list'),
    path('edu_group/list/', views.EduGroupList.as_view(), name='voi-teriminal-edu-group-list'),
    path('terminals/', views.TerminalList.as_view(), name='voi-terminal-list'),
    path('terminals/sort/', views.TerminalSortList.as_view(), name='voi-terminal-list-sort'),
    path('terminal_operate/', views.TerminalOperate.as_view(), name='voi-terminal-operate'),
]
