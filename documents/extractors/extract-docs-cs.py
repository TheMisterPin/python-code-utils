#!/usr/bin/env python3
"""
CLI script to extract XML doc comments from C# files and save them as Markdown files.
"""

import os
import re
import argparse
from pathlib import Path
import sys
import importlib.util

utils_dir = os.path.join(os.path.dirname(__file__), 'utils')
cs_tags_path = os.path.join(utils_dir, 'handle-CsTags.py')
spec = importlib.util.spec_from_file_location('handle_CsTags', cs_tags_path)
cs_tags = importlib.util.module_from_spec(spec)
sys.modules['handle_CsTags'] = cs_tags
spec.loader.exec_module(cs_tags)
parse_csdoc_content = cs_tags.parse_csdoc_content
format_csdoc_as_markdown = cs_tags.format_csdoc_as_markdown

def extract_csdoc_comments(file_path):
    """
    Extract XML doc comments from a C# file.
    Args:
        file_path (str): Path to the C# file
    Returns:
        str: Combined XML doc comments content or empty string if none found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Find all XML doc comments (/// ...)
        # Group consecutive /// lines as a single doc comment
        doc_pattern = r'(?:^[ \t]*///.*\n)+'
        matches = re.finditer(doc_pattern, content, re.MULTILINE)
        docstrings = []
        for match in matches:
            doc_block = match.group(0)
            # Remove leading /// and whitespace
            lines = [re.sub(r'^\s*///\s?', '', l) for l in doc_block.split('\n') if l.strip()]
            cleaned_doc = '\n'.join(lines).strip()
            if cleaned_doc:
                # Try to find the next code element (class, method, property, etc.)
                start_pos = match.end()
                remaining_content = content[start_pos:start_pos + 1000]
                patterns = [
                    (r'^\s*public\s+class\s+(\w+)', 'CLASS'),
                    (r'^\s*public\s+interface\s+(\w+)', 'INTERFACE'),
                    (r'^\s*public\s+enum\s+(\w+)', 'ENUM'),
                    (r'^\s*public\s+struct\s+(\w+)', 'STRUCT'),
                    (r'^\s*public\s+(?:[\w<>\[\]]+\s+)+([\w_]+)\s*\(', 'METHOD'),
                    (r'^\s*public\s+(?:[\w<>\[\]]+\s+)+([\w_]+)\s*{', 'PROPERTY'),
                ]
                name = None
                doc_type = 'COMMENT'
                for pattern, pattern_type in patterns:
                    code_match = re.search(pattern, remaining_content, re.MULTILINE)
                    if code_match:
                        name = code_match.group(1)
                        doc_type = pattern_type
                        break
                if not name and match.start() < 200:
                    doc_type = 'MODULE'
                    name = 'module'
                if name:
                    docstrings.append(f"{doc_type}:{name}:{cleaned_doc}")
                else:
                    first_words = ' '.join(cleaned_doc.split()[:3])
                    docstrings.append(f"COMMENT:{first_words}:{cleaned_doc}")
        return "\n\n".join(docstrings) if docstrings else ""
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def find_cs_files(directory):
    """
    Recursively find all C# files in a directory.
    Args:
        directory (str): Directory to search in
    Returns:
        list: List of C# file paths
    """
    skip_dirs = {
        'bin', 'obj', '.git', '.svn', '.hg',
        'dist', 'build', 'node_modules',
        '__pycache__', '.pytest_cache', '.mypy_cache',
        '.tox', '.eggs', 'site-packages', 'packages', 'TestResults'
    }
    extensions = {'.cs'}
    cs_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                cs_files.append(os.path.join(root, file))
    return cs_files

def create_markdown_file(cs_file_path, csdoc_content, output_dir, project_name, input_root=None):
    """
    Create a markdown file with the extracted XML doc content, mimicking the original folder structure.
    Args:
        cs_file_path (str): Original C# file path
        csdoc_content (str): Extracted XML doc content
        output_dir (str): Output directory for markdown files
        project_name (str): Name of the project (last part of folder path)
        input_root (str): Root input folder to calculate relative path (optional)
    """
    file_name = Path(cs_file_path).stem
    # Determine relative path from input_root (if provided)
    if input_root:
        rel_path = os.path.relpath(cs_file_path, input_root)
        rel_dir = os.path.dirname(rel_path)
        target_dir = os.path.join(output_dir, rel_dir)
    else:
        target_dir = output_dir
    os.makedirs(target_dir, exist_ok=True)
    md_file_path = os.path.join(target_dir, f"{file_name}.md")
    programming_language = 'C#'
    md_content = f"# {file_name}\n\n"
    md_content += "---\n"
    md_content += f"Project: {project_name}\n"
    md_content += f"Programming Language: {programming_language}\n"
    file_type = None
    if 'CLASS:' in csdoc_content:
        file_type = 'Class'
    elif 'INTERFACE:' in csdoc_content:
        file_type = 'Interface'
    elif 'ENUM:' in csdoc_content:
        file_type = 'Enum'
    elif 'STRUCT:' in csdoc_content:
        file_type = 'Struct'
    elif 'METHOD:' in csdoc_content:
        file_type = 'Method'
    elif 'PROPERTY:' in csdoc_content:
        file_type = 'Property'
    elif 'MODULE:' in csdoc_content:
        file_type = 'Module'
    if file_type:
        md_content += f"File Type: {file_type}\n"
    md_content += "---\n\n"
    if csdoc_content:
        sections = []
        current_section = ""
        for line in csdoc_content.split('\n'):
            if any(line.startswith(prefix) for prefix in ['MODULE:', 'CLASS:', 'INTERFACE:', 'ENUM:', 'STRUCT:', 'METHOD:', 'PROPERTY:', 'COMMENT:']):
                if current_section:
                    sections.append(current_section)
                current_section = line
            else:
                if current_section:
                    current_section += '\n' + line
                else:
                    current_section = line
        if current_section:
            sections.append(current_section)
        module_doc = None
        classes = []
        interfaces = []
        enums = []
        structs = []
        methods = []
        properties = []
        comments = []
        for section in sections:
            if section.startswith('MODULE:'):
                module_doc = section.replace('MODULE:', '', 1).strip()
            elif section.startswith('CLASS:'):
                parts = section.replace('CLASS:', '', 1).split(':', 1)
                if len(parts) == 2:
                    class_name, class_doc = parts
                    classes.append({'name': class_name.strip(), 'doc': class_doc.strip()})
            elif section.startswith('INTERFACE:'):
                parts = section.replace('INTERFACE:', '', 1).split(':', 1)
                if len(parts) == 2:
                    iface_name, iface_doc = parts
                    interfaces.append({'name': iface_name.strip(), 'doc': iface_doc.strip()})
            elif section.startswith('ENUM:'):
                parts = section.replace('ENUM:', '', 1).split(':', 1)
                if len(parts) == 2:
                    enum_name, enum_doc = parts
                    enums.append({'name': enum_name.strip(), 'doc': enum_doc.strip()})
            elif section.startswith('STRUCT:'):
                parts = section.replace('STRUCT:', '', 1).split(':', 1)
                if len(parts) == 2:
                    struct_name, struct_doc = parts
                    structs.append({'name': struct_name.strip(), 'doc': struct_doc.strip()})
            elif section.startswith('METHOD:'):
                parts = section.replace('METHOD:', '', 1).split(':', 1)
                if len(parts) == 2:
                    method_name, method_doc = parts
                    methods.append({'name': method_name.strip(), 'doc': method_doc.strip()})
            elif section.startswith('PROPERTY:'):
                parts = section.replace('PROPERTY:', '', 1).split(':', 1)
                if len(parts) == 2:
                    prop_name, prop_doc = parts
                    properties.append({'name': prop_name.strip(), 'doc': prop_doc.strip()})
            elif section.startswith('COMMENT:'):
                parts = section.replace('COMMENT:', '', 1).split(':', 1)
                if len(parts) == 2:
                    comment_id, comment_doc = parts
                    comments.append({'id': comment_id.strip(), 'doc': comment_doc.strip()})
        md_content += "## Info\n\n"
        if module_doc:
            parsed_module = parse_csdoc_content(module_doc)
            if parsed_module.get('summary'):
                md_content += f"{parsed_module['summary']}\n\n"
            metadata = parsed_module.get('metadata', {})
            if metadata:
                metadata_parts = [f"**{k.title()}**: {v}" for k, v in metadata.items()]
                if metadata_parts:
                    md_content += '\n'.join(metadata_parts) + "\n\n"
        if classes:
            if len(classes) == 1:
                cls = classes[0]
                md_content += f"**Class**: `{cls['name']}`\n\n"
                parsed = parse_csdoc_content(cls['doc'])
                formatted = format_csdoc_as_markdown(parsed)
                md_content += f"{formatted}\n\n"
            else:
                md_content += "**Classes**:\n"
                for cls in classes:
                    parsed = parse_csdoc_content(cls['doc'])
                    summary = parsed.get('summary', '').split('\n')[0].strip()
                    md_content += f"- `{cls['name']}`: {summary}\n"
                md_content += "\n"
                for cls in classes:
                    md_content += f"### `{cls['name']}`\n\n"
                    parsed = parse_csdoc_content(cls['doc'])
                    formatted = format_csdoc_as_markdown(parsed)
                    md_content += f"{formatted}\n\n"
        if interfaces:
            if len(interfaces) == 1:
                iface = interfaces[0]
                md_content += f"**Interface**: `{iface['name']}`\n\n"
                parsed = parse_csdoc_content(iface['doc'])
                formatted = format_csdoc_as_markdown(parsed)
                md_content += f"{formatted}\n\n"
            else:
                md_content += "**Interfaces**:\n"
                for iface in interfaces:
                    parsed = parse_csdoc_content(iface['doc'])
                    summary = parsed.get('summary', '').split('\n')[0].strip()
                    md_content += f"- `{iface['name']}`: {summary}\n"
                md_content += "\n"
                for iface in interfaces:
                    md_content += f"### `{iface['name']}`\n\n"
                    parsed = parse_csdoc_content(iface['doc'])
                    formatted = format_csdoc_as_markdown(parsed)
                    md_content += f"{formatted}\n\n"
        if enums:
            for enum in enums:
                md_content += f"**Enum**: `{enum['name']}`\n\n{enum['doc']}\n\n"
        if structs:
            for struct in structs:
                md_content += f"**Struct**: `{struct['name']}`\n\n{struct['doc']}\n\n"
        if methods:
            if len(methods) == 1:
                m = methods[0]
                md_content += f"**Method**: `{m['name']}`\n\n"
                parsed = parse_csdoc_content(m['doc'])
                formatted = format_csdoc_as_markdown(parsed)
                md_content += f"{formatted}\n\n"
            else:
                md_content += "**Methods**:\n"
                for m in methods:
                    parsed = parse_csdoc_content(m['doc'])
                    summary = parsed.get('summary', '').split('\n')[0].strip()
                    md_content += f"- `{m['name']}`: {summary}\n"
                md_content += "\n"
                for m in methods:
                    md_content += f"### `{m['name']}`\n\n"
                    parsed = parse_csdoc_content(m['doc'])
                    formatted = format_csdoc_as_markdown(parsed)
                    md_content += f"{formatted}\n\n"
        if properties:
            for p in properties:
                md_content += f"**Property**: `{p['name']}`\n\n{p['doc']}\n\n"
        if comments:
            md_content += "**Documentation**:\n\n"
            for comment in comments:
                md_content += f"{comment['doc']}\n\n"
    else:
        md_content += "## Info\n\n*No XML doc comments found*\n"
    try:
        with open(md_file_path, 'w', encoding='utf-8') as md_file:
            md_file.write(md_content)
        print(f"Created: {md_file_path}")
    except Exception as e:
        print(f"Error writing {md_file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Extract XML doc comments from C# files and save as Markdown"
    )
    parser.add_argument(
        "folder",
        help="Folder to search for C# files"
    )
    parser.add_argument(
        "-o", "--output",
        default="./extracted",
        help="Output directory for markdown files (default: ./extracted)"
    )
    args = parser.parse_args()
    if not os.path.isdir(args.folder):
        print(f"Error: '{args.folder}' is not a valid directory")
        return
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    folder_path = Path(args.folder).resolve()
    project_name = folder_path.name
    cs_files = find_cs_files(args.folder)
    if not cs_files:
        print(f"No C# files found in '{args.folder}'")
        return
    print(f"Found {len(cs_files)} C# files")
    print(f"Output directory: {output_dir}")
    print(f"Project: {project_name}")
    print("-" * 50)
    processed = 0
    skipped = 0
    for cs_file in cs_files:
        csdoc_content = extract_csdoc_comments(cs_file)
        if csdoc_content.strip() and len(csdoc_content.strip().split('\n')) > 3:
            create_markdown_file(cs_file, csdoc_content, output_dir, project_name, folder_path)
            processed += 1
        else:
            skipped += 1
            if csdoc_content.strip():
                print(f"Skipped (XML doc too short): {cs_file}")
            else:
                print(f"Skipped (no XML doc): {cs_file}")
    print("-" * 50)
    print(f"Processed {processed} files with substantial XML doc comments successfully!")
    print(f"Skipped {skipped} files (no XML doc or too short).")

if __name__ == "__main__":
    main()