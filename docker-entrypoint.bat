@echo off
REM SPDX-FileCopyrightText: 2025-present Tobias Kunze
REM SPDX-License-Identifier: Apache-2.0

setlocal enabledelayedexpansion

REM Wait for database to be ready
echo Waiting for PostgreSQL...
if not defined DB_HOST set DB_HOST=db
if not defined DB_PORT set DB_PORT=5432
if not defined DB_USER set DB_USER=imanage

:wait_for_db
pg_isready -h %DB_HOST% -p %DB_PORT% -U %DB_USER% >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 1 /nobreak >nul
    goto :wait_for_db
)
echo PostgreSQL is ready!

REM Run migrations
echo Running database migrations...
cd /app/src
python manage.py migrate --noinput

REM Create superuser if environment variables are set
if defined DJANGO_SUPERUSER_USERNAME (
    if defined DJANGO_SUPERUSER_PASSWORD (
        if defined DJANGO_SUPERUSER_EMAIL (
            echo Creating superuser...
            python manage.py shell --unsafe-disable-scopes < superuser_create.py
        )
    )
)

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput --clear 2>&1
if %errorlevel% neq 0 (
    echo Warning: Static collection failed. This is expected if frontend assets haven't been built yet.
)

REM Start the Django development server
echo Starting Django development server on 0.0.0.0:8000...
python manage.py runserver 0.0.0.0:8000

endlocal
