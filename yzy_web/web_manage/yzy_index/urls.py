from django.urls import path
from web_manage.yzy_index import views

urlpatterns = [
    path('get_top_data/', views.SystemMonitorTopData.as_view(), name='system-monitor-top-data'),
    path('get_resource_statistic/', views.ResourceStatisticData.as_view(), name='resource-statistic-data'),
    path('get_operation_log/', views.OperationLogData.as_view(), name='operation-log-data'),
    path('get_voi_server_data/', views.SystemMonitorVoiServerDate.as_view(), name='system-monitor-voi-server-data'),
    path('get_voi_resource_statistic/', views.ResourceStatisticVOIData.as_view(), name='voi-resource-statistic-data'),
    path('get_fuse_resource_statistic/', views.ResourceStatisticFuseData.as_view(), name='fuse-resource-statistic-data')
]