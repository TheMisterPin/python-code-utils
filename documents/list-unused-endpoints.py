import os
import re
from pathlib import Path
import sys
import argparse

# Utilities copied/adapted from extract-endpoints.py to handle comments and strings
def strip_string_literals(s: str) -> str:
    string_re = re.compile(r"('(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`)", re.DOTALL)
    def _repl(m):
        return ' ' * (m.end() - m.start())
    return string_re.sub(_repl, s)

def build_comment_ranges(s: str):
    ranges = []
    for m in re.finditer(r'//.*?$' , s, flags=re.MULTILINE):
        ranges.append((m.start(), m.end()))
    for m in re.finditer(r'/\*[\s\S]*?\*/', s):
        ranges.append((m.start(), m.end()))
    return ranges

def is_pos_in_ranges(pos: int, ranges) -> bool:
    for a, b in ranges:
        if a <= pos < b:
            return True
    return False

def normalize_endpoint(endpoint: str) -> str:
    endpoint = endpoint.split('?', 1)[0]
    endpoint = endpoint.rstrip('/')
    return endpoint

def extract_controller_info(content: str):
    # Find class name (Controller) and class-level Route attribute (if any)
    # We search for pattern: [Route("...")] optionally before class
    class_route = None
    class_name = None

    # Remove strings for safer detection
    stripped = strip_string_literals(content)
    # Find class name
    class_match = re.search(r'class\s+([A-Za-z0-9_]*Controller)\b', stripped)
    if class_match:
        class_name = class_match.group(1)
    # Find the nearest Route attribute before the class definition
    if class_match:
        upto = class_match.start()
        before = stripped[max(0, upto-800):upto]
        route_match = re.search(r'\[Route\s*\(\s*"([^"]+)"\s*\)\]', before, re.IGNORECASE)
        if route_match:
            class_route = route_match.group(1)
    # Detect class-level AllowAnonymous
    class_allowanonymous = False
    if class_match:
        before_lower = before.lower() if 'before' in locals() and before is not None else ''
        if re.search(r'\[allowanonymous\]', before_lower, re.IGNORECASE):
            class_allowanonymous = True
    return class_name, class_route, class_allowanonymous

def find_post_endpoints(root_dir, anonymous_only=False):
    # Find Controller.cs files (case-insensitive) excluding bin/obj
    cs_files = [p for p in Path(root_dir).rglob("*.cs") if p.name.lower().endswith('controller.cs') and 'bin' not in p.parts and 'obj' not in p.parts]
    total = len(cs_files)
    print(f"Found {total} controller files to scan.")

    endpoints = {}

    # Patterns
    http_post_attr_block_re = re.compile(r'\[(?:[^\]]*?HttpPost[^\]]*?)\]', re.IGNORECASE | re.DOTALL)
    route_attr_re = re.compile(r'\[Route\s*\(\s*"([^"]+)"\s*\)\]', re.IGNORECASE)
    allowanonymous_attr_re = re.compile(r'\[AllowAnonymous\]', re.IGNORECASE)
    # method signature capture: access modifiers + return type + name(
    method_sig_re = re.compile(r'\b(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?[\w<>,\s\[\]]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', re.MULTILINE)

    for idx, cs_file in enumerate(cs_files, start=1):
        print(f"Processing {idx}/{total}: {cs_file}", end='\r', flush=True)
        try:
            content = cs_file.read_text(encoding='utf-8')
            stripped = strip_string_literals(content)
            comment_ranges = build_comment_ranges(stripped)

            class_name, class_route, class_allowanonymous = extract_controller_info(content)
            controller_base = None
            if class_name:
                controller_base = class_name
                if controller_base.lower().endswith('controller'):
                    controller_base = controller_base[:-10]  # remove 'Controller'

            for m in http_post_attr_block_re.finditer(content):
                # Ignore if attribute inside comment
                if is_pos_in_ranges(m.start(), comment_ranges):
                    continue

                attr_text = m.group(0)
                # Try to extract route from the attribute itself
                route_in_attr = None
                q = re.search(r'"([^"]+)"', attr_text)
                if q:
                    route_in_attr = q.group(1)

                # Look ahead for method signature to get method name
                after_pos = m.end()
                method_match = method_sig_re.search(content, after_pos)
                method_name = method_match.group(1) if method_match else None

                # Also check for Route attribute between attribute and method (or right before attribute)
                method_route = route_in_attr
                if not method_route:
                    # search small window around attribute for Route attribute
                    window_start = max(0, m.start() - 200)
                    window_end = min(len(content), m.end() + 200)
                    window = content[window_start:window_end]
                    rm = route_attr_re.search(window)
                    if rm:
                        method_route = rm.group(1)
                if not method_route and method_name:
                    method_route = method_name

                # Build the full route string. Always prefix with the controller base so
                # we get ControllerName/Action form even if method has a route.
                combined_parts = []
                if class_route:
                    # class-level route wins as the base
                    combined_parts.append(class_route)
                elif controller_base:
                    combined_parts.append(controller_base)

                # Prefer the explicit method-level route if present, otherwise method name
                if method_route:
                    combined_parts.append(method_route)
                elif method_name:
                    combined_parts.append(method_name)

                combined = '/'.join([p for p in combined_parts if p])

                # Replace tokens
                if controller_base:
                    combined = combined.replace('[controller]', controller_base)
                if method_name:
                    combined = combined.replace('[action]', method_name)

                combined = normalize_endpoint(combined)

                # Detect AllowAnonymous for this method: in the attribute block itself or nearby,
                # or inherited from the class-level AllowAnonymous
                method_allowanonymous = False
                # Check attribute block text
                if allowanonymous_attr_re.search(attr_text):
                    method_allowanonymous = True
                # Check the same small window for a Route or AllowAnonymous
                if not method_allowanonymous:
                    window_aa = re.search(r'\[AllowAnonymous\]', window, re.IGNORECASE) if 'window' in locals() else None
                    if window_aa:
                        method_allowanonymous = True
                # If not found at method, inherit from class
                if not method_allowanonymous and class_allowanonymous:
                    method_allowanonymous = True

                # If caller requested only anonymous endpoints and this one isn't anonymous, skip it
                if anonymous_only and not method_allowanonymous:
                    continue

                if combined not in endpoints:
                    endpoints[combined] = set()
                endpoints[combined].add(Path(cs_file).name)

        except Exception as e:
            print(f"\nError reading {cs_file}: {e}")

    print('\nScan complete.')
    return endpoints


