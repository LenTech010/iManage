<!--
SPDX-FileCopyrightText: 2022-present Tobias Kunze
SPDX-License-Identifier: Apache-2.0
-->

# imanage-schedule-editor

## Project setup
```
npm ci
```

### Compiles and hot-reloads for development
```
npm start
```

### Compiles and minifies for production
```
npm run build
```

### Build for imanage (web component)
```
npm run build:wc
```

Then copy ``dist/*js`` to ``src/imanage/static/orga/js/`` in imanage.

### Release library to npm

```sh
npm version minor|patch
npm publish --access=public
```

### Lints and fixes files
```
npm run lint
```
