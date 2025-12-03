#!/usr/bin/env python3
import subprocess
import argparse
from collections import defaultdict
import sys


def get_commits_grouped_by_day(repo_path=".", since=None, until=None, author=None):
    """
    Returns a dict: { 'YYYY-MM-DD': [commit_message, ...], ... }
    """
    cmd = ["git", "-C", repo_path, "log", "--date=short", "--pretty=format:%ad|%s"]

    # Insert filters just after "git -C <repo>"
    insert_pos = 4

    if since:
        cmd.insert(insert_pos, f"--since={since}")
        insert_pos += 1
    if until:
        cmd.insert(insert_pos, f"--until={until}")
        insert_pos += 1
    if author:
        cmd.insert(insert_pos, f"--author={author}")
        insert_pos += 1

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print("Error running git log:", e, file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

    lines = result.stdout.strip().splitlines()
    grouped = defaultdict(list)

    for line in lines:
        if not line.strip():
            continue
        try:
            date_str, msg = line.split("|", 1)
        except ValueError:
            # Line not in expected format, skip
            continue
        grouped[date_str.strip()].append(msg.strip())

    return grouped


def print_report(grouped):
    if not grouped:
        print("No commits found for the selected period.")
        return

    for day in sorted(grouped.keys()):
        print(day)
        for msg in grouped[day]:
            print(f"  - {msg}")
        print()  # blank line between days


def main():
    parser = argparse.ArgumentParser(
        description="Group git commit messages by day for reporting."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Folder of the git repository (default: current directory).",
    )
    parser.add_argument(
        "--since",
        default="30 days ago",
        help='Lower date bound, passed to git --since (default: "30 days ago"). '
        'Examples: "2025-11-01", "2 weeks ago", "1 month ago".',
    )
    parser.add_argument(
        "--until",
        default=None,
        help='Upper date bound, passed to git --until. Examples: "2025-12-01".',
    )
    parser.add_argument(
        "--author",
        default=None,
        help='Filter by author, passed to git --author. Example: "Michele".',
    )

    args = parser.parse_args()

    grouped = get_commits_grouped_by_day(
        repo_path=args.path,
        since=args.since,
        until=args.until,
        author=args.author,
    )
    print_report(grouped)


if __name__ == "__main__":
    main()
