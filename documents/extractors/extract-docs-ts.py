#!/usr/bin/env python3
"""
CLI script to extract JSDoc comments from TypeScript/JavaScript files and save them as Markdown files.
"""

import os
import re
import argparse
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.output_helpers import get_output_base_dir

# Simple JSDoc parser implementation integrated directly
def parse_jsdoc_content(jsdoc_text):
    """
    Parse JSDoc content to extract comprehensive tag information.
    
    Args:
        jsdoc_text (str): The cleaned JSDoc content
        
    Returns:
        dict: Parsed JSDoc with comprehensive tag support
    """
    result = {
        'description': '',
        'params': [],
        'returns': None,
        'throws': [],
        'examples': [],
        'properties': [],
        'metadata': {},
        'api': {},
        'tags': {}
    }
    
    lines = jsdoc_text.strip().split('\n')
    current_section = 'description'
    current_content = []
    
    for line in lines:
        line = line.strip()
        
        # Check if line starts with a JSDoc tag
        tag_match = re.match(r'^@(\w+)(?:\s+(.*))?$', line)
        
        if tag_match:
            # Save previous content
            if current_content and current_section == 'description':
                result['description'] = '\n'.join(current_content).strip()
                current_content = []
            
            tag_name = tag_match.group(1)
            tag_content = tag_match.group(2) or ''
            
            # Handle different tag types
            if tag_name == 'param':
                # Parse @param {type} name - description OR @param name - description
                param_match_with_type = re.match(r'\{([^}]+)\}\s+(\S+)(?:\s*-?\s*(.*))?', tag_content)
                param_match_no_type = re.match(r'(\S+)(?:\s*-?\s*(.*))?', tag_content)
                
                if param_match_with_type:
                    param_type, param_name, param_desc = param_match_with_type.groups()
                    result['params'].append({
                        'name': param_name,
                        'type': param_type,
                        'description': param_desc or '',
                        'optional': param_name.startswith('[') and param_name.endswith(']')
                    })
                elif param_match_no_type:
                    param_name, param_desc = param_match_no_type.groups()
                    result['params'].append({
                        'name': param_name,
                        'type': 'unknown',
                        'description': param_desc or '',
                        'optional': param_name.startswith('[') and param_name.endswith(']')
                    })
                    
            elif tag_name in ['returns', 'return']:
                # Parse @returns {type} description
                returns_match = re.match(r'\{([^}]+)\}(?:\s*(.*))?', tag_content)
                if returns_match:
                    return_type, return_desc = returns_match.groups()
                    result['returns'] = {
                        'type': return_type,
                        'description': return_desc or ''
                    }
                else:
                    result['returns'] = {
                        'type': 'unknown',
                        'description': tag_content
                    }
                    
            elif tag_name == 'throws':
                # Parse @throws {type} description
                throws_match = re.match(r'\{([^}]+)\}(?:\s*(.*))?', tag_content)
                if throws_match:
                    error_type, error_desc = throws_match.groups()
                    result['throws'].append({
                        'type': error_type,
                        'description': error_desc or ''
                    })
                else:
                    result['throws'].append({
                        'type': 'Error',
                        'description': tag_content
                    })
                    
            elif tag_name == 'example':
                if tag_content:
                    result['examples'].append(tag_content)
                current_section = 'example'
                current_content = []
                
            elif tag_name in ['property', 'prop']:
                # Parse @property {type} name - description
                prop_match = re.match(r'\{([^}]+)\}\s+(\S+)(?:\s*-?\s*(.*))?', tag_content)
                if prop_match:
                    prop_type, prop_name, prop_desc = prop_match.groups()
                    result['properties'].append({
                        'name': prop_name,
                        'type': prop_type,
                        'description': prop_desc or ''
                    })
                    
            elif tag_name == 'api':
                # Parse @api {method} /path Description
                api_match = re.match(r'\{(\w+)\}\s+(\S+)(?:\s+(.*))?', tag_content)
                if api_match:
                    method, path, desc = api_match.groups()
                    result['api'] = {
                        'method': method.upper(),
                        'path': path,
                        'description': desc or ''
                    }
                    
            elif tag_name in ['file', 'version', 'author', 'since', 'component']:
                result['metadata'][tag_name] = tag_content
                
            elif tag_name == 'description':
                # Explicit @description tag
                result['description'] = tag_content
                
            elif tag_name == 'function':
                # @function tag - just store as metadata, don't override description
                result['metadata']['function'] = tag_content
                
            else:
                # Store other tags
                result['tags'][tag_name] = tag_content
            
            current_section = tag_name
            
        else:
            # Continuation of current section
            if line:  # Skip empty lines
                if current_section == 'param' and result['params']:
                    # Continue description of last param
                    result['params'][-1]['description'] += f" {line}"
                elif current_section in ['returns', 'return'] and result['returns']:
                    # Continue returns description
                    if 'description' in result['returns']:
                        result['returns']['description'] += f" {line}"
                elif current_section == 'example':
                    # Continue example content
                    current_content.append(line)
                elif current_section in result['tags']:
                    # Continue custom tag content
                    result['tags'][current_section] += f" {line}"
                else:
                    current_content.append(line)
    
    # Handle remaining description content
    if current_content and current_section == 'description':
        result['description'] = '\n'.join(current_content).strip()
    elif current_section == 'example' and current_content:
        result['examples'].append('\n'.join(current_content).strip())
    
    return result


