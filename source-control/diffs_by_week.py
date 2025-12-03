#!/usr/bin/env python3
import subprocess
import argparse
import sys
import os
import json
import re
import shutil
from collections import defaultdict
from datetime import date


def run_git(cmd):
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


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_ansi(text):
    return ANSI_ESCAPE_RE.sub("", text)


def parse_numstat_value(token):
    token = strip_ansi(token).strip()
    if not token:
        return None
    if token == "-":
        return 0
    normalized = token.replace(",", "")
    try:
        return int(normalized)
    except ValueError:
        return None


def get_commits_metadata(repo_path, since=None, until=None, author=None):
    """
    Returns a list of commits:
    [
      { "id": "...", "date": "YYYY-MM-DD", "author": "...", "message": "..." },
      ...
    ]
    """
    cmd = ["git", "-C", repo_path, "log"]
    cmd.append("--color=never")

    if since:
        cmd.append(f"--since={since}")
    if until:
        cmd.append(f"--until={until}")
    if author:
        cmd.append(f"--author={author}")

    cmd.extend([
        "--date=short",
        "--pretty=format:%H|%ad|%an|%s"
    ])

    output = run_git(cmd)
    commits = []

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        commit_id, date, auth, msg = parts
        commits.append({
            "id": commit_id.strip(),
            "date": date.strip(),
            "author": auth.strip(),
            "message": msg.strip(),
        })

    return commits


