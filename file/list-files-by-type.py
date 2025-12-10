import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.output_helpers import get_output_base_dir

# File types to list (add more extensions as needed)
file_types = ['.scss']

# Root directory to scan (use '.' for current directory)
root_dir = 'C:\\Code\\Progetti-BK\\IONIC\\WSpace\\src\\app'

def has_matching_files(root, file_types):
    for r, d, f in os.walk(root):
        if any(file.endswith(ext) for ext in file_types for file in f):
            return True
    return False

def generate_markdown_list(root_dir, file_types):
    markdown = ''
    for root, dirs, files in os.walk(root_dir):
        if not has_matching_files(root, file_types):
            continue
        # Calculate depth relative to root_dir
        depth = root.replace(root_dir, '').count(os.sep)
        if depth == 0:
            # Top level
            header = '# ' + os.path.basename(root) if os.path.basename(root) != '.' else '# Root Directory'
        else:
            header = '#' * (depth + 1) + ' ' + os.path.basename(root)
        markdown += header + '\n\n'
        
        # Sort files for consistency
        files.sort()
        for file in files:
            if any(file.endswith(ext) for ext in file_types):
                markdown += '- [ ] ' + file + '\n'
        markdown += '\n'
    
    return markdown

if __name__ == '__main__':
    markdown_output = generate_markdown_list(root_dir, file_types)
    output_path = os.path.join(get_output_base_dir(), "file_list.md")
    with open(output_path, 'w') as f:
        f.write(markdown_output)
    print("Markdown file generated: " + output_path)
