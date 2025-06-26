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
Migration script to convert unittest-based test files to pytest format.

This script helps convert the remaining unittest test files to pytest format.
It provides a template and guidance for the conversion process.
"""

import os
import re
import sys
from pathlib import Path


def convert_test_file(input_file, output_file):
    """Convert a unittest file to pytest format."""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add pytest import
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
            new_lines.append(f'@pytest.mark.unit')
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
    """Main migration function."""
    
    tests_dir = Path('tests')
    
    # List of files to convert (excluding already converted ones)
    files_to_convert = [
        'configfiletest.py',
        'conflicttests.py', 
        'dependencytest.py',
        'fetchtest.py',
        'filetest.py',
        'filestest.py',
        'graphtest.py',
        'historytest.py',
        'metadatatest.py',
        'mirrorstest.py',
        'packagetest.py',
        'relationtest.py',
        'replacetest.py',
        'shelltest.py',
        'specfiletests.py',
        'srcarchivetest.py',
        'uritest.py',
        'utiltest.py',
    ]
    
    print("PiSi Test Migration to pytest")
    print("=" * 40)
    
    for filename in files_to_convert:
        input_file = tests_dir / filename
        output_file = tests_dir / f'test_{filename.replace("test.py", "").replace("tests.py", "")}.py'
        
        if input_file.exists():
            print(f"Converting {filename} to {output_file.name}")
            try:
                convert_test_file(input_file, output_file)
                print(f"  ✓ Converted successfully")
            except Exception as e:
                print(f"  ✗ Error converting {filename}: {e}")
        else:
            print(f"  - File {filename} not found, skipping")
    
    print("\nMigration completed!")
    print("\nNext steps:")
    print("1. Review the converted test files")
    print("2. Install pytest: pip install -r requirements-test.txt")
    print("3. Run tests: pytest")
    print("4. Fix any remaining issues manually")


if __name__ == '__main__':
    main() 