from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

# Create your models here.
# Вспомогательные справочники
class Position(models.Model):
    """Должность преподавателя"""
    title = models.CharField(max_length=100, unique=True, verbose_name="Название должности")
    
    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"
    
    def __str__(self):
        return self.title
    
    
class ControlForm(models.Model):
    """Форма итогового контроля"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Форма контроля")
    
    class Meta:
        verbose_name = "Форма итогового контроля"
        verbose_name_plural = "Формы итогового контроля"
    
    def __str__(self):
        return self.name
    
    
    # Пользователи и роли

class User(AbstractUser):
    """
    Кастомная модель пользователя.
    Роль определяет доступ к разделам системы.
    """
    class Role(models.TextChoices):
        STUDENT = 'student', 'Ученик'
        TEACHER = 'teacher', 'Учитель'
        ADMIN = 'admin', 'Администратор'
        HEAD = 'head', 'Руководитель'
        METHODIST = 'methodist', 'Методист'
    
    role = models.CharField(max_length=20, choices=Role.choices, verbose_name="Роль в системе")
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


    # Основные объекты
class Direction(models.Model):
    """Направление обучения"""
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_open = models.BooleanField(default=True, verbose_name="Статус (открыто)")
    
    class Meta:
        verbose_name = 'Направление обучения'
        verbose_name_plural = 'Направления обучения'

    def __str__(self):
        return self.title


class Group(models.Model):
    """Учебная группа"""
    FORM_CHOICES = [
        ('full_time', 'Очная'),
        ('distance', 'Дистанционная'),
    ]
    
    STATUS_CHOICES = [
        ('forming', 'Формируется'),
        ('studying', 'Обучается'),
        ('graduated', 'Выпущена'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Название группы")
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE, related_name='groups', verbose_name="Направление")
    study_form = models.CharField(max_length=20, choices=FORM_CHOICES, verbose_name="Форма обучения")
    date_start = models.DateField(verbose_name="Дата начала обучения")
    date_finish = models.DateField(verbose_name="Дата окончания обучения")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='forming', verbose_name="Статус")
    
    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
    
    def __str__(self):
        return self.title
    
    def clean(self):
        """Проверка максимального количества учеников в группе"""
        max_students = 12 if self.study_form == 'full_time' else 15
        if self.pk and self.students.count() > max_students:
            raise ValidationError(f"Максимальное количество учеников в группе: {max_students}. Нельзя набрать больше. Требуется сформировать новую группу.")
        
        def save(self, *args, **kwargs):
            self.full_clean()
            super().save(*args, **kwargs)


class Student(models.Model):
    """Ученик, зачисленный на обучение"""
    STATUS_CHOICES = [
        ('studying', 'Обучается'),
        ('dismissed', 'Отчислен'),
        ('graduated', 'Выпущен'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='student_profile')
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    birth_date = models.DateField(verbose_name="Дата рождения")
    phone = models.CharField(max_length=20, unique=True, verbose_name="Номер телефона")
    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    photo = models.ImageField(upload_to='student_photos', blank=True, null=True, verbose_name="Фотография")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, verbose_name="Группа")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='studying', verbose_name="Статус обучения")
    date_enrolled = models.DateField(default=timezone.now, verbose_name="Дата зачисления")
        
    class Meta:
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"
    
    
class Teacher(models.Model):
    """Преподаватель"""
    STATUS_CHOICES = [
        ('active', 'Работает'),
        ('fired', 'Уволен'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='teacher_profile')
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    birth_date = models.DateField(verbose_name="Дата рождения")
    phone = models.CharField(max_length=20, unique=True, verbose_name="Номер телефона")
    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    specialization = models.CharField(max_length=200, verbose_name="Специализация")
    max_weekly_hours = models.PositiveIntegerField(default=36, verbose_name="Максимальная нагрузка (часов в неделю)")
    hire_date = models.DateField(verbose_name="Дата приёма на работу")
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, verbose_name="Должность")
    photo = models.ImageField(upload_to='student_photos', blank=True, null=True, verbose_name="Фотография")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='studying', verbose_name="Статус")
        
    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"
    
    
class Subject(models.Model):
    """Учебный предмет"""
    title = models.CharField(max_length=200, verbose_name="Название предмета")
    hours = models.PositiveIntegerField(verbose_name="Количество часов")
    description = models.TextField(blank=True, verbose_name="Описание")
    control_form = models.ForeignKey(ControlForm, on_delete=models.SET_NULL, null=True, verbose_name="Форма итогового контроля")
    directions = models.ManyToManyField(Direction, related_name='subjects', verbose_name="Направления")
    
    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
    
    def __str__(self):
        return self.title


class Curriculum(models.Model):
    """
    Учебный план группы. Связывает группу, предмет, преподавателя. определяет, какой преподаватель ведёт предмет в конкретной группе.
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='curriculum_entries', verbose_name="Группа")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='curriculum_entries', verbose_name="Предмет")
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='curriculum_entries', verbose_name="Преподаватель")
    
    class Meta:
        verbose_name = 'Учебный план'
        verbose_name_plural = 'Учебные планы'
        unique_together = [['group', 'subject']] # в одной группе предмет не дублируется
    
    def __str__(self):
        return f"{self.group} - {self.subject} ({self.teacher or 'Не назначено'})"


