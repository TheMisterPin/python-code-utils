#!/usr/bin/env python3
import argparse
import os
import sys
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.gui_helpers import FieldSpec, build_form, render_output, run_script_capture
from utils.output_helpers import get_output_base_dir


DEFAULT_FILE_TYPES = [".scss"]


def has_matching_files(root: str, file_types: List[str]) -> bool:
    for _, _, files in os.walk(root):
        if any(file.endswith(ext) for ext in file_types for file in files):
            return True
    return False


def generate_markdown_list(root_dir: str, file_types: List[str]) -> str:
    markdown = ""
    for root, _, files in os.walk(root_dir):
        if not has_matching_files(root, file_types):
            continue
        depth = root.replace(root_dir, "").count(os.sep)
        if depth == 0:
            header = "# " + (os.path.basename(root) or "Root Directory")
        else:
            header = "#" * (depth + 1) + " " + os.path.basename(root)
        markdown += header + "\n\n"

        files.sort()
        for file in files:
            if any(file.endswith(ext) for ext in file_types):
                markdown += "- [ ] " + file + "\n"
        markdown += "\n"

    return markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List files by type into a markdown checklist.")
    parser.add_argument(
        "--root-dir",
        default=os.getcwd(),
        help="Root directory to scan.",
    )
    parser.add_argument(
        "--types",
        default=",".join(DEFAULT_FILE_TYPES),
        help="Comma-separated list of file extensions to include.",
    )
    parser.add_argument("--gui", action="store_true", help="Launch the GUI.")
    parser.add_argument("--cli", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def should_launch_gui() -> bool:
    return "--cli" not in sys.argv and ("--gui" in sys.argv or len(sys.argv) == 1)


def launch_gui() -> None:
    fields = [
        FieldSpec(key="root_dir", label="Root folder", field_type="dir", default=os.getcwd()),
        FieldSpec(
            key="types",
            label="Extensions (comma-separated)",
            field_type="text",
            default=",".join(DEFAULT_FILE_TYPES),
        ),
    ]

    def on_submit(values, output_widget):
        args = ["--root-dir", values["root_dir"], "--types", values["types"]]
        code, stdout, stderr = run_script_capture(__file__, args)
        if code != 0 and not stderr:
            stderr = f"Command failed with exit code {code}."
        render_output(output_widget, stdout, stderr)

    build_form("File Type Checklist Generator", fields, on_submit)


def main() -> None:
    if should_launch_gui():
        launch_gui()
        return

    args = parse_args()
    file_types = [ext.strip() for ext in args.types.split(",") if ext.strip()]
    if not file_types:
        print("Error: No file types provided.")
        sys.exit(1)

    markdown_output = generate_markdown_list(args.root_dir, file_types)
    output_path = os.path.join(get_output_base_dir(), "file_list.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_output)
    print("Markdown file generated: " + output_path)


if __name__ == "__main__":
    main()
