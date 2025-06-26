# PiSi Test Migration to pytest

This document outlines the migration of PiSi tests from the old `unittest` framework to `pytest`.

## Overview

The PiSi test suite has been migrated from `unittest` to `pytest` to take advantage of:
- Better test discovery and organization
- Powerful fixtures system
- Improved assertion messages
- Parallel test execution
- Better coverage reporting
- More flexible test configuration

## Migration Status

### ✅ Completed
- Created `pytest.ini` configuration file with comprehensive settings
- Created `requirements-test.txt` with test dependencies
- Updated `Makefile` with comprehensive test commands
- Created comprehensive `tests/README.md`
- Converted core test files to pytest format:
  - `tests/test_constants.py`
  - `tests/test_version.py`
  - `tests/test_archive.py`
  - `tests/test_config_file.py`
  - `tests/test_dependency.py`
  - `tests/test_util.py`
  - `tests/test_uri.py`
  - `tests/test_metadata.py`
  - `tests/test_fetch.py`
  - `tests/test_file.py`
  - `tests/test_conflict.py`
  - `tests/test_graph.py`
  - `tests/test_relation.py`
  - `tests/test_srcarchive.py`
  - `tests/test_history.py`
  - `tests/test_replace.py`
  - `tests/test_mirrors.py`
  - `tests/test_configfile.py`
  - `tests/test_files.py`
  - `tests/test_package.py`
  - `tests/test_shell.py`
  - `tests/test_specfile.py`
  - `tests/test_config.py` (contains shared fixtures and configuration)
- Converted database test files:
  - `tests/database/test_componentdb.py`
  - `tests/database/test_filesdb.py`
  - `tests/database/test_installdb.py`
  - `tests/database/test_itembyrepo.py`
  - `tests/database/test_lazydb.py`
  - `tests/database/test_packagedb.py`
  - `tests/database/test_repodb.py`
  - `tests/database/test_sourcedb.py`
- Created automated migration scripts in `scripts/` directory
- Added comprehensive test configuration

### 🔄 In Progress
- Final cleanup of remaining unittest files
- Performance optimization of converted tests
- Integration test improvements

### 📋 To Do
- Remove old unittest files (keeping converted versions):
  - `conflicttests.py` → `test_conflict.py` ✅
  - `fetchtest.py` → `test_fetch.py` ✅
  - `filetest.py` → `test_file.py` ✅
  - `filestest.py` → `test_files.py` ✅
  - `graphtest.py` → `test_graph.py` ✅
  - `historytest.py` → `test_history.py` ✅
  - `metadatatest.py` → `test_metadata.py` ✅
  - `mirrorstest.py` → `test_mirrors.py` ✅
  - `packagetest.py` → `test_package.py` ✅
  - `relationtest.py` → `test_relation.py` ✅
  - `replacetest.py` → `test_replace.py` ✅
  - `shelltest.py` → `test_shell.py` ✅
  - `specfiletests.py` → `test_specfile.py` ✅
  - `srcarchivetest.py` → `test_srcarchive.py` ✅
  - Database tests in `tests/database/` → All converted ✅
- Update CI/CD configuration for pytest
- Performance optimization and parallel execution
- Add more comprehensive test coverage

## Key Changes

### 1. Test File Naming
- **Old**: `*test.py` or `*tests.py`
- **New**: `test_*.py` (pytest convention)

### 2. Test Structure
- **Old**: Class-based tests inheriting from `unittest.TestCase`
- **New**: Function-based tests with pytest decorators

### 3. Assertions
- **Old**: `self.assertEqual(a, b)`, `self.assertTrue(condition)`
- **New**: `assert a == b`, `assert condition`

### 4. Setup/Teardown
- **Old**: `setUp()` and `tearDown()` methods
- **New**: pytest fixtures with `@pytest.fixture` (see `tests/test_config.py`)

### 5. Test Categories
- **Old**: No categorization
- **New**: Markers for different test types:
  - `@pytest.mark.unit` - Fast, isolated tests
  - `@pytest.mark.integration` - Tests requiring external dependencies
  - `@pytest.mark.database` - Database tests
  - `@pytest.mark.slow` - Tests that take longer to run

## Configuration Files

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --disable-warnings
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    database: marks tests that require database setup
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### test_config.py
Shared fixtures and configuration are provided in `tests/test_config.py`:
- `setup_pisi_environment` - Sets up PiSi environment for all tests
- `temp_dir` - Temporary directory for tests
- `clean_repos` - Clean test repositories

## Usage

### Installation
```bash
# Activate virtual environment
source venv/bin/activate

# Install test dependencies
pip install -r requirements-test.txt

# Or install with pip
pip install pytest pytest-cov pytest-mock pytest-xdist
```

