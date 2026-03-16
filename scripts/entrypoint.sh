#!/bin/bash
set -e

# Django Application Startup Script
# Runs migrations, collects static files, and starts application

echo "Starting Django application..."

# Load environment
export PYTHONUNBUFFERED=1

# Step 1: Wait for database connection
echo "Waiting for database..."
until python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection
connection.ensure_connection()
print('Database connected!')
" 2>/dev/null; do
  echo "Database not ready, waiting..."
  sleep 2
done

# Step 2: Ensure required PostgreSQL extensions exist
echo "Ensuring PostgreSQL extensions..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('CREATE EXTENSION IF NOT EXISTS citext;')
print('PostgreSQL extensions ready!')
"

# Step 3: Run migrations
echo "Running database migrations..."
python manage.py migrate --no-input

# Step 4: Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Step 5: Create cache table (if using database cache)
echo "Setting up cache table..."
python manage.py createcachetable 2>/dev/null || true

# Step 6: Start application
echo "Starting Gunicorn..."
exec gunicorn \
  -c docker/gunicorn.conf.py \
  config.asgi:application
