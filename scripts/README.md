# Development Scripts

This directory contains various utility and development scripts for the iManage project.

## Scripts

### Data Setup and Testing

- **`create_iccike.py`** - Creates a test ICCIKE event with sample data
  - Sets up an organiser, event, questions, and review score categories
  - Useful for development and testing purposes

- **`setup_data.py`** - Comprehensive setup script for development environment
  - Creates a superuser (admin@example.com / admin)
  - Sets up ICCIKE event with questions and review categories
  - Creates sample submissions
  - Useful for initial development environment setup

- **`test_404.py`** - Test script for reproducing 404 error scenarios
  - Tests EventStartpage view behavior
  - Useful for debugging URL resolution issues

- **`repro_issue.py`** - Script to reproduce specific issues
  - Tests for missing date fields and duplicate event scenarios
  - Useful for debugging and issue reproduction

### Rebranding Tools

- **`rebrand.py`** - Basic rebranding utility
  - Performs case-sensitive replacements in project files
  - **Note:** Contains placeholder values - modify search/replace strings before use
  - Use with caution - intended for one-time rebranding operations

- **`rebrand_v2.py`** - Enhanced rebranding utility
  - Includes file and directory renaming capabilities
  - More comprehensive than rebrand.py
  - **Note:** Contains placeholder values - modify search/replace strings before use
  - Use with caution - intended for one-time rebranding operations

## Usage

These scripts are development utilities and should not be included in production deployments. They are excluded from the distribution package via `MANIFEST.in`.

To run any script:

```bash
cd /path/to/iManage
python scripts/script_name.py
```

**Note:** Most scripts require Django environment setup and will attempt to configure it automatically.
