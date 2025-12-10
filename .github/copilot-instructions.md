# Python Code Utils - Copilot Instructions

## Project Overview
**python-code-utils** is a collection of focused Python automation scripts organized by category. Each folder contains utilities for specific workflows: file organization, database schema management, documentation extraction/generation, source control analysis, email management, CSS property analysis, and password generation.

**Owner:** TheMisterPin  
**Repository:** python-code-utils  
**Primary Language:** Python 3.11+  
**Environment:** Windows (PowerShell 5.1)  
**Current Date:** December 2025

---

## Current Active Projects

### 1. Database Schema Management (`database/`)
- **Primary Script:** `generate_tables.py`
- **Purpose:** Connects to SQL Server, compares live schema with local `.sql` files, and generates updated definitions
- **Status:** Active, requires SQL Server connection (ODBC Driver 17)
- **Output Location:** `_outputs/database/changed-tables/`

### 2. Documentation Pipeline (`documents/`)
- **Extractors:** Parse docstrings/comments from Python, TypeScript, JavaScript, and C# files into Markdown
- **Generators:** Create API reference docs, fill placeholder documentation via Ollama LLM
- **Key Scripts:** 
  - `extractors/extract-docs-py.py` - Python docstring extraction
  - `extractors/extract-docs-ts.py` - TypeScript/JS comment extraction
  - `extractors/extract-docs-cs.py` - C# XML doc extraction
  - `generators/write-docs.py` - AI-powered documentation completion
  - `generators/make-md-files.py` - Scaffold markdown files
  - `generators/list-unused-endpoints.py` - API endpoint analysis

### 3. Source Control Analysis (`source-control/`)
- **Primary Script:** `diffs_by_week.py`
- **Purpose:** Analyze git commits, extract diffs grouped by day/week
- **Output Location:** `_outputs/source-control/raw/by-day/` (patch files) and `_outputs/summary.json`

### 4. CSS Property Analysis (`css/`)
- **Primary Script:** `list-properties.py`
- **Purpose:** Scan SCSS/CSS files, categorize properties by family (color, layout, typography, etc.)
- **Output Location:** `_outputs/css/lists/{date}/`

### 5. File Management (`file/`)
- **Scripts:**
  - `file-organizer.py` - Sort Downloads folder by file type into subdirectories
  - `list-files-by-type.py` - Generate markdown inventory of files by extension

### 6. Email Automation (`Email/`)
- **Primary Script:** `email-deleter.py`
- **Purpose:** Batch delete unread promotional Gmail using OAuth
- **Requires:** `credentials.json` and generates `token.pickle`

### 7. Utilities
- **Password Generator:** `Password-Generator/password_generator.py` - Interactive CLI password creation
- **CSV Converter:** `csv/converter.py` - Transform CSV to JSON (pandas-based)
- **Codebase Tools:** `codebase/create-index.py` - Generate TypeScript barrel exports

---

## Project Structure & Organization

### Root-Level Folders
```
python-code-utils/
├── _outputs/              # All generated output files (gitignored)
│   ├── database/          # Schema change snapshots
│   ├── source-control/    # Git diff patches and summaries
│   ├── css/               # CSS property analysis reports
│   └── documents/         # Extracted documentation
├── codebase/              # Code generation utilities
├── css/                   # CSS/SCSS analysis tools
├── csv/                   # CSV transformation scripts
├── database/              # Database schema management
│   └── Tables/            # Source of truth .sql files
├── documents/             # Documentation pipeline
│   ├── extractors/        # Parse source code for docs
│   └── generators/        # Create/enhance documentation
├── Email/                 # Gmail automation
├── file/                  # File system utilities
├── Password-Generator/    # Secure password creation
├── source-control/        # Git analysis tools
└── utils/                 # Shared utility functions
    ├── __init__.py        # Package initialization
    └── output_helpers.py  # Output directory management
```

### Standard Conventions

#### Output Directory Pattern
**Every script uses the shared `utils.output_helpers` module:**

The project follows DRY principles with a centralized output management system located in `utils/output_helpers.py`. All scripts import these functions instead of duplicating code:

```python
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.output_helpers import get_output_base_dir

# Use the function directly
output_dir = get_output_base_dir()
# Or with a subdirectory
output_dir = get_output_base_dir(subdirectory="changed-tables")
```

**Available functions in `utils.output_helpers`:**
- `find_root(start_dir=None)` - Traverse up to find project root (where `_outputs` exists)
- `get_output_base_dir(script_file=None, subdirectory=None)` - Create output path mirroring script's location
- `get_root_dir(start_dir=None)` - Alias for `find_root()` for backward compatibility

The module automatically:
- Detects the caller's location using introspection
- Finds the project root by looking for `_outputs/` directory
- Creates a mirrored path structure under `_outputs/`
- Creates directories if they don't exist

**Rule:** Scripts output to `_outputs/{category}/` matching their folder structure. For example:
- `database/generate_tables.py` → `_outputs/database/changed-tables/`
- `css/list-properties.py` → `_outputs/css/lists/{timestamp}/`
- `source-control/diffs_by_week.py` → `_outputs/source-control/raw/`

