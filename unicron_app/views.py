# unicron_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.urls import reverse
from django.db.models import Avg, Count, Q
from django.db import transaction
from datetime import datetime, timedelta
from django.template.loader import get_template
from io import BytesIO
import pdfkit
from django.conf import settings

from .models import *
from .forms import StudentApplicationForm, ScheduleForm, GradeForm
import openpyxl
from openpyxl.styles import Font


# ───────────────── Декораторы ─────────────────
def role_required(*roles):
    """Доступ только пользователям с указанной ролью."""
    def check_role(user):
        return user.is_authenticated and user.role in roles
    return user_passes_test(check_role, login_url='unicron_app:login')


def student_required(view_func):
    """Доступ только для роли 'student'."""
    return user_passes_test(lambda u: u.is_authenticated and u.role == 'student', login_url='unicron_app:login')(view_func)

def teacher_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == 'teacher', login_url='unicron_app:login')(view_func)

def methodist_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and u.role == 'methodist',
        login_url='unicron_app:login'
    )(view_func)


# ───────────────── Главная ─────────────────
@login_required
def dashboard(request):
    """Перенаправление в личный кабинет по роли."""
    role = request.user.role
    if role == 'student':
        return redirect('unicron_app:student_dashboard')
    elif role == 'teacher':
        return redirect('unicron_app:teacher_dashboard')
    elif role == 'methodist':
        return redirect('unicron_app:methodist_dashboard')
    else:
        return redirect('unicron_app:admin_cabinet')


# ───────────────── Студент ─────────────────
@login_required
@student_required
def student_dashboard(request):
    return redirect('unicron_app:student_account')


@login_required
@student_required
def student_account(request):
    student = request.user.student_profile
    now = datetime.now().time()
    if now < datetime.strptime('12:00', '%H:%M').time():
        greeting = 'Доброе утро'
    elif now < datetime.strptime('18:00', '%H:%M').time():
        greeting = 'Добрый день'
    else:
        greeting = 'Добрый вечер'
    context = {
        'student': student,
        'greeting': greeting,
        'active_tab': 'account'
    }
    return render(request, 'unicron_app/student_account.html', context)


@login_required
@student_required
def student_schedule_week(request):
    student = request.user.student_profile
    today = timezone.now().date()
    monday = today - timedelta(days=today.weekday())
    days = [monday + timedelta(days=i) for i in range(5)]

    schedules = Schedule.objects.filter(
        group=student.group,
        date__range=[monday, monday + timedelta(days=6)],
        is_cancelled=False
    ).select_related('subject').order_by('date', 'time_start')

    week_data = {day: schedules.filter(date=day) for day in days}

    now = datetime.now().time()
    if now < datetime.strptime('12:00', '%H:%M').time():
        greeting = 'Доброе утро'
    elif now < datetime.strptime('18:00', '%H:%M').time():
        greeting = 'Добрый день'
    else:
        greeting = 'Добрый вечер'

    context = {
        'student': student,
        'greeting': greeting,
        'days': days,
        'week_data': week_data,
        'active_tab': 'schedule'
    }
    return render(request, 'unicron_app/student_schedule_week.html', context)


@login_required
@student_required
def student_schedule_day(request, year, month, day):
    student = request.user.student_profile
    try:
        date = datetime(year, month, day).date()
    except ValueError:
        raise Http404("Неверная дата")

    schedules = Schedule.objects.filter(
        group=student.group,
        date=date,
        is_cancelled=False
    ).select_related('subject', 'teacher').order_by('time_start')

    context = {
        'student': student,
        'date': date,
        'schedules': schedules,
        'active_tab': 'schedule'
    }
    return render(request, 'unicron_app/student_schedule_day.html', context)


