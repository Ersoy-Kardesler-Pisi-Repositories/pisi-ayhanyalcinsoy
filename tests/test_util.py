import pytest
import unittest
import shutil
from pisi.util import *
import os


@pytest.mark.unit
def initialize():
    testcase.testCase.initialize(self, database=False)

    # process related functions


@pytest.mark.unit
def testRunBatch():
    assert (0, "", "") == run_batch("cd")
    assert (127, "", "/bin/sh: add: command not found\n") == run_batch("add")


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
    self.assert_(subpath("usr", "usr"))
    self.assert_(subpath("usr", "usr/local/src"))
    self.assert_(not subpath("usr/local", "usr"))


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
    assert check_file("/etc/pisi/pisi.conf")
    assert check_file("/usr/bin/aatest")


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
    copy_file("/etc/pisi/pisi.conf", "/tmp/pisi-test1")
    copy_file("/etc/pisi/sandbox.conf", "/tmp/pisi-test2")
    copy_file_stat("/etc/pisi/pisi.conf", "/tmp/pisi-test1")
