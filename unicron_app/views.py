from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Avg, Count, Q
from datetime import timedelta
from .models import *
from .forms import StudentApplicationForm, ScheduleForm, GradeForm
import openpyxl
from openpyxl.styles import Font
from django.template.loader import get_template
# from xhtml2pdf import pisa
from io import BytesIO
import pdfkit
from django.conf import settings
# ───────────────── Декораторы ─────────────────
def role_required(*roles):
    """Доступ только пользователям с указанной ролью."""
    def check_role(user):
        return user.is_authenticated and user.role in roles
    return user_passes_test(check_role, login_url='unicron_app:login')

# ───────────────── Главная ─────────────────
@login_required
def dashboard(request):
    """Перенаправление в личный кабинет по роли."""
    role = request.user.role
    if role == 'student':
        return redirect('unicron_app:student_cabinet')
    elif role == 'teacher':
        return redirect('unicron_app:teacher_cabinet')
    else:
        return redirect('unicron_app:admin_cabinet')

# ───────────────── Личные кабинеты ─────────────────
@login_required
@role_required('student')
def student_cabinet(request):
    student = request.user.student_profile
    today = timezone.now().date()
    schedules = Schedule.objects.filter(group=student.group, date=today, is_cancelled=False).order_by('time_start')
    grades = Grade.objects.filter(student=student).select_related('subject')
    context = {'student': student, 'schedules': schedules, 'grades': grades}
    return render(request, 'unicron_app/student_cabinet.html', context)

@login_required
@role_required('teacher')
def teacher_cabinet(request):
    teacher = request.user.teacher_profile
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    schedules = Schedule.objects.filter(teacher=teacher, date__range=[week_start, week_end], is_cancelled=False)
    curriculums = Curriculum.objects.filter(teacher=teacher)
    context = {'teacher': teacher, 'schedules': schedules, 'curriculums': curriculums}
    return render(request, 'unicron_app/teacher_cabinet.html', context)

@login_required
@role_required('admin', 'head', 'methodist')
def admin_cabinet(request):
    total_directions = Direction.objects.count()
    total_groups = Group.objects.count()
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    groups = Group.objects.annotate(num_students=Count('students'))
    context = {
        'total_directions': total_directions,
        'total_groups': total_groups,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'groups': groups,
    }
    return render(request, 'unicron_app/admin_cabinet.html', context)

# ───────────────── Расписание ─────────────────
def schedule_view(request):
    groups = Group.objects.all()
    selected_group = request.GET.get('group')
    schedules = Schedule.objects.none()
    if selected_group:
        schedules = Schedule.objects.filter(group_id=selected_group, date__gte=timezone.now()).order_by('date', 'time_start')
    return render(request, 'unicron_app/schedule.html', {'groups': groups, 'schedules': schedules, 'selected_group': selected_group})

