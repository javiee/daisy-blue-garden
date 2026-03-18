# This makes `celery -A config` work without shadowing the celery package
from .celery import app as celery_app

__all__ = ('celery_app',)
