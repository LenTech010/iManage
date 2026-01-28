# Docker Setup for iManage

This directory contains Docker configuration files to run the complete iManage application (backend and frontend) with a single command.

## Quick Start

### Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 1.29 or higher)

### Running the Application

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/LenTech010/iManage.git
   cd iManage
   ```

2. **Configure environment variables** (optional):
   ```bash
   cp .env.example .env
   # Edit .env to customize settings
   ```

3. **Run the application**:
   
   **Linux/Mac:**
   ```bash
   ./run_all.sh
   ```
   
   **Windows:**
   ```batch
   run_all.bat
   ```

That's it! The script will:
- Build Docker images for backend and frontend
- Start all services (PostgreSQL, Django backend, Vite frontend)
- Run database migrations
- Create a Django superuser
- Display URLs where services are accessible

### Accessing the Application

After running `./run_all.sh` (or `run_all.bat` on Windows), you can access:

- **Backend (Django)**: http://localhost:3000
- **Frontend (Vite)**: http://localhost:3000
- **Database (PostgreSQL)**: localhost:5432

### Default Credentials

- **Username**: admin
- **Password**: admin
- **Email**: admin@localhost

You can change these by editing the `.env` file before running the setup.

## Docker Files

- **`Dockerfile.backend`**: Builds the Django backend container
  - Based on Python 3.12
  - Installs dependencies from `pyproject.toml`
  - Runs migrations and creates superuser on startup
  - Exposes port 3000

- **`Dockerfile.frontend`**: Builds the Vite frontend container
  - Based on Node.js 18 (runtime for Vite)
  - Installs dependencies from `package.json`
  - Runs Vite dev server
  - Exposes port 3000

- **`docker-compose.yml`**: Orchestrates all services
  - **db**: PostgreSQL 15 database
  - **backend**: Django application
  - **frontend**: Vite development server

- **`run_all.sh` / `run_all.bat`**: Automation scripts (Linux/Mac and Windows)
  - Builds and starts all containers
  - Displays service URLs and useful commands

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example` to customize:

- **Database settings**:
  - `DB_NAME`: Database name (default: imanage)
  - `DB_USER`: Database user (default: imanage)
  - `DB_PASSWORD`: Database password (default: imanage)

- **Superuser settings**:
  - `DJANGO_SUPERUSER_USERNAME`: Admin username (default: admin)
  - `DJANGO_SUPERUSER_PASSWORD`: Admin password (default: admin)
  - `DJANGO_SUPERUSER_EMAIL`: Admin email (default: admin@localhost)

- **Site settings**:
  - `SITE_URL`: Site URL (default: http://localhost:3000)
  - `TIME_ZONE`: Time zone (default: UTC)
  - `LANGUAGE_CODE`: Language code (default: en)

## Development Workflow

### Hot Reloading

Both backend and frontend support hot reloading during development:

- **Backend**: Code changes in `./src` are automatically reflected
- **Frontend**: Changes in `./frontend/src` trigger Vite's hot module replacement

**You DO NOT need to rebuild containers for code changes!** See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for details on when to rebuild vs. when changes auto-reload.

### Useful Commands

View all service logs:
```bash
docker-compose logs -f
```

View specific service logs:
```bash
docker-compose logs -f backend   # Backend logs
docker-compose logs -f frontend  # Frontend logs
docker-compose logs -f db        # Database logs
```

Stop all services:
```bash
docker-compose down
```

Restart services:
```bash
docker-compose restart
```

Access backend shell:
```bash
docker-compose exec backend bash
```

Access database shell:
```bash
docker-compose exec db psql -U imanage
```

Run Django management commands:
```bash
docker-compose exec backend python /app/src/manage.py <command>
```

### Rebuilding Containers

If you make changes to dependencies or Dockerfiles:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

Or simply run:

**Linux/Mac:**
```bash
./run_all.sh
```

**Windows:**
```batch
run_all.bat
```

**Note**: You only need to rebuild when you change dependencies (package.json, pyproject.toml) or Docker configuration. For code changes (Vue files, Python files), just save the file and the changes will auto-reload. See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for details.

## Troubleshooting

### UI/UX changes not appearing

If you've made changes to Vue files but don't see them in your browser:

1. **Do NOT run `./run_all.sh` / `run_all.bat`** - This rebuilds everything unnecessarily
2. **Try a hard refresh**: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
3. **Check frontend logs**: `docker-compose logs -f frontend` for any errors
4. **Restart frontend only**: `docker-compose restart frontend` (takes ~10 seconds)

**Full guide**: See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for complete troubleshooting steps.

### Backend won't start

Check logs:
```bash
docker-compose logs backend
```

Common issues:
- Database not ready: Wait a few seconds and check again
- Port 8000 already in use: Stop other services using that port

### Frontend won't start

Check logs:
```bash
docker-compose logs frontend
```

Common issues:
- Port 3000 already in use: Stop other services using that port
- npm install failed: Try rebuilding with `docker-compose build --no-cache frontend`

### Database connection issues

Ensure the database service is healthy:
```bash
docker-compose ps
```

Reset database (WARNING: This will delete all data):
```bash
docker-compose down -v
./run_all.sh
```

## Production Deployment

This Docker setup is optimized for **development**. For production deployment:

1. Use production-grade web servers (e.g., Gunicorn for Django)
2. Build and serve static frontend files
3. Use environment-specific settings
4. Set up proper SSL/TLS certificates
5. Configure database backups
6. Use secrets management for sensitive data

Refer to the [iManage documentation](https://docs.imanage.org/) for production deployment guidelines.

## License

This Docker setup follows the same license as iManage. See LICENSE file for details.
