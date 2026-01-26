# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: Apache-2.0

set windows-shell := ["powershell.exe", "-c"]
set shell := ["sh", "-c"]

[private]
default:
    @just --list

# Install dependencies (use --extras to include e.g. dev, devdocs, postgres, redis)
[group('development')]
install *args:
    uv lock --upgrade
    uv sync {{ args }}

# Install all dependencies (dev, devdocs, postgres, redis)
[group('development')]
install-all:
    uv lock --upgrade
    uv sync --all-extras

# Install all dependencies (dev, devdocs, postgres, redis)
[group('development')]
[working-directory("src/imanage/frontend/schedule-editor/")]
install-npm:
    npm ci

# Install a plugin
[group('development')]
install-plugin path="":
    uv pip install -e {{ path }}

# Check for outdated dependencies
[group('development')]
deps-outdated:
    uv pip list --outdated --format=json | python -c " \
    import json, sys, tomllib; \
    from packaging.requirements import Requirement; \
    outdated = {p['name'].lower(): p for p in json.load(sys.stdin)}; \
    deps = tomllib.load(open('pyproject.toml', 'rb')).get('project', {}).get('dependencies', []); \
    direct = {Requirement(d).name.lower() for d in deps}; \
    [print(f\"{p['name']}: {p['version']} → {p['latest_version']}\") for name in sorted(outdated.keys() & direct) if (p := outdated[name])]"

# Bump a dependency version
[group('development')]
deps-bump package version:
    python -c " \
    import tomllib; \
    from pathlib import Path; \
    from packaging.requirements import Requirement; \
    p = Path('pyproject.toml'); \
    deps = tomllib.load(open('pyproject.toml', 'rb')).get('project', {}).get('dependencies', []); \
    old = next((d for d in deps if Requirement(d).name.lower() == '{{package}}'.lower()), None); \
    old and p.write_text(p.read_text().replace(old, f'{Requirement(old).name}~={{version}}'))"
    uv lock --upgrade-package {{package}}


# Run the development server or other commands, e.g. `just run makemigrations`
[group('development')]
[working-directory("src")]
run *args="runserver --skip-checks":
    uv run python manage.py {{ args }}

# Update translation files
[group('development')]
[working-directory("src")]
makemessages:
    just run rebuild --npm-install
    just run makemessages --keep-pot --all

# Build the documentation
[group('documentation')]
[working-directory("doc")]
docs *args="html":
    uv run make {{ args }}

# Serve the documentation from a live server
[group('documentation')]
[working-directory("doc")]
docs-serve *args="--port 8001":
    python -c "import shutil; shutil.rmtree('_build/html', ignore_errors=True)"
    uv run sphinx-autobuild . _build/html {{ args }}

# Update the API documentation
[group('documentation')]
api-docs:
    just run spectacular --color --file ../doc/api/schema.yml

# Check codebase for licensing problems
[group('linting')]
reuse:
    uv run reuse lint

# Format code with black
[group('linting')]
black *args="src":
    uv run --extra=dev black {{ args }}

# Check code with black (check only)
[group('linting')]
black-check *args="src":
    just black --check {{ args }}

# Check import sorting with isort (check only)
[group('linting')]
isort-check *args="src":
    just isort --check {{ args }}

# Sort imports with isort
[group('linting')]
isort *args="src":
    uv run --extra=dev isort {{ args }}

# Run flake8 linter
[group('linting')]
flake8 *args="src":
    uv run --extra=dev flake8 {{ args }}

# Check Django templates with djhtml (check only)
[group('linting')]
djhtml-check:
    just djhtml --check

# Format Django templates with djhtml
[group('linting')]
djhtml *args="":
    python -c "import pathlib, subprocess; [subprocess.run(['uv', 'run', '--extra=dev', 'djhtml'] + (['{{args}}'] if '{{args}}' else []) + [str(p)]) for p in pathlib.Path('src').rglob('*.html') if not any(x in p.parts for x in ['vendored', 'node_modules', 'htmlcov', 'local', 'dist']) and p.name != 'imanage-schedule' and not p.name.endswith('.min.html')]"

# Run all formatters and linters
[group('linting')]
fmt: black isort djhtml flake8

# Run all code quality checks
[group('linting')]
check: black-check isort-check djhtml-check flake8

# Open Django shell with access to all events
[group('development')]
shell event="" *args:
    just run shell --event {{ event }} {{ args }}

# Open Django shell with access to all events
[group('development')]
unsafe-shell *args:
    just run shell --unsafe-disable-scopes {{ args }}

# Clean up generated files
[group('development')]
clean:
    python -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [p.unlink(missing_ok=True) for p in pathlib.Path('.').rglob('*.pyc')]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('*.egg-info')]; shutil.rmtree('.pytest_cache', ignore_errors=True); shutil.rmtree('.coverage', ignore_errors=True); shutil.rmtree('htmlcov', ignore_errors=True); shutil.rmtree('dist', ignore_errors=True); shutil.rmtree('build', ignore_errors=True)"

# Run the test suite
[group('tests')]
test *args:
    uv run --extra=dev --extra=devdocs pytest {{ args }}
    git checkout -- src/imanage/locale

# Run tests in parallel (requires pytest-xdist)
[group('tests')]
[working-directory("src")]
test-parallel n="auto" *args:
    just test -n {{ n }} {{ args }}

# Run tests with coverage report
[group('tests')]
[working-directory("src")]
test-coverage *args:
    just test {{ args }}

# Show test coverage report in browser
[group('tests')]
[working-directory("src")]
test-coverage-report: test-coverage
    python -c "import os, webbrowser; path = os.path.abspath('htmlcov/index.html'); webbrowser.open('file://' + path) if os.path.exists(path) else print('Coverage report generated in htmlcov/index.html')"

# Run release checks
[group('release')]
release-checks:
    uv run check-manifest
    uv run python -m build
    uv run twine check dist/*
    python -c "import zipfile, sys, pathlib; [sys.exit(0 if any('frontend' in n for n in zipfile.ZipFile(f).namelist()) else 1) for f in pathlib.Path('dist').glob('imanage*.whl')]"
    python -c "import zipfile, sys, pathlib; [sys.exit(1 if any('node_modules' in n for n in zipfile.ZipFile(f).namelist()) else 0) for f in pathlib.Path('dist').glob('imanage*.whl')]"
    echo "All release checks successful"

# Release a new Imanage version
[group('release')]
release version:
    uv pip install build
    git commit -am "Release {{ version }}"
    git tag -m "Release {{ version }}" {{ version }}
    python -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['dist', 'build', 'imanage.egg-info']]"
    uv run python -m build -n
    uvx twine upload dist/imanage-*
    git push
    git push --tags
