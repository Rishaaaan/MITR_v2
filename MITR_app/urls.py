from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('add_task/', views.add_task_view, name='add_task'),
    path('add_employee/',views.add_employee_view, name='add_employee'),
    path('task/<int:task_id>/', views.task_view, name='task_view'),
    path('task/<int:task_id>/delete/', views.delete_task_view, name='delete_task'),
    path('task/<int:task_id>/set_incomplete/', views.set_incomplete_view, name='set_incomplete'),
    path('employee_list/', views.employee_list_view, name='employee_list'),
    path('confirm_remove_employee/<str:employee_id>/', views.confirm_remove_employee, name='confirm_remove_employee'),
    path('employee/<int:employee_id>/progress/', views.employee_progress, name='employee_progress'),
    path('summary_report/', views.summary_report, name='summary_report'),
    path('download_summary_report/<date>/<report_type>/<status_filter>/', views.download_summary_report, name='download_summary_report'),
]
