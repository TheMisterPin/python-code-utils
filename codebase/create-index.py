import os
import sys

def create_barrel(folder):
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

    ts_files = sorted(set(ts_files))  # ensure uniqueness

    lines = []

    # Export subfolders first
    for sub in sorted(subfolders):
        lines.append(f'export * from "./{sub}";')

    # Export TS and TSX files
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


def walk(root):
    """
    Recursively walks through all directories and creates barrel files.
    """
    for folder, subdirs, files in os.walk(root):
        create_barrel(folder)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create-index.py <target_folder>")
        print("Example: python create-index.py C:\\Projects\\my-app\\src")
        sys.exit(1)

    target_folder = sys.argv[1]
    
    if not os.path.exists(target_folder):
        print(f"Error: Target folder does not exist: {target_folder}")
        sys.exit(1)
    
    if not os.path.isdir(target_folder):
        print(f"Error: Target path is not a directory: {target_folder}")
        sys.exit(1)
    
    print(f"Scanning: {os.path.abspath(target_folder)}\n")
    walk(target_folder)
    print(f"\nDone! All index.ts files have been created/updated in: {os.path.abspath(target_folder)}")
