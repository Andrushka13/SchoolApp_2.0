from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Group, Student, Teacher, Schedule, Grade

@receiver(pre_delete, sender=Group)
def handle_group_delete(sender, instance, **kwargs):
    """При удалении группы – студенты открепляются, их статус меняется."""
    for student in instance.students.all():
        student.group = None
        student.status = Student.DISMISSED
        student.save()

@receiver(pre_delete, sender=Teacher)
def handle_teacher_delete(sender, instance, **kwargs):
    """При удалении преподавателя – записи плана и расписания обновляются."""
    # Учебный план – учитель заменяется на "не назначен" (уже SET_NULL)
    # В расписании – занятия не отменяются, но учитель пропадает (SET_NULL)
    pass

@receiver(pre_delete, sender=Student)
def handle_student_delete(sender, instance, **kwargs):
    """Обезличивание персональных данных студента перед удалением."""
    # Можно заменить на анонимного пользователя или очистить поля
    # Здесь сохраним оценки, привязав их к специальному пользователю "Аноним"
    anon_user = User.objects.filter(username='anonymous').first()
    if not anon_user:
        # Создаём один раз
        anon_user = User.objects.create_user(username='anonymous', role='student')
        Student.objects.create(user=anon_user, first_name='Аноним', last_name='', birth_date='2000-01-01', phone='', email='')
    # Переносим оценки и посещаемости на анонима
    Grade.objects.filter(student=instance).update(student=anon_user.student_profile)
    # ... другие связанные записи

@receiver(post_save, sender=Schedule)
def notify_schedule_change(sender, instance, created, **kwargs):
    """Уведомление об изменении/добавлении расписания."""
    if not created:
        # Простая заглушка – выводим в консоль
        print(f"[УВЕДОМЛЕНИЕ] Изменено занятие {instance.group} {instance.date} {instance.time_start}")