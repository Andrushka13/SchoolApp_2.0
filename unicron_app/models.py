# unicron_app/models.py
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


# ──────────────────────────────────────
# Справочники
# ──────────────────────────────────────
class Position(models.Model):
    """Должность преподавателя"""
    title = models.CharField(max_length=100, unique=True, verbose_name="Название")

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"

    def __str__(self):
        return self.title


class ControlForm(models.Model):
    """Форма итогового контроля (зачёт, экзамен)"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Форма контроля")

    class Meta:
        verbose_name = "Форма итогового контроля"
        verbose_name_plural = "Формы итогового контроля"

    def __str__(self):
        return self.name


# ──────────────────────────────────────
# Кастомный пользователь
# ──────────────────────────────────────
class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'student', 'Ученик'
        TEACHER = 'teacher', 'Преподаватель'
        ADMIN = 'admin', 'Администратор'
        HEAD = 'head', 'Руководитель'
        METHODIST = 'methodist', 'Методист'
        SECRETARY = 'secretary', 'Секретарь приёмной комиссии'

    role = models.CharField(max_length=20, choices=Role.choices, verbose_name="Роль")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


# ──────────────────────────────────────
# Основные объекты
# ──────────────────────────────────────
class Direction(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название направления")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_open = models.BooleanField(default=True, verbose_name="Открыто")

    class Meta:
        verbose_name = "Направление обучения"
        verbose_name_plural = "Направления обучения"

    def __str__(self):
        return self.title


class Group(models.Model):
    title = models.CharField(max_length=100, verbose_name="Название группы")
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE, related_name='groups', verbose_name="Направление")

    FULL_TIME = 'full_time'
    DISTANCE = 'distance'
    FORM_CHOICES = [
        (FULL_TIME, 'Очная'),
        (DISTANCE, 'Дистанционная'),
    ]
    form = models.CharField(max_length=20, choices=FORM_CHOICES, verbose_name="Форма обучения")
    date_start = models.DateField(verbose_name="Дата начала")
    date_end = models.DateField(verbose_name="Дата окончания")

    FORMING = 'forming'
    STUDYING = 'studying'
    GRADUATED = 'graduated'
    STATUS_CHOICES = [
        (FORMING, 'Формируется'),
        (STUDYING, 'Обучается'),
        (GRADUATED, 'Выпущена'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=FORMING, verbose_name="Статус")

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.title

    def max_students(self):
        """Возвращает максимально допустимое количество студентов в группе."""
        return 12 if self.form == self.FULL_TIME else 15

    def clean(self):
        # Проверка переполнения выполняется на уровне студента при добавлении,
        # но можно оставить заглушку.
        super().clean()


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='student_profile')
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=50, blank=True, verbose_name="Отчество")
    birth_date = models.DateField(verbose_name="Дата рождения")
    phone = models.CharField(max_length=20, unique=True, verbose_name="Номер телефона")
    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True, verbose_name="Фотография")

    STUDYING = 'studying'
    DISMISSED = 'dismissed'
    GRADUATED = 'graduated'
    STATUS_CHOICES = [
        (STUDYING, 'Обучается'),
        (DISMISSED, 'Отчислен'),
        (GRADUATED, 'Выпущен'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STUDYING, verbose_name="Статус обучения")
    date_enrolled = models.DateField(default=timezone.now, verbose_name="Дата зачисления")

    # Связь: студент принадлежит ровно одной группе
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name="Группа"
    )

    class Meta:
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def clean(self):
        # Проверка уникальности телефона и email уже обеспечивается полем unique=True
        # Проверка заполненности группы
        if self.group and self.group.students.count() >= self.group.max_students():
            raise ValidationError(f"Группа '{self.group.title}' уже заполнена (максимум {self.group.max_students()} человек).")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='teacher_profile')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    birth_date = models.DateField()
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)
    specialization = models.CharField(max_length=200, verbose_name="Специализация")
    max_weekly_hours = models.PositiveIntegerField(default=36, verbose_name="Макс. нагрузка (часов/нед)")
    hire_date = models.DateField(verbose_name="Дата приёма")
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, verbose_name="Должность")

    ACTIVE = 'active'
    FIRED = 'fired'
    STATUS_CHOICES = [(ACTIVE, 'Работает'), (FIRED, 'Уволен')]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ACTIVE)

    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"

    def __str__(self):
        return f"{self.last_name} {self.first_name}"
    

class Secretary(models.Model):
    """Секретарь приёмной комиссии"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='secretary_profile')
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=100, verbose_name="Отчество")
    phone = models.CharField(max_length=20, unique=True, verbose_name="Номер телефона")
    email = models.EmailField(unique=True, verbose_name="Email")
    photo = models.ImageField(upload_to='secretary_photos/', blank=True, null=True, verbose_name="Фотография")
    
    class Meta:
        verbose_name = 'Секретарь'
        verbose_name_plural = 'Секретари'
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"
    