@login_required
@student_required
def student_my_grades(request):
    student = request.user.student_profile
    group = student.group
    subjects = Subject.objects.filter(curriculum_entries__group=group).distinct()

    grades_data = []
    for subject in subjects:
        final_grades = Grade.objects.filter(
            student=student,
            subject=subject,
            control_type='final'
        )
        exam = None
        zachet = None
        for grade in final_grades:
            if subject.control_form and subject.control_form.name == 'экзамен':
                exam = grade.score
            elif subject.control_form and subject.control_form.name == 'зачёт':
                zachet = 'Зачтено' if grade.is_passed else 'Не зачтено'
        grades_data.append({
            'subject': subject,
            'exam': exam,
            'zachet': zachet,
        })

    context = {
        'student': student,
        'grades_data': grades_data,
        'active_tab': 'grades'
    }
    return render(request, 'unicron_app/student_grades.html', context)


# ───────────────── Преподаватель ─────────────────
@login_required
@teacher_required
def teacher_dashboard(request):
    return redirect('unicron_app:teacher_account')


@login_required
@teacher_required
def teacher_account(request):
    teacher = request.user.teacher_profile
    now = datetime.now().time()
    if now < datetime.strptime('12:00', '%H:%M').time():
        greeting = 'Доброе утро'
    elif now < datetime.strptime('18:00', '%H:%M').time():
        greeting = 'Добрый день'
    else:
        greeting = 'Добрый вечер'

    context = {
        'teacher': teacher,
        'greeting': greeting,
        'active_tab': 'account'
    }
    return render(request, 'unicron_app/teacher_account.html', context)


@login_required
@teacher_required
def teacher_schedule_week(request):
    teacher = request.user.teacher_profile
    today = timezone.now().date()
    monday = today - timedelta(days=today.weekday())
    days = [monday + timedelta(days=i) for i in range(5)]

    schedules = Schedule.objects.filter(
        teacher=teacher,
        date__range=[monday, monday + timedelta(days=6)],
        is_cancelled=False
    ).select_related('subject', 'group').order_by('date', 'time_start')

    week_data = {day: schedules.filter(date=day) for day in days}

    now = datetime.now().time()
    if now < datetime.strptime('12:00', '%H:%M').time():
        greeting = 'Доброе утро'
    elif now < datetime.strptime('18:00', '%H:%M').time():
        greeting = 'Добрый день'
    else:
        greeting = 'Добрый вечер'

    context = {
        'teacher': teacher,
        'greeting': greeting,
        'days': days,
        'week_data': week_data,
        'active_tab': 'schedule'
    }
    return render(request, 'unicron_app/teacher_schedule_week.html', context)


@login_required
@teacher_required
def teacher_schedule_day(request, year, month, day):
    teacher = request.user.teacher_profile
    try:
        date = datetime(year, month, day).date()
    except ValueError:
        raise Http404("Неверная дата")

    schedules = Schedule.objects.filter(
        teacher=teacher,
        date=date,
        is_cancelled=False
    ).select_related('subject', 'group').order_by('time_start')

    context = {
        'teacher': teacher,
        'date': date,
        'schedules': schedules,
        'active_tab': 'schedule'
    }
    return render(request, 'unicron_app/teacher_schedule_day.html', context)


@login_required
@teacher_required
def teacher_groups(request):
    teacher = request.user.teacher_profile
    groups = Group.objects.filter(
        curriculum_entries__teacher=teacher
    ).distinct()

    context = {
        'teacher': teacher,
        'groups': groups,
        'active_tab': 'groups'
    }
    return render(request, 'unicron_app/teacher_groups.html', context)


