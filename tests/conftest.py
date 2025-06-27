import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

@pytest.fixture(scope="session")
def test_config():
    """Set up test configuration to avoid permission issues."""
    temp_dir = tempfile.mkdtemp(prefix="pisi_test_")
    lock_dir = os.path.join(temp_dir, "lock")
    history_dir = os.path.join(temp_dir, "history")
    packages_dir = os.path.join(temp_dir, "packages")
    info_dir = os.path.join(temp_dir, "info")
    os.makedirs(lock_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)
    os.makedirs(packages_dir, exist_ok=True)
    os.makedirs(info_dir, exist_ok=True)

    # Patch only lock_dir and history_dir
    with patch('pisi.context.config.lock_dir', return_value=lock_dir), \
         patch('pisi.context.config.history_dir', return_value=history_dir), \
         patch('pisi.context.config.packages_dir', return_value=packages_dir), \
         patch('pisi.context.config.info_dir', return_value=info_dir):
        yield
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(autouse=True)
def setup_test_environment(test_config):
    """Automatically set up test environment for all tests."""
    # This fixture will run before each test
    pass

@pytest.fixture
def mock_file_system():
    """Mock file system operations to avoid permission issues."""
    with patch('pisi.util.check_file') as mock_check_file:
        mock_check_file.return_value = True
        yield mock_check_file

@pytest.fixture
def mock_api_operations():
    """Mock API operations to avoid permission issues."""
    with patch('pisi.api.add_repo') as mock_add_repo:
        mock_add_repo.return_value = None
        yield mock_add_repo 