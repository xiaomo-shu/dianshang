from django.urls import path
from . import views

urlpatterns = [
    path('group/', views.PersonalGroupView.as_view(), name='group'),
    path('user/', views.GroupUserView.as_view(), name='user'),
    path('user/import/', views.GroupUserUploadView.as_view(), name='user_import'),
    path('desktop/', views.PersonalDesktopGroupView.as_view(), name='personal_desktop'),
    path('desktop/random/', views.DesktopRandomView.as_view(), name='random_desktop'),
    path('desktop/static/', views.DesktopStaticView.as_view(), name='static_desktop'),
    path('instance/', views.PersonalInstanceView.as_view(), name='personal_instance')
]