#### README Pattern
- Every folder has a `Readme.md` explaining scripts, parameters, and usage
- Root `Readme.md` provides high-level overview with links to folder READMEs

---

## Coding Style & Standards

### General Python Conventions
1. **Python Version:** 3.11+ (use modern type hints when applicable)
2. **Encoding:** UTF-8 with `encoding='utf-8'` in file operations
3. **Shebang:** `#!/usr/bin/env python3` for executable scripts
4. **Line Length:** Generally 80-100 characters, flexible for readability
5. **DRY Principle:** Use shared utilities from `utils/` package instead of duplicating code

### Function Definitions
- **Naming:** snake_case for functions and variables
- **Docstrings:** Use triple-quoted strings for function documentation
- **Type Hints:** Used in newer scripts (`documents/generators/write-docs.py`), optional in older utilities

**Example:**
```python
def extract_docstring(file_path):
    """
    Extract docstrings from a Python file (module, functions, and classes).
    
    Args:
        file_path (str): Path to the Python file
        
    Returns:
        str: Combined docstrings content or empty string if no docstrings found
    """
    # Implementation...
```

### Import Organization
```python
# Standard library imports first
import os
import sys
import json

# Third-party imports
import pandas as pd
import pyodbc

# Local imports (if any)
from .utils import helper_function
```

### Error Handling
- **Explicit try-except blocks** for file I/O and external connections
- **Print error messages to stderr:** `print("Error:", e, file=sys.stderr)`
- **Graceful degradation:** Log errors but continue processing when possible

**Example:**
```python
try:
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
except Exception as e:
    print(f"Error reading {file_path}: {e}", file=sys.stderr)
    return ""
```

### Path Handling
- **Use `os.path` for Windows compatibility** (primary environment)
- **Absolute paths preferred:** `os.path.abspath(__file__)`
- **Path normalization:** `os.path.join()` for cross-platform compatibility
- **Modern scripts may use `pathlib.Path`** (e.g., `documents/generators/write-docs.py`)

### Command-Line Interface
- **Use `argparse`** for CLI arguments
- **Provide helpful defaults** and descriptions
- **Interactive prompts** acceptable for user-facing tools (e.g., password generator)

**Example:**
```python
parser = argparse.ArgumentParser(description='Extract docstrings from Python files')
parser.add_argument('directory', help='Directory to scan')
parser.add_argument('--output', default='_outputs/docs', help='Output directory')
args = parser.parse_args()
```

### External Dependencies
**Core Libraries (install via pip):**
- `pandas` - Data manipulation (CSV, JSON)
- `pyodbc` - SQL Server connectivity
- `requests` - HTTP calls (Ollama API)
- `google-auth`, `google-auth-oauthlib`, `google-api-python-client` - Gmail OAuth
- `pytz` - Timezone handling

**Standard Library Heavy:**
- Most scripts minimize external dependencies
- Use `subprocess` for git operations
- Use `ast` for Python parsing
- Use `re` for regex operations

### Database Connections
```python
# Standard SQL Server connection pattern
server = '172.16.100.5'
database = 'DBK Suite BASE DEV'
username = 'Bks'
password = 'P1@niga'

dsn = (
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password}'
)

conn = pyodbc.connect(dsn)
cursor = conn.cursor()
```

### File Processing Patterns

#### Directory Traversal
```python
# Standard recursive file scan with exclusions
skip_dirs = {
    'venv', 'env', '.venv', '.env',
    '__pycache__', '.git', '.svn', '.hg',
    'node_modules', '.pytest_cache'
}

for root, dirs, files in os.walk(directory):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for file in files:
        if file.endswith('.py'):
            # Process file...
```

#### Output File Naming
- **Timestamps:** Use ISO format `YYYY-MM-DD` or `YYYYMMDD`
- **Descriptive names:** `{category}_{timestamp}.{ext}`
- **JSON for structured data:** `summary.json`, `report.json`
- **Markdown for reports:** `file_list.md`, `api-reference.md`

---

## Git & Source Control Patterns

### Git Command Execution
```python
def run_git(cmd):
    """Execute git command with error handling."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace"
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("Git command failed:", " ".join(cmd), file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
```

### ANSI Escape Handling
```python
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

def strip_ansi(text):
    """Remove ANSI color codes from git output."""
    return ANSI_ESCAPE_RE.sub("", text)
```

---

## Documentation Patterns

### Markdown Generation
```python
def generate_markdown_list(root_dir, file_types):
    """Generate markdown file list with proper formatting."""
    lines = [
        f"# Files in {os.path.basename(root_dir)}",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Files:",
        ""
    ]
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if any(file.endswith(ft) for ft in file_types):
                rel_path = os.path.relpath(os.path.join(root, file), root_dir)
                lines.append(f"- {rel_path}")
    
    return "\n".join(lines)
```

### AI Integration (Ollama)
```python
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "deepseek-v3.1:671b-cloud"

def call_ollama(prompt: str) -> str:
    """Send prompt to local Ollama instance."""
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    
    import requests
    response = requests.post(OLLAMA_URL, json=payload, timeout=None)
    response.raise_for_status()
    data = response.json()
    
    return str(data["response"]).strip()
```

