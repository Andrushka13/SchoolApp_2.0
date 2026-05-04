# unicron_app/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'unicron_app'

urlpatterns = [
    # Аутентификация
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Дашборд
    path('', views.dashboard, name='dashboard'),

    # Личные кабинеты
    path('student/', views.student_cabinet, name='student_cabinet'),
    path('teacher/', views.teacher_cabinet, name='teacher_cabinet'),
    path('admin-cabinet/', views.admin_cabinet, name='admin_cabinet'),

    # Расписание
    path('schedule/', views.schedule_view, name='schedule'),
    path('schedule/add/', views.schedule_add, name='schedule_add'),
    path('schedule/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),

    # Успеваемость
    path('grades/', views.grades_manage, name='grades_manage'),
    path('grades/add/', views.grade_add, name='grade_add'),
    path('grades/student/<int:student_id>/', views.student_grades, name='student_grades'),

    # Посещаемость
    path('attendance/', views.attendance_view, name='attendance'),
    path('attendance/mark/<int:schedule_id>/', views.mark_attendance, name='mark_attendance'),

    # Отчёты
    path('reports/', views.reports, name='reports'),
    path('reports/export/excel/', views.export_excel, name='export_excel'),
    path('reports/export/pdf/', views.export_pdf, name='export_pdf'),

    # Заявка на поступление
    path('apply/', views.apply, name='apply'),
]