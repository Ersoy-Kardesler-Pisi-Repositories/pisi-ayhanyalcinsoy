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
Script to convert database tests to pytest format.
"""

import os
import re
from pathlib import Path


def convert_database_test_file(input_file, output_file):
    """Convert a database test file to pytest format."""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add pytest import and header
    if 'import pytest' not in content:
        content = content.replace('import unittest', 'import pytest\nimport unittest')
    
    # Convert test class to functions
    lines = content.split('\n')
    new_lines = []
    in_test_class = False
    class_name = None
    
    for line in lines:
        # Detect test class
        if re.match(r'class.*TestCase.*unittest\.TestCase', line):
            in_test_class = True
            class_name = line.split('(')[0].split('class ')[1].strip()
            continue
        
        # Skip class definition and setup/teardown
        if in_test_class and (line.strip().startswith('class ') or 
                              line.strip().startswith('def setUp') or
                              line.strip().startswith('def tearDown')):
            continue
        
        # Convert test methods to functions
        if in_test_class and line.strip().startswith('def test_'):
            # Convert method to function
            method_name = line.split('def ')[1].split('(')[0]
            new_lines.append(f'@pytest.mark.database')
            new_lines.append(f'def {method_name}():')
            continue
        
        # Convert assertions
        if in_test_class:
            line = convert_assertions(line)
        
        new_lines.append(line)
    
    # Write converted content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))


def convert_assertions(line):
    """Convert unittest assertions to pytest assertions."""
    
    # Convert common assertions
    conversions = [
        (r'self\.assertEqual\((.*?),\s*(.*?)\)', r'assert \1 == \2'),
        (r'self\.assertNotEqual\((.*?),\s*(.*?)\)', r'assert \1 != \2'),
        (r'self\.assertTrue\((.*?)\)', r'assert \1'),
        (r'self\.assertFalse\((.*?)\)', r'assert not \1'),
        (r'self\.assertIn\((.*?),\s*(.*?)\)', r'assert \1 in \2'),
        (r'self\.assertNotIn\((.*?),\s*(.*?)\)', r'assert \1 not in \2'),
        (r'self\.assertIsNone\((.*?)\)', r'assert \1 is None'),
        (r'self\.assertIsNotNone\((.*?)\)', r'assert \1 is not None'),
        (r'self\.assertRaises\((.*?),\s*(.*?)\)', r'pytest.raises(\1):\n        \2'),
    ]
    
    for pattern, replacement in conversions:
        line = re.sub(pattern, replacement, line)
    
    return line


def main():
    """Main conversion function."""
    
    database_dir = Path('tests/database')
    
    # List of database test files to convert
    files_to_convert = [
        'componentdbtest.py',
        'filesdbtest.py',
        'installdbtest.py',
        'itembyrepotest.py',
        'lazydbtest.py',
        'packagedbtest.py',
        'repodbtest.py',
        'sourcedbtest.py',
    ]
    
    print("Converting database tests to pytest...")
    print("=" * 40)
    
    for filename in files_to_convert:
        input_file = database_dir / filename
        output_file = database_dir / f'test_{filename.replace("test.py", "").replace("dbtest.py", "_db")}.py'
        
        if input_file.exists():
            print(f"Converting {filename} to {output_file.name}")
            try:
                convert_database_test_file(input_file, output_file)
                print(f"  ✓ Converted successfully")
            except Exception as e:
                print(f"  ✗ Error converting {filename}: {e}")
        else:
            print(f"  - File {filename} not found, skipping")
    
    print("\nDatabase test conversion completed!")
    print("\nNext steps:")
    print("1. Review the converted database test files")
    print("2. Install pytest: pip install -r requirements-test.txt")
    print("3. Run database tests: pytest -m database")
    print("4. Fix any remaining issues manually")


if __name__ == '__main__':
    main() 