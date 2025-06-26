# PiSi Unit Tests

This directory contains the unit tests for the PiSi package management system. The tests have been migrated from the old `unittest` framework to `pytest` for better test discovery, fixtures, and reporting.

## Setup

### Prerequisites

Install the test dependencies:

```bash
# Install pytest and test dependencies
pip install -r requirements-test.txt

# Or install with pip
pip install pytest pytest-cov pytest-mock pytest-xdist
```

### Test Repository Setup

Before running tests, you need to create test repositories:

```bash
cd tests/repos
python createrepos.py
cd ..
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run tests with verbose output
```bash
pytest -v
```

### Run specific test files
```bash
pytest tests/test_version.py
pytest tests/test_constants.py
```

### Run tests by markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only database tests
pytest -m database

# Skip slow tests
pytest -m "not slow"
```

### Run tests with coverage
```bash
pytest --cov=pisi --cov-report=html
```

### Run tests in parallel
```bash
pytest -n auto
```

## Test Structure

### Test Files
- `test_*.py` - Test files (pytest naming convention)
- `conftest.py` - Shared fixtures and configuration
- `pytest.ini` - Pytest configuration

### Test Categories
- **Unit tests** (`@pytest.mark.unit`) - Fast, isolated tests
- **Integration tests** (`@pytest.mark.integration`) - Tests that require external dependencies
- **Database tests** (`@pytest.mark.database`) - Tests that require database setup
- **Slow tests** (`@pytest.mark.slow`) - Tests that take longer to run

### Fixtures
- `setup_pisi_environment` - Sets up PiSi environment for all tests
- `temp_dir` - Provides a temporary directory for tests
- `clean_repos` - Cleans and recreates test repositories

## Migration from unittest

The tests have been migrated from the old `unittest` framework to `pytest`. Here are the key changes:

### Test Class to Function
```python
# Old unittest style
class TestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(a, b)

# New pytest style
def test_something():
    assert a == b
```

### Setup/Teardown to Fixtures
```python
# Old unittest style
def setUp(self):
    self.temp_dir = tempfile.mkdtemp()

def tearDown(self):
    shutil.rmtree(self.temp_dir)

# New pytest style
@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir
```

### Assertions
```python
# Old unittest style
self.assertEqual(a, b)
self.assertTrue(condition)
self.assertIn(item, collection)

# New pytest style
assert a == b
assert condition
assert item in collection
```

## Configuration

The test configuration is in `pytest.ini`:

- Test discovery patterns
- Markers for test categorization
- Default options for running tests
- Warning filters

## Continuous Integration

The tests can be run in CI environments with:

```bash
# Install dependencies
pip install -e .[test]

# Run tests
pytest --cov=pisi --cov-report=xml
```

## Troubleshooting

### Import Errors
If you get import errors for `pytest`, make sure you have installed the test dependencies:

```bash
pip install -r requirements-test.txt
```

### Repository Errors
If tests fail due to missing repositories, recreate them:

```bash
cd tests/repos && python createrepos.py && cd ..
```

### Permission Errors
Some tests may require specific permissions. Run with appropriate user privileges if needed. 