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
Script to fix remaining parsing errors in test files.
"""

import os
import re
from pathlib import Path


def fix_remaining_errors(file_path):
    """Fix remaining parsing errors in a test file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    
    # Keep the header (first 15 lines)
    header_end = 0
    for i, line in enumerate(lines):
        if line.startswith('import') or line.startswith('from'):
            header_end = i + 1
        elif line.strip() and not line.startswith('#') and i > 15:
            break
    
    new_lines.extend(lines[:header_end])
    new_lines.append('')
    
    # Process the rest of the file
    in_method = False
    method_indent = 0
    
    for line in lines[header_end:]:
        stripped = line.strip()
        
        if not stripped:
            if in_method:
                new_lines.append('')
            continue
        
        # Check if this is a method definition with self parameter
        if stripped.startswith('def ') and '(self)' in stripped:
            # Convert to pytest function
            method_name = stripped.split('def ')[1].split('(')[0]
            new_lines.append('@pytest.mark.unit')
            new_lines.append(f'def {method_name}():')
            in_method = True
            method_indent = 4
            continue
        
        # Check if this is a method definition without self parameter
        if stripped.startswith('def ') and '(self,' in stripped:
            # Convert to pytest function with parameters
            method_name = stripped.split('def ')[1].split('(')[0]
            params = stripped.split('(')[1].split(')')[0].replace('self,', '').replace('self', '')
            new_lines.append('@pytest.mark.unit')
            new_lines.append(f'def {method_name}({params}):')
            in_method = True
            method_indent = 4
            continue
        
        # If we're in a method, fix indentation
        if in_method:
            # Remove any existing indentation and add proper indentation
            if stripped.startswith('self.'):
                # Convert self references
                stripped = stripped.replace('self.fail()', 'pytest.fail()')
                # Remove self. prefix for common patterns
                if 'self.cf' in stripped:
                    stripped = stripped.replace('self.cf', 'cf')
                if 'self.spec' in stripped:
                    stripped = stripped.replace('self.spec', 'spec')
                if 'self.g0' in stripped:
                    stripped = stripped.replace('self.g0', 'g0')
                if 'self.g1' in stripped:
                    stripped = stripped.replace('self.g1', 'g1')
                if 'self.url' in stripped:
                    stripped = stripped.replace('self.url', 'url')
                if 'self.destpath' in stripped:
                    stripped = stripped.replace('self.destpath', 'destpath')
                if 'self.fetch' in stripped:
                    stripped = stripped.replace('self.fetch', 'fetch')
                if 'self.spec' in stripped:
                    stripped = stripped.replace('self.spec', 'spec')
                if 'self.cf' in stripped:
                    stripped = stripped.replace('self.cf', 'cf')
            
            new_lines.append(' ' * method_indent + stripped)
        else:
            # Not in a method, keep as is
            new_lines.append(line)
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))


def main():
    """Main function to fix remaining parsing errors."""
    
    tests_dir = Path('tests')
    
    # List of files that still have parsing errors
    files_with_errors = [
        'test_dependency.py',
        'test_history.py',
        'test_metadata.py',
        'test_replace.py',
        'test_mirrors.py',
        'test_srcarchive.py',
        'test_relation.py',
        'test_util.py',
        'test_file.py',
        'test_conflict.py',
        'test_graph.py',
        'test_fetch.py',
    ]
    
    print("Fixing remaining parsing errors...")
    print("=" * 45)
    
    for filename in files_with_errors:
        file_path = tests_dir / filename
        if file_path.exists():
            print(f"Fixing {filename}")
            try:
                fix_remaining_errors(file_path)
                print(f"  ✓ Fixed successfully")
            except Exception as e:
                print(f"  ✗ Error fixing {filename}: {e}")
        else:
            print(f"  - File {filename} not found, skipping")
    
    print("\nRemaining parsing errors fixed!")
    print("\nNext steps:")
    print("1. Run black again: black tests/")
    print("2. Run tests: pytest")
    print("3. Review any remaining issues manually")


if __name__ == '__main__':
    main() 