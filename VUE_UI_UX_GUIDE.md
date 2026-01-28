# Vue UI/UX Guide for iManage

## Overview

This project uses **Vue.js** for specific interactive components, primarily the **Schedule Editor** in the organizer area. The rest of the application uses Django templates. This guide explains the Vue architecture and how to maintain UI/UX consistency.

## Current Vue Setup

### Location
```
src/imanage/frontend/schedule-editor/
├── src/
│   ├── App.vue              # Main schedule editor component
│   ├── main.js              # Entry point
│   ├── components/
│   │   ├── Editor.vue       # Session editor modal
│   │   ├── GridSchedule.vue # Grid-based schedule view
│   │   └── Session.vue      # Individual session component
│   └── styles/
│       ├── global.styl      # Global styles
│       └── variables.styl   # Style variables
├── package.json             # Dependencies and scripts
├── vite.config.js          # Vite build configuration
└── locales/                # Translations
```

### Technology Stack

**Vue 3** with:
- **Vite** - Fast build tool and dev server
- **Pug** - Template language (instead of plain HTML)
- **Stylus** - CSS preprocessor
- **Buntpapier** - UI component library
- **i18next** - Internationalization

### Where Vue is Used

The Vue schedule editor is currently used in:
- **Organizer Schedule Management** (`/orga/event/{slug}/schedule/`)
  - Integrated via `/src/imanage/orga/templates/orga/schedule/index.html`
  - Uses Vite to load the Vue app: `{% vite_asset "src/main.js" %}`

## UI/UX Design Principles

### 1. Component Structure

Vue components in this project follow a consistent pattern:

```vue
<template lang="pug">
.component-name(:class="classes", @event="handler")
  .header
    // Header content
  .content
    // Main content
  .footer
    // Footer content
</template>

<script>
export default {
  props: {
    // Component props
  },
  data() {
    return {
      // Component state
    }
  },
  computed: {
    // Computed properties
  },
  methods: {
    // Methods
  }
}
</script>

<style lang="stylus">
.component-name
  // Styles using Stylus
</style>
```

### 2. Styling Guidelines

**Colors (from variables.styl):**
```stylus
$color-primary = #3aa57c
$color-danger = #dc3545
$color-warning = #ffc107
$color-info = #17a2b8
```

**Common Patterns:**
- Use CSS custom properties: `var(--color-primary)`
- Track colors: `--track-color`
- Responsive design with media queries
- Print-friendly with `.no-print` classes

### 3. Session Component Styling

Sessions have different visual states:

```vue
.c-linear-schedule-session
  &.istalk         // Regular talk sessions
  &.isbreak        // Break sessions (green)
  &.isblocker      // Blocker sessions (internal, gray)
  &.pending        // Pending approval (yellow border)
  &.dragging       // Being dragged (semi-transparent)
  &.condensed      // Compact view mode
```

### 4. Interaction Patterns

**Drag and Drop:**
- Sessions can be dragged between time slots and rooms
- Visual feedback during drag: `isDragged` prop
- Drop zones highlighted on hover

**Editing:**
- Click session to open editor modal
- Modal overlays the schedule with dark background
- Form-based editing with validation

**View Modes:**
- **Expanded**: Full details visible
- **Condensed**: Compact view for overview

## Maintaining UI/UX Consistency

### When Creating New Vue Components

1. **Follow Existing Patterns**
   ```vue
   // Use the same structure as existing components
   // Example: See Session.vue for reference
   ```

2. **Use Existing Styles**
   ```stylus
   // Stylus is configured globally in vite.config.js
   // Variables are auto-imported from variables.styl
   // Use consistent spacing, colors, and typography
   .my-component
     padding: 10px
     color: $color-primary
   ```

3. **Maintain Accessibility**
   - Use semantic HTML
   - Include ARIA labels where needed
   - Support keyboard navigation
   - Test with screen readers

4. **Internationalization**
   ```vue
   // Always use translations
   {{ $t('Translation key') }}
   
   // For dynamic content
   {{ getLocalizedString(object.name) }}
   ```

### Color Scheme

The Vue components use the same color scheme as the main application:

| Purpose | Color | Usage |
|---------|-------|-------|
| Primary | `#3aa57c` | Main actions, links, active states |
| Success | `#28a745` | Confirmations, breaks |
| Danger | `#dc3545` | Errors, deletions, warnings |
| Warning | `#ffc107` | Pending states, cautions |
| Info | `#17a2b8` | Information, secondary actions |
| Blocker | Gray | Internal planning items |

### Typography

