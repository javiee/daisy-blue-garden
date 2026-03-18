"""Celery app re-export so `celery -A config` works."""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('daisyblue')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
