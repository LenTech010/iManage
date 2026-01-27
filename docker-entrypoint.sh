#!/bin/bash
# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: Apache-2.0

set -e

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-imanage}"; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Run migrations
echo "Running database migrations..."
cd /app/src
python manage.py migrate --noinput

# Create superuser if environment variables are set
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
  echo "Creating superuser..."
  python manage.py shell << 'PYEOF'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
name = os.environ.get('DJANGO_SUPERUSER_USERNAME')

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        password=password,
        name=name
    )
    print("Superuser created successfully")
else:
    print("Superuser already exists")
PYEOF
fi

# Collect static files
echo "Collecting static files..."
if python manage.py collectstatic --noinput --clear 2>&1; then
  echo "Static files collected successfully"
else
  echo "Warning: Static collection failed. This is expected if frontend assets haven't been built yet."
fi

# Start the Django development server
echo "Starting Django development server on 0.0.0.0:8000..."
exec python manage.py runserver 0.0.0.0:8000
