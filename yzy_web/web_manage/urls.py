from django.urls import path, include

urlpatterns = [
    path('', include('web_manage.yzy_admin.urls')),
    path('resource_mgr/', include('web_manage.yzy_resource_mgr.urls')),
    path('education/', include('web_manage.yzy_edu_desktop_mgr.urls')),
    path('personal/', include('web_manage.yzy_user_desktop_mgr.urls')),
    path('system/', include('web_manage.yzy_system_mgr.urls')),
    path('terminal_mgr/', include('web_manage.yzy_terminal_mgr.urls')),
    path('index/', include('web_manage.yzy_index.urls')),
    path('voi/education/', include('web_manage.yzy_voi_edu_desktop_mgr.urls')),
    path('voi/terminal_mgr/', include('web_manage.yzy_voi_terminal_mgr.urls')),
    path('monitor_mgr/', include('web_manage.yzy_monitor_mgr.urls')),
]
