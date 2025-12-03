# Schema Snapshot Generator

`generate_tables.py` walks the live SQL Server catalog next to the `.sql` files stored under `database/Tables`. It rewrites any local schema definitions that diverge from the database and records the new CREATE TABLE statements inside `_outputs/changed-tables` so you can review what changed without blindly overwriting the repo.

## Features

- Connects to SQL Server through `pyodbc` and the `ODBC Driver 17 for SQL Server`.
- Reads every table in `dbo`, fetches column metadata, primary keys, and foreign keys, and assembles a CREATE TABLE statement that mirrors what is actually deployed.
- Annotates the generated SQL using the comments already present in `database/Tables` and only rewrites files that experienced schema drift.
- Saves snapshots of changed tables under `_outputs/changed-tables` so the diff history is explicit.

## Requirements & Configuration

1. Install `pyodbc` (`pip install pyodbc`) and be able to load the ODBC driver listed in the script.
2. Update the hard-coded `server`, `database`, `username`, and `password` with credentials that can read `INFORMATION_SCHEMA`.
3. Ensure `database/Tables` contains at least one `.sql` file per table you want to keep in sync.

## How to Run

1. From the repository root, execute `python database/generate_tables.py`.
2. The script compares the live schema to every file in `database/Tables` and overwrites each `.sql` that changed, including the PK/FK clauses.
3. For every modified table, a copy of the final CREATE TABLE is stored in `_outputs/changed-tables/<TableName>.sql` so you can inspect the adjustments.

## Usage Example

```
$ python database/generate_tables.py
Connecting to database...
Connected to database.
Found 42 .sql files in Tables folder.
Processing 38 tables matching .sql files.
Checked 38/200 tables. Modified: 3

Checked 200/200 tables. Modified: 5
```

Keep an eye on `_outputs/changed-tables` to capture any schema drift that deserves a PR rather than a blind overwrite.