def format_jsdoc_as_markdown(parsed_jsdoc):
    """
    Format parsed JSDoc into markdown sections with comprehensive tag support.
    
    Args:
        parsed_jsdoc (dict): Parsed JSDoc content
        
    Returns:
        str: Formatted markdown content
    """
    md_parts = []
    
    # Add main description
    if parsed_jsdoc.get('description'):
        md_parts.append(parsed_jsdoc['description'])
    
    # Add metadata section if any
    metadata = parsed_jsdoc.get('metadata', {})
    if metadata:
        metadata_parts = []
        for key, value in metadata.items():
            if key == 'version':
                metadata_parts.append(f"**Version**: {value}")
            elif key == 'author':
                metadata_parts.append(f"**Author**: {value}")
            elif key == 'since':
                metadata_parts.append(f"**Since**: {value}")
            elif key == 'file':
                metadata_parts.append(f"**File**: {value}")
            elif key == 'component' and value:  # Only show if it has a meaningful value
                metadata_parts.append(f"**Component**: {value}")
        
        if metadata_parts:
            md_parts.append('\n'.join(metadata_parts))
    
    # Add API documentation if present
    api = parsed_jsdoc.get('api', {})
    if api:
        if api.get('method') and api.get('path'):
            api_line = f"**API**: `{api['method']} {api['path']}`"
            if api.get('description'):
                api_line += f" - {api['description']}"
            md_parts.append(api_line)
    
    # Add parameters section
    params = parsed_jsdoc.get('params', [])
    if params:
        md_parts.append("## Parameters")
        for param in params:
            param_line = f"- **{param['name']}** (`{param.get('type', 'unknown')}`)"
            if param.get('optional'):
                param_line += " *(optional)*"
            if param.get('description'):
                param_line += f": {param['description']}"
            md_parts.append(param_line)
    
    # Add returns section  
    returns = parsed_jsdoc.get('returns')
    if returns:
        md_parts.append("## Returns")
        if isinstance(returns, dict):
            return_line = f"`{returns.get('type', 'unknown')}`"
            if returns.get('description'):
                return_line += f" - {returns['description']}"
            md_parts.append(return_line)
        else:
            md_parts.append(str(returns))
    
    # Add properties section
    properties = parsed_jsdoc.get('properties', [])
    if properties:
        md_parts.append("## Properties")
        for prop in properties:
            prop_line = f"- **{prop['name']}** (`{prop.get('type', 'unknown')}`)"
            if prop.get('description'):
                prop_line += f": {prop['description']}"
            md_parts.append(prop_line)
    
    # Add throws section
    throws = parsed_jsdoc.get('throws', [])
    if throws:
        md_parts.append("## Throws")
        for throw in throws:
            throw_line = f"- **{throw.get('type', 'Error')}**"
            if throw.get('description'):
                throw_line += f": {throw['description']}"
            md_parts.append(throw_line)
    
    # Add examples section
    examples = parsed_jsdoc.get('examples', [])
    if examples:
        md_parts.append("## Examples")
        for example in examples:
            md_parts.append(f"```\n{example}\n```")
    
    # Add custom tags as remarks
    tags = parsed_jsdoc.get('tags', {})
    if tags:
        remarks_parts = []
        for tag_name, tag_content in tags.items():
            if tag_name in ['remarks', 'note', 'warning', 'important']:
                remarks_parts.append(f"**{tag_name.title()}**: {tag_content}")
        
        if remarks_parts:
            md_parts.append("## Remarks")
            md_parts.extend(remarks_parts)
    
    return '\n\n'.join(md_parts)


