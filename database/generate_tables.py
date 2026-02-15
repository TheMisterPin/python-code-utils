#!/usr/bin/env python3
import argparse
import os
import sys

import pyodbc

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.gui_helpers import FieldSpec, build_form, render_output, run_script_capture
from utils.output_helpers import get_output_base_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate SQL table definitions from a SQL Server database.",
    )
    parser.add_argument("--server", default="172.16.100.5", help="SQL Server hostname or IP.")
    parser.add_argument("--database", default="DBK Suite BASE DEV", help="Database name.")
    parser.add_argument("--username", default="Bks", help="Database username.")
    parser.add_argument("--password", default="P1@niga", help="Database password.")
    parser.add_argument(
        "--tables-folder",
        default="Tables",
        help="Folder containing .sql table files.",
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
        FieldSpec(key="server", label="Server", field_type="text", default="172.16.100.5", required=True),
        FieldSpec(
            key="database",
            label="Database",
            field_type="text",
            default="DBK Suite BASE DEV",
            required=True,
        ),
        FieldSpec(key="username", label="Username", field_type="text", default="Bks", required=True),
        FieldSpec(
            key="password",
            label="Password",
            field_type="text",
            default="",
            required=True,
            show="*",
        ),
        FieldSpec(key="tables_folder", label="Tables folder", field_type="dir", default="Tables"),
    ]

    def on_submit(values, output_widget):
        args = [
            "--server",
            values["server"],
            "--database",
            values["database"],
            "--username",
            values["username"],
            "--password",
            values["password"],
            "--tables-folder",
            values["tables_folder"],
        ]
        code, stdout, stderr = run_script_capture(__file__, args)
        if code != 0 and not stderr:
            stderr = f"Command failed with exit code {code}."
        render_output(output_widget, stdout, stderr)

    build_form("Database Table Generator", fields, on_submit)


def run_git_command(cursor, query: str):
    cursor.execute(query)


def get_columns(cursor, table: str):
    cursor.execute(
        f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table}' AND TABLE_SCHEMA = 'dbo'
        """
    )
    return cursor.fetchall()


def get_primary_keys(cursor, table: str):
    cursor.execute(
        f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
        AND TABLE_NAME = '{table}' AND TABLE_SCHEMA = 'dbo'
        """
    )
    return [row.COLUMN_NAME for row in cursor.fetchall()]


def column_def(col):
    name, dtype, maxlen, nullable = col
    if dtype.upper() in ["NVARCHAR", "VARCHAR", "CHAR", "NCHAR"]:
        if maxlen is None or maxlen < 0:
            type_str = f"{dtype.upper()}(MAX)"
        else:
            type_str = f"{dtype.upper()}({maxlen})"
    elif dtype.upper() == "IMAGE":
        type_str = "IMAGE"
    else:
        type_str = dtype.upper()
    null_str = "NULL" if nullable == "YES" else "NOT NULL"
    return f"[{name}] {type_str} {null_str}"


def add_visual_cues(table: str, col_defs: str, pk_str: str) -> str:
    return (
        f"""CREATE TABLE [dbo].[{table}]
(
    {col_defs}{pk_str}
)
"""
    )


def parse_create_table(sql: str):
    import re

    columns = []
    pk = []
    comments = {}
    col_pattern = re.compile(
        r"(--.*\n)?\s*\[(.*?)\]\s+(\w+(?:\(\d+\)|\(MAX\))?)\s+(NOT NULL|NULL|DEFAULT [^,\n]+)",
        re.IGNORECASE,
    )
    pk_pattern = re.compile(r"PRIMARY KEY \((.*?)\)", re.IGNORECASE)
    lines = sql.splitlines()
    for i, line in enumerate(lines):
        comment_match = re.match(r"\s*--(.*)", line)
        if comment_match:
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            col_match = re.match(r"\s*\[(.*?)\]", next_line)
            if col_match:
                comments[col_match.group(1)] = line.strip()
        col_match = col_pattern.match(line)
        if col_match:
            columns.append((col_match.group(2), col_match.group(3), col_match.group(4)))
    pk_match = pk_pattern.search(sql)
    if pk_match:
        pk = [c.strip(" []") for c in pk_match.group(1).split(",")]
    return columns, pk, comments


