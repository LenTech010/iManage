# Repository Restructuring Summary

## What Changed

The iManage repository has been restructured to eliminate confusion caused by duplicate `src` directories.

### Before (Confusing Structure)

```
iManage/
└── src/
    ├── imanage/
    │   ├── frontend/
    │   │   └── schedule-editor/
    │   │       └── src/          ← Confusing! Second "src"
    │   │           ├── App.vue
    │   │           └── ...
    │   ├── agenda/
    │   ├── cfp/
    │   └── ...
    ├── manage.py
    └── tests/
```

**Problems:**
- Two different `src` directories
- Frontend deeply nested 5 levels deep
- Hard to navigate and understand structure
- Confusion about where to find code

### After (Clean Structure) ✅

```
iManage/
├── src/                        # Backend: Django application
│   ├── imanage/
│   │   ├── agenda/
│   │   ├── cfp/
│   │   ├── common/
│   │   └── ...
│   ├── manage.py
│   └── tests/
├── frontend/                   # Frontend: Vue 3 application  
│   ├── src/
│   │   ├── App.vue
│   │   ├── components/
│   │   │   ├── Editor.vue
│   │   │   ├── GridSchedule.vue
│   │   │   └── Session.vue
│   │   └── main.js
│   ├── package.json
│   ├── vite.config.js
│   └── locales/
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── run_all.sh
```

**Benefits:**
- ✅ Clear separation: Backend vs Frontend
- ✅ No more duplicate `src` confusion
- ✅ Easier to navigate
- ✅ Follows industry standards (monorepo pattern)
- ✅ New developers can quickly understand the structure

## Files Changed

### Docker Configuration

**`Dockerfile.frontend`**
```diff
- COPY src/imanage/frontend/schedule-editor/package*.json ./
+ COPY frontend/package*.json ./

- COPY src/imanage/frontend/schedule-editor/ ./
+ COPY frontend/ ./
```

**`docker-compose.yml`**
```diff
  frontend:
    volumes:
-     - ./src/imanage/frontend/schedule-editor/src:/app/frontend/src
-     - ./src/imanage/frontend/schedule-editor/locales:/app/frontend/locales
+     - ./frontend/src:/app/frontend/src
+     - ./frontend/locales:/app/frontend/locales
```

### Python Management Commands

Three Django management commands were updated to navigate to the new frontend location:

1. **`src/imanage/common/management/commands/devserver.py`**
   - Starts Vite dev server alongside Django
   - Updated path calculation to reach `/frontend`

2. **`src/imanage/common/management/commands/makemessages.py`**
   - Extracts translations from Vue components
   - Updated frontend path and translation file locations

3. **`src/imanage/common/management/commands/rebuild.py`**
   - Builds Vue app for production
   - Updated frontend directory path

### Documentation

All documentation updated to reflect new structure:

- `DEVELOPMENT_WORKFLOW.md` - Updated all path references
- `DOCKER_README.md` - Updated volume mount paths  
- `QUICK_START_GUIDE.md` - Updated frontend location
- `VUE_UI_UX_GUIDE.md` - Updated directory structure examples

## Migration Guide

If you have local changes or branches, here's what you need to know:

### For Developers

**If you were working on Vue components:**
- Old location: `src/imanage/frontend/schedule-editor/src/`
- New location: `frontend/src/`

**Your old commands still work:**
```bash
# These still work the same way:
docker-compose up
./run_all.sh
npm run start  # (from frontend/ directory)
```

**Update your IDE/Editor:**
- Update any workspace settings pointing to the old path
- Search paths should now be `frontend/src/` for Vue code

### For Git Operations

**Pulling this change:**
```bash
git pull origin main  # or your branch
```

Git will automatically handle the file moves.

**If you have uncommitted changes to frontend:**
```bash
# Before pulling, commit or stash your work
git add src/imanage/frontend/schedule-editor/
git commit -m "WIP: my frontend changes"

# After pulling, your changes will be in frontend/
```

**Resolving merge conflicts:**
If you have a branch with frontend changes:
```bash
git checkout your-branch
git rebase main  # or git merge main

# Git should handle the renames automatically
# If conflicts occur, they'll be in frontend/ directory now
```

## Technical Details

### Path Calculation Changes

Python management commands use relative paths from their file location. The changes account for the new directory structure:

**Old path calculation:**
```python
# From: src/imanage/common/management/commands/
# Up 4 levels → src/imanage
# Then: frontend/schedule-editor
frontend_dir = Path(__file__).parent.parent.parent.parent / "frontend/schedule-editor"
```

**New path calculation:**
```python
# From: src/imanage/common/management/commands/  
# Up 6 levels → repo root
# Then: frontend
frontend_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "frontend"
```

### Docker Volume Mounts

The Docker setup uses volume mounts for hot-reloading during development:

**Before:**
```yaml
volumes:
  - ./src/imanage/frontend/schedule-editor/src:/app/frontend/src
```

**After:**
```yaml
volumes:
  - ./frontend/src:/app/frontend/src
```

This means:
- Changes to files in `frontend/src/` on your host
- Are immediately reflected in `/app/frontend/src` in the container
- Triggering Vite's Hot Module Replacement (HMR)

## Testing Checklist

After this restructuring, verify:

- [ ] `./run_all.sh` starts all services
- [ ] Backend accessible at http://localhost:8000
- [ ] Frontend dev server at http://localhost:3000  
- [ ] Vue hot reload works (edit a .vue file, see instant update)
- [ ] Production build works: `docker-compose exec backend python /app/src/manage.py rebuild`
- [ ] Translations extract: `docker-compose exec backend python /app/src/manage.py makemessages`

## Rollback (If Needed)

If you need to roll back this change:

```bash
# Revert to commit before restructuring
git revert <commit-hash>

# Or reset to previous commit (⚠️ loses uncommitted changes)
git reset --hard HEAD~1
```

## Future Improvements

This restructuring sets the stage for potential future improvements:

1. **Separate repositories** (optional): Backend and frontend could be split into separate repos
2. **Shared types** (future): Could add a `/shared` directory for TypeScript types used by both
3. **Testing separation**: Easier to run frontend-only or backend-only tests
4. **CI/CD optimization**: Build and deploy frontend/backend independently

## Questions?

If you encounter issues with this restructuring:

1. Check this guide first
2. Ensure Docker volumes are mounted correctly
3. Try rebuilding containers: `docker-compose down && docker-compose build`
4. Check the commit history for this restructuring to see exact changes

## Summary

**This change:**
- ✅ Fixes confusing duplicate `src` directories  
- ✅ Makes code easier to find and navigate
- ✅ Follows industry-standard monorepo patterns
- ✅ Maintains all existing functionality
- ✅ No code logic changes - only directory organization

**Everything still works the same way** - just in a cleaner, more logical structure! 🎉
