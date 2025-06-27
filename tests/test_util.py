import pytest
import unittest
import shutil
from pisi.util import *
import os


@pytest.mark.unit
def initialize():
    # Initialize test environment if needed
    pass

    # process related functions


@pytest.mark.unit
def testRunBatch():
    result = run_batch("cd")
    # Handle both string and bytes output
    if isinstance(result[1], bytes):
        assert result[0] == 0
        assert result[1] == b""
        assert result[2] == b""
    else:
        assert result == (0, "", "")
    
    result = run_batch("add")
    # Only check error code and that error message contains 'not found'
    assert result[0] == 127
    err = result[2]
    if isinstance(err, bytes):
        err = err.decode()
    assert "not found" in err


@pytest.mark.unit
def testRunLogged():
    assert 0 == run_logged("ls")
    assert 1 == run_logged("rm")


@pytest.mark.unit
def testXtermTitle():
    xterm_title("pardus")
    xterm_title_reset()

    # path processing functions tests


@pytest.mark.unit
def testSplitPath():
    assert ["usr", "local", "src"] == splitpath("usr/local/src")
    assert ["usr", "lib", "pardus"] == splitpath("usr/lib/pardus")


@pytest.mark.unit
def testSubPath():
    assert subpath("usr", "usr")
    assert subpath("usr", "usr/local/src")
    assert not subpath("usr/local", "usr")


@pytest.mark.unit
def testRemovePathPrefix():
    pathname = removepathprefix("usr/local", "usr/local/src")
    assert "src" == pathname

    pathname = removepathprefix("usr/local", "usr/local/bin")
    assert not "bim" == pathname


@pytest.mark.unit
def testJoinPath():
    assert "usr/local/src" == join_path("usr/local", "src")
    assert not "usr/lib/hal" == join_path("usr", "hal")
    assert "usr/sbin/lpc" == join_path("usr", "sbin/lpc")

    # file/directory related functions tests


@pytest.mark.unit
def testCheckFile():
    # Test with existing files
    assert check_file("/etc/passwd")  # This should exist on any Unix system
    assert check_file("/usr/bin/python3")  # Python should be available
    
    # Test with non-existent file should raise exception
    import pytest
    with pytest.raises(FileError):
        check_file("/nonexistent/file")


@pytest.mark.unit
def testCleanDir():
    assert None == clean_dir("usr/lib")
    assert None == clean_dir("usr/local")
    assert not "tmp/pisi-root" == clean_dir("usr/tmp")


@pytest.mark.unit
def testDirSize():
    assert dir_size("usr/lib/pardus") != 2940
    assert dir_size("usr/lib") != 65


@pytest.mark.unit
def testCopyFile():
    # Create a test file to copy
    test_src = "/tmp/pisi-test-src"
    test_dest = "/tmp/pisi-test-dest"
    
    # Create a test file
    with open(test_src, "w") as f:
        f.write("test content")
    
    try:
        copy_file(test_src, test_dest)
        assert os.path.exists(test_dest)
        
        # Test copy_file_stat
        copy_file_stat(test_src, "/tmp/pisi-test-stat")
        assert os.path.exists("/tmp/pisi-test-stat")
    finally:
        # Clean up
        for f in [test_src, test_dest, "/tmp/pisi-test-stat"]:
            if os.path.exists(f):
                os.remove(f)
