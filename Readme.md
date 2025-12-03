# Python Code Utils

A collection of focused Python tooling for the everyday workflows that feel too boring to build from scratch every time. Each folder bundles a handful of scripts that solve a particular category of tasks; the section below points to the folder-level documentation and the scripts that belong there.

## Getting Started

- **Python version & virtual environment** – Install Python 3.11+ and run `python -m venv .venv` followed by `\.venv\Scripts\Activate.ps1` from PowerShell so you work inside an isolated interpreter.
- **Core dependencies** – The scripts currently rely on `pandas`, `pyodbc`, `google-auth`, `google-auth-oauthlib`, `google-api-python-client`, `pytz`, and `requests`. Install them with `pip install pandas pyodbc google-auth google-auth-oauthlib google-api-python-client pytz requests`; the extractor/generator helpers otherwise only use the standard library.
- **External services & secrets** – `database/generate_tables.py` requires a reachable SQL Server and a working ODBC driver (the script is already set up for `ODBC Driver 17 for SQL Server`), and you must edit the hard-coded `server`, `database`, `username`, and `password` before running. `Email/email-deleter.py` expects `credentials.json` in the folder and writes `token.pickle` on the first OAuth handshake. `documents/generators/write-docs.py` posts prompts to Ollama (`http://127.0.0.1:11434/api/generate`), so ensure Ollama + `MODEL_NAME` are available locally.
- **Running the scripts** – Pick a folder, consult its README for parameters, and invoke the helper with `python <path/to/script>.py`. Most tools print progress and sample output so you can chain operations (e.g., extract docstrings ➜ list endpoints ➜ fill documentation) without guesswork.

## Utilities
- Interactive password creation is handled by [Password-Generator/password_generator.py](Password-Generator/password_generator.py). It asks for a minimum length and whether numbers or punctuation should be included, then guarantees the generated password meets those criteria. See [Password-Generator/Readme.md](Password-Generator/Readme.md) for the full guide.

## File Handling
The `file` folder keeps desktop helpers for curating downloads and auditing directories. See [file/Readme.md](file/Readme.md) for configuration tips.
- [file/file-organizer.py](file/file-organizer.py) watches a Downloads-style folder, sorts media, docs, archives, installers, and code into typed subdirectories, and shows how to update the folder map.
- [file/list-files-by-type.py](file/list-files-by-type.py) walks a target directory tree, lists files with the configured extensions, and writes the result to `file_list.md` for quick audits.

## Email
- [Email/email-deleter.py](Email/email-deleter.py) connects to Gmail via OAuth (requires `credentials.json` + `token.pickle`), then walks through unread promotional mail in batches to keep the inbox lean. See [Email/Readme.md](Email/Readme.md) for the UI flow and running tips.

## Documents
The `documents` folder hosts two sets of utilities: extraction helpers and generator helpers. Read the landing page ([documents/Readme.md](documents/Readme.md)) for how they fit together, then dive into [documents/extractors/Readme.md](documents/extractors/Readme.md) and [documents/generators/Readme.md](documents/generators/Readme.md) for script-by-script guidance. Key capabilities include:
- Extracting Python, TypeScript/JavaScript, and C# docstrings or comments into Markdown using the dedicated scripts in `documents/extractors`.
- Producing API reference markdown and filling in placeholder documentation via the tools in `documents/generators`.

## Database
- [database/generate_tables.py](database/generate_tables.py) connects to the SQL Server catalog, compares the live schema with local `.sql` files in `database/Tables`, and rewrites the `Tables` definitions plus the `_outputs/changed-tables` snapshots when differences appear. More context is in [database/Readme.md](database/Readme.md).

## Converters
- [converters/csv-converter.py](converters/csv-converter.py) pivots `converters/dataset/dataset.csv` into `submission.json` via pandas. See [converters/Readme.md](converters/Readme.md) for the CLI steps.

## Source Control
See [source-control/Readme.md](source-control/Readme.md) for how to run the git-diff tooling.
- [source-control/diffs_by_week.py](source-control/diffs_by_week.py) is the main Python helper: it inspects recent commits, writes daily `.patch` files under `_outputs/rawdiffs/by-day`, and dumps a JSON summary to `_outputs/summary.json`.
- [source-control/get_diffs_branch.py](source-control/get_diffs_branch.py) is currently a placeholder for future branch-level exports.

## Contributing
Feel free to fork the repository, make changes, and submit pull requests. If you have ideas for new automation helpers or improvements to existing scripts, drop a PR and description.

## License
This project is open-source and available under the [MIT License](LICENSE).
