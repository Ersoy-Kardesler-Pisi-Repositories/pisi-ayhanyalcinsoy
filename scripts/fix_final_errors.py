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
Script to fix final parsing errors in test files.
"""

import os
import re
from pathlib import Path


def fix_final_errors(file_path):
    """Fix final parsing errors in a test file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix common issues
    # 1. Fix missing newlines between functions
    content = re.sub(r'    @pytest\.mark\.', '\n\n@pytest.mark.', content)
    
    # 2. Fix indentation issues
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines at the beginning
        if not stripped and not new_lines:
            continue
            
        # Fix function definitions that are not properly indented
        if stripped.startswith('@pytest.mark.') and new_lines and new_lines[-1].strip():
            new_lines.append('')
            new_lines.append(line)
        elif stripped.startswith('def test_') and new_lines and new_lines[-1].strip():
            new_lines.append('')
            new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))


def main():
    """Main function to fix final parsing errors."""
    
    tests_dir = Path('tests')
    
    # List of files that still have parsing errors
    files_with_errors = [
        'test_file.py',
        'test_conflict.py',
        'test_fetch.py',
        'test_metadata.py',
        'test_graph.py',
    ]
    
    print("Fixing final parsing errors...")
    print("=" * 40)
    
    for filename in files_with_errors:
        file_path = tests_dir / filename
        if file_path.exists():
            print(f"Fixing {filename}")
            try:
                fix_final_errors(file_path)
                print(f"  ✓ Fixed successfully")
            except Exception as e:
                print(f"  ✗ Error fixing {filename}: {e}")
        else:
            print(f"  - File {filename} not found, skipping")
    
    print("\nFinal parsing errors fixed!")
    print("\nNext steps:")
    print("1. Run black again: black tests/")
    print("2. Run tests: pytest")
    print("3. Review any remaining issues manually")


if __name__ == '__main__':
    main() 