#!/usr/bin/env python3
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.gui_helpers import FieldSpec, build_form, render_output, run_script_capture


def create_barrel(folder: str) -> None:
    """
    Creates or updates an index.ts barrel file in the given folder.
    Exports all TypeScript files and subfolders.
    """
    entries = os.listdir(folder)

    subfolders = [
        name for name in entries
        if os.path.isdir(os.path.join(folder, name)) and not name.startswith(".")
    ]

    ts_files = []
    for name in entries:
        if name in ("index.ts", "index.tsx"):
            continue
        if name.endswith(".ts") or name.endswith(".tsx"):
            ts_files.append(os.path.splitext(name)[0])

    ts_files = sorted(set(ts_files))

    lines = []

    for sub in sorted(subfolders):
        lines.append(f'export * from "./{sub}";')

    for file in sorted(ts_files):
        lines.append(f'export * from "./{file}";')

    index_path = os.path.join(folder, "index.ts")

    new_content = "\n".join(lines) + "\n"
    old_content = ""
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            old_content = f.read()

    if new_content != old_content:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"[UPDATED] {index_path}")
    else:
        print(f"[SKIPPED] {index_path} (no changes)")


def walk(root: str) -> None:
    """
    Recursively walks through all directories and creates barrel files.
    """
    for folder, _, _ in os.walk(root):
        create_barrel(folder)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create index.ts barrel files for a folder tree.",
    )
    parser.add_argument(
        "target_folder",
        help="Target folder to scan for TypeScript files.",
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
        FieldSpec(key="target_folder", label="Target folder", field_type="dir", required=True),
    ]

    def on_submit(values, output_widget):
        args = [values["target_folder"]]
        code, stdout, stderr = run_script_capture(__file__, args)
        if code != 0 and not stderr:
            stderr = f"Command failed with exit code {code}."
        render_output(output_widget, stdout, stderr)

    build_form("TypeScript Barrel Index Generator", fields, on_submit)


def main() -> None:
    if should_launch_gui():
        launch_gui()
        return

    args = parse_args()
    target_folder = args.target_folder

    if not os.path.exists(target_folder):
        print(f"Error: Target folder does not exist: {target_folder}")
        sys.exit(1)

    if not os.path.isdir(target_folder):
        print(f"Error: Target path is not a directory: {target_folder}")
        sys.exit(1)

    print(f"Scanning: {os.path.abspath(target_folder)}\n")
    walk(target_folder)
    print(f"\nDone! All index.ts files have been created/updated in: {os.path.abspath(target_folder)}")


if __name__ == "__main__":
    main()
