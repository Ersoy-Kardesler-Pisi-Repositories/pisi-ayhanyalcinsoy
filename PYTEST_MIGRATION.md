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
- Created `pytest.ini` configuration file
- Created `tests/conftest.py` with shared fixtures
- Created `requirements-test.txt` with test dependencies
- Updated `setup.py` with test dependencies
- Created `Makefile` with test commands
- Created comprehensive `tests/README.md`
- Converted several test files to pytest format:
  - `tests/test_constants.py`
  - `tests/test_version.py`
  - `tests/test_archive.py`
  - `tests/test_config_file.py`
  - `tests/test_dependency.py`
  - `tests/test_util.py`
  - `tests/test_uri.py`

### 🔄 In Progress
- Migration of remaining test files using automated script
- Database test conversion
- Integration test setup

### 📋 To Do
- Convert remaining unittest files:
  - `conflicttests.py`
  - `fetchtest.py`
  - `filetest.py`
  - `filestest.py`
  - `graphtest.py`
  - `historytest.py`
  - `metadatatest.py`
  - `mirrorstest.py`
  - `packagetest.py`
  - `relationtest.py`
  - `replacetest.py`
  - `shelltest.py`
  - `specfiletests.py`
  - `srcarchivetest.py`
- Convert database tests in `tests/database/`
- Update CI/CD configuration
- Performance optimization

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
- **New**: pytest fixtures with `@pytest.fixture`

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
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    database: marks tests that require database setup
```

### conftest.py
Provides shared fixtures:
- `setup_pisi_environment` - Sets up PiSi environment
- `temp_dir` - Temporary directory for tests
- `clean_repos` - Clean test repositories

## Usage

### Installation
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Or install with pip
pip install pytest pytest-cov pytest-mock pytest-xdist
```

### Running Tests
```bash
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
```

### Using Makefile
```bash
make install-test-deps
make test
make test-unit
make test-coverage
make clean-tests
```

## Migration Script

The `scripts/migrate_tests_to_pytest.py` script helps automate the conversion of remaining unittest files:

```bash
python scripts/migrate_tests_to_pytest.py
```

This script:
- Converts test classes to functions
- Transforms assertions
- Adds pytest decorators
- Preserves test logic

## Benefits

### 1. Better Test Discovery
- Automatic discovery of test files
- No need for manual test suite creation
- Flexible naming conventions

### 2. Powerful Fixtures
- Shared setup across tests
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
- Use fixtures for shared setup
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

2. **Test Discovery Issues**
   - Verify file naming follows pytest conventions
   - Check `pytest.ini` configuration

3. **Fixture Errors**
   - Ensure fixtures are properly defined
   - Check fixture scope and dependencies

4. **Assertion Failures**
   - Review error messages for debugging
   - Check test data and expected results

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

## Conclusion

The migration to pytest provides a modern, powerful testing framework for the PiSi project. The new structure offers better organization, improved performance, and enhanced developer experience while maintaining compatibility with existing test logic.

The migration is designed to be incremental, allowing for gradual adoption and testing of the new framework while maintaining the existing test suite functionality. 