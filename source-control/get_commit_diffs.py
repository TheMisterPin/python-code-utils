#!/usr/bin/env python3
"""Generate per-file git diffs for a commit as markdown outputs."""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List


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


def ensure_commit(repo_path: str, commit: str) -> str:
    """Validate commit-ish and return full hash."""

    return run_git(repo_path, "rev-parse", commit)


def list_changed_files(repo_path: str, commit: str) -> List[str]:
    """Return the list of files changed in a commit."""

    output = run_git(repo_path, "show", "--pretty=", "--name-only", commit)
    files = [line for line in output.splitlines() if line.strip()]
    return files


def get_file_diff(repo_path: str, commit: str, file_path: str) -> str:
    """Return the diff for a single file in the commit."""

    return run_git(
        repo_path,
        "show",
        commit,
        "--pretty=format:",
        "--patch",
        "--",
        file_path,
    )


def write_markdown(output_dir: Path, file_path: str, commit: str, diff_text: str) -> None:
    """Write a markdown file for the diff of a single file."""

    destination = output_dir / f"{file_path}.md"
    destination.parent.mkdir(parents=True, exist_ok=True)

    content_lines = [
        f"# Diff for `{file_path}`",
        "",
        f"Commit: `{commit}`",
        "",
    ]

    if diff_text:
        content_lines.append("```diff")
        content_lines.append(diff_text)
        content_lines.append("```")
    else:
        content_lines.append("No diff content available.")

    destination.write_text("\n".join(content_lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create per-file markdown diff documents for a specific commit inside "
            "the _outputs/source-control/commits/<commit>/diffs directory."
        )
    )
    parser.add_argument(
        "commit",
        help="Commit hash or reference to export diffs for.",
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Path to the git repository (default: current directory).",
    )
    parser.add_argument(
        "--output-root",
        default="_outputs",
        help="Root output directory (default: _outputs).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_path = args.path

    full_commit = ensure_commit(repo_path, args.commit)
    short_commit = run_git(repo_path, "rev-parse", "--short", full_commit)

    files = list_changed_files(repo_path, full_commit)
    if not files:
        print(f"No changed files found in commit {short_commit}.")
        return

    output_dir = Path(os.path.join(repo_path, args.output_root)) / "source-control" / "commits" / short_commit / "diffs"

    for file_path in files:
        diff_text = get_file_diff(repo_path, full_commit, file_path)
        write_markdown(output_dir, file_path, short_commit, diff_text)

    print(
        f"Wrote diffs for {len(files)} file(s) to {output_dir}",
    )


if __name__ == "__main__":
    main()
