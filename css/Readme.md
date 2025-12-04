# CSS / SCSS Property Audit

This script helps you inventory and normalize your Ionic (or any) CSS/SCSS codebase before introducing shared variables and design tokens.

## scan_css_properties.py

**Features**
- Recursively scans a target folder for `.scss` and `.css` files.
- Extracts each CSS/SCSS property declaration and counts how many times it appears across the project.
- Classifies properties into logical families (color, background, spacing, border, typography, layout, size, transform, misc, other).
- For each family, collects all distinct values used per property (e.g. every value of `color`, `margin`, `font-size`) and counts how often each value occurs.
- Generates Markdown reports for quick review and refactoring.

**Output Structure**  
All reports are written relative to the script location, not the scanned project root:

```text
_output/
  css/
    lists/
      MMDD/
        summary.md
        color-details.md
        background-details.md
        spacing-details.md
        border-details.md
        typography-details.md
        layout-details.md
        size-details.md
        transform-details.md
        misc-details.md
        other-details.md   (if any properties don’t match a known family)
```

Where `MMDD` is the current month and day at the time of execution (e.g. `1204` for December 4).

- **summary.md**
  - Global table of all properties and how many times each is declared.
  - Per-family breakdown with property counts (e.g. all spacing-related properties and their totals).
- **{family}-details.md**
  - For each family (e.g. `color`), lists every property in that family.
  - For each property, shows all distinct values and how many times each value occurs.
  - Perfect for spotting duplicate hex/RGB values, inconsistent spacing scales, or random one-off font sizes.

**How to Run**
1. Place `scan_css_properties.py` somewhere accessible (for example in a `tools/` or `scripts/` folder).
2. From your Ionic or web project root, run:
   ```bash
   python3 /path/to/scan_css_properties.py <target-folder>
   ```
   - If you omit `<target-folder>`, it defaults to the current directory (`.`).
3. The script will walk the folder tree, scan `.scss` and `.css` files, and then write the Markdown reports under the `_output/css/lists/MMDD/` directory next to the script.

**Usage Examples**

Scan the current directory:
```bash
$ python3 tools/scan_css_properties.py .
Scanning: /path/to/ionic-app

Summary written to:
  /path/to/tools/_output/css/lists/1204/summary.md
Details for 'color' written to:
  /path/to/tools/_output/css/lists/1204/color-details.md
...
Total distinct properties: 87
```

Scan only your theme folder:
```bash
$ python3 tools/scan_css_properties.py src/theme
```

Open `summary.md` to see which properties dominate the codebase, then open the `{family}-details.md` files (especially `color` and `spacing`) to decide which values should become SCSS variables or design tokens.