---

## Common Task Patterns

### Adding a New Script
1. **Choose appropriate folder** based on script category
2. **Create script with shebang:** `#!/usr/bin/env python3`
3. **Add module docstring** explaining purpose
4. **Import shared utilities** if generating output:
   ```python
   import sys
   import os
   
   # Add parent directory to path for imports
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   from utils.output_helpers import get_output_base_dir
   ```
5. **Use `argparse`** for CLI arguments
6. **Update folder's `Readme.md`** with script description and usage
7. **Test with Python 3.11+** in Windows PowerShell

### Output File Management
- **Always use `utils.output_helpers`** for consistent output paths
- **Never duplicate** `find_root()` or `get_output_base_dir()` functions
- **Use descriptive filenames** with timestamps for reports
- **JSON for structured data**, **Markdown for human-readable reports**

### Error Reporting
- **Print progress messages** to stdout: `print("Processing...")`
- **Print errors** to stderr: `print("Error:", msg, file=sys.stderr)`
- **Exit with status code** on fatal errors: `sys.exit(1)`
- **Continue on non-fatal errors** with warnings

---

## External Services & Configuration

### SQL Server
- **Connection:** ODBC Driver 17, hardcoded credentials in `database/generate_tables.py`
- **Server:** 172.16.100.5
- **Database:** DBK Suite BASE DEV
- **Schema:** Focuses on `dbo` schema tables

### Gmail API
- **OAuth Flow:** Requires `credentials.json` in `Email/` folder
- **Token Storage:** `token.pickle` generated on first auth
- **Scopes:** Gmail modification for bulk deletion

### Ollama LLM
- **Endpoint:** `http://127.0.0.1:11434/api/generate`
- **Model:** deepseek-v3.1:671b-cloud
- **Usage:** Documentation completion in `documents/generators/write-docs.py`
- **Requirement:** Ollama server must be running locally

---

## Testing & Execution

### Python Environment Setup
```powershell
# Create virtual environment
python -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install pandas pyodbc google-auth google-auth-oauthlib google-api-python-client pytz requests
```

### Running Scripts
```powershell
# Standard execution
python .\database\generate_tables.py

# With arguments
python .\documents\extractors\extract-docs-py.py C:\path\to\source --output .\docs

# Check help
python .\css\list-properties.py --help
```

---

## Key Insights for Future Sessions

### 1. Project Philosophy
- **Focused utilities over monolithic tools:** Each script solves one problem well
- **Minimal external dependencies:** Prefer standard library when possible
- **Reproducible outputs:** All generated files go to `_outputs/`
- **Self-documenting:** Every folder has a README

### 2. When Adding Features
- **Maintain output directory pattern** (`_outputs/` mirroring)
- **Follow existing naming conventions** (snake_case, descriptive)
- **Add README documentation** for new scripts
- **Preserve Windows/PowerShell compatibility**

### 3. Common Modifications
- **Update database credentials** in `database/generate_tables.py` for different environments
- **Adjust file type mappings** in `file/file-organizer.py` for new extensions
- **Configure skip directories** in document extractors for project-specific folders
- **Modify Ollama model** in `documents/generators/write-docs.py` for different LLMs

### 4. Output Expectations
- **JSON files:** Machine-readable summaries and structured data
- **Markdown files:** Human-readable reports and documentation
- **SQL files:** Database schema definitions and change tracking
- **Patch files:** Git diffs organized by date

### 5. Limitations & Known Issues
- **Hardcoded paths** in some scripts (e.g., `file-organizer.py` uses specific user Downloads)
- **No centralized configuration:** Each script manages its own settings
- **No automated tests:** Scripts are utility-focused, manually tested
- **Windows-centric:** Path handling assumes Windows filesystem conventions

---

## Quick Reference

### File Extensions by Category
- **Python:** `.py`
- **Web:** `.ts`, `.tsx`, `.js`, `.jsx`, `.html`, `.css`, `.scss`
- **Data:** `.json`, `.csv`, `.sql`
- **Documents:** `.md`, `.pdf`, `.txt`, `.doc`
- **Archives:** `.zip`, `.rar`, `.7z`
- **Images:** `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`
- **Executables:** `.exe`, `.msi`

### Common Directories to Skip
```python
skip_dirs = {
    'venv', 'env', '.venv', '.env',
    '__pycache__', '.git', '.svn', '.hg',
    'node_modules', '.pytest_cache',
    '__pycache__', 'dist', 'build'
}
```

### Standard Imports
```python
# File operations
import os
import shutil
from pathlib import Path

# Data processing
import json
import csv
import pandas as pd

# Text processing
import re
import ast

# External processes
import subprocess
import argparse

# Date/time
from datetime import datetime, date
import pytz

# Error handling
import sys
```

---

## Maintenance Notes

- **Last Updated:** December 2025
- **Python Version:** 3.11+
- **OS:** Windows 10/11
- **Shell:** PowerShell 5.1
- **Primary Use Case:** Developer productivity automation

For questions about specific scripts, refer to the folder-level README files or examine the script's module docstring.
