# Quick Start Guide - Research Conference Manager (iManage)

## Overview

This is a fully functional Research Conference Manager application built with Django (backend) and Vue.js (frontend). It handles:

- Conference event creation and management
- Paper submissions (Call for Papers/CFP)
- Review and selection process
- Scheduling and program management
- Speaker and attendee management
- Multi-language support

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 1.29 or higher)
- Web browser for accessing the application

## Quick Start

### 1. Start the Application

```bash
# Clone the repository (if not already done)
git clone https://github.com/LenTech010/iManage.git
cd iManage

# Run the application
./run_all.sh
```

The script will:
- Build Docker images for backend and frontend
- Start PostgreSQL database
- Run database migrations
- Create a superuser account
- Collect static files
- Start all services

### 2. Access the Application

After starting, you can access:

- **Backend (Django Admin/Management)**: http://localhost:8000
- **Frontend (Schedule Editor Dev Server)**: Running on port 3000 (integrated into backend)
- **Database**: PostgreSQL on localhost:5432

### 3. Login Credentials

**Default Superuser:**
- Username: `admin`
- Password: `admin`
- Email: `admin@localhost`

⚠️ **Security Warning**: Change these credentials before using in production!

## Application Features

### Dashboard
- View all your conferences (active, upcoming, past)
- Quick access to create new events
- User profile management
- System settings

### Event/Conference Management
1. **Create New Event**:
   - Go to Dashboard → Click "+" button or "Create a new event"
   - Choose languages (English, German, and many community translations available)
   - Select organiser
   - Configure event details

2. **Event Configuration**:
   - Basic information (name, dates, location)
   - Call for Papers (CFP) settings
   - Review process configuration
   - Schedule management
   - Email templates

### Submission Management
- Configure submission types (talks, workshops, posters, etc.)
- Set submission deadlines
- Define review criteria
- Manage reviewer assignments

### Review Process
- Assign reviewers to submissions
- Track review progress
- Score and comment on submissions
- Make acceptance/rejection decisions

### Schedule Editor
- Drag-and-drop schedule builder
- Multi-track support
- Room assignment
- Speaker conflict detection
- Export options

## Configuration

### Environment Variables

You can customize settings by creating a `.env` file:

```bash
cp .env.example .env
# Edit .env with your preferred settings
```

Available settings:
- `DB_NAME`: Database name (default: imanage)
- `DB_USER`: Database user (default: imanage)
- `DB_PASSWORD`: Database password (default: imanage)
- `DJANGO_SUPERUSER_USERNAME`: Admin username (default: admin)
- `DJANGO_SUPERUSER_PASSWORD`: Admin password (default: admin)
- `DJANGO_SUPERUSER_EMAIL`: Admin email (default: admin@localhost)
- `SITE_URL`: Site URL (default: http://localhost:8000)
- `TIME_ZONE`: Timezone (default: UTC)
- `LANGUAGE_CODE`: Language (default: en)
- `DEBUG`: Debug mode (default: True)

## Useful Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Stop Services

```bash
docker-compose down
```

### Restart Services

```bash
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Access Backend Shell

```bash
docker-compose exec backend bash

# Once inside, run Django management commands
python /app/src/manage.py --help
```

### Access Database

```bash
docker-compose exec db psql -U imanage
```

### Run Django Management Commands

```bash
docker-compose exec backend python /app/src/manage.py <command>

# Examples:
docker-compose exec backend python /app/src/manage.py createsuperuser
docker-compose exec backend python /app/src/manage.py migrate
docker-compose exec backend python /app/src/manage.py collectstatic
```

### Rebuild Containers

If you make changes to Dockerfiles or dependencies:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

Or simply run:
```bash
./run_all.sh
```

## Troubleshooting

### My UI/UX Changes Aren't Showing Up! 🔥

**Most Common Issue**: You just edited Vue files but don't see changes?

**Solution**: You **DO NOT need to run `run_all.sh` again**! The frontend uses hot-reloading:

1. **Save your Vue file** - Changes should appear in 1-2 seconds
2. **Hard refresh your browser**: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
3. **If still not working**:
   ```bash
   # Just restart the frontend service (takes 10 seconds)
   docker-compose restart frontend
   ```

**See detailed guide**: [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) - Complete explanation of when to rebuild vs. when changes auto-reload

### Backend Won't Start

Check logs:
```bash
docker-compose logs backend
```

Common issues:
- Database not ready: Wait a few seconds and check again
- Port 8000 already in use: Stop other services using that port

### Frontend Won't Start

Check logs:
```bash
docker-compose logs frontend
```

Common issues:
- Port 3000 already in use: Stop other services using that port
- npm install failed: Try rebuilding with `docker-compose build --no-cache frontend`

### Database Connection Issues

Ensure database is healthy:
```bash
docker-compose ps
```

Reset database (⚠️ This will delete all data):
```bash
docker-compose down -v
./run_all.sh
```

### SSL Certificate Errors

The Dockerfiles include SSL certificate workarounds for development environments. If you encounter SSL issues in different environments, you may need to adjust:
- `Dockerfile.backend`: pip trusted hosts configuration
- `Dockerfile.frontend`: npm SSL settings

## Development Workflow

### Hot Reloading

Both services support hot reloading:
- **Backend**: Changes in `./src` are automatically detected
- **Frontend**: Changes in `./frontend/src` trigger Vite HMR

### Making Code Changes

1. Edit files in `./src` directory
2. Changes are reflected immediately (backend restarts automatically, frontend hot-reloads)
3. For Vue/Frontend changes: Your browser should auto-reload within 1-2 seconds
4. For Backend changes: Django restarts automatically (may take 2-3 seconds)

**Important**: You DO NOT need to run `./run_all.sh` again for code changes! Only run it when you change dependencies or Docker configuration.

**See detailed workflow guide**: [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)

### Database Migrations

After model changes:
```bash
docker-compose exec backend python /app/src/manage.py makemigrations
docker-compose exec backend python /app/src/manage.py migrate
```

## Production Deployment

⚠️ This setup is for **development only**. For production:

1. Change all default passwords
2. Set `DEBUG=False`
3. Use production-grade web servers (Gunicorn/uWSGI)
4. Set up proper SSL/TLS certificates
5. Configure database backups
6. Use secrets management
7. Enable Redis and Celery for better performance
8. Configure proper email backend

Refer to the [iManage documentation](https://docs.imanage.org/) for production deployment guidelines.

## Support & Documentation

- **Official Documentation**: https://docs.imanage.org/
- **GitHub Repository**: https://github.com/imanage/imanage
- **Issue Tracker**: https://github.com/imanage/imanage/issues/

## License

This project is licensed under the Apache License 2.0. See LICENSE file for details.

## Contributing

Contributions are welcome! Please check the developer documentation and submit pull requests via GitHub.

---

**Note**: This is a development setup. For production use, please follow the official iManage deployment documentation.