@login_required
@teacher_required
def teacher_group_detail(request, group_id):
    teacher = request.user.teacher_profile
    group = get_object_or_404(Group, pk=group_id)
    if not Curriculum.objects.filter(teacher=teacher, group=group).exists():
        raise Http404("Вы не ведёте эту группу")

    students = group.students.all()
    taught_subjects = Subject.objects.filter(
        curriculum_entries__teacher=teacher,
        curriculum_entries__group=group
    )

    student_data = []
    for student in students:
        grades_dict = {}
        for subject in taught_subjects:
            final_grades = Grade.objects.filter(
                student=student,
                subject=subject,
                control_type='final'
            ).order_by('-date')
            last_grade = final_grades.first()
            if last_grade:
                if subject.control_form and subject.control_form.name == 'экзамен':
                    grade_value = last_grade.score
                elif subject.control_form and subject.control_form.name == 'зачёт':
                    grade_value = 'Зачтено' if last_grade.is_passed else 'Не зачтено'
                else:
                    grade_value = last_grade.score if last_grade.score else last_grade.is_passed
            else:
                grade_value = '—'
            grades_dict[subject.id] = grade_value
        student_data.append({
            'student': student,
            'grades': grades_dict,
        })

    context = {
        'teacher': teacher,
        'group': group,
        'taught_subjects': taught_subjects,
        'student_data': student_data,
        'active_tab': 'groups'
    }
    return render(request, 'unicron_app/teacher_group_detail.html', context)


# ───────────────── Методист (единственные определения) ─────────────────
@login_required
@methodist_required
def methodist_dashboard(request):
    return redirect('unicron_app:methodist_today')


@login_required
@methodist_required
def methodist_today(request):
    today = timezone.now().date()
    now = datetime.now().time()

    if now < datetime.strptime('12:00', '%H:%M').time():
        greeting = 'Доброе утро'
    elif now < datetime.strptime('18:00', '%H:%M').time():
        greeting = 'Добрый день'
    else:
        greeting = 'Добрый вечер'

    schedules = Schedule.objects.filter(
        date=today,
        is_cancelled=False
    ).select_related('group', 'subject', 'teacher').order_by('time_start')

    context = {
        'greeting': greeting,
        'today': today,
        'schedules': schedules,
        'active_tab': 'today'
    }
    return render(request, 'unicron_app/methodist_today.html', context)


@login_required
@methodist_required
def methodist_schedule_week(request):
    """Расписание с навигацией по неделям."""
    today = timezone.now().date()
    try:
        week_offset = int(request.GET.get('week_offset', '0'))
    except ValueError:
        week_offset = 0

    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    days = [monday + timedelta(days=i) for i in range(5)]

    schedules = Schedule.objects.filter(
        date__range=[monday, monday + timedelta(days=6)],
        is_cancelled=False
    ).select_related('group', 'subject', 'teacher').order_by('date', 'time_start')

    week_data = {day: schedules.filter(date=day) for day in days}
    has_schedule = schedules.exists()

    context = {
        'days': days,
        'week_data': week_data,
        'monday': monday,
        'week_offset': week_offset,
        'has_schedule': has_schedule,
        'active_tab': 'schedule'
    }
    return render(request, 'unicron_app/methodist_schedule_week.html', context)


