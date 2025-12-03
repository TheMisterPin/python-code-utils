# Extractors

Each script in this folder crawls through a codebase, grabs the structured documentation that already lives in docstrings/comments, and emits Markdown files you can open, review, or ship to other teams.

## extract-docs.py

**Features**
- AST-based parser for Python modules, functions, and classes.
- Skips files with no docstrings or docstrings that are shorter than three lines so the output only keeps meaningful content.
- Writes a Markdown file per Python source inside the specified output directory (default: `./extracted`).

**How to Run**
1. `python documents/extractors/extract-docs.py path/to/your/python/project`
2. Optionally add `--output ./docs/out` to change the target folder.

**Usage Example**
```
$ python documents/extractors/extract-docs.py my_service -o docs/extracted
Found 12 Python files
Output directory: docs/extracted
Processed 9 files with substantial docstrings successfully!
```

## extract-docs-py.py

**Features**
- Similar to `extract-docs.py` but adds metadata headers (project name, language) to each Markdown file.
- Persists structured summaries for modules, functions, and classes so downstream tooling can parse the pages again.

**How to Run**
1. `python documents/extractors/extract-docs-py.py path/to/python/code`
2. The output defaults to `./extracted`; use `-o` to override.

**Usage Example**
```
$ python documents/extractors/extract-docs-py.py ./packages/core
Found 45 Python files
Output directory: ./extracted
Project: core
```

## extract-docs-ts.py

**Features**
- Complex JSDoc parser that understands `@param`, `@returns`, `@api`, and custom tags.
- Respects TypeScript and JavaScript files, mirrors folder structure inside the Markdown target, and keeps metadata such as version, author, and component names.

**How to Run**
1. `python documents/extractors/extract-docs-ts.py path/to/ts-project`
2. Use `-o docs/generated` to set the destination for the Markdown files.

**Usage Example**
```
$ python documents/extractors/extract-docs-ts.py ./frontend/src -o docs/generated
Found 127 TypeScript/JavaScript files
Output directory: docs/generated
Project: src
```

## extract-docs-cs.py

**Features**
- Targets C# files, detecting `///` XML doc comments for classes, methods, properties, enums, and structs.
- Writes Markdown files that inherit the folder structure from the scanned project (helpful for large ASP.NET trees).

**How to Run**
1. `python documents/extractors/extract-docs-cs.py path/to/csharp/project`
2. Add `-o docs/cs` to customize the output directory.

**Usage Example**
```
$ python documents/extractors/extract-docs-cs.py ./server -o docs/csharp
Found 38 C# files
Output directory: docs/csharp
Project: server
```

## extract-endpoints.py

**Features**
- Scans `.ts` files (prefers `src/` if present) and captures every `/Api/` string literal or loose regex match.
- Normalizes `/Api/Controller/Action` routes, skips references inside comments, and optionally dumps debug JSON logs.
- Writes the final list of unique endpoints to `api_references.md` (default path) and prints summary statistics.

**How to Run**
1. `python documents/extractors/extract-endpoints.py` from the repo root to scan `.`.
2. Pass `--quiet` to suppress progress lines or `--debug --debug-output debug.log` to log every candidate.

**Usage Example**
```
$ python documents/extractors/extract-endpoints.py ./webapp --output docs/api_references.md
Found 214 TypeScript files to scan.
Scan complete.
Found 82 unique endpoints in 27 files (102 total references).
Markdown file generated: docs/api_references.md
```
