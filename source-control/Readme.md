# Source Control Helpers

These scripts capture Git history in a structured way so you can replay daily diffs or export summaries for reporting.

## diffs_by_week.py

**Features**
- Enumerates commits between the provided `--since`/`--until` range and optionally filters by `--author`.
- For each commit it parses the `git show --numstat --name-status` output, collects per-file statistics, and appends the full diff to `_outputs/rawdiffs/by-day/<YYYY-MM-DD>.patch`.
- Writes `_outputs/summary.json` with totals for files added/modified/deleted and the lines added/removed per commit.

**How to Run**
1. `pip install` is not required beyond Git; run the script via `python source-control/diffs_by_week.py .` from the repository root.
2. Optional flags: `--since "7 days ago"`, `--until "yesterday"`, `--author "Your Name"`.
3. The tool cleans `_outputs/rawdiffs/by-day` before writing new `.patch` files, so review the directory after the run.

**Usage Example**
```
$ python source-control/diffs_by_week.py --since "30 days ago"
Wrote daily diffs to: _outputs/rawdiffs/by-day
Wrote summary.json to: _outputs/summary.json
```

## get_diffs_branch.py

**Status**
- Currently an empty placeholder. Future work will export the diffs of an entire branch into files, similar to `diffs_by_week.py` but scoped to a branch name.
