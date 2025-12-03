import pyodbc
import os

# Database connection details
server = '172.16.100.5'
database = 'DBK Suite BASE DEV'
username = 'Bks'
password = 'P1@niga'

tables_folder = 'Tables'
output_folder = 'changed-tables'
checked_tables = 0
modified_tables = 0
os.makedirs(output_folder, exist_ok=True)

# Connect to SQL Server
dsn = (
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password}'
)

print('Connecting to database...')
conn = pyodbc.connect(dsn)
cursor = conn.cursor()
print('Connected to database.')

# Get all tables


cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' AND TABLE_SCHEMA='dbo'")
tables = [row.TABLE_NAME for row in cursor.fetchall()]
# List .sql files in Tables folder
sql_files = [f for f in os.listdir(tables_folder) if f.lower().endswith('.sql')]
print(f'Found {len(sql_files)} .sql files in Tables folder.')
# Only process tables for which a .sql file exists
table_names_in_files = set(os.path.splitext(f)[0] for f in sql_files)
tables_to_process = [t for t in tables if t in table_names_in_files]
print(f'Processing {len(tables_to_process)} tables matching .sql files.')

def get_columns(table):
    cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table}' AND TABLE_SCHEMA = 'dbo'
    """)
    return cursor.fetchall()

def get_primary_keys(table):
    cursor.execute(f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
        AND TABLE_NAME = '{table}' AND TABLE_SCHEMA = 'dbo'
    """)
    return [row.COLUMN_NAME for row in cursor.fetchall()]
