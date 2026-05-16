from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Student, Teacher, Schedule, Grade, Group, Subject, Attendance, User

class StudentApplicationForm(forms.ModelForm):
    """Форма заявки на поступление (регистрирует и студента, и пользователя)"""
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    group = forms.ModelChoiceField(queryset=Group.objects.filter(status=Group.FORMING), label='Желаемая группа')

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'middle_name', 'birth_date', 'phone', 'email', 'photo', 'group']

    def save(self, commit=True):
        # Создаём user
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            role='student'
        )
        student = super().save(commit=False)
        student.user = user
        if commit:
            student.save()
            student.group.students.add(student)   # автоматически через related_name, но у нас ForeignKey
        return student


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time_start': forms.TimeInput(attrs={'type': 'time'}),
            'time_end': forms.TimeInput(attrs={'type': 'time'}),
        }


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'subject', 'group', 'control_type', 'score', 'is_passed', 'comment', 'date']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('score') and cleaned.get('is_passed'):
            raise forms.ValidationError('Выберите что-то одно: балл или зачёт/незачёт.')
        return cleaned


class CustomAuthForm(AuthenticationForm):
    error_messages = {
        'invalid_login': "Неверный логин или пароль",
        'inactive': "Эта запись не активна",
    }
