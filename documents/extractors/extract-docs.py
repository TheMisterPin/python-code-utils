#!/usr/bin/env python3
"""
CLI script to extract docstrings from Python files and save them as Markdown files.
"""

import os
import ast
import argparse
from pathlib import Path


def extract_docstring(file_path):
    """
    Extract docstrings from a Python file (module, functions, and classes).
    
    Args:
        file_path (str): Path to the Python file
        
    Returns:
        str: Combined docstrings content or empty string if no docstrings found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Parse the Python file into an AST
        tree = ast.parse(content)
        
        docstrings = []
        
        # Get module-level docstring
        module_docstring = None
        if (tree.body and 
            isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            module_docstring = tree.body[0].value.value.strip()
            if module_docstring:
                docstrings.append(f"MODULE:{module_docstring}")
        
        # Extract function and class docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    func_doc = node.body[0].value.value.strip()
                    if func_doc:
                        docstrings.append(f"FUNCTION:{node.name}:{func_doc}")
            
            elif isinstance(node, ast.ClassDef):
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    class_doc = node.body[0].value.value.strip()
                    if class_doc:
                        docstrings.append(f"CLASS:{node.name}:{class_doc}")
        
        return "\n\n".join(docstrings) if docstrings else ""
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""


def find_python_files(directory):
    """
    Recursively find all Python files in a directory.
    
    Args:
        directory (str): Directory to search in
        
    Returns:
        list: List of Python file paths
    """
    # Directories to skip
    skip_dirs = {
        'venv', 'env', '.venv', '.env',
        '__pycache__', '.git', '.svn', '.hg',
        'node_modules', '.pytest_cache', '.mypy_cache',
        'build', 'dist', '.tox', '.eggs',
        'site-packages', 'lib', 'lib64'
    }
    
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Remove directories we want to skip from the dirs list
        # This prevents os.walk from descending into them
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


def create_markdown_file(py_file_path, docstring, output_dir):
    """
    Create a markdown file with the extracted docstring.
    
    Args:
        py_file_path (str): Original Python file path
        docstring (str): Extracted docstring
        output_dir (str): Output directory for markdown files
    """
    # Get the filename without extension
    file_name = Path(py_file_path).stem
    md_file_path = os.path.join(output_dir, f"{file_name}.md")
    
    # Get relative path from current working directory
    try:
        relative_path = os.path.relpath(py_file_path)
    except ValueError:
        # If we can't get relative path, use the filename
        relative_path = py_file_path
    
    # Create markdown content with H1 filename
    md_content = f"# {file_name}\n\n"
    
    # Add path property
    md_content += f"**Path**: `{relative_path}`\n\n"
    
    # Add TOC block
    md_content += "```toc\nmaxLevel1\n```\n\n"
    
    if docstring:
        # Parse the structured docstring
        sections = docstring.split('\n\n')
        
        module_doc = None
        functions = []
        classes = []
        
        for section in sections:
            if section.startswith('MODULE:'):
                module_doc = section.replace('MODULE:', '', 1).strip()
            elif section.startswith('FUNCTION:'):
                # Parse FUNCTION:name:docstring
                parts = section.replace('FUNCTION:', '', 1).split(':', 1)
                if len(parts) == 2:
                    func_name, func_docstring = parts
                    functions.append({
                        'name': func_name.strip(),
                        'docstring': func_docstring.strip()
                    })
            elif section.startswith('CLASS:'):
                # Parse CLASS:name:docstring
                parts = section.replace('CLASS:', '', 1).split(':', 1)
                if len(parts) == 2:
                    class_name, class_docstring = parts
                    classes.append({
                        'name': class_name.strip(),
                        'docstring': class_docstring.strip()
                    })
        
        # Add Info section
        md_content += "## Info\n\n"
        
        # Add module documentation
        if module_doc:
            md_content += f"{module_doc}\n\n"
        
        # Add functions section
        if functions:
            if len(functions) == 1:
                func = functions[0]
                md_content += f"**Function**: `{func['name']}`\n\n"
                md_content += f"{func['docstring']}\n\n"
            else:
                md_content += "**Functions**:\n"
                for func in functions:
                    # Extract first line as summary
                    first_line = func['docstring'].split('\n')[0].strip()
                    md_content += f"- `{func['name']}`: {first_line}\n"
                md_content += "\n"
                
                # Add detailed docstrings for each function
                for func in functions:
                    md_content += f"### `{func['name']}`\n\n"
                    md_content += f"{func['docstring']}\n\n"
        
        # Add classes section
        if classes:
            if len(classes) == 1:
                cls = classes[0]
                md_content += f"**Class**: `{cls['name']}`\n\n"
                md_content += f"{cls['docstring']}\n\n"
            else:
                md_content += "**Classes**:\n"
                for cls in classes:
                    # Extract first line as summary
                    first_line = cls['docstring'].split('\n')[0].strip()
                    md_content += f"- `{cls['name']}`: {first_line}\n"
                md_content += "\n"
                
                # Add detailed docstrings for each class
                for cls in classes:
                    md_content += f"### `{cls['name']}`\n\n"
                    md_content += f"{cls['docstring']}\n\n"
        
    else:
        md_content += "## Info\n\n*No docstring found*\n"
    
    # Write the markdown file
    try:
        with open(md_file_path, 'w', encoding='utf-8') as md_file:
            md_file.write(md_content)
        print(f"Created: {md_file_path}")
    except Exception as e:
        print(f"Error writing {md_file_path}: {e}")

def main():
    """Main function to handle CLI arguments and process files."""
    parser = argparse.ArgumentParser(
        description="Extract docstrings from Python files and save as Markdown"
    )
    parser.add_argument(
        "folder", 
        help="Folder to search for Python files"
    )
    parser.add_argument(
        "-o", "--output", 
        default="./extracted",
        help="Output directory for markdown files (default: ./extracted)"
    )
    
    args = parser.parse_args()
    
    # Validate input folder
    if not os.path.isdir(args.folder):
        print(f"Error: '{args.folder}' is not a valid directory")
        return
    
    # Create output directory if it doesn't exist
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all Python files
    python_files = find_python_files(args.folder)
    
    if not python_files:
        print(f"No Python files found in '{args.folder}'")
        return
    
    print(f"Found {len(python_files)} Python files")
    print(f"Output directory: {output_dir}")
    print("-" * 50)
    
    # Process each Python file
    processed = 0
    skipped = 0
    for py_file in python_files:
        docstring = extract_docstring(py_file)
        if docstring.strip() and len(docstring.strip().split('\n')) > 3:  # Only create file if docstring exists and is more than 3 lines
            create_markdown_file(py_file, docstring, output_dir)
            processed += 1
        else:
            skipped += 1
            if docstring.strip():
                print(f"Skipped (docstring too short): {py_file}")
            else:
                print(f"Skipped (no docstring): {py_file}")
    
    print("-" * 50)
    print(f"Processed {processed} files with substantial docstrings successfully!")
    print(f"Skipped {skipped} files (no docstring or too short).")


if __name__ == "__main__":
    main()