def get_foreign_keys(table):
    cursor.execute(f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsForeignKey') = 1
        AND TABLE_NAME = '{table}' AND TABLE_SCHEMA = 'dbo'
    """)
    return [row.COLUMN_NAME for row in cursor.fetchall()]

def column_def(col):
    name, dtype, maxlen, nullable = col
    if dtype.upper() in ['NVARCHAR', 'VARCHAR', 'CHAR', 'NCHAR']:
        if maxlen is None or maxlen < 0:
            type_str = f'{dtype.upper()}(MAX)'
        else:
            type_str = f'{dtype.upper()}({maxlen})'
    elif dtype.upper() == 'IMAGE':
        type_str = 'IMAGE'
    else:
        type_str = dtype.upper()
    null_str = 'NULL' if nullable == 'YES' else 'NOT NULL'
    return f'[{name}] {type_str} {null_str}'


def add_visual_cues(table, col_defs, pk_str):
    return f"""CREATE TABLE [dbo].[{table}]
(
    {col_defs}{pk_str}
)
"""

def parse_create_table(sql):
    import re
    # Extract columns, PKs, and comments from CREATE TABLE statement
    columns = []
    pk = []
    comments = {}
    col_pattern = re.compile(r'(--.*\n)?\s*\[(.*?)\]\s+(\w+(?:\(\d+\)|\(MAX\))?)\s+(NOT NULL|NULL|DEFAULT [^,\n]+)', re.IGNORECASE)
    pk_pattern = re.compile(r'PRIMARY KEY \((.*?)\)', re.IGNORECASE)
    lines = sql.splitlines()
    for i, line in enumerate(lines):
        comment_match = re.match(r'\s*--(.*)', line)
        if comment_match:
            next_line = lines[i+1] if i+1 < len(lines) else ''
            col_match = re.match(r'\s*\[(.*?)\]', next_line)
            if col_match:
                comments[col_match.group(1)] = line.strip()
        col_match = col_pattern.match(line)
        if col_match:
            columns.append((col_match.group(2), col_match.group(3), col_match.group(4)))
    pk_match = pk_pattern.search(sql)
    if pk_match:
        pk = [c.strip(' []') for c in pk_match.group(1).split(',')]
    return columns, pk, comments

tables_folder = 'Tables'
for table in tables_to_process:
    columns = get_columns(table)
    pk = get_primary_keys(table)
    col_defs_list = []
    # Check for discrepancies with Tables folder
    tables_path = os.path.join(tables_folder, f'{table}.sql')
    existing_comments = {}
    if os.path.exists(tables_path):
        with open(tables_path, 'r', encoding='utf-8') as f:
            existing_sql = f.read()
        existing_cols, existing_pk, existing_comments = parse_create_table(existing_sql)
    # Build column definitions, preserving comments
    for col in columns:
        col_name = col[0]
        comment = existing_comments.get(col_name, '')
        if comment:
            col_defs_list.append(f'{comment}\n    {column_def(col)}')
        else:
            col_defs_list.append(f'{column_def(col)}')
    col_defs = ',\n    '.join(col_defs_list)
    pk_str = ''
    if pk:
        pk_cols = ', '.join([f'[{c}]' for c in pk])
        pk_str = f',\n    CONSTRAINT [PK_{table}] PRIMARY KEY ({pk_cols})'

    # Foreign key constraints
    fk_constraints = []
    cursor.execute(f"""
        SELECT kcu.CONSTRAINT_NAME, kcu.COLUMN_NAME, ccu.TABLE_NAME AS REFERENCED_TABLE_NAME, ccu.COLUMN_NAME AS REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu ON rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
        JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu ON rc.UNIQUE_CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
        WHERE kcu.TABLE_NAME = '{table}' AND kcu.TABLE_SCHEMA = 'dbo'
    """)
    for row in cursor.fetchall():
        fk_constraints.append(f"CONSTRAINT [{row.CONSTRAINT_NAME}] FOREIGN KEY ([{row.COLUMN_NAME}]) REFERENCES [dbo].[{row.REFERENCED_TABLE_NAME}]([{row.REFERENCED_COLUMN_NAME}])")
    if fk_constraints:
        fk_str = ',\n    ' + ',\n    '.join(fk_constraints)
        create_stmt = f"CREATE TABLE [dbo].[{table}]\n(\n    {col_defs}{pk_str}{fk_str}\n)\n"
    else:
        create_stmt = add_visual_cues(table, col_defs, pk_str)

    # Compare new and existing structure
    if os.path.exists(tables_path):
        new_cols, new_pk, _ = parse_create_table(create_stmt)
        if existing_cols != new_cols or existing_pk != new_pk:
            with open(tables_path, 'w', encoding='utf-8') as f:
                f.write(create_stmt)
            modified = True
        else:
            modified = False
    else:
        with open(tables_path, 'w', encoding='utf-8') as f:
            f.write(create_stmt)
        modified = True

    checked_tables += 1
    if modified:
        modified_tables += 1
    print(f'Checked {checked_tables}/{len(tables)} tables. Modified: {modified_tables}', end='\r')

checked_tables = 0
modified_tables = 0
for table in tables:
    columns = get_columns(table)
    pk = get_primary_keys(table)
    col_defs_list = []
    tables_path = os.path.join(tables_folder, f'{table}.sql')
    existing_comments = {}
    if os.path.exists(tables_path):
        with open(tables_path, 'r', encoding='utf-8') as f:
            existing_sql = f.read()
        existing_cols, existing_pk, existing_comments = parse_create_table(existing_sql)
    for col in columns:
        col_name = col[0]
        comment = existing_comments.get(col_name, '')
        if comment:
            col_defs_list.append(f'{comment}\n    {column_def(col)}')
        else:
            col_defs_list.append(f'{column_def(col)}')
    col_defs = ',\n    '.join(col_defs_list)
    pk_str = ''
    if pk:
        pk_cols = ', '.join([f'[{c}]' for c in pk])
        pk_str = f',\n    CONSTRAINT [PK_{table}] PRIMARY KEY ({pk_cols})'
    fk_constraints = []
    cursor.execute(f"""
        SELECT kcu.CONSTRAINT_NAME, kcu.COLUMN_NAME, ccu.TABLE_NAME AS REFERENCED_TABLE_NAME, ccu.COLUMN_NAME AS REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu ON rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
        JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu ON rc.UNIQUE_CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
        WHERE kcu.TABLE_NAME = '{table}' AND kcu.TABLE_SCHEMA = 'dbo'
    """)
    for row in cursor.fetchall():
        fk_constraints.append(f"CONSTRAINT [{row.CONSTRAINT_NAME}] FOREIGN KEY ([{row.COLUMN_NAME}]) REFERENCES [dbo].[{row.REFERENCED_TABLE_NAME}]([{row.REFERENCED_COLUMN_NAME}])")
    if fk_constraints:
        fk_str = ',\n    ' + ',\n    '.join(fk_constraints)
        create_stmt = f"-- CREATE TABLE Statement for [{table}]\nCREATE TABLE [dbo].[{table}]\n(\n    {col_defs}{pk_str}{fk_str}\n)\n"
    else:
        create_stmt = add_visual_cues(table, col_defs, pk_str)
    checked_tables += 1
    modified = False
    if os.path.exists(tables_path):
        new_cols, new_pk, _ = parse_create_table(create_stmt)
        if existing_cols != new_cols or existing_pk != new_pk:
            with open(os.path.join(output_folder, f'{table}.sql'), 'w', encoding='utf-8') as f:
                f.write(create_stmt)
            modified = True
    else:
        with open(os.path.join(output_folder, f'{table}.sql'), 'w', encoding='utf-8') as f:
            f.write(create_stmt)
        modified = True
    if modified:
        modified_tables += 1
print(f'\nChecked {checked_tables}/{len(tables)} tables. Modified: {modified_tables}')

cursor.close()
conn.close()
