import os
from celery import Celery

# Устанавливаем настройки Django для Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создаем экземпляр приложения Celery.
# 'config' — это имя корневого модуля проекта.
app = Celery('config')

# Используем настройки Django: все конфигурации Celery должны начинаться с префикса CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматический поиск задач в файлах tasks.py внутри каждого приложения, указанного в INSTALLED_APPS
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')