class Schedule(models.Model):
    """Расписание занятий"""
    FORMAT_CHOICES = [
        ('offline', 'Очно'),
        ('online', 'Дистанционно'),
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='Schedules', verbose_name="Группа")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Преподаватель")
    date = models.DateField(verbose_name="Дата проведения")
    time_start = models.TimeField(verbose_name="Время начала")
    time_end = models.TimeField(verbose_name="Время завершения")
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, verbose_name="Формат обучения")
    classroom = models.CharField(max_length=20, blank=True, null=True, verbose_name="Аудитория")
    video_link = models.URLField(blank=True, null=True, verbose_name="Ссылка на видеоконференцию")
    is_camcelled = models.BooleanField(default=False, verbose_name="Отменено")
    change_reason = models.TextField(blank=True, verbose_name="Причина изменения")
    
    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписание"
        ordering = ['date', 'time_start']
    
    def __str__(self):
        return f"{self.date} {self.time_start}-{self.time_end} {self.group}"

    def clean(self):
        """Проверка конфликтов и нагрузки преподавателя при сохранении"""
        # конфликт преподавателя
        if self.teacher:
            conflict = Schedule.objects.filter(
                teacher = self.teacher,
                date = self.date,
                time_start__lt = self.time_end,
                time_end__gt = self.time_start
            ).exclude(pk=self.pk)
            if conflict.exists():
                raise ValidationError("Преподаватель занят в это время!")
        # Кофликт аудитории
        if self.format == 'offline' and self.classroom:
            room_conflict = Schedule.objects.filter(
                classroom = self.classroom,
                date = self.date,
                time_start__lt = self.time_end,
                time_end__gt = self.time_start
            ).exclude(pk=self.pk)
            if room_conflict.exists():
                raise ValidationError("Аудитория в это время занята")
        # проверка недельной нагрузуи преподавателя
        if self.teacher:
            # Определяем начало и конец недели
            # Неделя начинается с понедельника
            weekday = self.date.weekday() # 0 - пн, 6 - вс
            start_of_week = self.date - timedelta(days=weekday)
            end_of_week = start_of_week + timedelta(days=6)
            weekly_hours = 0
            teacher_schedule = Schedule.objects.filter(
                teacher = self.teacher,
                date__range = [start_of_week, end_of_week]
            ).exclude(pk=self.pk)
            for s in teacher_schedule:
                tdelta = (s.time_end.hour + s.time_end.minute/60) - (s.time_start.hour + s.time_start.minute/60)
                weekly_hours += tdelta
            current_hours = (self.time_end.hour + self.time_end.minute/60) - (self.time_start.hour + self.time_start.minute/60)
            if (weekly_hours + current_hours) > self.teacher.max_weekly_hours:
                raise ValidationError(f"Превышена максимальная недельная нагрузка преподавателя {self.teacher.last_name} ({self.teacher.max_weekly_hours} ч.)")
    
    def save_base(self, *args, **kwargs):
        if self.pk:
            old = Schedule.objects.get(pk=self.pk)
            if old.date != self.date and old.time_start != self.time_start or old.time_end != self.time_end or old.teacher != self.teacher:
                pass
        self.full_clean()
        super.save(*args, **kwargs)
class Attendance(models.Model):
    """Посещаемость – отметка о присутствии на занятии"""
    schedule = models.ForeignKey(Schedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendances', verbose_name="Занятие")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Ученик")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Группа")  # Денормализация для случаев удаления schedule
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    date = models.DateField(verbose_name="Дата занятия")  # Дублируется из schedule, но храним
    is_present = models.BooleanField(default=False, verbose_name="Присутствовал")

    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"
        unique_together = [['schedule', 'student']]  # Одна отметка на пару

    def __str__(self):
        return f"{self.student} - {self.date} - {'Присутствовал' if self.is_present else 'Отсутствовал'}"

class Grade(models.Model):
    """Оценка успеваемости"""
    # Тип контроля
    CURRENT = 'current'
    INTERMEDIATE = 'intermediate'
    FINAL = 'final'
    CONTROL_TYPE_CHOICES = [
        (CURRENT, 'Текущий'),
        (INTERMEDIATE, 'Промежуточный'),
        (FINAL, 'Итоговый'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Ученик")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Группа")
    schedule = models.ForeignKey(Schedule, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Связанное занятие")
    control_type = models.CharField(max_length=20, choices=CONTROL_TYPE_CHOICES, verbose_name="Тип контроля")
    date = models.DateField(verbose_name="Дата выставления")
    # Оценка: 1-5 или "зачет/незачет" – храним в одном поле, но для простоты используем IntegerField
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Балл",
        null=True, blank=True  # null если зачёт/незачёт хранятся иначе
    )
    # Для зачёт/незачёт можно добавить поле
    is_passed = models.BooleanField(null=True, blank=True, verbose_name="Зачёт/незачёт")
    comment = models.TextField(blank=True, verbose_name="Комментарий преподавателя")

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"

    def __str__(self):
        return f"{self.student} - {self.subject} ({self.get_control_type_display()}): {self.score if self.score is not None else 'зачёт/незачёт'}"
