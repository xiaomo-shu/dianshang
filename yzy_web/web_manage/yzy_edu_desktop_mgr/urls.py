from django.urls import path
from . import views

urlpatterns = [
    path('template/', views.EducationTemplateView.as_view(), name='template'),
    path('group/', views.EducationGroupView.as_view(), name='group'),
    path('desktop/', views.EducationDesktopGroupView.as_view(), name='desktop'),
    path('instance/', views.EducationInstanceView.as_view(), name='instance'),
    path('template/image/', views.TemplateImageView.as_view(), name='tempalte-image'),
    path('template/check_ip/', views.TemplateIpView.as_view(), name='tempalte-check-ip'),
]