@login_required
@role_required('admin', 'methodist')
def schedule_add(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('unicron_app:schedule')
    else:
        form = ScheduleForm()
    return render(request, 'unicron_app/schedule_form.html', {'form': form, 'action': 'Добавить'})

@login_required
@role_required('admin', 'methodist')
def schedule_edit(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            return redirect('unicron_app:schedule')
    else:
        form = ScheduleForm(instance=schedule)
    return render(request, 'unicron_app/schedule_form.html', {'form': form, 'action': 'Изменить'})

# ───────────────── Оценки ─────────────────
@login_required
@role_required('teacher')
def grades_manage(request):
    teacher = request.user.teacher_profile
    curriculums = Curriculum.objects.filter(teacher=teacher)
    return render(request, 'unicron_app/grades_manage.html', {'curriculums': curriculums})

@login_required
@role_required('teacher')
def grade_add(request):
    teacher = request.user.teacher_profile
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('unicron_app:grades_manage')
    else:
        # Ограничиваем группы и предметы теми, которые ведёт преподаватель
        form = GradeForm()
        form.fields['group'].queryset = Group.objects.filter(curriculum_entries__teacher=teacher)
        form.fields['subject'].queryset = Subject.objects.filter(curriculum_entries__teacher=teacher)
    return render(request, 'unicron_app/grade_form.html', {'form': form})

def student_grades(request, student_id):
    """
    Если student_id = 0, то показываем оценки всех студентов по фильтру (группа, предмет).
    Иначе — оценки конкретного студента.
    """
    group_id = request.GET.get('group')
    subject_id = request.GET.get('subject')

    if student_id == 0:
        # Режим просмотра оценок всей группы по предмету
        if group_id and subject_id:
            grades = Grade.objects.filter(
                group_id=group_id,
                subject_id=subject_id
            ).select_related('student', 'subject').order_by('student__last_name', 'date')
        else:
            grades = Grade.objects.none()
        context = {
            'grades': grades,
            'group': Group.objects.filter(pk=group_id).first(),
            'subject': Subject.objects.filter(pk=subject_id).first(),
        }
        return render(request, 'unicron_app/group_grades.html', context)
    else:
        # Конкретный студент
        student = get_object_or_404(Student, pk=student_id)
        grades = Grade.objects.filter(student=student).order_by('subject', 'date')
        return render(request, 'unicron_app/student_grades.html', {
            'student': student,
            'grades': grades,
        })

# ───────────────── Посещаемость ─────────────────
@login_required
@role_required('teacher')
def attendance_view(request):
    teacher = request.user.teacher_profile
    group_id = request.GET.get('group')
    schedules = Schedule.objects.filter(
        teacher=teacher,
        date=timezone.now().date(),
        is_cancelled=False
    )
    if group_id:
        schedules = schedules.filter(group_id=group_id)
    return render(request, 'unicron_app/attendance.html', {'schedules': schedules})


@login_required
@role_required('teacher')
def mark_attendance(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    students = schedule.group.students.all()
    if request.method == 'POST':
        for student in students:
            present = request.POST.get(f'present_{student.pk}') == 'on'
            Attendance.objects.update_or_create(
                schedule=schedule,
                student=student,
                defaults={
                    'group': schedule.group,
                    'subject': schedule.subject,
                    'date': schedule.date,
                    'is_present': present
                }
            )
        return redirect('unicron_app:attendance')
    # Получить уже отмеченных
    attendances = Attendance.objects.filter(schedule=schedule)
    attendance_dict = {a.student_id: a.is_present for a in attendances}
    return render(request, 'unicron_app/mark_attendance.html', {
        'schedule': schedule,
        'students': students,
        'attendance_dict': attendance_dict,
    })

# ───────────────── Отчёты ─────────────────
@login_required
@role_required('admin', 'head', 'methodist')
def reports(request):
    return render(request, 'unicron_app/reports.html')

def export_excel(request):
    workbook = openpyxl.Workbook()
    ws = workbook.active
    ws.title = "Успеваемость"
    ws.append(['Студент', 'Предмет', 'Тип контроля', 'Балл', 'Дата'])
    grades = Grade.objects.select_related('student', 'subject').all()
    for g in grades:
        ws.append([str(g.student), g.subject.title, g.get_control_type_display(), g.score, g.date])
    # Сохраняем в BytesIO
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=grades.xlsx'
    return response

@login_required
@role_required('admin', 'head', 'methodist')
def export_pdf(request):
    template = get_template('unicron_app/report_pdf.html')
    groups = Group.objects.all()
    html_string = template.render(
        {
            'groups': groups,
        }
    )
    config = pdfkit.configuration()
    if hasattr(settings, 'WKHTMLTOPDF_PATH'):
        config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH)
    
    options = {
        'encoding': 'UTF-8',
        'enable-local-file-access': None
    }
    
    pdf = pdfkit.from_string(html_string, False, options=options, configuration=config)
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Diposition'] = 'attachment; filename="report.pdf"'
    return response
    
# ───────────────── Заявка на поступление ─────────────────
def apply(request):
    if request.method == 'POST':
        form = StudentApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('unicron_app:login')
    else:
        form = StudentApplicationForm()
    return render(request, 'unicron_app/apply.html', {'form': form})