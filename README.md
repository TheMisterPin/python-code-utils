# Python Code Utils

A collection of lightweight Python utilities for working with repositories and documentation. Scripts are organized by purpose under the top-level folders.

## Contents
- `source-control/` — helpers for inspecting git history and diffs.
- `documents/` — scripts for working with endpoint documentation.
- `_outputs/` — default location for generated artifacts (created on demand).

## Source control utilities
Common git-focused helpers live in the [`source-control/`](source-control/README.md) folder. Key tools include:
- `get_diffs_branch.py` — compare two refs with options for file names, stats, or patches.
- `get_commit_diffs.py` — export per-file diff markdown files for a single commit into `_outputs/source-control/commits/<short-hash>/diffs`.
- `get_file_diffs.py` — show diffs for a single file against another ref or across a date range.
- `diffs_by_week.py` — group commit messages by day over a chosen window.

Refer to the [source-control README](source-control/README.md) for full usage examples and flags.

## Running scripts
Use Python 3.9+ and ensure `git` is installed for the git utilities.

```bash
python path/to/script.py --help
```

Run commands from the repository root unless otherwise noted.
