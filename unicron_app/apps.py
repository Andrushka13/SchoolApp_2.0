from django.apps import AppConfig


class UnicronAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'unicron_app'

    def ready(self):
        import unicron_app.signals
