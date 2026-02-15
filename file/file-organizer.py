#!/usr/bin/env python3
import argparse
import os
import shutil
import sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.gui_helpers import FieldSpec, build_form, render_output, run_script_capture


FILE_GROUPS: Dict[str, List[str]] = {
    "images": [".jpg", ".png", ".jpeg", ".gif", ".webp"],
    "videos": [".mp4"],
    "audio": [".mp3"],
    "docs": [".pdf", ".doc", ".txt"],
    "archives": [".zip", ".rar", ".7z"],
    "unity": [".unitypackage"],
    "apps": [".exe", ".msi"],
    "icons": [".svg"],
    "code": [".ts", ".tsx", ".js", ".json", ".html", ".css", ".py", ".c", ".cs"],
}


def ensure_directories(base_dir: str) -> Dict[str, str]:
    destinations = {}
    for group in FILE_GROUPS:
        dest = os.path.join(base_dir, group)
        os.makedirs(dest, exist_ok=True)
        destinations[group] = dest
    return destinations


def find_group_for_extension(extension: str) -> Optional[str]:
    for group, extensions in FILE_GROUPS.items():
        if extension in extensions:
            return group
    return None


def organize_files(source_dir: str, destination_root: str) -> Tuple[int, int]:
    destinations = ensure_directories(destination_root)
    file_list = os.listdir(source_dir)
    moved = 0
    skipped = 0

    for filename in file_list:
        source_path = os.path.join(source_dir, filename)
        if not os.path.isfile(source_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        group = find_group_for_extension(ext)
        if not group:
            skipped += 1
            continue

        shutil.move(source_path, os.path.join(destinations[group], filename))
        moved += 1

    return moved, skipped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Organize files into folders by type.")
    parser.add_argument("--source", default=os.getcwd(), help="Source directory to organize.")
    parser.add_argument(
        "--destination",
        default=None,
        help="Destination root for organized folders (defaults to source).",
    )
    parser.add_argument("--gui", action="store_true", help="Launch the GUI.")
    parser.add_argument("--cli", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def should_launch_gui() -> bool:
    return "--cli" not in sys.argv and ("--gui" in sys.argv or len(sys.argv) == 1)


def launch_gui() -> None:
    fields = [
        FieldSpec(key="source", label="Source folder", field_type="dir", default=os.getcwd(), required=True),
        FieldSpec(key="destination", label="Destination root (optional)", field_type="dir", default=""),
    ]

    def on_submit(values, output_widget):
        args = ["--source", values["source"]]
        if values["destination"]:
            args.extend(["--destination", values["destination"]])
        code, stdout, stderr = run_script_capture(__file__, args)
        if code != 0 and not stderr:
            stderr = f"Command failed with exit code {code}."
        render_output(output_widget, stdout, stderr)

    build_form("File Organizer", fields, on_submit)


def main() -> None:
    if should_launch_gui():
        launch_gui()
        return

    args = parse_args()
    source_dir = args.source
    destination_root = args.destination or source_dir

    if not os.path.isdir(source_dir):
        print(f"Error: Source directory does not exist: {source_dir}")
        sys.exit(1)

    if not os.path.isdir(destination_root):
        print(f"Error: Destination directory does not exist: {destination_root}")
        sys.exit(1)

    moved, skipped = organize_files(source_dir, destination_root)
    print(f"Moved {moved} files. Skipped {skipped} files.")


if __name__ == "__main__":
    main()
