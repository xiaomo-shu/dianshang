from django.urls import path
from web_manage.yzy_monitor_mgr import views

urlpatterns = [
    path('nodes/', views.MonitorNodeInfo.as_view(), name='monitor-node-performance'),
    path('node/history_perf/', views.MonitorNodeHisPerformance.as_view(), name='monitor-node-performance'),
    path('node/current_perf/', views.MonitorNodeCurPerformance.as_view(), name='monitor-node-performance'),
]
