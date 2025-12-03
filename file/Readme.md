# File Handling Helpers

This folder contains desktop-first utilities to keep a Downloads-like folder organized and get quick inventories of files that match specific extensions.

## file-organizer.py

**Features**
- Defines destination folders for images, video, audio, documents, archives, Unity packages, installers, UI kits, and code so everything in `Downloads` has a predictable place.
- Creates the directories if they do not already exist and moves each matching file by extension.

**How to Run**
1. Update the `source_dir` and destination paths at the top of the script to match your environment (the current defaults assume Windows user paths).
2. Run `python file/file-organizer.py` from the repository root.
3. Watch for permissions issues if files are in use; the script currently moves files synchronously.

**Usage Example**
```
$ python file/file-organizer.py
Moved 132 files from C:\Users\You\Downloads into the categorized subfolders.
```

## list-files-by-type.py

**Features**
- Walks the configured `root_dir` tree (defaults to an Ionic app path) and only includes folders that contain files matching the `file_types` list.
- Outputs a Markdown hierarchy (`file_list.md`) that shows the directory structure and lists files still pending review.

**How to Run**
1. Set `root_dir` to the directory you want to audit and extend `file_types` with the extensions you care about.
2. `python file/list-files-by-type.py` rewrites `file_list.md` with the latest results.

**Usage Example**
```
$ python file/list-files-by-type.py
Markdown file generated: file_list.md
```

Open `file_list.md` to quickly scan where the targeted files live; it uses nested headers to represent the folder depth.
