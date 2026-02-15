#!/usr/bin/env python3
"""Show git diffs for a single file by branch comparison or time range."""

import argparse
import os
import subprocess
import sys
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.gui_helpers import FieldSpec, build_form, render_output, run_script_capture


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
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the GUI.",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def should_launch_gui() -> bool:
    return "--cli" not in sys.argv and ("--gui" in sys.argv or len(sys.argv) == 1)


def launch_gui() -> None:
    fields = [
        FieldSpec(key="path", label="Repository folder", field_type="dir", default="."),
        FieldSpec(key="file", label="File to diff", field_type="file", required=True),
        FieldSpec(
            key="mode",
            label="Comparison mode",
            field_type="choice",
            default="Compare refs",
            options=["Compare refs", "Date range"],
        ),
        FieldSpec(key="ref", label="Base ref", field_type="text", default="main"),
        FieldSpec(key="target", label="Target ref", field_type="text", default="HEAD"),
        FieldSpec(key="since", label="Since date (optional)", field_type="text", default=""),
        FieldSpec(key="until", label="Until date (optional)", field_type="text", default=""),
    ]

    def on_submit(values, output_widget):
        repo_path = values["path"] or "."
        file_path = values["file"]
        if os.path.isabs(file_path) and os.path.isabs(repo_path):
            try:
                relative = os.path.relpath(file_path, repo_path)
                if not relative.startswith(".."):
                    file_path = relative
            except ValueError:
                pass

        args: List[str] = [file_path, "--path", repo_path]
        if values["mode"] == "Date range":
            if values["since"]:
                args.extend(["--since", values["since"]])
            if values["until"]:
                args.extend(["--until", values["until"]])
        else:
            if values["ref"]:
                args.extend(["--ref", values["ref"]])
            if values["target"]:
                args.extend(["--target", values["target"]])

        code, stdout, stderr = run_script_capture(__file__, args)
        if code != 0 and not stderr:
            stderr = f"Command failed with exit code {code}."
        render_output(output_widget, stdout, stderr)

    build_form("Git File Diff", fields, on_submit)


def main() -> None:
    if should_launch_gui():
        launch_gui()
        return

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
