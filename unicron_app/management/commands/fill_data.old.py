# unicron_app/management/commands/fill_data.py
import datetime
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from unicron_app.models import (
    User, Position, ControlForm,
    Direction, Group, Student, Teacher, Subject,
    Curriculum, Schedule, Attendance, Grade
)

class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными для демонстрации'

    def handle(self, *args, **options):
        # Очистка (осторожно: удаляет все данные из таблиц)
        self.stdout.write('Очистка старых данных...')
        # Удаляем объекты в порядке обратных зависимостей
        Grade.objects.all().delete()
        Attendance.objects.all().delete()
        Schedule.objects.all().delete()
        Curriculum.objects.all().delete()
        Student.objects.filter().delete()
        Teacher.objects.filter().delete()
        Group.objects.all().delete()
        Subject.objects.all().delete()
        Direction.objects.all().delete()
        Position.objects.all().delete()
        ControlForm.objects.all().delete()
        User.objects.all().delete() # не трогаем суперпользователя, если есть

        # 1. Создание справочников
        self.stdout.write('Создание справочников...')
        pos_prepod = Position.objects.create(title='преподаватель')
        pos_star_prepod = Position.objects.create(title='старший преподаватель')

        cf_zachet = ControlForm.objects.create(name='зачёт')
        cf_exam = ControlForm.objects.create(name='экзамен')

        # 2. Создание пользователей и ролей
        self.stdout.write('Создание пользователей...')
        default_password = 'password_1'

        # 2.1. Администратор (1) и руководитель (1), методист (1)
        admin_user = User.objects.create_user(
            username='admin', password=default_password, role='admin',
            email='admin@unicron.ru',
            is_staff=True,
            is_superuser=True
        )
        head_user = User.objects.create_user(
            username='head', password=default_password, role='head',
            email='head@unicron.ru',
            is_staff=True,
            is_superuser=True
        )
        methodist_user = User.objects.create_user(
            username='methodist', password=default_password, role='methodist',
            email='methodist@unicron.ru',
            is_staff=True,
        )

        # 2.2. Преподаватели (10 человек)
        teachers = []
        specializations = [
            'Python', 'Java', 'C++', 'Web-разработка', 'Базы данных',
            'Сетевые технологии', 'Информационная безопасность', 'DevOps',
            'Машинное обучение', 'Мобильная разработка'
        ]
        for i in range(1, 11):
            username = f'teacher{i}'
            last_name = f'Преподавателев{i}'
            first_name = f'Иван{i}'
            user = User.objects.create_user(
                username=username, password=default_password, role='teacher',
                email=f'{username}@unicron.ru'
            )
            # Выбираем должность: преподаватель или старший преподаватель
            position = pos_prepod if i <= 7 else pos_star_prepod  # 7 обычных, 3 старших
            teacher = Teacher.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                middle_name=f'Отчество{i}',
                birth_date=datetime.date(1980 + i, 1, 15),
                phone=f'+7900111220{i:02d}',
                email=user.email,
                specialization=specializations[(i-1) % len(specializations)],
                max_weekly_hours=40 if position == pos_star_prepod else 36,
                hire_date=datetime.date(2024, 9, 1),
                position=position,
                status='active'
            )
            teachers.append(teacher)

        # 2.3. Ученики (30 человек)
        students = []
        for i in range(1, 31):
            username = f'student{i}'
            last_name = f'Учеников{i}'
            first_name = f'Алексей{i}' if i % 2 == 0 else f'Мария{i}'
            user = User.objects.create_user(
                username=username, password=default_password, role='student',
                email=f'{username}@unicron.ru'
            )
            student = Student.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                middle_name=f'Отчество{i}',
                birth_date=datetime.date(2000, 1, 1) + datetime.timedelta(days=i*10),
                phone=f'+7900555123{i:02d}',
                email=user.email,
                status='studying',
                date_enrolled=datetime.date(2025, 9, 1),
                group=None  # назначим позже
            )
            students.append(student)

        # 3. Направления обучения (5)
        self.stdout.write('Создание направлений...')
        directions = []
        dir_names = [
            'Веб-разработка на Python',
            'Мобильная разработка',
            'Data Science и аналитика',
            'Кибербезопасность',
            'Системное администрирование и DevOps'
        ]
        for name in dir_names:
            d = Direction.objects.create(
                title=name,
                description=f'Направление обучения: {name}',
                is_open=True
            )
            directions.append(d)

        # 4. Предметы (10)
        self.stdout.write('Создание предметов...')
        subjects = []
        subj_data = [
            {'title': 'Основы Python', 'hours': 72, 'control': cf_zachet, 'desc': 'Введение в Python'},
            {'title': 'Веб-фреймворк Django', 'hours': 90, 'control': cf_exam, 'desc': 'Разработка на Django'},
            {'title': 'Базы данных PostgreSQL', 'hours': 80, 'control': cf_exam, 'desc': 'Реляционные БД'},
            {'title': 'Java для Android', 'hours': 85, 'control': cf_exam, 'desc': 'Разработка под Android'},
            {'title': 'Swift и iOS', 'hours': 70, 'control': cf_zachet, 'desc': 'Разработка под iOS'},
            {'title': 'Машинное обучение', 'hours': 100, 'control': cf_exam, 'desc': 'ML и нейросети'},
            {'title': 'Сетевые технологии', 'hours': 60, 'control': cf_zachet, 'desc': 'Основы сетей'},
            {'title': 'Информационная безопасность', 'hours': 75, 'control': cf_exam, 'desc': 'Защита информации'},
            {'title': 'Linux и DevOps', 'hours': 90, 'control': cf_zachet, 'desc': 'Администрирование Linux'},
            {'title': 'Проектирование ПО', 'hours': 65, 'control': cf_zachet, 'desc': 'UML, паттерны'},
        ]
        for sd in subj_data:
            s = Subject.objects.create(
                title=sd['title'],
                hours=sd['hours'],
                description=sd['desc'],
                control_form=sd['control']
            )
            subjects.append(s)

        # Связываем предметы с направлениями (каждый предмет с релевантными направлениями)
        # Определим вручную соответствие
        mapping = {
            directions[0]: [subjects[0], subjects[1], subjects[9]],  # Веб
            directions[1]: [subjects[3], subjects[4], subjects[2], subjects[9]],  # Мобильная
            directions[2]: [subjects[5], subjects[0], subjects[2]],  # Data Science
            directions[3]: [subjects[7], subjects[6], subjects[2]],  # Кибербезопасность
            directions[4]: [subjects[8], subjects[6], subjects[2], subjects[9]],  # DevOps
        }
        for direction, subj_list in mapping.items():
            direction.subjects.add(*subj_list)

        self.stdout.write('Предметы привязаны к направлениям.')

        # 5. Группы (3)
        self.stdout.write('Создание групп...')
        groups = []
        # Группа 1: Очная, направление "Веб-разработка на Python"
        g1 = Group.objects.create(
            title='Веб-2025/1',
            direction=directions[0],
            form='full_time',
            date_start=datetime.date(2025, 9, 1),
            date_end=datetime.date(2026, 6, 30),
            status='studying'
        )
        # Группа 2: Дистанционная, направление "Data Science и аналитика"
        g2 = Group.objects.create(
            title='Data-2025/Д',
            direction=directions[2],
            form='distance',
            date_start=datetime.date(2025, 9, 1),
            date_end=datetime.date(2026, 6, 30),
            status='studying'
        )
        # Группа 3: Очная, направление "Кибербезопасность"
        g3 = Group.objects.create(
            title='Безопасность-2025/1',
            direction=directions[3],
            form='full_time',
            date_start=datetime.date(2025, 9, 1),
            date_end=datetime.date(2026, 6, 30),
            status='studying'
        )
        groups = [g1, g2, g3]

        # Распределение студентов по группам (по 10 в каждую)
        for i, student in enumerate(students):
            if i < 10:
                student.group = g1
            elif i < 20:
                student.group = g2
            else:
                student.group = g3
            student.save()

        # 6. Учебный план (Curriculum) — по несколько предметов на группу
        self.stdout.write('Формирование учебного плана...')
        # Назначаем преподавателей на предметы в группах
        # Для простоты распределим преподавателей по циклу
        teacher_cycle = teachers * 2  # чтобы хватило
        for group in groups:
            # определим предметы, соответствующие направлению группы
            dir_subjects = list(group.direction.subjects.all())
            # выберем до 6 предметов
            for idx, subj in enumerate(dir_subjects[:6]):
                teacher = teacher_cycle[idx % len(teachers)]
                Curriculum.objects.create(
                    group=group,
                    subject=subj,
                    teacher=teacher
                )

        # 7. Расписание занятий на ближайшую неделю
        self.stdout.write('Создание расписания...')
        today = timezone.now().date()
        weekday = today.weekday()  # 0-пн
        # Начнём с понедельника этой недели
        monday = today - datetime.timedelta(days=weekday)
        times = [
            ('09:00', '10:30'),
            ('10:45', '12:15'),
            ('13:00', '14:30'),
        ]
        # Для каждой группы закрепим временной слот: 
        group_times = {
            groups[0]: times[0],  # 9:00-10:30
            groups[1]: times[1],  # 10:45-12:15
            groups[2]: times[2],  # 13:00-14:30
        }

        for group in groups:
            curriculums = Curriculum.objects.filter(group=group)
            time_start_str, time_end_str = group_times[group]
            time_start = datetime.datetime.strptime(time_start_str, '%H:%M').time()
            time_end = datetime.datetime.strptime(time_end_str, '%H:%M').time()
            for day_offset in range(5):
                date = monday + datetime.timedelta(days=day_offset)
                if date < today:
                    continue
                curriculum = curriculums[day_offset % len(curriculums)]
                Schedule.objects.create(
                    group=group,
                    subject=curriculum.subject,
                    teacher=curriculum.teacher,
                    date=date,
                    time_start=time_start,
                    time_end=time_end,
                    format='offline' if group.form == 'full_time' else 'online',
                    classroom=f'Ауд. 101' if group.form == 'full_time' else '',
                    video_link='https://meet.unicron.ru/123' if group.form == 'distance' else '',
                    is_cancelled=False
                )

        # 8. Оценки и посещаемость (несколько записей)
        self.stdout.write('Создание оценок и посещаемости...')
        # Для каждого студента по паре предметов поставим текущие оценки
        for student in students:
            group = student.group
            curriculums = Curriculum.objects.filter(group=group)[:2]  # два предмета
            for curriculum in curriculums:
                # текущая оценка
                Grade.objects.create(
                    student=student,
                    subject=curriculum.subject,
                    group=group,
                    control_type='current',
                    date=today - datetime.timedelta(days=10),
                    score=random.randint(3, 5)
                )
                # итоговая (не у всех)
                if student.pk % 3 == 0:
                    Grade.objects.create(
                        student=student,
                        subject=curriculum.subject,
                        group=group,
                        control_type='final',
                        date=today - datetime.timedelta(days=2),
                        score=random.randint(3, 5)
                    )
            # Посещаемость: отметим последнее занятие
            last_schedule = Schedule.objects.filter(group=group).order_by('-date').first()
            if last_schedule:
                Attendance.objects.create(
                    schedule=last_schedule,
                    student=student,
                    group=group,
                    subject=last_schedule.subject,
                    date=last_schedule.date,
                    is_present=random.choice([True, True, False])  # чаще True
                )

        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена!'))
        self.stdout.write(f'Пользователи созданы, пароль у всех: {default_password}')