def analyze_commit_and_write_diff(repo_path, commit, diffs_dir):
    """
    - Runs `git show --name-status` for this commit to collect statuses and the patch.
    - Runs `git diff-tree --numstat` to gather added/removed line counts per file.
    - Appends the full patch output into the diffs directory for that date.
    Returns:
      {
        "files": [
          { "path": "...", "status": "A/M/D", "addedLines": int, "removedLines": int },
          ...
        ],
        "linesAdded": total_added,
        "linesRemoved": total_removed,
        "filesCreated": set([...]),
        "filesModified": set([...]),
        "filesDeleted": set([...]),
      }
    """
    commit_id = commit["id"]
    date = commit["date"]

    show_cmd = [
        "git", "-C", repo_path,
        "show",
        "--name-status",
        "--color=never",
        commit_id
    ]
    show_output = run_git(show_cmd)
    lines = show_output.splitlines()

    status_by_path = {}
    for line in lines:
        if line.startswith("diff --git"):
            break
        if not line.strip():
            continue

        parts = line.split("\t")
        if len(parts) >= 2 and parts[0]:
            status_field = parts[0]
            status = status_field[0]
            if status in ("A", "M", "D", "R", "C"):
                path = parts[-1].strip()
                if path:
                    status_by_path[path] = status

    stats_cmd = [
        "git", "-C", repo_path,
        "diff-tree",
        "--numstat",
        "--color=never",
        "-r",
        commit_id
    ]
    stats_output = run_git(stats_cmd)
    added_by_path = defaultdict(int)
    removed_by_path = defaultdict(int)

    for line in stats_output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue

        a_str, d_str, *path_parts = parts
        path = "\t".join(path_parts).strip()

        if "=>" in path:
            path = path.split("=>")[-1].strip()

        added = parse_numstat_value(a_str)
        removed = parse_numstat_value(d_str)

        if added is None or removed is None or not path:
            continue

        added_by_path[path] += added
        removed_by_path[path] += removed

    files_changed = []
    files_created = set()
    files_modified = set()
    files_deleted = set()
    total_added = 0
    total_removed = 0

    paths = set(added_by_path.keys()) | set(removed_by_path.keys()) | set(status_by_path.keys())

    for path in sorted(paths):
        status = status_by_path.get(path, "M")
        if status in ("R", "C"):
            status = "M"

        added = added_by_path.get(path, 0)
        removed = removed_by_path.get(path, 0)

        total_added += added
        total_removed += removed

        if status == "A":
            files_created.add(path)
        elif status == "D":
            files_deleted.add(path)
        else:
            files_modified.add(path)

        files_changed.append({
            "path": path,
            "status": status,
            "addedLines": added,
            "removedLines": removed,
        })

    # Append diff to by-day file
    day_file = os.path.join(diffs_dir, f"{date}.patch")
    with open(day_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n=== COMMIT {commit_id} ===\n")
        f.write(f"Author: {commit['author']}\n")
        f.write(f"Date:   {date}\n")
        f.write(f"Message: {commit['message']}\n")
        f.write("\n")
        f.write(show_output)
        f.write("\n")

    return {
        "files": files_changed,
        "linesAdded": total_added,
        "linesRemoved": total_removed,
        "filesCreated": files_created,
        "filesModified": files_modified,
        "filesDeleted": files_deleted,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate daily diffs and JSON summary from git history."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Folder of the git repository (default: current directory)."
    )
    parser.add_argument(
        "--since",
        default="30 days ago",
        help='Lower date bound for commits (default: "30 days ago").'
    )
    parser.add_argument(
        "--until",
        default=None,
        help='Upper date bound for commits.'
    )
    parser.add_argument(
        "--author",
        default=None,
        help='Filter by author. Example: "Michele".'
    )

    args = parser.parse_args()
    repo_path = args.path

    # Get script location and output dirs
    script_dir = os.path.dirname(os.path.abspath(__file__))
    outputs_root = os.path.normpath(os.path.join(script_dir, "..", "_outputs"))
    source_control_root = os.path.join(outputs_root, "source-control")

    repo_abs_path = os.path.normpath(os.path.abspath(repo_path))
    repo_name = os.path.basename(repo_abs_path) or "repo"
    repo_safe_name = repo_name.lower().replace(" ", "-")
    run_suffix = date.today().strftime("%m%d")

    diffs_by_day_dir = os.path.join(
        source_control_root,
        "raw",
        "diffsbyday",
        f"{repo_safe_name}-{run_suffix}"
    )
    summary_dir = os.path.join(source_control_root, "summaries", repo_safe_name)
    summary_path = os.path.join(summary_dir, f"summary-{repo_safe_name}-{run_suffix}.json")

    os.makedirs(outputs_root, exist_ok=True)
    os.makedirs(source_control_root, exist_ok=True)

    if os.path.exists(diffs_by_day_dir):
        shutil.rmtree(diffs_by_day_dir)
    os.makedirs(diffs_by_day_dir, exist_ok=True)
    os.makedirs(summary_dir, exist_ok=True)

    commits = get_commits_metadata(
        repo_path=repo_path,
        since=args.since,
        until=args.until,
        author=args.author,
    )

    if not commits:
        print("No commits found for the selected period.")
        return

    # Global summaries
    global_files_created = set()
    global_files_modified = set()
    global_files_deleted = set()
    total_lines_added = 0
    total_lines_removed = 0

    commit_entries = []

    for commit in commits:
        stats = analyze_commit_and_write_diff(repo_path, commit, diffs_by_day_dir)

        global_files_created |= stats["filesCreated"]
        global_files_modified |= stats["filesModified"]
        global_files_deleted |= stats["filesDeleted"]

        total_lines_added += stats["linesAdded"]
        total_lines_removed += stats["linesRemoved"]

        commit_entries.append({
            "id": commit["id"],
            "date": commit["date"],
            "author": commit["author"],
            "message": commit["message"],
            "filesChanged": stats["files"],
        })

    summary = {
        "repo": repo_abs_path,
        "since": args.since,
        "until": args.until,
        "author": args.author,
        "filesSummary": {
            "created": len(global_files_created),
            "modified": len(global_files_modified),
            "deleted": len(global_files_deleted),
        },
        "linesSummary": {
            "added": total_lines_added,
            "removed": total_lines_removed,
        },
        "commits": commit_entries,
    }

    os.makedirs(outputs_root, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Wrote daily diffs to: {diffs_by_day_dir}")
    print(f"Wrote summary to: {summary_path}")


if __name__ == "__main__":
    main()
