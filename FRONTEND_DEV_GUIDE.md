# Frontend Development Guide - iManage Schedule Editor

## Overview

The iManage frontend is a **Vue 3 web component** built with Vite. It's designed to be embedded in Django backend pages, not run as a standalone application.

## Architecture

### Two Modes of Operation

#### 1. Development Mode (Vite Dev Server - Port 3000)
- **Purpose**: Fast development with hot module replacement (HMR)
- **URL**: http://localhost:3000
- **Behavior**: 
  - Loads successfully and shows Vue app structure
  - Displays loading state (black spinner) because it needs backend API data
  - Proxies API requests to Django backend at port 3000
  - **This is expected behavior** - the frontend needs a Django event context to display content

#### 2. Production Mode (Web Component in Django)
- **Purpose**: Final integration with Django
- **URL**: http://localhost:3000 (accessed through Django)
- **Behavior**:
  - Schedule editor embedded in Django templates
  - Full functionality with backend API integration
  - **This is the primary way users interact with the app**

## Quick Start

### Running with Docker (Recommended)

```bash
# Start all services (database, backend, frontend)
./run_all.sh

# Access the app
# - Django Backend: http://localhost:3000
# - Vite Dev Server: http://localhost:3000 (for development)
```

### Development Workflow

1. **Make changes to Vue files** in `frontend/src/`
2. **Save the file** - changes auto-reload via Vite HMR
3. **Refresh browser** if needed (Ctrl+Shift+R for hard refresh)
4. **DO NOT run `./run_all.sh` again** unless changing dependencies

## Project Structure

```
frontend/
├── index.html              # Vite entry point (development mode)
├── package.json            # Node dependencies
├── vite.config.js          # Vite configuration + API proxy
├── src/
│   ├── main.js            # Vue app initialization
│   ├── App.vue            # Root component (schedule editor)
│   ├── lib/
│   │   └── i18n.js        # i18next internationalization setup
│   ├── components/        # Vue components
│   │   ├── Editor.vue     # Session editor
│   │   ├── GridSchedule.vue  # Schedule grid view
│   │   └── Session.vue    # Session card component
│   ├── styles/
│   │   ├── global.styl    # Global Stylus styles
│   │   └── variables.styl # Color and design tokens
│   ├── api.js             # Backend API client
│   └── utils.js           # Utility functions
└── locales/
    └── en/
        └── translation.json  # English translations
```

## Key Technologies

- **Vue 3**: Progressive JavaScript framework
- **Vite**: Fast build tool and dev server
- **Stylus**: CSS preprocessor
- **Buntpapier**: UI component library
- **i18next**: Internationalization framework
- **Moment.js**: Date/time handling

## API Integration

### How the Proxy Works

The frontend needs to communicate with the Django backend. In Docker:

```javascript
// vite.config.js
server: {
  proxy: {
    '/orga': { target: 'http://backend:8000' },  // Backend container
    '/api': { target: 'http://backend:8000' }
  }
}
```

### API Endpoints Used

- `/orga/event/{slug}/schedule/api/talks/` - Fetch schedule sessions
- `/orga/event/{slug}/schedule/api/availabilities/` - Fetch room availabilities
- `/orga/event/{slug}/schedule/api/warnings/` - Fetch scheduling warnings
- `/api/events/{slug}/rooms` - Fetch room list

## Common Tasks

### Install Dependencies

```bash
cd frontend
npm install
```

### Run Dev Server Locally (Outside Docker)

```bash
cd frontend
npm run start
# Opens on http://localhost:3000
```

**Note**: You'll need Django backend running at localhost:3000 for API calls to work.

### Build for Production

```bash
cd frontend
npm run build
# Creates web component in dist/
```

### Linting

```bash
cd frontend
npm run lint              # Run all linters
npm run lint:eslint       # JavaScript/Vue linting
npm run lint:stylelint    # Stylus/CSS linting
```

