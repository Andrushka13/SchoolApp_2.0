from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (('Роль', {'fields': ('role',)}),)

@admin.register(Position, ControlForm, Direction)
class SimpleAdmin(admin.ModelAdmin):
    pass

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'direction', 'form', 'status', 'current_students')
    list_filter = ('form', 'status')

    def current_students(self, obj):
        return obj.students.count()
    current_students.short_description = 'Учеников'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone', 'group', 'status')
    list_filter = ('status', 'group')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'specialization', 'max_weekly_hours', 'status')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    filter_horizontal = ('directions',)

@admin.register(Curriculum, Schedule, Attendance, Grade)
class DefaultAdmin(admin.ModelAdmin):
    pass

@admin.register(Secretary)
class SecretaryAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone', 'email')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'floor', 'capacity')
