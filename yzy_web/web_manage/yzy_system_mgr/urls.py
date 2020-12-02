from django.urls import path
from web_manage.yzy_system_mgr import views

urlpatterns = [
    # path('database/backs/', views.DatabaseBackList.as_view(), name='database-back-list'),
    path('crontab/task/', views.CrontabTaskView.as_view(), name='crontab-task-list'),
    path('database/', views.DatabaseBackView.as_view(), name='database-back'),
    path('database/download/', views.DatabaseDownloadView.as_view(), name='database-download'),
    path('logs/operation/', views.OperationLogView.as_view(), name='operation-log'),
    path('auth/', views.AuthView.as_view(), name='auth'),
    path('auth/ukey/', views.AuthUkeyView.as_view(), name='auth_ukey'),
    path('voi_setup/', views.VoiSetupView.as_view(), name='voi_setup'),
    path('logs/export/', views.ExportLogView.as_view(), name='export-log'),
    path('logs/warn/',  views.WarningLogView.as_view(), name='warn-log'),
    path('logs/warn/setup/',  views.WarningLogSetupView.as_view(), name='warn-log-setup'),
    path('upgrade/', views.UpgradeView.as_view(), name='upgrade'),
    path('logs/setup/cron/',  views.LogSetupCronView.as_view(), name='log-setup-cron'),
    path('task_info',  views.TaskInfoView.as_view(), name='task_info'),
    path('strategy/system_time',  views.SetSystemTime.as_view(), name='set_system_time'),

]
