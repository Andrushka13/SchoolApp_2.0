# unicron_app/context_processors.py
from datetime import datetime


def user_greeting(request):
    """
    Добавляет в контекст шаблона приветствие и сегодняшнюю дату.
    """
    context = {
        'greeting': '',
        'today': None,
    }

    if request.user.is_authenticated:
        now = datetime.now()
        today = now.date()
        current_time = now.time()

        # Определение времени суток
        if current_time < datetime.strptime('12:00', '%H:%M').time():
            greeting = 'Доброе утро'
        elif current_time < datetime.strptime('18:00', '%H:%M').time():
            greeting = 'Добрый день'
        else:
            greeting = 'Добрый вечер'

        # Формируем имя пользователя
        user = request.user
        if user.first_name and user.last_name:
            # Если есть имя и фамилия
            name = f"{user.first_name} {user.last_name}"
        elif user.first_name:
            name = user.first_name
        else:
            name = user.username  # fallback

        greeting = f"{greeting}, {name}!"

        context = {
            'greeting': greeting,
            'today': today,
        }

    return context