from django.conf.urls import url  # noqa
from django.urls import path
from . import views

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
    # path('session/create/', views.LoginView.as_view(), name='login'),
    path('auth/', views.AuthView.as_view(), name='auth'),
    path('menus/', views.MenusView.as_view(), name='menus'),
    path('pwd_check/', views.PasswordCheckView.as_view(), name=''),
    path('admin_users/', views.AdminUsersView.as_view(), name='admin-user-list'),
    path('admin_user/name_check/', views.AdminUserNameCheck.as_view(), name='admin-user-name-check'),
    path('roles/', views.RolesView.as_view(), name='role-list'),
    path('permissions/<str:role>/', views.PermissionsView.as_view(), name='permission-list'),
    # path('test/', views.OrderView.as_view(), name='menus')
    path('admin_user/enable/', views.AdminUserEnableView.as_view(), name='admin-user-enable')

]
