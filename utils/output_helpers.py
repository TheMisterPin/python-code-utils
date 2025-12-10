#!/usr/bin/env python3
"""
Shared utility functions for managing output directories across all scripts.

This module provides standardized functions for finding the project root
and creating output directories that mirror the script's location.
"""

import os


def find_root(start_dir=None):
    """
    Traverse up the directory tree to find the project root.
    
    The project root is identified by the presence of the '_outputs' directory.
    
    Args:
        start_dir (str, optional): Starting directory for the search.
                                  If None, uses the caller's directory.
    
    Returns:
        str: Absolute path to the project root directory
        
    Raises:
        ValueError: If project root cannot be found
    """
    if start_dir is None:
        # Get the caller's directory (2 frames up: this function -> caller)
        import inspect
        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back
            caller_file = caller_frame.f_globals.get('__file__')
            if caller_file:
                start_dir = os.path.dirname(os.path.abspath(caller_file))
            else:
                start_dir = os.getcwd()
        finally:
            del frame
    
    current = start_dir
    while True:
        if os.path.exists(os.path.join(current, "_outputs")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            raise ValueError(
                f"Could not find project root with '_outputs' directory. "
                f"Started from: {start_dir}"
            )
        current = parent


def get_output_base_dir(script_file=None, subdirectory=None):
    """
    Create and return the output directory path for a script.
    
    The output directory mirrors the script's location under '_outputs/'.
    For example, if the script is at 'database/generate_tables.py',
    the output will be at '_outputs/database/'.
    
    Args:
        script_file (str, optional): Path to the script file. If None, 
                                    uses the caller's __file__.
        subdirectory (str, optional): Additional subdirectory under the 
                                     base output path (e.g., 'changed-tables')
    
    Returns:
        str: Absolute path to the output directory (created if needed)
        
    Raises:
        ValueError: If project root cannot be found
    """
    if script_file is None:
        # Get the caller's __file__
        import inspect
        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back
            script_file = caller_frame.f_globals.get('__file__')
            if script_file is None:
                raise ValueError("Could not determine script file path")
        finally:
            del frame
    
    script_dir = os.path.dirname(os.path.abspath(script_file))
    root = find_root(script_dir)
    
    # Calculate relative path from root to script directory
    relative_path = os.path.relpath(script_dir, root)
    
    # Create base output directory
    base_dir = os.path.join(root, "_outputs", relative_path)
    
    # Add subdirectory if specified
    if subdirectory:
        base_dir = os.path.join(base_dir, subdirectory)
    
    # Create directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)
    
    return base_dir


def get_root_dir(start_dir=None):
    """
    Alias for find_root() for backward compatibility.
    
    Args:
        start_dir (str, optional): Starting directory for the search
    
    Returns:
        str: Absolute path to the project root directory
    """
    return find_root(start_dir)
