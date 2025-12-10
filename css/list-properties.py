#!/usr/bin/env python3
import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.output_helpers import get_output_base_dir

# Match a CSS/SCSS property name at the start of a line:
# e.g. "color: red;" -> "color"
PROPERTY_RE = re.compile(r'^\s*([-\w]+)\s*:')

# File extensions to scan
CSS_EXTENSIONS = {'.scss', '.css'}


# Family patterns: if a property == pattern OR starts with pattern + "-"
# it will be classified under that family.
FAMILY_PATTERNS = {
    "color": [
        "color",
        "background-color",
        "border-color",
        "outline-color",
        "text-shadow",
        "fill",
        "stroke"
    ],
    "background": [
        "background",
        "background-image",
        "background-position",
        "background-size",
        "background-repeat",
        "background-attachment",
        "background-origin",
        "background-clip"
    ],
    "spacing": [
        "margin",
        "padding",
        "gap",
        "column-gap",
        "row-gap"
    ],
    "border": [
        "border",
        "outline",
        "box-shadow"
    ],
    "typography": [
        "font",
        "font-size",
        "font-weight",
        "font-style",
        "font-family",
        "line-height",
        "letter-spacing",
        "text-align",
        "text-transform",
        "text-decoration",
        "text-indent",
        "white-space"
    ],
    "layout": [
        "display",
        "position",
        "top",
        "right",
        "bottom",
        "left",
        "z-index",
        "float",
        "clear",
        "flex",
        "flex-direction",
        "flex-wrap",
        "flex-flow",
        "justify-content",
        "align-items",
        "align-content",
        "align-self",
        "order",
        "grid",
        "grid-template",
        "grid-template-columns",
        "grid-template-rows",
        "grid-template-areas",
        "grid-area",
        "grid-column",
        "grid-row",
        "grid-auto-flow",
        "grid-auto-rows",
        "grid-auto-columns"
    ],
    "size": [
        "width",
        "height",
        "min-width",
        "max-width",
        "min-height",
        "max-height",
        "box-sizing"
    ],
    "transform": [
        "transform",
        "transform-origin",
        "transition",
        "animation"
    ],
    "misc": [
        "opacity",
        "cursor",
        "overflow",
        "overflow-x",
        "overflow-y",
        "visibility",
        "pointer-events"
    ],
}


def is_css_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in CSS_EXTENSIONS


def extract_property_and_value(line):
    """
    Try to extract a CSS/SCSS property name and value from a single line.
    Returns (prop, value) or (None, None) if not a declaration.
    """
    stripped = line.strip()

    # Skip obvious non-declaration lines
    if not stripped:
        return None, None
    if stripped.startswith(("//", "/*", "*")):
        return None, None  # comments
    if stripped.startswith("@"):
        return None, None  # @mixin, @include, @media, etc.
    if stripped.startswith("$"):
        return None, None  # SCSS variable definitions
    if stripped.startswith("#{"):
        return None, None  # SCSS interpolation edge cases in selectors

    m = PROPERTY_RE.match(stripped)
    if not m:
        return None, None

    prop = m.group(1)

    # Filter out some obvious false positives (very basic)
    if "(" in stripped.split(":", 1)[0]:
        return None, None

    # Extract value (everything after first ":" up to ";" if present)
    rest = stripped[m.end():].lstrip()
    if ";" in rest:
        value = rest.split(";", 1)[0].strip()
    else:
        value = rest.strip()

    return prop, value


def classify_family(prop):
    """
    Classify a property into a family based on FAMILY_PATTERNS.
    If none match, returns "other".
    """
    for family, patterns in FAMILY_PATTERNS.items():
        for pattern in patterns:
            if prop == pattern or prop.startswith(pattern + "-"):
                return family
    return "other"


def scan_folder(root):
    """
    Walk the folder recursively and count CSS/SCSS properties.
    Returns:
      - global Counter of all properties
      - dict[family] -> Counter of properties in that family
      - dict[family] -> dict[property] -> Counter of values
      - Counter of colors
    """
    global_counter = Counter()
    family_counters = defaultdict(Counter)
    family_value_counters = defaultdict(lambda: defaultdict(Counter))
    color_counter = Counter()
    important_seen = set()

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if not is_css_file(filename):
                continue

            full_path = os.path.join(dirpath, filename)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        prop, value = extract_property_and_value(line)
                        if prop:
                            global_counter[prop] += 1
                            fam = classify_family(prop)
                            family_counters[fam][prop] += 1
                            if value:
                                family_value_counters[fam][prop][value] += 1
                                if fam == "color":
                                    clean_value = value.replace(" !important", "").strip()
                                    if " !important" in value:
                                        if clean_value not in important_seen:
                                            color_counter[clean_value] += 1
                                            important_seen.add(clean_value)
                                    else:
                                        color_counter[clean_value] += 1
            except Exception as e:
                print(f"[WARN] Failed to read {full_path}: {e}")

    return global_counter, family_counters, family_value_counters, color_counter


