# emp/apps.py
from django.apps import AppConfig


class EmpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'emp'

    def ready(self):
        import emp.signals  # registers signals
