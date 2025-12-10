# Source control utilities

Python helpers that wrap common git reporting tasks. All scripts accept a `--path` argument to point at a repository (default: current directory).

## Tools

### `get_diffs_branch.py`
Compare two refs (defaults to current branch vs `main`).

Examples:
- Show filename and stat summary: `python source-control/get_diffs_branch.py --base main --branch feature-branch`
- Show only file names: `python source-control/get_diffs_branch.py --name-only`
- Include patch hunks: `python source-control/get_diffs_branch.py --patch`

### `get_commit_diffs.py`
Export diffs for every file in a commit into markdown files under `_outputs/source-control/commits/<short-hash>/diffs`.

Examples:
- Generate outputs for a commit: `python source-control/get_commit_diffs.py <commit-ish>`
- Specify a different repo path: `python source-control/get_commit_diffs.py <commit-ish> --path /path/to/repo`
- Change output root folder: `python source-control/get_commit_diffs.py <commit-ish> --output-root /tmp/outputs`

### `get_file_diffs.py`
Show diffs for a single file either against another ref or across a date range.

Examples:
- Compare the file in `HEAD` against `main`: `python source-control/get_file_diffs.py path/to/file --ref main --target HEAD`
- Compare two arbitrary refs: `python source-control/get_file_diffs.py path/to/file --ref release --target feature`
- Show all diffs for the file since a date: `python source-control/get_file_diffs.py path/to/file --since 2024-01-01`
- Limit by date range: `python source-control/get_file_diffs.py path/to/file --since 2024-01-01 --until 2024-06-30`

### `diffs_by_week.py`
Group commit messages by day within a time window (default last 30 days).

Examples:
- Default report for the current repo: `python source-control/diffs_by_week.py`
- Filter by author and date: `python source-control/diffs_by_week.py --author "Alice" --since "2 weeks ago" --until "yesterday"`