def build_summary_markdown(global_counts, family_counts, scanned_path):
    lines = []
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"# CSS / SCSS Property Usage Summary\n")
    lines.append(f"- Generated on: **{date_str}**")
    lines.append(f"- Scanned path: `{scanned_path}`")
    lines.append("")
    lines.append(f"Total distinct properties: **{len(global_counts)}**")
    lines.append("")

    # ---- Global usage ----
    lines.append("## Global property usage\n")
    lines.append("| Property | Count |")
    lines.append("|----------|-------|")

    items = sorted(global_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    for prop, count in items:
        lines.append(f"| `{prop}` | {count} |")

    lines.append("")

    # ---- Families ----
    lines.append("## By family\n")

    families_sorted = sorted(
        family_counts.items(),
        key=lambda kv: -sum(kv[1].values())
    )

    for family, counter in families_sorted:
        total = sum(counter.values())
        lines.append(f"### {family}")
        lines.append(f"Total declarations: **{total}**")
        lines.append("")
        lines.append("| Property | Count |")
        lines.append("|----------|-------|")
        for prop, count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"| `{prop}` | {count} |")
        lines.append("")

    return "\n".join(lines)


def build_family_details_markdown(family, prop_value_counters, scanned_path):
    lines = []
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"# {family.capitalize()} family details\n")
    lines.append(f"- Generated on: **{date_str}**")
    lines.append(f"- Scanned path: `{scanned_path}`")
    lines.append("")

    # Sort properties by total usage
    props_sorted = sorted(
        prop_value_counters.items(),
        key=lambda kv: -sum(kv[1].values())
    )

    for prop, value_counter in props_sorted:
        total = sum(value_counter.values())
        lines.append(f"## `{prop}`")
        lines.append(f"Total declarations: **{total}**")
        lines.append("")
        lines.append("| Value | Count |")
        lines.append("|-------|-------|")

        for value, count in sorted(value_counter.items(), key=lambda kv: (-kv[1], kv[0])):
            # Show empty values clearly (should be rare)
            display_value = value if value else "<empty>"
            lines.append(f"| `{display_value}` | {count} |")

        lines.append("")

    return "\n".join(lines)


def build_used_colors_markdown(color_counts, scanned_path):
    lines = []
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"# Used Colors\n")
    lines.append(f"- Generated on: **{date_str}**")
    lines.append(f"- Scanned path: `{scanned_path}`")
    lines.append("")

    lines.append(f"Total distinct colors: **{len(color_counts)}**")
    lines.append("")

    lines.append("| Color | Count |")
    lines.append("|-------|-------|")

    for color, count in sorted(color_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| `{color}` | {count} |")

    lines.append("")

    return "\n".join(lines)


# Import shared output helpers (added at the top of file)
# from utils.output_helpers import get_output_base_dir

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Scan a folder and list CSS/SCSS properties with usage counts, "
            "grouped by families, and output Markdown reports."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root folder to scan (default: current directory).",
    )
    args = parser.parse_args()

    root = os.path.abspath(args.path)
    print(f"Scanning: {root}\n")

    if not os.path.isdir(root):
        print("Error: path is not a directory.")
        return

    global_counts, family_counts, family_value_counters, color_counts = scan_folder(root)

    if not global_counts:
        print("No properties found in .scss/.css files.")
        return

    date_folder = datetime.now().strftime("%m%d")
    out_base = os.path.join(get_output_base_dir(), "lists", date_folder)
    os.makedirs(out_base, exist_ok=True)

    # Summary
    summary_md = build_summary_markdown(global_counts, family_counts, root)
    summary_path = os.path.join(out_base, "summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_md)

    print(f"Summary written to:\n  {summary_path}")

    # Per-family details
    for family, prop_values in family_value_counters.items():
        details_md = build_family_details_markdown(family, prop_values, root)
        details_path = os.path.join(out_base, f"{family}-details.md")
        with open(details_path, "w", encoding="utf-8") as f:
            f.write(details_md)
        print(f"Details for '{family}' written to:\n  {details_path}")

    # Used colors
    used_colors_md = build_used_colors_markdown(color_counts, root)
    used_colors_path = os.path.join(out_base, "used-colors.md")
    with open(used_colors_path, "w", encoding="utf-8") as f:
        f.write(used_colors_md)
    print(f"Used colors written to:\n  {used_colors_path}")

    print(f"\nTotal distinct properties: {len(global_counts)}")
    print(f"Total distinct colors: {len(color_counts)}")


if __name__ == "__main__":
    main()
