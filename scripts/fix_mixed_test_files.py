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
Script to fix mixed test files that contain both pytest and unittest structures.
"""

import os
import re
from pathlib import Path


def fix_mixed_test_file(file_path):
    """Fix a test file that has mixed pytest and unittest structures."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file has mixed content
    if 'self.cf' in content or 'self.spec' in content or 'unittest.TestCase.setUp' in content:
        # This is a mixed file, need to convert it properly
        lines = content.split('\n')
        new_lines = []
        
        # Keep the header
        header_lines = []
        for line in lines:
            if line.startswith('#') or line.startswith('import') or line.startswith('from'):
                header_lines.append(line)
            else:
                break
        
        new_lines.extend(header_lines)
        new_lines.append('')
        
        # Add pytest import if not present
        if 'import pytest' not in content:
            new_lines.insert(-1, 'import pytest')
        
        # Convert class methods to functions
        in_class = False
        class_name = None
        
        for line in lines[len(header_lines):]:
            line = line.strip()
            if not line:
                continue
                
            # Detect class definition
            if line.startswith('class ') and 'unittest.TestCase' in line:
                in_class = True
                class_name = line.split('(')[0].split('class ')[1].strip()
                continue
            
            # Skip class definition line
            if in_class and line.startswith('class '):
                continue
                
            # Convert setUp method to fixture
            if in_class and line.startswith('def setUp(self):'):
                new_lines.append('@pytest.fixture')
                new_lines.append('def setup_config():')
                new_lines.append('    """Setup configuration for tests."""')
                new_lines.append('    cf = ConfigurationFile(\'pisi.conf\')')
                new_lines.append('    return cf')
                new_lines.append('')
                continue
                
            # Convert test methods to functions
            if in_class and line.startswith('def test'):
                method_name = line.split('def ')[1].split('(')[0]
                new_lines.append('@pytest.mark.unit')
                new_lines.append(f'def {method_name}(setup_config):')
                continue
                
            # Convert self references
            if in_class and line.startswith('self.'):
                # Remove 'self.' prefix
                line = line.replace('self.cf', 'cf')
                line = line.replace('self.spec', 'spec')
                line = line.replace('self.fail()', 'pytest.fail()')
                new_lines.append('    ' + line)
            elif in_class and line.startswith('cf = self.cf'):
                new_lines.append('    cf = setup_config')
            elif in_class and line.startswith('spec = self.spec'):
                new_lines.append('    spec = setup_config')
            elif in_class and line:
                # Regular line in test method
                new_lines.append('    ' + line)
        
        # Write the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))


def main():
    """Main function to fix mixed test files."""
    
    tests_dir = Path('tests')
    
    # List of files that still have parsing errors
    files_with_errors = [
        'test_configfile.py',
        'test_dependency.py',
        'test_history.py',
        'test_relation.py',
        'test_replace.py',
        'test_metadata.py',
        'test_files.py',
        'test_uri.py',
        'test_specfile.py',
        'test_mirrors.py',
        'test_shell.py',
        'test_srcarchive.py',
        'test_package.py',
        'test_conflict.py',
        'test_util.py',
        'test_file.py',
        'test_fetch.py',
        'test_graph.py',
    ]
    
    print("Fixing mixed test files...")
    print("=" * 40)
    
    for filename in files_with_errors:
        file_path = tests_dir / filename
        if file_path.exists():
            print(f"Fixing {filename}")
            try:
                fix_mixed_test_file(file_path)
                print(f"  ✓ Fixed successfully")
            except Exception as e:
                print(f"  ✗ Error fixing {filename}: {e}")
        else:
            print(f"  - File {filename} not found, skipping")
    
    print("\nMixed test files fixed!")
    print("\nNext steps:")
    print("1. Run black again: black tests/")
    print("2. Run tests: pytest")
    print("3. Review any remaining issues manually")


if __name__ == '__main__':
    main() 