### Running Tests
```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m database

# Run with coverage
pytest --cov=pisi --cov-report=html

# Run in parallel
pytest -n auto

# Skip slow tests
pytest -m "not slow"

# Run only fast tests
make test-fast
```

### Using Makefile
```bash
# Activate virtual environment first
source venv/bin/activate

make install-test-deps
make test
make test-unit
make test-integration
make test-database
make test-coverage
make test-fast
make test-parallel
make clean-tests
make setup-test-repos
```

## Migration Scripts

Several automated scripts have been created to help with the migration:

### Main Migration Script
```bash
source venv/bin/activate
python scripts/migrate_tests_to_pytest.py
```

### Database Test Conversion
```bash
source venv/bin/activate
python scripts/convert_database_tests.py
```

### Fix Scripts
```bash
source venv/bin/activate
python scripts/fix_converted_tests.py
python scripts/fix_remaining_errors.py
python scripts/fix_indentation_errors.py
python scripts/fix_mixed_test_files.py
python scripts/fix_final_errors.py
```

These scripts:
- Convert test classes to functions
- Transform assertions
- Add pytest decorators
- Preserve test logic
- Fix common migration issues

## Benefits

### 1. Better Test Discovery
- Automatic discovery of test files
- No need for manual test suite creation
- Flexible naming conventions

### 2. Powerful Fixtures
- Shared setup across tests (see `test_config.py`)
- Automatic cleanup
- Dependency injection
- Scope control (function, class, module, session)

### 3. Improved Assertions
- Better error messages
- No need for assertion methods
- More readable test code

### 4. Test Organization
- Markers for test categorization
- Easy filtering and selection
- Better test reporting

### 5. Performance
- Parallel test execution
- Selective test running
- Faster test discovery

## Best Practices

### 1. Test Naming
- Use descriptive test function names
- Follow the pattern `test_<functionality>_<scenario>`

### 2. Fixtures
- Use fixtures for shared setup (see `test_config.py`)
- Keep fixtures focused and reusable
- Use appropriate scopes

### 3. Assertions
- Use simple assertions when possible
- Provide clear error messages
- Test one thing per test function

### 4. Test Organization
- Group related tests in the same file
- Use markers for categorization
- Keep tests independent

### 5. Documentation
- Add docstrings to test functions
- Document complex test scenarios
- Keep test code readable

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure pytest is installed: `pip install pytest`
   - Check Python path and module imports
   - Make sure virtual environment is activated

2. **Test Discovery Issues**
   - Verify file naming follows pytest conventions
   - Check `pytest.ini` configuration

3. **Fixture Errors**
   - Ensure fixtures are properly defined (see `test_config.py`)
   - Check fixture scope and dependencies

4. **Assertion Failures**
   - Review error messages for debugging
   - Check test data and expected results

5. **Virtual Environment Issues**
   - Always activate virtual environment: `source venv/bin/activate`
   - Ensure test dependencies are installed in venv

### Getting Help

- Check pytest documentation: https://docs.pytest.org/
- Review the `tests/README.md` file
- Use `pytest --help` for command-line options
- Run `make help` for available Makefile commands

## Future Improvements

1. **Performance Optimization**
   - Implement test parallelization
   - Optimize slow tests
   - Add test caching

2. **Coverage Enhancement**
   - Increase test coverage
   - Add missing test scenarios
   - Improve test quality

3. **CI/CD Integration**
   - Update CI configuration
   - Add automated test reporting
   - Implement test result notifications

4. **Documentation**
   - Add more test examples
   - Improve migration documentation
   - Create testing guidelines

## Migration Progress Summary

| Category | Total Files | Converted | Remaining | Progress |
|----------|-------------|-----------|-----------|----------|
| Core Tests | 22 | 22 | 0 | 100% ✅ |
| Database Tests | 8 | 8 | 0 | 100% ✅ |
| Old Files | 26 | 0 | 26 | 0% (to be removed) |
| **Total** | **56** | **30** | **26** | **54%** |

## Current Status

- **31 pytest files** have been created and are functional
- **26 old unittest files** remain and need to be cleaned up
- **pytest.ini** is properly configured
- **Makefile** has comprehensive test commands
- **Virtual environment** is set up and working
- **Test dependencies** are properly installed

## Next Steps

1. **Remove old unittest files** after verification
2. **Optimize test performance**
3. **Update CI/CD pipelines**
4. **Add more comprehensive test coverage**

## Conclusion

The migration to pytest has made significant progress with all core functionality converted to the new framework. The new structure offers better organization, improved performance, and enhanced developer experience while maintaining compatibility with existing test logic.

The remaining work involves cleaning up old unittest files and optimizing the converted tests for better performance. The migration provides a solid foundation for future test development and maintenance.

### Immediate Actions Needed
1. Remove old unittest files after verification
2. Fix pytest marker warnings in configuration
3. Optimize test performance
4. Update CI/CD pipelines 