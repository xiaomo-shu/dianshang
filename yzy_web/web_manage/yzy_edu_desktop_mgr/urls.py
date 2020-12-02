from django.urls import path
from . import views

urlpatterns = [
    path('template/', views.EducationTemplateView.as_view(), name='template'),
    path('group/', views.EducationGroupView.as_view(), name='group'),
    path('desktop/', views.EducationDesktopGroupView.as_view(), name='desktop'),
    path('instance/', views.EducationInstanceView.as_view(), name='instance'),
    path('template/image/', views.TemplateImageView.as_view(), name='template-image'),
    path('template/check_ip/', views.TemplateIpView.as_view(), name='template-check-ip'),
    path('term/', views.TermView.as_view({'get': 'list', "post": "create"}), name='term'),
    path('term/check_name_existence/', views.TermView.as_view({'get': 'check_name_existence'}), name='term-check-name-existence'),
    path('term/current_date/', views.TermView.as_view({'get': 'get_current_date'}), name='current-date'),
    path('term/<str:term_uuid>/', views.TermView.as_view({"put": "update", "delete": "delete"}), name='term-update'),
    path('term/<str:term_uuid>/edu_groups/', views.TermView.as_view({'get': 'get_edu_groups'}), name='term-edu-groups'),
    path('term/<str:term_uuid>/weeks_num_map/', views.TermView.as_view({'get': 'get_weeks_num_map'}), name='term-weeks-num-map'),
    path('course_schedule/', views.CourseScheduleView.as_view({"get": "get", "put": "update", "delete": "delete"}), name='course-schedule'),
    path('course_schedule/<str:course_schedule_uuid>/apply/', views.CourseScheduleView.as_view({"post": "apply"}), name='course-schedule-apply'),
    path('course_schedule/enable/', views.CourseScheduleView.as_view({"post": "enable"}), name='course-schedule-enable'),
    path('course_schedule/disable/', views.CourseScheduleView.as_view({"post": "disable"}), name='course-schedule-disable'),

]