def generate_tables(server: str, database: str, username: str, password: str, tables_folder: str) -> None:
    output_folder = os.path.join(get_output_base_dir(), "changed-tables")
    checked_tables = 0
    modified_tables = 0

    os.makedirs(output_folder, exist_ok=True)

    dsn = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password}"
    )

    print("Connecting to database...")
    conn = pyodbc.connect(dsn)
    cursor = conn.cursor()
    print("Connected to database.")

    cursor.execute(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' AND TABLE_SCHEMA='dbo'"
    )
    tables = [row.TABLE_NAME for row in cursor.fetchall()]

    if not os.path.isdir(tables_folder):
        print(f"Error: Tables folder not found: {tables_folder}")
        return

    sql_files = [f for f in os.listdir(tables_folder) if f.lower().endswith(".sql")]
    print(f"Found {len(sql_files)} .sql files in Tables folder.")

    table_names_in_files = set(os.path.splitext(f)[0] for f in sql_files)
    tables_to_process = [t for t in tables if t in table_names_in_files]
    print(f"Processing {len(tables_to_process)} tables matching .sql files.")

    for table in tables_to_process:
        columns = get_columns(cursor, table)
        pk = get_primary_keys(cursor, table)
        col_defs_list = []
        tables_path = os.path.join(tables_folder, f"{table}.sql")
        existing_comments = {}
        if os.path.exists(tables_path):
            with open(tables_path, "r", encoding="utf-8") as f:
                existing_sql = f.read()
            existing_cols, existing_pk, existing_comments = parse_create_table(existing_sql)

        for col in columns:
            col_name = col[0]
            comment = existing_comments.get(col_name, "")
            if comment:
                col_defs_list.append(f"{comment}\n    {column_def(col)}")
            else:
                col_defs_list.append(f"{column_def(col)}")
        col_defs = ",\n    ".join(col_defs_list)
        pk_str = ""
        if pk:
            pk_cols = ", ".join([f"[{c}]" for c in pk])
            pk_str = f",\n    CONSTRAINT [PK_{table}] PRIMARY KEY ({pk_cols})"

        fk_constraints = []
        cursor.execute(
            f"""
            SELECT kcu.CONSTRAINT_NAME, kcu.COLUMN_NAME, ccu.TABLE_NAME AS REFERENCED_TABLE_NAME, ccu.COLUMN_NAME AS REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu ON rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu ON rc.UNIQUE_CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
            WHERE kcu.TABLE_NAME = '{table}' AND kcu.TABLE_SCHEMA = 'dbo'
            """
        )
        for row in cursor.fetchall():
            fk_constraints.append(
                f"CONSTRAINT [{row.CONSTRAINT_NAME}] FOREIGN KEY ([{row.COLUMN_NAME}]) REFERENCES [dbo].[{row.REFERENCED_TABLE_NAME}]([{row.REFERENCED_COLUMN_NAME}])"
            )
        if fk_constraints:
            fk_str = ",\n    " + ",\n    ".join(fk_constraints)
            create_stmt = (
                f"CREATE TABLE [dbo].[{table}]\n(\n    {col_defs}{pk_str}{fk_str}\n)\n"
            )
        else:
            create_stmt = add_visual_cues(table, col_defs, pk_str)

        if os.path.exists(tables_path):
            new_cols, new_pk, _ = parse_create_table(create_stmt)
            if existing_cols != new_cols or existing_pk != new_pk:
                with open(tables_path, "w", encoding="utf-8") as f:
                    f.write(create_stmt)
                modified = True
            else:
                modified = False
        else:
            with open(tables_path, "w", encoding="utf-8") as f:
                f.write(create_stmt)
            modified = True

        checked_tables += 1
        if modified:
            modified_tables += 1
        print(f"Checked {checked_tables}/{len(tables)} tables. Modified: {modified_tables}", end="\r")

    checked_tables = 0
    modified_tables = 0
    for table in tables:
        columns = get_columns(cursor, table)
        pk = get_primary_keys(cursor, table)
        col_defs_list = []
        tables_path = os.path.join(tables_folder, f"{table}.sql")
        existing_comments = {}
        if os.path.exists(tables_path):
            with open(tables_path, "r", encoding="utf-8") as f:
                existing_sql = f.read()
            existing_cols, existing_pk, existing_comments = parse_create_table(existing_sql)
        else:
            existing_cols = []
            existing_pk = []

        for col in columns:
            col_name = col[0]
            comment = existing_comments.get(col_name, "")
            if comment:
                col_defs_list.append(f"{comment}\n    {column_def(col)}")
            else:
                col_defs_list.append(f"{column_def(col)}")
        col_defs = ",\n    ".join(col_defs_list)
        pk_str = ""
        if pk:
            pk_cols = ", ".join([f"[{c}]" for c in pk])
            pk_str = f",\n    CONSTRAINT [PK_{table}] PRIMARY KEY ({pk_cols})"
        fk_constraints = []
        cursor.execute(
            f"""
            SELECT kcu.CONSTRAINT_NAME, kcu.COLUMN_NAME, ccu.TABLE_NAME AS REFERENCED_TABLE_NAME, ccu.COLUMN_NAME AS REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu ON rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu ON rc.UNIQUE_CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
            WHERE kcu.TABLE_NAME = '{table}' AND kcu.TABLE_SCHEMA = 'dbo'
            """
        )
        for row in cursor.fetchall():
            fk_constraints.append(
                f"CONSTRAINT [{row.CONSTRAINT_NAME}] FOREIGN KEY ([{row.COLUMN_NAME}]) REFERENCES [dbo].[{row.REFERENCED_TABLE_NAME}]([{row.REFERENCED_COLUMN_NAME}])"
            )
        if fk_constraints:
            fk_str = ",\n    " + ",\n    ".join(fk_constraints)
            create_stmt = (
                f"-- CREATE TABLE Statement for [{table}]\nCREATE TABLE [dbo].[{table}]\n(\n    {col_defs}{pk_str}{fk_str}\n)\n"
            )
        else:
            create_stmt = add_visual_cues(table, col_defs, pk_str)
        checked_tables += 1
        modified = False
        if os.path.exists(tables_path):
            new_cols, new_pk, _ = parse_create_table(create_stmt)
            if existing_cols != new_cols or existing_pk != new_pk:
                with open(os.path.join(output_folder, f"{table}.sql"), "w", encoding="utf-8") as f:
                    f.write(create_stmt)
                modified = True
        else:
            with open(os.path.join(output_folder, f"{table}.sql"), "w", encoding="utf-8") as f:
                f.write(create_stmt)
            modified = True
        if modified:
            modified_tables += 1

    print(f"\nChecked {checked_tables}/{len(tables)} tables. Modified: {modified_tables}")

    cursor.close()
    conn.close()


def main() -> None:
    if should_launch_gui():
        launch_gui()
        return

    args = parse_args()
    generate_tables(args.server, args.database, args.username, args.password, args.tables_folder)


if __name__ == "__main__":
    main()
