#!/usr/bin/env python3
"""Show git diffs for a single file by branch comparison or time range."""

import argparse
import os
import subprocess
import sys
from typing import List, Optional


def run_git(repo_path: str, *args: str) -> str:
    """Run a git command inside repo_path and return stdout.

    Raises SystemExit with an error message on failure.
    """

    cmd: List[str] = ["git", "-C", repo_path, *args]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: git is not installed or not found in PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or "Unknown git error"
        print(f"Error running {' '.join(cmd)}: {stderr}", file=sys.stderr)
        sys.exit(exc.returncode or 1)

    return result.stdout.strip()


def ensure_ref_exists(repo_path: str, ref: str) -> str:
    """Validate that a git ref exists and return its resolved name."""

    return run_git(repo_path, "rev-parse", "--verify", ref)


def ensure_file(repo_path: str, file_path: str) -> None:
    """Validate that the file exists in the repository working tree."""

    absolute_path = os.path.join(repo_path, file_path)
    if not os.path.isfile(absolute_path):
        print(f"Error: file not found at {file_path}", file=sys.stderr)
        sys.exit(1)


def diff_against_ref(repo_path: str, file_path: str, ref: str, target: str) -> str:
    """Return the diff for file_path between ref and target."""

    ensure_ref_exists(repo_path, ref)
    ensure_ref_exists(repo_path, target)
    return run_git(repo_path, "diff", f"{ref}..{target}", "--", file_path)


def diffs_in_time_range(
    repo_path: str,
    file_path: str,
    since: Optional[str],
    until: Optional[str],
) -> str:
    """Return patch diffs for file_path across commits in a time window."""

    args: List[str] = ["log", "--pretty=format:commit %H %cd", "--date=iso", "-p"]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    args.extend(["--", file_path])
    return run_git(repo_path, *args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Show git diffs for a single file. Compare against another ref/branch "
            "by default, or show all diffs in a date range with --since/--until."
        )
    )
    parser.add_argument("file", help="Path to the file relative to the repository root.")
    parser.add_argument(
        "--path", default=".", help="Path to the git repository (default: current directory)."
    )
    parser.add_argument(
        "--ref",
        default="main",
        help="Branch or ref to compare against the current HEAD (default: main).",
    )
    parser.add_argument(
        "--target",
        default="HEAD",
        help="Target ref to compare with --ref (default: HEAD).",
    )
    parser.add_argument(
        "--since",
        help="Show all diffs for the file in commits since this date (e.g., 2024-01-01).",
    )
    parser.add_argument(
        "--until",
        help="Upper date bound for diffs (inclusive). Can be used with or without --since.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_path = args.path
    file_path = args.file

    ensure_file(repo_path, file_path)

    if args.since or args.until:
        diff_output = diffs_in_time_range(repo_path, file_path, args.since, args.until)
        if diff_output:
            print(diff_output)
        else:
            print("No diffs found for the given time range.")
        return

    diff_output = diff_against_ref(repo_path, file_path, args.ref, args.target)
    if diff_output:
        print(diff_output)
    else:
        print(f"No differences between {args.ref} and {args.target} for {file_path}.")


if __name__ == "__main__":
    main()
