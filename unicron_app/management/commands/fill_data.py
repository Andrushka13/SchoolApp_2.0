# unicron_app/management/commands/fill_data.py
import datetime
import random
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.utils import timezone
from unicron_app.models import (
    User, Position, ControlForm,
    Direction, Group, Student, Teacher, Subject,
    Curriculum, Schedule, Attendance, Grade, Room
)


class Command(BaseCommand):
    help = 'Заполняет базу демонстрационными данными (300 студентов, 20 преподавателей, очные группы ≤ аудиторий)'

    def handle(self, *args, **options):
        # 1. Очистка
        self.stdout.write('Очистка старых данных...')
        Grade.objects.all().delete()
        Attendance.objects.all().delete()
        Schedule.objects.all().delete()
        Curriculum.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        Subject.objects.all().delete()
        Direction.objects.all().delete()
        Position.objects.all().delete()
        ControlForm.objects.all().delete()
        Room.objects.all().delete()

        # 2. Справочники
        self.stdout.write('Создание справочников...')
        pos_teacher = Position.objects.create(title='преподаватель')
        pos_senior = Position.objects.create(title='старший преподаватель')
        cf_zachet = ControlForm.objects.create(name='зачёт')
        cf_exam = ControlForm.objects.create(name='экзамен')

        # 3. Аудитории (20 шт., 2 этажа по 10)
        self.stdout.write('Создание аудиторий...')
        rooms = []
        for floor in [1, 2]:
            for num in range(1, 11):
                name = f"{floor}{num:02d}"
                room = Room.objects.create(name=name, floor=floor, capacity=random.randint(15, 30))
                rooms.append(room)
        max_offline_groups = len(rooms)  # 20

        # 4. Пользователи
        self.stdout.write('Создание пользователей...')
        pwd = 'password_1'

        User.objects.create_user(username='admin', password=pwd, role='admin',
                                 email='admin@unicron.ru', is_staff=True, is_superuser=True)
        User.objects.create_user(username='head', password=pwd, role='head', email='head@unicron.ru')
        User.objects.create_user(username='methodist', password=pwd, role='methodist', email='methodist@unicron.ru')
        User.objects.create_user(username='secretary', password=pwd, role='secretary', email='secretary@unicron.ru')

        # 20 преподавателей
        teachers = []
        specializations = [
            'Python', 'Java', 'C++', 'Web-разработка', 'Базы данных',
            'Сетевые технологии', 'Информационная безопасность', 'DevOps',
            'Машинное обучение', 'Мобильная разработка'
        ]
        for i in range(1, 21):
            email = f'teacher{i}@unicron.ru'
            u = User.objects.create_user(username=f'teacher{i}', password=pwd, role='teacher', email=email)
            pos = pos_senior if i > 15 else pos_teacher
            spec = specializations[(i - 1) % len(specializations)]
            t = Teacher.objects.create(
                user=u,
                first_name=f'Иван{i}',
                last_name=f'Преподавателев{i}',
                birth_date=datetime.date(1980 + (i % 20), 1, 15),
                phone=f'+7900111220{i:02d}',
                email=email,
                specialization=spec,
                max_weekly_hours=40 if pos == pos_senior else 36,
                hire_date=datetime.date(2024, 9, 1),
                position=pos,
                status='active'
            )
            teachers.append(t)

        # 300 студентов
        students = []
        first_names = ['Алексей', 'Мария', 'Дмитрий', 'Анна', 'Сергей',
                       'Екатерина', 'Николай', 'Юлия', 'Андрей', 'Виктория',
                       'Павел', 'Наталья', 'Максим', 'Ирина', 'Артём']
        last_names = ['Иванов', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев',
                      'Петров', 'Соколов', 'Михайлов', 'Новиков', 'Фёдоров',
                      'Морозов', 'Волков', 'Алексеев', 'Лебедев', 'Семёнов']
        for i in range(300):
            username = f'student{i + 1}'
            email = f'{username}@unicron.ru'
            phone = f'+7900{1000001 + i}'
            u = User.objects.create_user(username=username, password=pwd, role='student', email=email)
            s = Student.objects.create(
                user=u,
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                birth_date=datetime.date(2000, 1, 1) + datetime.timedelta(days=random.randint(1, 3650)),
                phone=phone,
                email=email,
                status='studying',
                date_enrolled=datetime.date(2025, 9, 1),
                group=None
            )
            students.append(s)

        # 5. Направления и предметы
        dir_names = [
            'Веб-разработка на Python',
            'Мобильная разработка',
            'Data Science и аналитика',
            'Кибербезопасность',
            'Системное администрирование и DevOps'
        ]
        directions = [Direction.objects.create(title=name, is_open=True) for name in dir_names]

        subjects = []
        subj_data = [
            ('Основы Python', 72, cf_zachet),
            ('Веб-фреймворк Django', 90, cf_exam),
            ('Базы данных PostgreSQL', 80, cf_exam),
            ('Java для Android', 85, cf_exam),
            ('Swift и iOS', 70, cf_zachet),
            ('Машинное обучение', 100, cf_exam),
            ('Сетевые технологии', 60, cf_zachet),
            ('Информационная безопасность', 75, cf_exam),
            ('Linux и DevOps', 90, cf_zachet),
            ('Проектирование ПО', 65, cf_zachet),
        ]
        for title, hours, control in subj_data:
            s = Subject.objects.create(title=title, hours=hours, control_form=control)
            subjects.append(s)

        mapping = {
            directions[0]: [0, 1, 2, 9],
            directions[1]: [3, 4, 2, 9],
            directions[2]: [5, 0, 2, 7],
            directions[3]: [7, 6, 2, 5],
            directions[4]: [8, 6, 2, 9],
        }
        for d, indexes in mapping.items():
            d.subjects.add(*[subjects[i] for i in indexes])

        # 6. Группы и распределение студентов с учётом аудиторного фонда
        self.stdout.write('Создание групп и распределение студентов...')
        groups = []
        random.shuffle(students)

        # Счётчики очных групп
        offline_group_counter = 0
        # Словарь для хранения последней группы: direction_id -> {'full_time': Group, 'distance': Group}
        last_group = defaultdict(lambda: {'full_time': None, 'distance': None})

        for student in students:
            direction = random.choice(directions)
            # Определяем форму: очная, только если есть ещё квоты на группы
            if offline_group_counter < max_offline_groups:
                form = random.choice(['full_time', 'distance'])
            else:
                form = 'distance'

            limit = 12 if form == 'full_time' else 15
            # Получаем последнюю группу для данного направления и формы
            last = last_group[direction.id][form]
            if last and last.students.count() < limit:
                candidate = last
            else:
                # Создаём новую группу
                if form == 'full_time':
                    offline_group_counter += 1
                idx = len([g for g in groups if g.form == form and g.direction_id == direction.id]) + 1
                candidate = Group.objects.create(
                    title=f'{direction.title[:20]}-{form[:4]}-{idx}',
                    direction=direction,
                    form=form,
                    date_start=datetime.date(2025, 9, 1),
                    date_end=datetime.date(2026, 6, 30),
                    status='studying'
                )
                groups.append(candidate)
                last_group[direction.id][form] = candidate
            student.group = candidate
            student.save()

        # Активируем статус всем группам
        for g in groups:
            g.status = 'studying'
            g.save()

        self.stdout.write(f'  Создано {len(groups)} групп (очных: {offline_group_counter})')

        # 7. Учебные планы
        self.stdout.write('Создание учебных планов...')
        teacher_cycle = teachers * 3
        for idx, group in enumerate(groups):
            dir_subjects = list(group.direction.subjects.all())
            for i, subj in enumerate(dir_subjects):
                teacher = teacher_cycle[(idx * len(dir_subjects) + i) % len(teacher_cycle)]
                Curriculum.objects.create(group=group, subject=subj, teacher=teacher)

        # 8. Расписание (синхронизация очных и дистанционных групп)
        self.stdout.write('Создание расписания...')
        today = timezone.now().date()
        monday = today - datetime.timedelta(days=today.weekday())
        time_slots = [
            (datetime.time(9, 0), datetime.time(10, 30)),
            (datetime.time(10, 45), datetime.time(12, 15)),
            (datetime.time(13, 0), datetime.time(14, 30)),
        ]

        # Группируем группы по направлениям
        dir_groups = defaultdict(list)
        for g in groups:
            dir_groups[g.direction_id].append(g)

        schedule_objects = []

        for direction_id, group_list in dir_groups.items():
            offline_groups = [g for g in group_list if g.form == 'full_time']
            online_groups = [g for g in group_list if g.form == 'distance']
            # Учебный план берём из первой группы направления (считаем, что одинаковый)
            sample_curriculums = list(Curriculum.objects.filter(group=group_list[0]))
            if not sample_curriculums:
                continue
            subjects_cycle = [c.subject for c in sample_curriculums]
            teachers_cycle = [c.teacher for c in sample_curriculums]

            # Цикл по дням и слотам
            for week in range(2):
                for day_offset in range(5):
                    date = monday + datetime.timedelta(days=day_offset + week * 7)
                    if date < today:
                        continue
                    for slot_idx, (time_start, time_end) in enumerate(time_slots):
                        # Выбираем предмет и преподавателя
                        item_idx = (day_offset + week * 5 + slot_idx) % len(subjects_cycle)
                        subject = subjects_cycle[item_idx]
                        teacher = teachers_cycle[item_idx] if item_idx < len(teachers_cycle) else random.choice(teachers)

                        # Ищем свободную аудиторию для очных групп
                        classroom = None
                        if offline_groups:
                            occupied_rooms = Schedule.objects.filter(
                                date=date,
                                time_start__lt=time_end,
                                time_end__gt=time_start,
                                classroom__isnull=False
                            ).values_list('classroom_id', flat=True)
                            free_room = Room.objects.exclude(id__in=occupied_rooms).first()
                            if free_room:
                                classroom = free_room

                        # Выбираем одну очную группу для этого занятия (по кругу)
                        offline_group = None
                        if classroom and offline_groups:
                            # Простейший циклический выбор
                            idx = (week * 5 + day_offset + slot_idx) % len(offline_groups)
                            offline_group = offline_groups[idx]

                        # Создаём запись для очной группы (если есть аудитория и группа)
                        if offline_group:
                            schedule_objects.append(Schedule(
                                group=offline_group,
                                subject=subject,
                                teacher=teacher,
                                date=date,
                                time_start=time_start,
                                time_end=time_end,
                                format='offline',
                                classroom=classroom,
                                video_link='',
                                is_cancelled=False
                            ))
                        # Для всех дистанционных групп – онлайн
                        video_link = f'https://meet.unicron.ru/{direction_id}_{date}_{time_start}'
                        for og in online_groups:
                            schedule_objects.append(Schedule(
                                group=og,
                                subject=subject,
                                teacher=teacher,
                                date=date,
                                time_start=time_start,
                                time_end=time_end,
                                format='online',
                                classroom=None,
                                video_link=video_link,
                                is_cancelled=False
                            ))

        # Пакетная вставка всех записей расписания
        Schedule.objects.bulk_create(schedule_objects)
        self.stdout.write(f'  Создано {len(schedule_objects)} записей расписания.')

        # 9. Оценки и посещаемость
        self.stdout.write('Создание оценок и посещаемости...')
        for group in groups:
            curriculums = Curriculum.objects.filter(group=group)
            subjects_of_group = [c.subject for c in curriculums]
            for student in group.students.all():
                for subject in subjects_of_group:
                    if random.random() < 0.8:
                        Grade.objects.create(
                            student=student, subject=subject, group=group,
                            control_type='current',
                            date=today - datetime.timedelta(days=random.randint(1, 30)),
                            score=random.randint(2, 5)
                        )
                    if subject.control_form and subject.control_form.name == 'экзамен':
                        Grade.objects.create(
                            student=student, subject=subject, group=group,
                            control_type='final',
                            date=today - datetime.timedelta(days=random.randint(1, 10)),
                            score=random.randint(2, 5)
                        )
                    else:
                        Grade.objects.create(
                            student=student, subject=subject, group=group,
                            control_type='final',
                            date=today - datetime.timedelta(days=random.randint(1, 10)),
                            is_passed=random.choice([True, True, False])
                        )
                sample_schedule = Schedule.objects.filter(group=group).order_by('?').first()
                if sample_schedule:
                    Attendance.objects.create(
                        schedule=sample_schedule, student=student, group=group,
                        subject=sample_schedule.subject, date=sample_schedule.date,
                        is_present=random.choice([True, True, False])
                    )

        # 10. Итоговая статистика
        self.stdout.write(self.style.SUCCESS(
            f'Готово! Создано: групп {Group.objects.count()}, '
            f'студентов {Student.objects.count()}, преподавателей {Teacher.objects.count()}, '
            f'оценок {Grade.objects.count()}, записей расписания {Schedule.objects.count()}'
        ))