def generate_markdown(endpoints, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for endpoint in sorted(endpoints.keys()):
            f.write(f"### {endpoint}\n")
            for filename in sorted(endpoints[endpoint]):
                f.write(f"- `{filename}`\n")
            f.write("\n")
    print(f"Wrote {len(endpoints)} unique POST endpoints to {output_file}.")


def load_ts_references(md_path: str):
    """Parse a markdown file produced by extract-endpoints.py and return a mapping
    of endpoint (string) -> set of filenames that reference it."""
    refs = {}
    try:
        text = Path(md_path).read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading references markdown {md_path}: {e}")
        return refs

    current = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('### '):
            current = line[4:].strip()
            refs[current.lower()] = set()
            continue
        if current and line.startswith('- `') and line.endswith('`'):
            filename = line[3:-1].strip()
            refs[current.lower()].add(filename)
    return refs


def generate_combined_report(endpoints, ts_refs, output_file, title='WSpace API Reference'):
    """Write a markdown report grouping C# POST endpoints by controller and splitting
    them into Referenced and Unreferenced according to ts_refs (case-insensitive keys)."""
    # Build controller -> list of (endpoint, filenames from TS or empty)
    controllers = {}
    for endpoint, filenames in endpoints.items():
        # endpoint expected like 'ControllerBase/Action'
        parts = endpoint.split('/', 1)
        controller = parts[0]
        action = parts[1] if len(parts) > 1 else ''
        controllers.setdefault(controller, []).append((endpoint, filenames))

    referenced = {}
    unreferenced = {}

    for controller, items in controllers.items():
        for endpoint, filenames in items:
            endpoint_key = endpoint.lower()
            if endpoint_key in ts_refs and ts_refs[endpoint_key]:
                referenced.setdefault(controller, []).append((endpoint, ts_refs[endpoint_key]))
            else:
                unreferenced.setdefault(controller, []).append((endpoint, filenames))

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        # Referenced
        f.write("## Referenced\n\n")
        if referenced:
            for controller in sorted(referenced.keys()):
                f.write(f"### {controller}\n\n")
                for endpoint, used_in in sorted(referenced[controller], key=lambda x: x[0]):
                    f.write(f"#### {endpoint}\n\n")
                    f.write("used in\n\n")
                    for filename in sorted(used_in):
                        f.write(f"- `{filename}`\n")
                    f.write("\n")
        else:
            f.write("_No referenced POST endpoints found._\n\n")

        # Unreferenced
        f.write("## Unreferenced\n\n")
        if unreferenced:
            for controller in sorted(unreferenced.keys()):
                f.write(f"### {controller}\n\n")
                for endpoint, filenames in sorted(unreferenced[controller], key=lambda x: x[0]):
                    f.write(f"#### {endpoint}\n\n")
                    f.write("Defined in\n\n")
                    for filename in sorted(filenames):
                        f.write(f"- `{filename}`\n")
                    f.write("\n")
        else:
            f.write("_No unreferenced POST endpoints found._\n\n")

    print(f"Wrote combined report to {output_file}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract [HttpPost] endpoints from Controller.cs files and output Markdown or combined report with TS references.')
    parser.add_argument('root_directory', nargs='?', default='.', help='Root directory to scan')
    parser.add_argument('-o', '--output', default='post_endpoints.md', help='Output markdown file')
    parser.add_argument('--references', help='Path to TypeScript endpoints markdown (from extract-endpoints.py) to compare against')
    parser.add_argument('--title', default='WSpace API Reference', help='Title for combined report H1')
    parser.add_argument('--quiet', action='store_true', help='suppress progress output')
    parser.add_argument('--anonymousOnly', action='store_true', help='Only show endpoints with [AllowAnonymous]')
    args = parser.parse_args()

    if not os.path.isdir(args.root_directory):
        print(f"Error: Invalid directory path: {args.root_directory}")
        sys.exit(1)

    endpoints = find_post_endpoints(args.root_directory, anonymous_only=args.anonymousOnly)
    if args.references:
        ts_refs = load_ts_references(args.references)
        generate_combined_report(endpoints, ts_refs, args.output, title=args.title)
    else:
        generate_markdown(endpoints, args.output)
