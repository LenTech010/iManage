@echo off
REM SPDX-FileCopyrightText: 2025-present Tobias Kunze
REM SPDX-License-Identifier: Apache-2.0

setlocal enabledelayedexpansion

echo ========================================
echo   iManage Docker Setup Script
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [91mError: Docker is not installed. Please install Docker first.[0m
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% equ 0 (
    set DOCKER_COMPOSE_CMD=docker-compose
) else (
    docker compose version >nul 2>&1
    if %errorlevel% equ 0 (
        set DOCKER_COMPOSE_CMD=docker compose
    ) else (
        echo [91mError: Docker Compose is not installed. Please install Docker Compose first.[0m
        exit /b 1
    )
)

REM Load environment variables from .env file if it exists
if exist .env (
    echo [92m✓ Loading environment variables from .env file[0m
    for /f "usebackq tokens=*" %%a in (".env") do (
        set "line=%%a"
        REM Skip empty lines and comments
        if not "!line!"=="" (
            echo !line! | findstr /r "^#" >nul
            if errorlevel 1 (
                set %%a
            )
        )
    )
) else (
    echo [93m! No .env file found. Using default values.[0m
    echo [93m  You can create a .env file to customize settings.[0m
)

REM Stop and remove existing containers
echo.
echo [94mStopping existing containers...[0m
%DOCKER_COMPOSE_CMD% down 2>nul

REM Build Docker images
echo.
echo [94mBuilding Docker images...[0m
%DOCKER_COMPOSE_CMD% build
if %errorlevel% neq 0 (
    echo [91mError building Docker images[0m
    exit /b 1
)

REM Start services
echo.
echo [94mStarting services...[0m
%DOCKER_COMPOSE_CMD% up -d
if %errorlevel% neq 0 (
    echo [91mError starting services[0m
    exit /b 1
)

REM Wait for services to be ready
echo.
echo [94mWaiting for services to start...[0m
timeout /t 5 /nobreak >nul

REM Check if backend is responding
echo [94mChecking backend health...[0m
set BACKEND_READY=false
for /l %%i in (1,1,30) do (
    curl -s http://localhost:3000 >nul 2>&1
    if !errorlevel! equ 0 (
        echo [92m✓ Backend is ready![0m
        set BACKEND_READY=true
        goto :backend_ready
    )
    timeout /t 2 /nobreak >nul
)

:backend_ready
if "!BACKEND_READY!"=="false" (
    echo [93m========================================[0m
    echo [93m  WARNING: Backend did not start[0m
    echo [93m========================================[0m
    echo.
    echo [93mThe backend service did not respond within 60 seconds.[0m
    echo [93mThis may be normal if it's still starting up.[0m
    echo.
    echo [94mCheck logs with:[0m %DOCKER_COMPOSE_CMD% logs backend
    echo.
    echo [93mPress Ctrl+C to stop, or wait for services to continue starting...[0m
    echo.
)

REM Display status
echo.
echo [92m========================================[0m
echo [92m  Services are up and running![0m
echo [92m========================================[0m
echo.
echo [92mWebsite (Django):[0m    http://localhost:3000
echo [92mDatabase (PostgreSQL):[0m localhost:5432
echo.
echo [94mDefault superuser credentials:[0m
if defined DJANGO_SUPERUSER_USERNAME (
    echo   Username: %DJANGO_SUPERUSER_USERNAME%
) else (
    echo   Username: admin
)
if defined DJANGO_SUPERUSER_PASSWORD (
    echo   Password: %DJANGO_SUPERUSER_PASSWORD%
) else (
    echo   Password: admin
)
if defined DJANGO_SUPERUSER_EMAIL (
    echo   Email:    %DJANGO_SUPERUSER_EMAIL%
) else (
    echo   Email:    admin@localhost
)
echo.
echo [94mUseful commands:[0m
echo   View logs:           %DOCKER_COMPOSE_CMD% logs -f
echo   Stop services:       %DOCKER_COMPOSE_CMD% down
echo   Restart services:    %DOCKER_COMPOSE_CMD% restart
echo   View backend logs:   %DOCKER_COMPOSE_CMD% logs -f backend
echo   View frontend logs:  %DOCKER_COMPOSE_CMD% logs -f frontend
echo   Enter backend shell: %DOCKER_COMPOSE_CMD% exec backend bash
echo.
echo [93m========================================[0m
echo [93m  📝 IMPORTANT: Development Tip[0m
echo [93m========================================[0m
echo [93mAfter making UI/UX changes to Vue files:[0m
echo   [92m✓ DO NOT run run_all.bat again![0m
echo   [92m✓ Just save your files[0m
echo   [92m✓ Refresh your browser (Ctrl+Shift+R)[0m
echo.
echo [93mOnly rebuild when you change:[0m
echo   - package.json (npm dependencies)
echo   - pyproject.toml (Python dependencies)
echo   - Dockerfiles or docker-compose.yml
echo.
echo [94mFor more info, see:[0m DEVELOPMENT_WORKFLOW.md
echo.
echo [92m========================================[0m

endlocal
