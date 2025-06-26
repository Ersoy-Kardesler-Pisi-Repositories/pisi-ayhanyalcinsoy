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
Script to fix converted test files after automated migration.
This script cleans up the converted files by:
- Adding proper headers
- Removing unittest imports
- Fixing formatting issues
- Adding proper pytest decorators
"""

import os
import re
from pathlib import Path


def fix_test_file(file_path):
    """Fix a converted test file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add proper header if missing
    if not content.startswith('#!/usr/bin/env python3'):
        header = '''#!/usr/bin/env python3
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

'''
        content = header + content
    
    # Remove unittest import
    content = re.sub(r'import unittest\n', '', content)
    content = re.sub(r'import unittest', '', content)
    
    # Fix indentation issues
    lines = content.split('\n')
    fixed_lines = []
    in_test_function = False
    indent_level = 0
    
    for line in lines:
        # Skip empty lines at the beginning
        if not line.strip() and not fixed_lines:
            continue
            
        # Fix indentation for test functions
        if line.strip().startswith('def test_'):
            in_test_function = True
            indent_level = 0
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
        else:
            in_test_function = False
            fixed_lines.append(line)
    
    # Add pytest decorators if missing
    content = '\n'.join(fixed_lines)
    
    # Add @pytest.mark.unit decorator to test functions that don't have it
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        if line.strip().startswith('def test_') and i > 0:
            prev_line = lines[i-1].strip()
            if not prev_line.startswith('@pytest.mark.'):
                fixed_lines.append('@pytest.mark.unit')
        fixed_lines.append(line)
    
    # Write fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))


def main():
    """Main function to fix all converted test files."""
    
    tests_dir = Path('tests')
    
    # List of converted test files to fix
    test_files = [
        'test_configfile.py',
        'test_conflict.py',
        'test_dependency.py',
        'test_fetch.py',
        'test_file.py',
        'test_files.py',
        'test_graph.py',
        'test_history.py',
        'test_metadata.py',
        'test_mirrors.py',
        'test_package.py',
        'test_relation.py',
        'test_replace.py',
        'test_shell.py',
        'test_specfile.py',
        'test_srcarchive.py',
    ]
    
    print("Fixing converted test files...")
    print("=" * 40)
    
    for filename in test_files:
        file_path = tests_dir / filename
        if file_path.exists():
            print(f"Fixing {filename}")
            try:
                fix_test_file(file_path)
                print(f"  ✓ Fixed successfully")
            except Exception as e:
                print(f"  ✗ Error fixing {filename}: {e}")
        else:
            print(f"  - File {filename} not found, skipping")
    
    print("\nAll test files have been fixed!")
    print("\nNext steps:")
    print("1. Install pytest: pip install -r requirements-test.txt")
    print("2. Run tests: pytest")
    print("3. Review and fix any remaining issues manually")


if __name__ == '__main__':
    main() 