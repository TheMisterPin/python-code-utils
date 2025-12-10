import os
import re
from pathlib import Path
import sys
import argparse
import time
import json

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.output_helpers import get_output_base_dir

def normalize_endpoint(endpoint: str) -> str:
    """Normalize endpoint string by removing query strings and trailing slashes."""
    # Remove query strings if present
    endpoint = endpoint.split('?', 1)[0]
    # Remove any trailing slashes
    endpoint = endpoint.rstrip('/')
    return endpoint

def strip_string_literals(s: str) -> str:
    """Replace string literal contents with spaces, preserving length and indices.
    Handles single, double and backtick-quoted strings with simple escape handling."""
    string_re = re.compile(r"('(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`)", re.DOTALL)
    def _repl(m):
        return ' ' * (m.end() - m.start())
    return string_re.sub(_repl, s)

def build_comment_ranges(s: str):
    """Return list of (start, end) ranges for comments in the source string.
    Single-line comments (//...) and multi-line (/* ... */) are detected. Assumes strings are removed."""
    ranges = []
    # Single-line comments
    for m in re.finditer(r'//.*?$' , s, flags=re.MULTILINE):
        ranges.append((m.start(), m.end()))
    # Multi-line comments
    for m in re.finditer(r'/\*[\s\S]*?\*/', s):
        ranges.append((m.start(), m.end()))
    return ranges

def is_pos_in_ranges(pos: int, ranges) -> bool:
    for a, b in ranges:
        if a <= pos < b:
            return True
    return False

def find_api_references(root_dir, debug=False, debug_output=None):
    # We'll extract '/Api/...' occurrences that appear inside string literals
    string_re = re.compile(r"""(?:(?:\"(?:\\.|[^\"\\])*\")|(?:'(?:\\.|[^'\\])*)|(?:`(?:\\.|[^`\\])*) )""", re.DOTALL)
    endpoints = {}
    debug_entries = []  # Collect debug info here

    # Prefer the 'src' folder under the root if present
    src_dir = Path(root_dir) / 'src'
    if src_dir.exists() and src_dir.is_dir():
        ts_files = [p for p in src_dir.rglob("*.ts") if 'node_modules' not in p.parts]
        print(f"Scanning only under {src_dir} (excluding node_modules)")
    else:
        print(f"Warning: no 'src' folder found under {root_dir}; falling back to entire tree (excluding node_modules)")
        ts_files = [p for p in Path(root_dir).rglob("*.ts") if 'node_modules' not in p.parts]
    total_files = len(ts_files)
    print(f"Found {total_files} TypeScript files to scan.")

    for idx, ts_file in enumerate(ts_files, start=1):
        # Visual feedback: show progress line
        print(f"Processing {idx}/{total_files}: {ts_file}", end='\r', flush=True)
        try:
            with open(ts_file, 'r', encoding='utf-8') as f:
                content = f.read()

                # Prepare a version with string literals stripped so comment detection is robust
                stripped = strip_string_literals(content)
                comment_ranges = build_comment_ranges(stripped)

                # Iterate string literals and pick those containing /Api/
                for m in string_re.finditer(content):
                    # If string literal itself is inside a comment, skip
                    in_comment = is_pos_in_ranges(m.start(), comment_ranges)
                    s = m.group(0)
                    if len(s) < 3:
                        continue
                    inner = s[1:-1]
                    start_search = 0
                    while True:
                        p = inner.find('/Api/', start_search)
                        if p == -1:
                            break
                        raw = inner[p + len('/Api/'):]
                        # conservative trimming: stop at common concatenation or interpolation
                        cleaned = re.split(r"""[\s+\"'`{(,)]""", raw)[0]
                        cleaned = cleaned.strip()
                        captured = cleaned if cleaned else ''
                        entry = {
                            'file': str(ts_file),
                            'line': content.count('\n', 0, m.start()) + 1,
                            'method': 'string',
                            'in_comment': in_comment,
                            'raw': raw,
                            'captured': captured,
                            'action': 'captured' if captured and not in_comment else ('ignored_comment' if in_comment else 'trimmed')
                        }
                        if debug:
                            debug_entries.append(entry)

                        if captured and not in_comment:
                            endpoint_norm = normalize_endpoint(captured)
                            endpoints.setdefault(endpoint_norm, set()).add(Path(ts_file).name)

                        start_search = p + len('/Api/')

                # Also perform a loose regex scan for /Api/ occurrences outside strings
                loose_re = re.compile(r"/Api/([^\"'`\s)\];,]*)")
                for m in loose_re.finditer(content):
                    in_comment = is_pos_in_ranges(m.start(), comment_ranges)
                    raw = m.group(1)
                    # trim further conservative separators
                    cleaned = re.split(r"""[\s+\"'`{(,)]""", raw)[0].strip()
                    entry = {
                        'file': str(ts_file),
                        'line': content.count('\n', 0, m.start()) + 1,
                        'method': 'regex',
                        'in_comment': in_comment,
                        'raw': raw,
                        'captured': cleaned,
                        'action': 'captured' if cleaned and not in_comment else ('ignored_comment' if in_comment else 'trimmed')
                    }
                    if debug:
                        debug_entries.append(entry)
                    if cleaned and not in_comment:
                        endpoint_norm = normalize_endpoint(cleaned)
                        endpoints.setdefault(endpoint_norm, set()).add(Path(ts_file).name)
        except Exception as e:
            # Print the error on its own line so it doesn't break the progress line
            print(f"\nError reading {ts_file}: {e}")

    # End the progress line
    print('\nScan complete.')
    # Write debug information if requested
    if debug and debug_output:
        try:
            with open(debug_output, 'w', encoding='utf-8') as out:
                for e in debug_entries:
                    out.write(json.dumps(e, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Error writing debug output {debug_output}: {e}")
    return endpoints

def generate_markdown(endpoints, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for endpoint in sorted(endpoints.keys()):
            f.write(f"### {endpoint}\n")
            for filename in sorted(endpoints[endpoint]):
                f.write(f"- `{filename}`\n")
            f.write("\n")

    print(f"Wrote {len(endpoints)} unique endpoints to {output_file}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract /Api/ endpoints from TypeScript files and emit a Markdown list of references.")
    parser.add_argument('root_directory', nargs='?', default='.',
                        help='Root directory to scan (defaults to current directory)')
    parser.add_argument('-o', '--output', default='api_references.md',
                        help='Output markdown file (default: api_references.md)')
    parser.add_argument('--quiet', action='store_true', help='suppress progress output')
    parser.add_argument('--debug', action='store_true', help='log debug info for every /Api/ occurrence')
    parser.add_argument('--debug-output', default='api_references_debug.log', help='Path to write debug log (JSON lines)')
    args = parser.parse_args()

    root_directory = args.root_directory
    output_md = args.output or os.path.join(get_output_base_dir(), "api_references.md")

    if not os.path.isdir(root_directory):
        print(f"Error: Invalid directory path: {root_directory}")
        sys.exit(1)

    try:
        if args.quiet:
            endpoints = find_api_references(root_directory, debug=args.debug, debug_output=args.debug_output)
        else:
            endpoints = find_api_references(root_directory, debug=args.debug, debug_output=args.debug_output)

        # Compute summary statistics for CLI
        unique_endpoints = len(endpoints)
        files_set = set()
        total_references = 0
        for s in endpoints.values():
            files_set.update(s)
            total_references += len(s)
        files_count = len(files_set)
        print(f"Found {unique_endpoints} unique endpoints in {files_count} files ({total_references} total references).")

        generate_markdown(endpoints, output_md)
        print(f"Markdown file generated: {output_md}")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
