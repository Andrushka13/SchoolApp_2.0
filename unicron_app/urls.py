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
    # path('teacher/', views.teacher_cabinet, name='teacher_cabinet'),
    path('admin-cabinet/', views.admin_cabinet, name='admin_cabinet'),
    
    # Студент – личный кабинет
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/account/', views.student_account, name='student_account'),
    path('student/schedule/', views.student_schedule_week, name='student_schedule_week'),
    path('student/schedule/<int:year>/<int:month>/<int:day>/', views.student_schedule_day, name='student_schedule_day'),
    path('student/grades/', views.student_my_grades, name='student_my_grades'),
    
    # Преподаватель – личный кабинет
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/account/', views.teacher_account, name='teacher_account'),
    path('teacher/schedule/', views.teacher_schedule_week, name='teacher_schedule_week'),
    path('teacher/schedule/<int:year>/<int:month>/<int:day>/', views.teacher_schedule_day, name='teacher_schedule_day'),
    path('teacher/groups/', views.teacher_groups, name='teacher_groups'),
    path('teacher/groups/<int:group_id>/', views.teacher_group_detail, name='teacher_group_detail'),
    
    # Методист
    # path('methodist/', views.methodist_dashboard, name='methodist_dashboard'),
    # path('methodist/today/', views.methodist_today, name='methodist_today'),
    # path('methodist/schedule/', views.methodist_schedule_week, name='methodist_schedule_week'),
    # path('methodist/schedule/<int:year>/<int:month>/<int:day>/', views.methodist_schedule_day, name='methodist_schedule_day'),
    # path('methodist/groups/', views.methodist_groups, name='methodist_groups'),
    # path('methodist/groups/<int:group_id>/', views.methodist_group_detail, name='methodist_group_detail'),

        # Методист
    path('methodist/', views.methodist_dashboard, name='methodist_dashboard'),
    path('methodist/today/', views.methodist_today, name='methodist_today'),
    path('methodist/schedule/', views.methodist_schedule_week, name='methodist_schedule_week'),
    path('methodist/schedule/<int:year>/<int:month>/<int:day>/', views.methodist_schedule_day, name='methodist_schedule_day'),
    path('methodist/groups/', views.methodist_groups, name='methodist_groups'),
    path('methodist/groups/<int:group_id>/', views.methodist_group_detail, name='methodist_group_detail'),
    path('methodist/generate-schedule/', views.methodist_generate_schedule, name='methodist_generate_schedule'),
    
    # Секретарь приёмной комиссии
    path('secretary/', views.secretary_dashboard,name='secretary_dashboard'),
    path('secretary/today/', views.secretary_today,name='secretary_today'),
    # path('secretary/schedule/', views.secretary_schedule_week,name='secretary_schedule_week'),
    # path('secretary/schedule/<int:year>/<int:month>/<int:day>/',views.secretary_schedule_day, name='secretary_schedule_day'),
    # path('secretary/groups/', views.secretary_groups,name='secretary_groups'),
    # path('secretary/groups/<int:group_id>/', views.secretary_group_detail, name='secretary_group_detail'),

    # Расписание
    path('schedule/', views.schedule_view, name='schedule'),
    path('schedule/add/', views.schedule_add, name='schedule_add'),
    path('schedule/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),

    # Успеваемость
    path('grades/', views.grades_manage, name='grades_manage'),
    path('grades/add/', views.grade_add, name='grade_add'),

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