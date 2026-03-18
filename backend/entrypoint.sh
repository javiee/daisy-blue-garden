#!/bin/sh
set -e

echo "Waiting for database..."
python -c "
import time, os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()
from django.db import connections
from django.db.utils import OperationalError
for i in range(30):
    try:
        connections['default'].ensure_connection()
        print('Database ready.')
        break
    except OperationalError:
        print(f'Attempt {i+1}/30 - waiting...')
        time.sleep(2)
"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting server..."
exec "$@"
