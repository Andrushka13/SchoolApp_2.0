# unicron_app/signals.py
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import Group, Student, Teacher, Schedule, Grade, Attendance

@receiver(pre_delete, sender=Group)
def handle_group_delete(sender, instance, **kwargs):
    """При удалении группы – студенты открепляются, их статус меняется."""
    for student in instance.students.all():
        student.group = None
        student.status = Student.DISMISSED
        student.save()

@receiver(pre_delete, sender=Teacher)
def handle_teacher_delete(sender, instance, **kwargs):
    """При удалении преподавателя – в учебном плане выставляется NULL автоматически."""
    pass

@receiver(pre_delete, sender=Student)
def handle_student_delete(sender, instance, **kwargs):
    """Заглушка: при удалении студента никаких дополнительных действий не производим."""
    pass

@receiver(post_save, sender=Schedule)
def notify_schedule_change(sender, instance, created, **kwargs):
    """Уведомление об изменении/добавлении расписания."""
    if not created:
        print(f"[УВЕДОМЛЕНИЕ] Изменено занятие {instance.group} {instance.date} {instance.time_start}")