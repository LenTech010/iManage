# Development Workflow Guide

## Understanding the Docker Setup

The iManage project uses Docker with volume mounting for development, which enables **hot reloading** without rebuilding containers. This guide explains when you need to rebuild and when you don't.

## 🚀 Quick Answer: UI/UX Changes

**If you've made Vue UI/UX changes, you DO NOT need to run `run_all.sh` / `run_all.bat` again!**

The frontend is configured with hot reloading (Vite HMR), so your changes should appear automatically in your browser.

### What to do instead:

1. **Just save your Vue files** - Changes in `.vue`, `.js`, `.css`, or `.styl` files are automatically detected
2. **Check your browser** - The page should auto-reload within 1-2 seconds
3. **If changes don't appear**:
   ```bash
   # Option 1: Hard refresh your browser
   # Press Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
   
   # Option 2: Restart just the frontend service
   docker-compose restart frontend
   
   # Option 3: Check frontend logs for errors
   docker-compose logs -f frontend
   ```

## 📋 When to Use Each Command

### ❌ Do NOT run `run_all.sh` / `run_all.bat` for:

- ✅ Vue component changes (`.vue` files)
- ✅ JavaScript/TypeScript changes
- ✅ CSS/Stylus changes
- ✅ Template/HTML changes
- ✅ Python backend code changes
- ✅ Django template changes
- ✅ Application configuration files (e.g., Django settings, environment variables)

**Why?** These files are mounted as volumes and support hot reloading!

### ✅ DO run `run_all.sh` / `run_all.bat` when:

- 📦 You add/remove npm packages (change `package.json`)
- 📦 You add/remove Python packages (change `pyproject.toml`)
- 🐳 You modify Dockerfiles
- 🗄️ You need to reset the database completely
- 🆕 You're setting up the project for the first time
- 🔧 You modify `docker-compose.yml`

## 🛠️ Common Development Scenarios

### Scenario 1: Making Vue UI/UX Changes

**What you changed:** Modified components, styles, or templates in `frontend/src/`

**Command needed:**
```bash
# No command needed! Just save and wait for auto-reload
# If browser doesn't update, do a hard refresh (Ctrl+Shift+R)
```

**Alternative (if auto-reload fails):**
```bash
# Just restart the frontend container
docker-compose restart frontend
```

### Scenario 2: Adding a New npm Package

**What you changed:** Ran `npm install some-package` or modified `package.json`

**Commands needed:**
```bash
# Stop services
docker-compose down

# Rebuild frontend container
docker-compose build frontend

# Start services again
docker-compose up -d

# Or just use run_all.sh / run_all.bat to rebuild everything
# Linux/Mac:
./run_all.sh
# Windows:
run_all.bat
```

### Scenario 3: Backend Code Changes

**What you changed:** Modified Python files in `src/imanage/`

**Command needed:**
```bash
# No rebuild needed! Django auto-reloads on file changes
# Just check the backend logs if something seems wrong:
docker-compose logs -f backend
```

### Scenario 4: Database Model Changes

**What you changed:** Modified Django models

**Commands needed:**
```bash
# Create and apply migrations
docker-compose exec backend python /app/src/manage.py makemigrations
docker-compose exec backend python /app/src/manage.py migrate
```

### Scenario 5: Frontend Build Issues or Cache Problems

**What you're experiencing:** Changes not appearing, build errors, or strange behavior

**Commands to try:**
```bash
# Option 1: Clear frontend cache and restart
docker-compose restart frontend

# Option 2: Rebuild frontend container without cache
docker-compose build --no-cache frontend
docker-compose up -d frontend

# Option 3: Full reset (nuclear option)
docker-compose down
# Linux/Mac:
./run_all.sh
# Windows:
run_all.bat
```

## 🔍 Debugging: Changes Not Appearing

If your Vue changes aren't showing up in the browser:

