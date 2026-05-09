# unicron_app/management/commands/fill_data.py
# -*- coding: utf-8 -*-
import datetime
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from unicron_app.models import (
    User, Position, ControlForm,
    Direction, Group, Student, Teacher, Subject,
    Curriculum, Schedule, Attendance, Grade, Secretary
)


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными для демонстрации работы системы'

    def handle(self, *args, **options):
        # 1. Очистка старых данных
        self.stdout.write('Очистка старых данных...')
        # Удаляем в порядке обратных зависимостей
        Grade.objects.all().delete()
        Attendance.objects.all().delete()
        Schedule.objects.all().delete()
        Curriculum.objects.all().delete()
        User.objects.all().delete()          # каскадно удалит Student, Teacher
        Group.objects.all().delete()
        Subject.objects.all().delete()
        Direction.objects.all().delete()
        Position.objects.all().delete()
        ControlForm.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Старые данные удалены.'))

        # 2. Создание справочников
        self.stdout.write('Создание справочников...')
        pos_teacher = Position.objects.create(title='преподаватель')
        pos_senior = Position.objects.create(title='старший преподаватель')
        positions = [pos_teacher, pos_senior]

        cf_zachet = ControlForm.objects.create(name='зачёт')
        cf_exam = ControlForm.objects.create(name='экзамен')
        control_forms = [cf_zachet, cf_exam]

        # 3. Создание пользователей
        self.stdout.write('Создание пользователей...')
        default_password = 'password_1'

        # Администратор, руководитель, методист, секретарь
        admin_user = User.objects.create_user(
            username='admin',
            password=default_password,
            role='admin',
            email='admin@unicron.ru',
            is_staff=True,
            is_superuser=True
        )
        head_user = User.objects.create_user(
            username='head',
            password=default_password,
            role='head',
            email='head@unicron.ru',
        )
        methodist_user = User.objects.create_user(
            username='methodist',
            password=default_password,
            role='methodist',
            email='methodist@unicron.ru',
        )
        secretary_user = User.objects.create_user(
            username='secretary',
            password=default_password,
            role='secretary',
            email='secretary@unicron.ru',
        )
        Secretary.objects.create(
            user=secretary_user,
            first_name='Елена',
            last_name='Ветрова',
            middle_name='Сергеевна',
            phone='+79001234567',
            email=secretary_user.email,
        )

        # Преподаватели (10 человек)
        teachers = []
        specializations = [
            'Python-разработка',
            'Java-разработка',
            'Веб-технологии',
            'Базы данных',
            'Сетевые технологии',
            'Информационная безопасность',
            'DevOps и Linux',
            'Машинное обучение',
            'Мобильная разработка (Android)',
            'Мобильная разработка (iOS)'
        ]
        teacher_names = [
            ('Иван', 'Петров', 'Сергеевич'),
            ('Пётр', 'Сидоров', 'Алексеевич'),
            ('Анна', 'Кузнецова', 'Владимировна'),
            ('Елена', 'Смирнова', 'Игоревна'),
            ('Дмитрий', 'Васильев', 'Петрович'),
            ('Ольга', 'Фёдорова', 'Николаевна'),
            ('Сергей', 'Морозов', 'Андреевич'),
            ('Марина', 'Волкова', 'Дмитриевна'),
            ('Алексей', 'Лебедев', 'Михайлович'),
            ('Татьяна', 'Соколова', 'Павловна'),
        ]

        for i, (first_name, last_name, middle_name) in enumerate(teacher_names):
            username = f'teacher{i+1}'
            position = pos_teacher if i < 7 else pos_senior  # первые 7 — преподаватели, остальные — старшие
            user = User.objects.create_user(
                username=username,
                password=default_password,
                role='teacher',
                email=f'{username}@unicron.ru'
            )
            teacher = Teacher.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                birth_date=datetime.date(1980 + i, (i % 12) + 1, (i % 28) + 1),
                phone=f'+790011122{i:02d}',
                email=user.email,
                specialization=specializations[i],
                max_weekly_hours=40 if position == pos_senior else 36,
                hire_date=datetime.date(2024, 9, 1),
                position=position,
                status='active'
            )
            teachers.append(teacher)

        # Ученики (30 человек)
        students = []
        student_first_names = [
            'Алексей', 'Мария', 'Дмитрий', 'Анна', 'Сергей',
            'Екатерина', 'Николай', 'Юлия', 'Андрей', 'Виктория',
            'Павел', 'Наталья', 'Максим', 'Ирина', 'Артём',
            'Ксения', 'Владимир', 'Дарья', 'Роман', 'Евгения',
            'Игорь', 'Алёна', 'Станислав', 'Валерия', 'Григорий',
            'Полина', 'Константин', 'Анастасия', 'Борис', 'Людмила'
        ]
        student_last_names = [
            'Иванов', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев',
            'Петров', 'Соколов', 'Михайлов', 'Новиков', 'Фёдоров',
            'Морозов', 'Волков', 'Алексеев', 'Лебедев', 'Семёнов',
            'Егоров', 'Павлов', 'Козлов', 'Степанов', 'Николаев',
            'Орлов', 'Андреев', 'Макаров', 'Никитин', 'Захаров',
            'Зайцев', 'Соловьёв', 'Борисов', 'Яковлев', 'Григорьев'
        ]

        for i in range(30):
            username = f'student{i+1}'
            first_name = student_first_names[i]
            last_name = student_last_names[i]
            user = User.objects.create_user(
                username=username,
                password=default_password,
                role='student',
                email=f'{username}@unicron.ru'
            )
            student = Student.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                middle_name='',
                birth_date=datetime.date(2000, 1, 1) + datetime.timedelta(days=i*10),
                phone=f'+7900555123{i:02d}',
                email=user.email,
                status='studying',
                date_enrolled=datetime.date(2025, 9, 1),
                group=None  # назначим позже
            )
            students.append(student)

        # 4. Направления обучения (5)
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

        # 5. Предметы (10)
        self.stdout.write('Создание предметов...')
        subjects = []
        subj_data = [
            {'title': 'Основы Python', 'hours': 72, 'control': cf_zachet, 'desc': 'Введение в программирование на Python'},
            {'title': 'Веб-фреймворк Django', 'hours': 90, 'control': cf_exam, 'desc': 'Разработка веб-приложений на Django'},
            {'title': 'Базы данных PostgreSQL', 'hours': 80, 'control': cf_exam, 'desc': 'Реляционные базы данных и SQL'},
            {'title': 'Java для Android', 'hours': 85, 'control': cf_exam, 'desc': 'Разработка мобильных приложений под Android'},
            {'title': 'Swift и iOS', 'hours': 70, 'control': cf_zachet, 'desc': 'Разработка приложений под iOS'},
            {'title': 'Машинное обучение', 'hours': 100, 'control': cf_exam, 'desc': 'Основы ML, нейросети и анализ данных'},
            {'title': 'Сетевые технологии', 'hours': 60, 'control': cf_zachet, 'desc': 'Основы компьютерных сетей'},
            {'title': 'Информационная безопасность', 'hours': 75, 'control': cf_exam, 'desc': 'Защита информации и кибербезопасность'},
            {'title': 'Linux и DevOps', 'hours': 90, 'control': cf_zachet, 'desc': 'Администрирование Linux и CI/CD'},
            {'title': 'Проектирование ПО', 'hours': 65, 'control': cf_zachet, 'desc': 'UML, паттерны проектирования, архитектура ПО'},
        ]
        for sd in subj_data:
            s = Subject.objects.create(
                title=sd['title'],
                hours=sd['hours'],
                description=sd['desc'],
                control_form=sd['control']
            )
            subjects.append(s)

        # Связываем предметы с направлениями
        self.stdout.write('Привязка предметов к направлениям...')
        mapping = {
            directions[0]: [subjects[0], subjects[1], subjects[2], subjects[9]],      # Веб
            directions[1]: [subjects[3], subjects[4], subjects[2], subjects[9]],      # Мобильная
            directions[2]: [subjects[5], subjects[0], subjects[2], subjects[7]],      # Data Science
            directions[3]: [subjects[7], subjects[6], subjects[2], subjects[5]],      # Кибербезопасность
            directions[4]: [subjects[8], subjects[6], subjects[2], subjects[9]],      # DevOps
        }
        for direction, subj_list in mapping.items():
            direction.subjects.add(*subj_list)

        # 6. Группы (3)
        self.stdout.write('Создание групп...')
        groups = []
        # Группа 1: Очная
        g1 = Group.objects.create(
            title='Веб-2025/1',
            direction=directions[0],
            form='full_time',
            date_start=datetime.date(2025, 9, 1),
            date_end=datetime.date(2026, 6, 30),
            status='studying'
        )
        # Группа 2: Дистанционная
        g2 = Group.objects.create(
            title='Data-2025/Д',
            direction=directions[2],
            form='distance',
            date_start=datetime.date(2025, 9, 1),
            date_end=datetime.date(2026, 6, 30),
            status='studying'
        )
        # Группа 3: Очная
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
        self.stdout.write('Распределение студентов по группам...')
        for i, student in enumerate(students):
            if i < 10:
                student.group = g1
            elif i < 20:
                student.group = g2
            else:
                student.group = g3
            student.save()

        # 7. Учебный план (Curriculum)
        self.stdout.write('Формирование учебного плана...')
        # Назначаем преподавателей на предметы в группах
        teacher_cycle = teachers * 2  # чтобы хватило
        for group in groups:
            dir_subjects = list(group.direction.subjects.all())
            # Берём до 6 предметов
            for idx, subj in enumerate(dir_subjects[:6]):
                teacher = teacher_cycle[idx % len(teachers)]
                Curriculum.objects.create(
                    group=group,
                    subject=subj,
                    teacher=teacher
                )

        # 8. Расписание занятий на ближайшую неделю
        self.stdout.write('Создание расписания...')
        today = timezone.now().date()
        weekday = today.weekday()  # 0-пн, 6-вс
        monday = today - datetime.timedelta(days=weekday)

        # Каждой группе — свой временной слот
        times = [
            ('09:00', '10:30'),
            ('10:45', '12:15'),
            ('13:00', '14:30'),
        ]
        group_times = {
            g1: times[0],  # 9:00-10:30
            g2: times[1],  # 10:45-12:15
            g3: times[2],  # 13:00-14:30
        }

        for group in groups:
            curriculums = Curriculum.objects.filter(group=group)
            if not curriculums.exists():
                continue
            time_start_str, time_end_str = group_times[group]
            time_start = datetime.datetime.strptime(time_start_str, '%H:%M').time()
            time_end = datetime.datetime.strptime(time_end_str, '%H:%M').time()

            # Расписание на 5 дней (Пн-Пт), 2 недели вперёд для разнообразия
            for week_offset in range(2):
                for day_offset in range(5):
                    date = monday + datetime.timedelta(days=day_offset + week_offset * 7)
                    if date < today:
                        continue  # пропускаем прошедшие дни
                    # Выбираем предмет по циклу
                    curric_idx = (day_offset + week_offset * 5) % len(curriculums)
                    curriculum = curriculums[curric_idx]
                    Schedule.objects.create(
                        group=group,
                        subject=curriculum.subject,
                        teacher=curriculum.teacher,
                        date=date,
                        time_start=time_start,
                        time_end=time_end,
                        format='offline' if group.form == 'full_time' else 'online',
                        classroom='Ауд. 101' if group.form == 'full_time' else '',
                        video_link='https://meet.unicron.ru/abc123' if group.form == 'distance' else '',
                        is_cancelled=False
                    )

        # 9. Оценки и посещаемость
        self.stdout.write('Создание оценок и посещаемости...')
        for student in students:
            group = student.group
            if not group:
                continue
            # Берём предметы из учебного плана группы
            curriculums = Curriculum.objects.filter(group=group)[:3]
            for curriculum in curriculums:
                subject = curriculum.subject
                # Текущая оценка
                Grade.objects.create(
                    student=student,
                    subject=subject,
                    group=group,
                    control_type='current',
                    date=today - datetime.timedelta(days=random.randint(1, 30)),
                    score=random.randint(3, 5)
                )
                # Итоговая оценка (не у всех)
                if student.pk % 3 == 0:
                    if subject.control_form and subject.control_form.name == 'экзамен':
                        Grade.objects.create(
                            student=student,
                            subject=subject,
                            group=group,
                            control_type='final',
                            date=today - datetime.timedelta(days=random.randint(1, 10)),
                            score=random.randint(3, 5)
                        )
                    else:
                        Grade.objects.create(
                            student=student,
                            subject=subject,
                            group=group,
                            control_type='final',
                            date=today - datetime.timedelta(days=random.randint(1, 10)),
                            is_passed=random.choice([True, True, False])
                        )

            # Посещаемость: отметим последнее занятие в расписании группы
            last_schedule = Schedule.objects.filter(group=group).order_by('-date', '-time_start').first()
            if last_schedule:
                Attendance.objects.create(
                    schedule=last_schedule,
                    student=student,
                    group=group,
                    subject=last_schedule.subject,
                    date=last_schedule.date,
                    is_present=random.choice([True, True, True, False])  # 75% вероятность присутствия
                )

        # 10. Финальный вывод
        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена!'))
        self.stdout.write(f'Всего создано:')
        self.stdout.write(f'  Пользователей: {User.objects.count()}')
        self.stdout.write(f'  Направлений: {Direction.objects.count()}')
        self.stdout.write(f'  Предметов: {Subject.objects.count()}')
        self.stdout.write(f'  Групп: {Group.objects.count()}')
        self.stdout.write(f'  Студентов: {Student.objects.count()}')
        self.stdout.write(f'  Преподавателей: {Teacher.objects.count()}')
        self.stdout.write(f'  Записей расписания: {Schedule.objects.count()}')
        self.stdout.write(f'  Оценок: {Grade.objects.count()}')
        self.stdout.write(f'  Записей посещаемости: {Attendance.objects.count()}')
        self.stdout.write(f'')
        self.stdout.write(f'  Пароль для всех пользователей: {default_password}')
        self.stdout.write(f'  Логины: admin, head, methodist, teacher1..teacher10, student1..student30')