class Subject(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название предмета")
    hours = models.PositiveIntegerField(verbose_name="Количество часов")
    description = models.TextField(blank=True)
    control_form = models.ForeignKey(ControlForm, on_delete=models.SET_NULL, null=True, verbose_name="Форма итогового контроля")
    directions = models.ManyToManyField(Direction, related_name='subjects', verbose_name="Направления")

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"

    def __str__(self):
        return self.title


class Curriculum(models.Model):
    """Учебный план: определяет, какой преподаватель ведёт предмет в группе."""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='curriculum_entries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='curriculum_entries')
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='curriculum_entries')

    class Meta:
        verbose_name = "Учебный план"
        verbose_name_plural = "Учебные планы"
        unique_together = [['group', 'subject']]

    def __str__(self):
        return f"{self.group} - {self.subject} ({self.teacher or 'не назначен'})"


class Schedule(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='schedules')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(verbose_name="Дата")
    time_start = models.TimeField(verbose_name="Начало")
    time_end = models.TimeField(verbose_name="Конец")

    OFFLINE = 'offline'
    ONLINE = 'online'
    FORMAT_CHOICES = [(OFFLINE, 'Очно'), (ONLINE, 'Дистанционно')]
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, verbose_name="Формат")
    classroom = models.CharField(max_length=20, blank=True, null=True, verbose_name="Аудитория")
    video_link = models.URLField(blank=True, null=True, verbose_name="Ссылка на видеоконференцию")
    is_cancelled = models.BooleanField(default=False, verbose_name="Отменено")
    change_reason = models.TextField(blank=True, verbose_name="Причина изменения")

    class Meta:
        verbose_name = "Запись расписания"
        verbose_name_plural = "Расписание"
        ordering = ['date', 'time_start']

    def __str__(self):
        return f"{self.date} {self.time_start}-{self.time_end} {self.group}"

    def clean(self):
        # Проверка конфликтов
        if self.teacher:
            teacher_conflicts = Schedule.objects.filter(
                teacher=self.teacher,
                date=self.date,
                time_start__lt=self.time_end,
                time_end__gt=self.time_start
            ).exclude(pk=self.pk)
            if teacher_conflicts.exists():
                raise ValidationError('Преподаватель уже занят в это время.')
            if self.format == self.OFFLINE and self.classroom:
                room_conflicts = Schedule.objects.filter(
                    classroom=self.classroom,
                    date=self.date,
                    time_start__lt=self.time_end,
                    time_end__gt=self.time_start
                ).exclude(pk=self.pk)
                if room_conflicts.exists():
                    raise ValidationError('Аудитория занята.')
        # Проверка недельной нагрузки
        if self.teacher:
            weekday = self.date.weekday()  # 0=Пн
            week_start = self.date - timedelta(days=weekday)
            week_end = week_start + timedelta(days=6)
            weekly_schedules = Schedule.objects.filter(
                teacher=self.teacher,
                date__range=[week_start, week_end]
            ).exclude(pk=self.pk)
            total_hours = sum(
                (s.time_end.hour + s.time_end.minute/60) - (s.time_start.hour + s.time_start.minute/60)
                for s in weekly_schedules
            )
            current_hours = (self.time_end.hour + self.time_end.minute/60) - (self.time_start.hour + self.time_start.minute/60)
            if total_hours + current_hours > self.teacher.max_weekly_hours:
                raise ValidationError(
                    f'Превышена недельная нагрузка преподавателя (макс. {self.teacher.max_weekly_hours} ч).'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Attendance(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)   # денормализация
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=False, verbose_name="Присутствовал")

    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"
        unique_together = [['schedule', 'student']]   # одна отметка на занятие

    def __str__(self):
        return f"{self.student} - {self.date} {'✓' if self.is_present else '✗'}"


class Grade(models.Model):
    CURRENT = 'current'
    INTERMEDIATE = 'intermediate'
    FINAL = 'final'
    CONTROL_TYPES = [
        (CURRENT, 'Текущий'),
        (INTERMEDIATE, 'Промежуточный'),
        (FINAL, 'Итоговый'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Ученик")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Группа")
    schedule = models.ForeignKey(Schedule, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Связанное занятие")
    control_type = models.CharField(max_length=20, choices=CONTROL_TYPES, verbose_name="Тип контроля")
    date = models.DateField(verbose_name="Дата")
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        verbose_name="Балл"
    )
    is_passed = models.BooleanField(null=True, blank=True, verbose_name="Зачёт/незачёт")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"

    def clean(self):
        # Только одна итоговая оценка по предмету и ученику (если итоговая)
        if self.control_type == self.FINAL and not self.pk:
            if Grade.objects.filter(student=self.student, subject=self.subject, control_type=self.FINAL).exists():
                raise ValidationError("Итоговая оценка по этому предмету уже выставлена. Используйте повторную сдачу с новой датой.")