@login_required
@methodist_required
def methodist_generate_schedule(request):
    """Генерация расписания на выбранную неделю по образу предыдущей."""
    if request.method != 'POST':
        return redirect('unicron_app:methodist_schedule_week')

    try:
        week_offset = int(request.POST.get('week_offset', '0'))
    except ValueError:
        messages.error(request, 'Некорректный параметр недели.')
        return redirect('unicron_app:methodist_schedule_week')

    confirm = request.POST.get('confirm') == 'yes'

    today = timezone.now().date()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)

    existing = Schedule.objects.filter(
        date__range=[monday, monday + timedelta(days=6)]
    ).exists()

    if existing and not confirm:
        messages.warning(request, 'Подтвердите действие.')
        return redirect(f'{reverse("unicron_app:methodist_schedule_week")}?week_offset={week_offset}')

    previous_monday = monday - timedelta(weeks=1)
    previous_schedules = Schedule.objects.filter(
        date__range=[previous_monday, previous_monday + timedelta(days=6)]
    ).select_related('subject', 'teacher', 'group')

    if not previous_schedules.exists():
        messages.warning(request, 'Нет расписания предыдущей недели для копирования.')
        return redirect(f'{reverse("unicron_app:methodist_schedule_week")}?week_offset={week_offset}')

    if existing and confirm:
        Schedule.objects.filter(
            date__range=[monday, monday + timedelta(days=6)]
        ).delete()

    with transaction.atomic():
        for prev in previous_schedules:
            new_date = prev.date + timedelta(weeks=1)
            teacher = prev.teacher
            new_schedule = Schedule(
                group=prev.group,
                subject=prev.subject,
                teacher=teacher,
                date=new_date,
                time_start=prev.time_start,
                time_end=prev.time_end,
                format=prev.format,
                classroom=prev.classroom,
                video_link=prev.video_link,
                is_cancelled=False
            )
            try:
                new_schedule.save()
            except ValidationError:
                if teacher is None:
                    continue
                alternative_teachers = Teacher.objects.filter(
                    curriculum_entries__group=prev.group,
                    curriculum_entries__subject=prev.subject
                ).exclude(user_id=teacher.user_id)
                assigned = False
                for alt in alternative_teachers:
                    new_schedule.teacher = alt
                    try:
                        new_schedule.save()
                        assigned = True
                        break
                    except ValidationError:
                        continue
                if not assigned:
                    new_schedule.teacher = None
                    try:
                        new_schedule.save()
                    except ValidationError:
                        continue

    messages.success(request, 'Расписание сформировано.')
    return redirect(f'{reverse("unicron_app:methodist_schedule_week")}?week_offset={week_offset}')


@login_required
@methodist_required
def methodist_schedule_day(request, year, month, day):
    """Детализация расписания на конкретный день."""
    try:
        date = datetime(year, month, day).date()
    except ValueError:
        raise Http404("Неверная дата")

    schedules = Schedule.objects.filter(
        date=date,
        is_cancelled=False
    ).select_related('group', 'subject', 'teacher').order_by('time_start')

    context = {
        'date': date,
        'schedules': schedules,
        'active_tab': 'schedule'
    }
    return render(request, 'unicron_app/methodist_schedule_day.html', context)


@login_required
@methodist_required
def methodist_groups(request):
    """Список всех групп."""
    groups = Group.objects.all().select_related('direction').order_by('title')

    context = {
        'groups': groups,
        'active_tab': 'groups'
    }
    return render(request, 'unicron_app/methodist_groups.html', context)


@login_required
@methodist_required
def methodist_group_detail(request, group_id):
    """Детальная информация о группе: студенты, учебный план."""
    group = get_object_or_404(Group, pk=group_id)
    students = group.students.all()
    curriculums = Curriculum.objects.filter(group=group).select_related('subject', 'teacher')

    context = {
        'group': group,
        'students': students,
        'curriculums': curriculums,
        'active_tab': 'groups'
    }
    return render(request, 'unicron_app/methodist_group_detail.html', context)


# ───────────────── Администратор и общие ─────────────────
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


# ───────────────── Расписание (общий раздел) ─────────────────
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
        form = GradeForm()
        form.fields['group'].queryset = Group.objects.filter(curriculum_entries__teacher=teacher)
        form.fields['subject'].queryset = Subject.objects.filter(curriculum_entries__teacher=teacher)
    return render(request, 'unicron_app/grade_form.html', {'form': form})


def student_grades(request, student_id):
    group_id = request.GET.get('group')
    subject_id = request.GET.get('subject')

    if student_id == 0:
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
    html_string = template.render({'groups': groups})

    config = pdfkit.configuration()
    if hasattr(settings, 'WKHTMLTOPDF_PATH'):
        config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH)

    options = {
        'encoding': 'UTF-8',
        'enable-local-file-access': None,
    }
    pdf = pdfkit.from_string(html_string, False, options=options, configuration=config)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
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