def extract_jsdoc_comments(file_path):
    """
    Extract JSDoc comments from a TypeScript/JavaScript file.
    
    Args:
        file_path (str): Path to the TypeScript/JavaScript file
        
    Returns:
        str: Combined JSDoc comments content or empty string if none found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Find all JSDoc comments (/** ... */)
        jsdoc_pattern = r'/\*\*(.*?)\*/'
        matches = re.finditer(jsdoc_pattern, content, re.DOTALL)
        
        docstrings = []
        
        for match in matches:
            jsdoc_content = match.group(1).strip()
            start_pos = match.end()
            
            # Clean up the JSDoc content
            lines = jsdoc_content.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # Remove leading * and whitespace
                cleaned_line = re.sub(r'^\s*\*\s?', '', line)
                cleaned_lines.append(cleaned_line)
            
            cleaned_jsdoc = '\n'.join(cleaned_lines).strip()
            
            if cleaned_jsdoc:
                # Check if this is file-level documentation first
                if '@file' in cleaned_jsdoc or '@fileoverview' in cleaned_jsdoc:
                    doc_type = 'MODULE'
                    name = 'module'
                else:
                    # Look for the next code element after this JSDoc comment
                    # Check for various declaration patterns
                    remaining_content = content[start_pos:start_pos + 1000]  # Look ahead 1000 chars
                    
                    # Patterns for different code elements
                    patterns = [
                        (r'^\s*export\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)', 'FUNCTION'),
                        (r'^\s*(?:async\s+)?function\s+(\w+)', 'FUNCTION'),
                        (r'^\s*export\s+(?:default\s+)?class\s+(\w+)', 'CLASS'),
                        (r'^\s*class\s+(\w+)', 'CLASS'),
                        (r'^\s*export\s+(?:default\s+)?interface\s+(\w+)', 'INTERFACE'),
                        (r'^\s*interface\s+(\w+)', 'INTERFACE'),
                        (r'^\s*export\s+const\s+(\w+)\s*[:=]', 'VARIABLE'),
                        (r'^\s*const\s+(\w+)\s*[:=]', 'VARIABLE'),
                        (r'^\s*export\s+let\s+(\w+)\s*[:=]', 'VARIABLE'),
                        (r'^\s*let\s+(\w+)\s*[:=]', 'VARIABLE'),
                        (r'^\s*export\s+var\s+(\w+)\s*[:=]', 'VARIABLE'),
                        (r'^\s*var\s+(\w+)\s*[:=]', 'VARIABLE'),
                    ]
                    
                    name = None
                    doc_type = 'COMMENT'
                    
                    for pattern, pattern_type in patterns:
                        code_match = re.search(pattern, remaining_content, re.MULTILINE)
                        if code_match:
                            name = code_match.group(1)
                            doc_type = pattern_type
                            break
                    
                    # If no specific pattern matched, check if it's at the beginning of file (module doc)
                    if not name and match.start() < 200:  # If JSDoc is near the beginning of file
                        doc_type = 'MODULE'
                        name = 'module'
                
                # Add the docstring
                if name:
                    docstrings.append(f"{doc_type}:{name}:{cleaned_jsdoc}")
                else:
                    # If we can't identify what it documents, still include it as a general comment
                    # Extract first few words as identifier
                    first_words = ' '.join(cleaned_jsdoc.split()[:3])
                    docstrings.append(f"COMMENT:{first_words}:{cleaned_jsdoc}")
        
        return "\n\n".join(docstrings) if docstrings else ""
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""


def find_typescript_files(directory):
    """
    Recursively find all TypeScript and JavaScript files in a directory.
    
    Args:
        directory (str): Directory to search in
        
    Returns:
        list: List of TypeScript/JavaScript file paths
    """
    # Directories to skip
    skip_dirs = {
        'node_modules', '.git', '.svn', '.hg',
        'dist', 'build', '.next', '.nuxt',
        'coverage', '.nyc_output', '.cache',
        'venv', 'env', '.venv', '.env',
        '__pycache__', '.pytest_cache', '.mypy_cache',
        '.tox', '.eggs', 'site-packages'
    }
    
    # File extensions to include
    extensions = {'.ts', '.tsx', '.js', '.jsx'}
    
    typescript_files = []
    for root, dirs, files in os.walk(directory):
        # Remove directories we want to skip from the dirs list
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                typescript_files.append(os.path.join(root, file))
    
    return typescript_files


def create_markdown_file(ts_file_path, jsdoc_content, output_dir, project_name, input_root=None):
    """
    Create a markdown file with the extracted JSDoc content, mimicking the original folder structure.
    Args:
        ts_file_path (str): Original TypeScript/JavaScript file path
        jsdoc_content (str): Extracted JSDoc content
        output_dir (str): Output directory for markdown files
        project_name (str): Name of the project (last part of folder path)
        input_root (str): Root input folder to calculate relative path (optional)
    """
    file_name = Path(ts_file_path).stem
    # Determine relative path from input_root (if provided)
    if input_root:
        rel_path = os.path.relpath(ts_file_path, input_root)
        rel_dir = os.path.dirname(rel_path)
        target_dir = os.path.join(output_dir, rel_dir)
    else:
        target_dir = output_dir
    os.makedirs(target_dir, exist_ok=True)
    md_file_path = os.path.join(target_dir, f"{file_name}.md")
    
    # Get file extension to determine programming language
    file_ext = Path(ts_file_path).suffix.lower()
    if file_ext in ['.ts', '.tsx']:
        programming_language = 'TypeScript'
    elif file_ext in ['.js', '.jsx']:
        programming_language = 'JavaScript'
    else:
        programming_language = file_ext[1:].upper() if file_ext else 'Unknown'
    
    # Create markdown content with new header format
    md_content = f"# {file_name}\n\n"
    md_content += "---\n"
    md_content += f"Project: {project_name}\n"
    md_content += f"Programming Language: {programming_language}\n"
    
    # Detect file type from JSDoc content for header
    file_type = None
    if '@component' in jsdoc_content or 'COMPONENT:' in jsdoc_content:
        file_type = 'Component'
    elif '@function' in jsdoc_content or 'FUNCTION:' in jsdoc_content:
        file_type = 'Function'
    elif '@class' in jsdoc_content or 'CLASS:' in jsdoc_content:
        file_type = 'Class'
    elif '@interface' in jsdoc_content or 'INTERFACE:' in jsdoc_content:
        file_type = 'Interface'
    elif '@module' in jsdoc_content or 'MODULE:' in jsdoc_content:
        file_type = 'Module'
    elif '@file' in jsdoc_content:
        file_type = 'File'
    
    if file_type:
        md_content += f"File Type: {file_type}\n"
    
    md_content += "---\n\n"
    
    if jsdoc_content:
        # Parse the structured JSDoc content
        # Split on prefixes instead of double newlines to preserve JSDoc integrity
        sections = []
        current_section = ""
        
        for line in jsdoc_content.split('\n'):
            if any(line.startswith(prefix) for prefix in ['MODULE:', 'FUNCTION:', 'CLASS:', 'INTERFACE:', 'VARIABLE:', 'COMPONENT:', 'COMMENT:']):
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
        functions = []
        classes = []
        interfaces = []
        variables = []
        components = []
        comments = []
        
        for section in sections:
            if section.startswith('MODULE:'):
                module_doc = section.replace('MODULE:', '', 1).strip()
            elif section.startswith('FUNCTION:'):
                # Parse FUNCTION:name:jsdoc
                parts = section.replace('FUNCTION:', '', 1).split(':', 1)
                if len(parts) == 2:
                    func_name, func_jsdoc = parts
                    functions.append({
                        'name': func_name.strip(),
                        'jsdoc': func_jsdoc.strip()
                    })
            elif section.startswith('CLASS:'):
                # Parse CLASS:name:jsdoc
                parts = section.replace('CLASS:', '', 1).split(':', 1)
                if len(parts) == 2:
                    class_name, class_jsdoc = parts
                    classes.append({
                        'name': class_name.strip(),
                        'jsdoc': class_jsdoc.strip()
                    })
            elif section.startswith('INTERFACE:'):
                # Parse INTERFACE:name:jsdoc
                parts = section.replace('INTERFACE:', '', 1).split(':', 1)
                if len(parts) == 2:
                    interface_name, interface_jsdoc = parts
                    interfaces.append({
                        'name': interface_name.strip(),
                        'jsdoc': interface_jsdoc.strip()
                    })
            elif section.startswith('VARIABLE:'):
                # Parse VARIABLE:name:jsdoc
                parts = section.replace('VARIABLE:', '', 1).split(':', 1)
                if len(parts) == 2:
                    var_name, var_jsdoc = parts
                    variables.append({
                        'name': var_name.strip(),
                        'jsdoc': var_jsdoc.strip()
                    })
            elif section.startswith('COMPONENT:'):
                # Parse COMPONENT:name:jsdoc
                parts = section.replace('COMPONENT:', '', 1).split(':', 1)
                if len(parts) == 2:
                    comp_name, comp_jsdoc = parts
                    components.append({
                        'name': comp_name.strip(),
                        'jsdoc': comp_jsdoc.strip()
                    })
            elif section.startswith('COMMENT:'):
                # Parse COMMENT:identifier:jsdoc
                parts = section.replace('COMMENT:', '', 1).split(':', 1)
                if len(parts) == 2:
                    comment_id, comment_jsdoc = parts
                    comments.append({
                        'id': comment_id.strip(),
                        'jsdoc': comment_jsdoc.strip()
                    })
        
        # Add Info section
        md_content += "## Info\n\n"
        
        # Add module documentation
        if module_doc:
            # Parse the module documentation properly
            parsed_module = parse_jsdoc_content(module_doc)
            if parsed_module.get('description'):
                md_content += f"{parsed_module['description']}\n\n"
            # Add file metadata if present
            metadata = parsed_module.get('metadata', {})
            if metadata:
                metadata_parts = []
                for key, value in metadata.items():
                    if key == 'version':
                        metadata_parts.append(f"**Version**: {value}")
                    elif key == 'author':
                        metadata_parts.append(f"**Author**: {value}")
                    elif key == 'since':
                        metadata_parts.append(f"**Since**: {value}")
                    elif key == 'file':
                        metadata_parts.append(f"**File**: {value}")
                
                if metadata_parts:
                    md_content += '\n'.join(metadata_parts) + "\n\n"
        
        # Add functions section
        if functions:
            if len(functions) == 1:
                func = functions[0]
                md_content += f"**Function**: `{func['name']}`\n\n"
                # Parse and format the JSDoc
                parsed_jsdoc = parse_jsdoc_content(func['jsdoc'])
                formatted_jsdoc = format_jsdoc_as_markdown(parsed_jsdoc)
                md_content += f"{formatted_jsdoc}\n\n"
            else:
                md_content += "**Functions**:\n"
                for func in functions:
                    # Extract first line as summary - make sure to get the description, not tag content
                    parsed_jsdoc = parse_jsdoc_content(func['jsdoc'])
                    description = parsed_jsdoc.get('description', '').strip()
                    if description:
                        # Get the first meaningful line of description
                        first_line = description.split('\n')[0].strip()
                        # Remove any residual JSDoc tags that might have leaked through
                        first_line = re.sub(r'^@\w+\s*', '', first_line)
                        if not first_line:
                            first_line = "Function documentation"
                    else:
                        first_line = "Function documentation"
                    md_content += f"- `{func['name']}`: {first_line}\n"
                md_content += "\n"
                
                # Add detailed JSDoc for each function
                for func in functions:
                    md_content += f"### `{func['name']}`\n\n"
                    parsed_jsdoc = parse_jsdoc_content(func['jsdoc'])
                    formatted_jsdoc = format_jsdoc_as_markdown(parsed_jsdoc)
                    md_content += f"{formatted_jsdoc}\n\n"
        
        # Add classes section
        if classes:
            if len(classes) == 1:
                cls = classes[0]
                md_content += f"**Class**: `{cls['name']}`\n\n"
                md_content += f"{cls['jsdoc']}\n\n"
            else:
                md_content += "**Classes**:\n"
                for cls in classes:
                    # Extract first line as summary
                    first_line = cls['jsdoc'].split('\n')[0].strip()
                    md_content += f"- `{cls['name']}`: {first_line}\n"
                md_content += "\n"
                
                # Add detailed JSDoc for each class
                for cls in classes:
                    md_content += f"### `{cls['name']}`\n\n"
                    md_content += f"{cls['jsdoc']}\n\n"
        
        # Add interfaces section
        if interfaces:
            if len(interfaces) == 1:
                iface = interfaces[0]
                md_content += f"**Interface**: `{iface['name']}`\n\n"
                md_content += f"{iface['jsdoc']}\n\n"
            else:
                md_content += "**Interfaces**:\n"
                for iface in interfaces:
                    # Extract first line as summary
                    first_line = iface['jsdoc'].split('\n')[0].strip()
                    md_content += f"- `{iface['name']}`: {first_line}\n"
                md_content += "\n"
                
                # Add detailed JSDoc for each interface
                for iface in interfaces:
                    md_content += f"### `{iface['name']}`\n\n"
                    md_content += f"{iface['jsdoc']}\n\n"
        
        # Add variables section
        if variables:
            if len(variables) == 1:
                var = variables[0]
                md_content += f"**Variable**: `{var['name']}`\n\n"
                md_content += f"{var['jsdoc']}\n\n"
            else:
                md_content += "**Variables**:\n"
                for var in variables:
                    # Extract first line as summary
                    first_line = var['jsdoc'].split('\n')[0].strip()
                    md_content += f"- `{var['name']}`: {first_line}\n"
                md_content += "\n"
                
                # Add detailed JSDoc for each variable
                for var in variables:
                    md_content += f"### `{var['name']}`\n\n"
                    md_content += f"{var['jsdoc']}\n\n"
        
        # Add components section
        if components:
            if len(components) == 1:
                comp = components[0]
                md_content += f"**Component**: `{comp['name']}`\n\n"
                md_content += f"{comp['jsdoc']}\n\n"
            else:
                md_content += "**Components**:\n"
                for comp in components:
                    # Extract first line as summary
                    first_line = comp['jsdoc'].split('\n')[0].strip()
                    md_content += f"- `{comp['name']}`: {first_line}\n"
                md_content += "\n"
                
                # Add detailed JSDoc for each component
                for comp in components:
                    md_content += f"### `{comp['name']}`\n\n"
                    md_content += f"{comp['jsdoc']}\n\n"
        
        # Add comments section (for JSDoc that couldn't be associated with specific code)
        if comments:
            md_content += "**Documentation**:\n\n"
            for comment in comments:
                md_content += f"{comment['jsdoc']}\n\n"
        
    else:
        md_content += "## Info\n\n*No JSDoc comments found*\n"
    
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
        description="Extract JSDoc comments from TypeScript/JavaScript files and save as Markdown"
    )
    parser.add_argument(
        "folder", 
        help="Folder to search for TypeScript/JavaScript files"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Output directory for markdown files (default: auto-generated)"
    )
    args = parser.parse_args()
    if not os.path.isdir(args.folder):
        print(f"Error: '{args.folder}' is not a valid directory")
        return
    output_dir = args.output or get_output_base_dir()
    os.makedirs(output_dir, exist_ok=True)
    folder_path = Path(args.folder).resolve()
    project_name = folder_path.name
    typescript_files = find_typescript_files(args.folder)
    if not typescript_files:
        print(f"No TypeScript/JavaScript files found in '{args.folder}'")
        return
    print(f"Found {len(typescript_files)} TypeScript/JavaScript files")
    print(f"Output directory: {output_dir}")
    print(f"Project: {project_name}")
    print("-" * 50)
    processed = 0
    skipped = 0
    for ts_file in typescript_files:
        jsdoc_content = extract_jsdoc_comments(ts_file)
        if jsdoc_content.strip() and len(jsdoc_content.strip().split('\n')) > 3:
            create_markdown_file(ts_file, jsdoc_content, output_dir, project_name, folder_path)
            processed += 1
        else:
            skipped += 1
            if jsdoc_content.strip():
                print(f"Skipped (JSDoc too short): {ts_file}")
            else:
                print(f"Skipped (no JSDoc): {ts_file}")
    print("-" * 50)
    print(f"Processed {processed} files with substantial JSDoc comments successfully!")
    print(f"Skipped {skipped} files (no JSDoc or too short).")

if __name__ == "__main__":
    main()