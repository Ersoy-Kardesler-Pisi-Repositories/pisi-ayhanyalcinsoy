#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2010, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

"""
Script to fix indentation errors in test files that black couldn't parse.
"""

import os
import re
from pathlib import Path


def fix_indentation_errors(file_path):
    """Fix indentation errors in a test file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    in_test_function = False
    in_class = False
    
    for line in lines:
        # Skip empty lines at the beginning
        if not line.strip() and not fixed_lines:
            continue
        
        # Detect if we're in a test function
        if line.strip().startswith('def test_'):
            in_test_function = True
            in_class = False
            fixed_lines.append(line)
        elif line.strip().startswith('class '):
            in_class = True
            in_test_function = False
            fixed_lines.append(line)
        elif in_test_function and line.strip():
            # Fix indentation inside test functions
            if line.startswith('    '):
                fixed_lines.append(line)
            else:
                fixed_lines.append('    ' + line)
        elif in_test_function and not line.strip():
            # Empty line in test function
            fixed_lines.append('')
        elif in_class and line.strip().startswith('def '):
            # Convert class methods to functions
            method_name = line.split('def ')[1].split('(')[0]
            fixed_lines.append(f'@pytest.mark.unit')
            fixed_lines.append(f'def {method_name}():')
            in_test_function = True
            in_class = False
        elif in_class and line.strip() and not line.strip().startswith('def '):
            # Fix indentation for class content
            if line.startswith('    '):
                fixed_lines.append(line)
            else:
                fixed_lines.append('    ' + line)
        elif in_class and not line.strip():
            # Empty line in class
            fixed_lines.append('')
        else:
            in_test_function = False
            in_class = False
            fixed_lines.append(line)
    
    # Write fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))


def main():
    """Main function to fix indentation errors in test files."""
    
    tests_dir = Path('tests')
    
    # List of files that had parsing errors
    files_with_errors = [
        'test_configfile.py',
        'test_dependency.py',
        'test_conflict.py',
        'test_files.py',
        'test_file.py',
        'test_graph.py',
        'test_history.py',
        'test_specfile.py',
        'test_util.py',
        'test_relation.py',
        'test_srcarchive.py',
        'test_metadata.py',
        'test_replace.py',
        'test_uri.py',
        'test_mirrors.py',
        'test_shell.py',
        'test_package.py',
        'test_fetch.py',
    ]
    
    print("Fixing indentation errors in test files...")
    print("=" * 50)
    
    for filename in files_with_errors:
        file_path = tests_dir / filename
        if file_path.exists():
            print(f"Fixing {filename}")
            try:
                fix_indentation_errors(file_path)
                print(f"  ✓ Fixed successfully")
            except Exception as e:
                print(f"  ✗ Error fixing {filename}: {e}")
        else:
            print(f"  - File {filename} not found, skipping")
    
    print("\nIndentation errors fixed!")
    print("\nNext steps:")
    print("1. Run black again: black tests/")
    print("2. Run tests: pytest")
    print("3. Review any remaining issues manually")


if __name__ == '__main__':
    main() 