- **Font Family**: System fonts (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto`)
- **Headings**: Bold, larger sizes
- **Body Text**: Regular weight, readable sizes (14-16px)
- **Small Text**: 12px for metadata

### Spacing

Consistent spacing using multiples of 4px or 8px:
- Small: 4px, 8px
- Medium: 16px, 20px
- Large: 24px, 32px

## Development Workflow

### Running the Vue Dev Server

The Vue schedule editor supports hot module replacement (HMR):

```bash
# Using Docker (recommended)
docker-compose up frontend

# Or locally
cd src/imanage/frontend/schedule-editor
npm install
npm run start
```

Changes to `.vue` files will auto-reload in the browser!

### Building for Production

```bash
# In the schedule-editor directory
npm run build

# Or via Django management command
python manage.py rebuild
```

### Linting

```bash
# Check code style
npm run lint

# ESLint for JavaScript/Vue
npm run lint:eslint

# Stylelint for CSS/Stylus
npm run lint:stylelint
```

## Integrating Vue into Django Templates

To use the Vue schedule editor in a Django template:

```django
{% extends "base.html" %}
{% load vite %}

{% block scripts %}
    {% vite_hmr %}  {# Hot reload in development #}
    {% vite_asset "src/main.js" %}  {# Load Vue app #}
{% endblock scripts %}

{% block content %}
    <div id="app" data-gettext="{{ gettext_language }}"></div>
{% endblock content %}
```

## UI Component Library: Buntpapier

The Vue components use **Buntpapier** for common UI elements:

### Available Components

```vue
// Inputs
<bunt-input v-model="value" :placeholder="label" icon="search" />

// Tabs
<bunt-tabs :modelValue="activeTab">
  <bunt-tab id="tab1" header="Tab 1" />
</bunt-tabs>

// Buttons (use standard HTML with classes)
<button class="btn btn-primary">Action</button>
```

### Custom Directives

```vue
// Scrollbar (empty string is required)
<div v-scrollbar.y="">Content</div>
<div v-scrollbar.x.y="">Content</div>

// Tooltip (object with text property)
<span v-tooltip="{text: 'Tooltip text'}">Hover me</span>
<span v-tooltip.fixed="{text: 'Fixed tooltip', show: condition}">Conditional</span>
```

## Best Practices

### ✅ DO

- **Match existing component structure** - Follow patterns in Session.vue, Editor.vue
- **Use the style variables** - Import from `variables.styl`
- **Support both view modes** - Expanded and condensed
- **Add proper translations** - Use `$t()` for all user-facing text
- **Test drag-and-drop** - If adding interactive elements
- **Follow Pug syntax** - Use indentation-based templates
- **Use Stylus features** - Nesting, variables, mixins

### ❌ DON'T

- **Don't use inline styles** - Use Stylus classes instead
- **Don't hardcode strings** - Always use i18n
- **Don't mix template syntaxes** - Stick with Pug
- **Don't ignore existing patterns** - Check similar components first
- **Don't forget print styles** - Add `.no-print` where needed
- **Don't break hot reload** - Test changes reload properly

## Example: Creating a New Component

```vue
<!--
SPDX-FileCopyrightText: 2026-present Your Name
SPDX-License-Identifier: Apache-2.0
-->

<template lang="pug">
.my-new-component(:class="componentClasses")
  .header
    h3 {{ $t('Component Title') }}
  .content
    slot
  .footer.no-print
    button.btn.btn-primary(@click="handleAction")
      | {{ $t('Action') }}
</template>

<script>
import { getLocalizedString } from '~/utils'

export default {
  name: 'MyNewComponent',
  props: {
    data: {
      type: Object,
      required: true
    },
    mode: {
      type: String,
      default: 'expanded'
    }
  },
  data() {
    return {
      getLocalizedString
    }
  },
  computed: {
    componentClasses() {
      return [
        this.mode === 'condensed' ? 'condensed' : 'expanded',
        this.data.active ? 'active' : ''
      ]
    }
  },
  methods: {
    handleAction() {
      this.$emit('action', this.data)
    }
  }
}
</script>

<style lang="stylus">
// Variables are auto-imported via vite.config.js
// See: stylusOptions.imports in vite.config.js
.my-new-component
  padding: 16px
  background: white
  border-radius: 4px
  
  &.condensed
    padding: 8px
  
  .header
    border-bottom: 1px solid #ddd
    margin-bottom: 16px
    
    h3
      color: $color-primary
      margin: 0
  
  .content
    min-height: 100px
  
  .footer
    margin-top: 16px
    text-align: right
    
    button
      // Button styles inherited from global CSS
</style>
```

## Testing Your Vue Components

### Manual Testing Checklist

- [ ] Component renders correctly in both view modes
- [ ] Responsive on mobile, tablet, desktop
- [ ] Translations work in all supported languages
- [ ] Drag-and-drop works smoothly (if applicable)
- [ ] Print view looks good (hide interactive elements)
- [ ] Keyboard navigation works
- [ ] Screen reader announces content properly
- [ ] Hot reload works during development
- [ ] Production build works correctly

### Browser Testing

Test in:
- Chrome/Edge
- Firefox
- Safari
- Mobile browsers

## Common Issues and Solutions

### Issue: Changes not appearing

**Solution:**
```bash
# Check if Vite dev server is running
docker-compose logs frontend

# Hard refresh browser
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)

# Restart frontend
docker-compose restart frontend
```

### Issue: Styles not applying

**Solution:**
```vue
// Make sure you're using lang="stylus"
<style lang="stylus">
// Variables are auto-imported via vite.config.js
// No manual import needed - variables.styl is globally available
</style>
```

### Issue: Translations not working

**Solution:**
```bash
# Extract translations
npm run i18n:extract

# Check locale files
cat locales/en/translation.json
```

## Resources

- **Vue 3 Documentation**: https://vuejs.org/
- **Vite Documentation**: https://vitejs.dev/
- **Pug Documentation**: https://pugjs.org/
- **Stylus Documentation**: https://stylus-lang.com/
- **Buntpapier**: https://github.com/venueless/buntpapier

## Summary

The Vue schedule editor provides a rich, interactive experience for schedule management. When working with Vue in this project:

1. **Follow existing patterns** - Check App.vue, Session.vue, Editor.vue
2. **Maintain consistency** - Use the same colors, spacing, typography
3. **Use the tooling** - Vite HMR, linting, translations
4. **Test thoroughly** - Both view modes, all browsers, print view
5. **Document your changes** - Add comments, update this guide

The key is to keep the UI/UX consistent with the existing Vue components while leveraging the power of Vue 3's reactivity and component system.
