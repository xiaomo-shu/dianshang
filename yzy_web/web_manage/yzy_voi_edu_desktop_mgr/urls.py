from django.urls import path
from . import views

urlpatterns = [
    path('template/', views.VoiTemplateView.as_view(), name='voi_template'),
    path('template/operate/', views.VoiTemplateOperateView.as_view(), name='voi_template_operate'),
    path('template/ipaddr/', views.VoiTemplateIPaddrView.as_view(), name='template_ipaddr'),
    path('group/', views.VoiEducationGroupView.as_view(), name='voi_group'),
    path('desktop/', views.VoiDesktopGroupView.as_view(), name='voi_desktop'),
    path('instance/', views.EducationVoiInstanceView.as_view(), name='instance'),
]