### Extract Translations

```bash
cd frontend
npm run i18n:extract
```

## Troubleshooting

### Port 3000 Shows Only Loading Spinner

**This is expected!** The frontend is a web component that needs backend API data. 

**Solutions:**
1. Access the app through Django at http://localhost:3000
2. Create a conference event in Django, then the schedule editor will have data

### Stylus Compilation Errors

**Problem**: `TypeError: expected rgba or hsla, but got call:var(--color-primary)`

**Cause**: Stylus mixins can't process CSS variables dynamically

**Solution**: Use Stylus variables instead of CSS variables in mixin arguments:
```stylus
// ❌ Wrong
button-style(color: var(--color-primary), text-color: $clr-white)

// ✅ Correct
button-style(color: $clr-primary, text-color: $clr-white)
```

### Changes Not Appearing

1. **Hard refresh**: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
2. **Check frontend logs**: `docker compose logs -f frontend`
3. **Restart frontend only**: `docker compose restart frontend`
4. **Clear browser cache**

### API 404 Errors

Check that:
- Django backend is running at port 3000
- Proxy configuration in `vite.config.js` is correct
- You're accessing through a valid event URL in Django

## Environment Variables

### Docker (docker-compose.yml)

```yaml
environment:
  NODE_ENV: development
  BACKEND_URL: http://backend:8000  # Backend container name
```

### Local Development

```bash
export BACKEND_URL=http://localhost:3000
npm run start
```

## Hot Module Replacement (HMR)

Vite provides instant feedback when you edit files:

- **Vue components**: Auto-reload without full page refresh
- **Stylus files**: Styles update instantly
- **JavaScript**: Module hot-swaps in place

Changes to these files require rebuild:
- `package.json` (dependencies changed)
- `vite.config.js` (build config changed)
- `Dockerfile.frontend` (Docker config changed)

## Production Build

The production build creates a web component that Django serves:

```bash
npm run build

# Output:
# dist/
#   ├── imanage-schedule.min.js  # Web component
#   ├── imanage-manifest.json     # Asset manifest
#   └── *.css                      # Compiled styles
```

Copy `dist/imanage-schedule.min.js` to `backend/src/imanage/static/agenda/js/`

## Understanding the "Empty Page" at Port 3000

When you visit http://localhost:3000, you see a loading spinner because:

1. **No Event Context**: The URL doesn't include an event slug
2. **API Returns 404**: `/orga/event/undefined/schedule/api/talks/` fails
3. **App Waits for Data**: Vue component shows loading state

**This is by design!** The schedule editor is meant to be embedded in Django pages that provide event context.

### To See It Working:

1. Go to http://localhost:3000
2. Create a conference event
3. Navigate to the event's schedule page
4. The schedule editor will render with full functionality

## Development Best Practices

1. **Use Django for testing**: Always test through localhost:3000
2. **Hot reload**: Make changes, save, browser auto-updates
3. **Don't rebuild unnecessarily**: Only rebuild when changing dependencies
4. **Check logs**: `docker compose logs -f frontend` for errors
5. **Lint before commit**: `npm run lint` to catch issues

## Contributing

When making frontend changes:

1. Edit files in `frontend/src/`
2. Test in browser at localhost:3000
3. Ensure linting passes: `npm run lint`
4. Commit changes (Docker auto-rebuilds on next run)
5. Document any new dependencies or configuration

## Resources

- [Vue 3 Documentation](https://vuejs.org/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Stylus Documentation](https://stylus-lang.com/)
- [Buntpapier Components](https://github.com/venueless/buntpapier)
- [i18next Documentation](https://www.i18next.com/)

## Summary

- **Port 3000 = Dev server** for hot reload (shows loading state without event data)
- **Port 8000 = Full app** with Django integration (how users access it)
- **The "empty" page at 3000 is expected** - it's waiting for backend API data
- **Always test through Django** to see the schedule editor working properly
