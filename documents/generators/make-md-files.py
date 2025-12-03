#!/usr/bin/env python3
"""
Recursively walk the `src` tree, find every *.ts file, and generate a
mirrored *.md file inside `docs/generated`, preserving the original
directory structure relative to `src`.

Usage
-----
# From the root of the project (defaults to src -> docs/generated)
#   python docs/tools/make-md-files.py

# Custom source/destination
#   python docs/tools/make-md-files.py path/to/source --dest docs/custom
"""

import argparse
from pathlib import Path
import sys

# Patterns to exclude (files we don't want to document)
EXCLUDED_PATTERNS = [
    'routing.module.ts',
    '.module.ts'
]

def process_folder(source_root: Path, not_documented_file: Path) -> None:
    """
    Walk *source_root* recursively, locate *.ts files and add them to the
    not-documented list, skipping excluded patterns.
    """
    with not_documented_file.open("w", encoding="utf-8") as f:
        f.write("# File non documentati\n\n")
        for ts_file in source_root.rglob("*.ts"):
            # Skip excluded files
            if any(pattern in ts_file.name for pattern in EXCLUDED_PATTERNS):
                print(f"Skipped: {ts_file} (excluded pattern)")
                continue
            
            relative_path = ts_file.relative_to(source_root)
            f.write(f"- {ts_file.name}: {ts_file}\n")
            print(f"Added to list: {ts_file}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create .md files mirroring a *.ts tree inside docs/generated."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default="src",
        help="Source folder to process (relative to the project root). "
             "Defaults to 'src'."
    )
    parser.add_argument(
        "--dest",
        default="docs/autodocs/generated",
        help="Destination root for generated markdown (relative to the project root)."
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    source_root = (project_root / args.folder).resolve()
    destination_root = (project_root / args.dest).resolve()
    not_documented_file = project_root / "docs" / "autodocs" / "not-documented.md"

    if not source_root.is_dir():
        print(f"Error: {source_root} is not a directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {source_root} …")
    print(f"Generating not-documented.md …")
    process_folder(source_root, not_documented_file)
    print("Done.")

if __name__ == "__main__":
    main()