#!/usr/bin/env python3
"""Utility to show git diffs between branches without shell scripts."""

import argparse
import os
import subprocess
import sys
from typing import List

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


def get_current_branch(repo_path: str) -> str:
    """Return the current branch name or HEAD hash if detached."""

    branch = run_git(repo_path, "rev-parse", "--abbrev-ref", "HEAD")
    if branch == "HEAD":
        branch = run_git(repo_path, "rev-parse", "--short", "HEAD")
    return branch


def ensure_ref_exists(repo_path: str, ref: str) -> str:
    """Validate that a git ref exists and return its full name."""

    run_git(repo_path, "rev-parse", "--verify", ref)
    return ref


def build_diff_command(repo_path: str, base: str, branch: str, *, name_only: bool,
                       patch: bool, stat: bool) -> List[str]:
    """Construct the git diff command according to flags."""

    cmd: List[str] = ["git", "-C", repo_path, "diff", f"{base}..{branch}"]
    if name_only:
        cmd.append("--name-only")
    if stat:
        cmd.append("--stat")
    if patch:
        cmd.append("--patch")
    return cmd


def print_diff(repo_path: str, base: str, branch: str, *, name_only: bool,
               patch: bool, stat: bool) -> None:
    """Run and display a diff between two refs."""

    cmd = build_diff_command(repo_path, base, branch, name_only=name_only, patch=patch, stat=stat)
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"git diff failed with exit code {exc.returncode}", file=sys.stderr)
        sys.exit(exc.returncode or 1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show git diff between two branches (defaults to current branch vs main).",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the git repository (default: current directory).",
    )
    parser.add_argument(
        "--branch",
        dest="branch",
        help="Branch or ref to compare (default: current branch).",
    )
    parser.add_argument(
        "--base",
        dest="base",
        default="main",
        help="Base branch or ref to compare against (default: main).",
    )
    parser.add_argument(
        "--name-only",
        action="store_true",
        help="Show only the names of changed files.",
    )
    parser.add_argument(
        "--patch",
        action="store_true",
        help="Show patch contents (diff hunks).",
    )
    parser.add_argument(
        "--no-stat",
        dest="stat",
        action="store_false",
        help="Do not include the --stat summary.",
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
    parser.set_defaults(stat=True)
    return parser.parse_args()


def should_launch_gui() -> bool:
    return "--cli" not in sys.argv and ("--gui" in sys.argv or len(sys.argv) == 1)


def launch_gui() -> None:
    fields = [
        FieldSpec(key="path", label="Repository folder", field_type="dir", default="."),
        FieldSpec(key="branch", label="Branch to compare (optional)", field_type="text", default=""),
        FieldSpec(key="base", label="Base branch", field_type="text", default="main"),
        FieldSpec(key="name_only", label="Show filenames only", field_type="bool", default=False),
        FieldSpec(key="patch", label="Include patch hunks", field_type="bool", default=False),
        FieldSpec(key="stat", label="Include stats summary", field_type="bool", default=True),
    ]

    def on_submit(values, output_widget):
        args: List[str] = []
        repo_path = values["path"] or "."
        args.append(repo_path)
        if values["branch"]:
            args.extend(["--branch", values["branch"]])
        if values["base"]:
            args.extend(["--base", values["base"]])
        if values["name_only"]:
            args.append("--name-only")
        if values["patch"]:
            args.append("--patch")
        if not values["stat"]:
            args.append("--no-stat")

        code, stdout, stderr = run_script_capture(__file__, args)
        if code != 0 and not stderr:
            stderr = f"Command failed with exit code {code}."
        render_output(output_widget, stdout, stderr)

    build_form("Git Diff: Branch Compare", fields, on_submit)


def main() -> None:
    if should_launch_gui():
        launch_gui()
        return

    args = parse_args()
    repo_path: str = args.path

    branch = args.branch or get_current_branch(repo_path)
    base = args.base

    ensure_ref_exists(repo_path, branch)
    ensure_ref_exists(repo_path, base)

    print(f"Diffing {branch} against {base} in {repo_path}\n")
    print_diff(
        repo_path,
        base=base,
        branch=branch,
        name_only=args.name_only,
        patch=args.patch,
        stat=args.stat,
    )


if __name__ == "__main__":
    main()