### Step 1: Verify the file is in the right location
```bash
# Your Vue files should be in:
frontend/src/components/
frontend/src/
```

### Step 2: Check if Vite dev server is running
```bash
# Check frontend logs
docker-compose logs -f frontend

# You should see:
#   "VITE v4.x.x  ready in XXX ms"
#   "➜  Local:   http://localhost:3000/"
```

### Step 3: Verify browser is pointing to the correct URL
- Frontend dev server: http://localhost:3000
- Backend server: http://localhost:3000

### Step 4: Check for syntax errors
```bash
# Check frontend logs for compilation errors
docker-compose logs frontend | grep -i error

# Run linter
docker-compose exec frontend npm run lint
```

### Step 5: Hard refresh the browser
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`
- Or open DevTools and right-click the refresh button → "Empty Cache and Hard Reload"

### Step 6: Restart the frontend service
```bash
docker-compose restart frontend
```

## 📊 Volume Mounts Explained

The docker-compose.yml file mounts these directories:

```yaml
frontend:
  volumes:
    # Your Vue source files (hot-reload enabled)
    - ./frontend/src:/app/frontend/src
    # Translation files (hot-reload enabled)
    - ./frontend/locales:/app/frontend/locales

backend:
  volumes:
    # All backend source code (hot-reload enabled)
    - ./src:/app/src
    # Data directory
    - ./data:/app/data
```

**What this means:**
- Changes to files in these directories are **immediately visible** inside the containers
- No rebuild needed for file content changes
- Rebuild only needed for dependency or Docker configuration changes

## 🎯 Best Practices

1. **Keep Docker running**: Start once with `./run_all.sh` / `run_all.bat`, then just edit files
2. **Watch the logs**: Keep a terminal open with `docker-compose logs -f frontend`
3. **Test incrementally**: Make small changes and verify each one works
4. **Use the linter**: Run `docker-compose exec frontend npm run lint` before committing
5. **Hard refresh often**: Browser caching can sometimes interfere with hot reload

## ⚡ Quick Reference

| What Changed | Command to Run | Time |
|--------------|----------------|------|
| Vue component (.vue) | None (auto-reload) | ~1 sec |
| JavaScript (.js) | None (auto-reload) | ~1 sec |
| CSS/Stylus (.css/.styl) | None (auto-reload) | ~1 sec |
| Python backend code (.py) | None (auto-reload) | ~2 sec |
| package.json | `./run_all.sh` / `run_all.bat` or rebuild frontend | ~2 min |
| pyproject.toml | `./run_all.sh` / `run_all.bat` or rebuild backend | ~2 min |
| Dockerfile.* | `./run_all.sh` / `run_all.bat` | ~2 min |
| docker-compose.yml | `./run_all.sh` / `run_all.bat` | ~2 min |

## 🆘 Still Having Issues?

1. **Check if containers are running:**
   ```bash
   docker-compose ps
   ```

2. **View all logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Nuclear option (fresh start):**
   ```bash
   docker-compose down -v  # ⚠️ This deletes the database!
   # Linux/Mac:
   ./run_all.sh
   # Windows:
   run_all.bat
   ```

4. **Check the specific guides:**
   - [Quick Start Guide](QUICK_START_GUIDE.md) - Initial setup
   - [Docker README](DOCKER_README.md) - Docker configuration
   - [GitHub Issues](https://github.com/LenTech010/iManage/issues) - Report bugs

## 💡 Pro Tips

- **Use two terminals**: One for logs (`docker-compose logs -f`), one for commands
- **Browser DevTools**: Open Network tab to see if files are reloading
- **Vite HMR overlay**: Vite shows build errors as an overlay in the browser
- **Check file permissions**: Ensure your files are readable (should be by default)
- **WSL2 users**: File watching can be slower; consider using native Linux paths

---

**Remember**: The whole point of Docker volumes and hot reloading is to avoid rebuilding containers during development. Save time by only rebuilding when you actually need to!
