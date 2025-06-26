# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import pytest
import pisi


@pytest.fixture
def filesdb():
    """Provide a FilesDB instance for tests."""
    return pisi.db.filesdb.FilesDB()


@pytest.mark.database
def test_has_file(filesdb):
    """Test has_file method."""
    assert not filesdb.has_file("usr/bin/ethtool")
    pisi.api.install(["ethtool"])
    assert filesdb.has_file("usr/bin/ethtool")
    pisi.api.remove(["ethtool"])
    assert not filesdb.has_file("usr/bin/ethtool")


@pytest.mark.database
def test_get_file(filesdb):
    """Test get_file method."""
    pisi.api.install(["ethtool"])
    pkg, path = filesdb.get_file("usr/bin/ethtool")
    assert pkg == "ethtool"
    assert path == "usr/bin/ethtool"
    pisi.api.remove(["ethtool"])
    assert not filesdb.has_file("usr/bin/ethtool")


@pytest.mark.database
def test_add_remove_files(filesdb):
    """Test add_files and remove_files methods."""
    fileinfo1 = pisi.files.FileInfo()
    fileinfo1.path = "etc/pisi/pisi.conf"
    fileinfo2 = pisi.files.FileInfo()
    fileinfo2.path = "etc/pisi/mirrors.conf"

    files = pisi.files.Files()
    files.list.append(fileinfo1)
    files.list.append(fileinfo2)

    assert not filesdb.has_file("etc/pisi/pisi.conf")
    assert not filesdb.has_file("etc/pisi/mirrors.conf")

    filesdb.add_files("pisi", files)

    assert filesdb.has_file("etc/pisi/pisi.conf")
    assert filesdb.has_file("etc/pisi/mirrors.conf")

    pkg, path = filesdb.get_file("etc/pisi/pisi.conf")
    assert pkg == "pisi"

    # FIXME: inconsistency in filesdb.py add_remove and remove_remove parameters
    filesdb.remove_files(files.list)

    assert not filesdb.has_file("etc/pisi/pisi.conf")
    assert not filesdb.has_file("etc/pisi/mirrors.conf")


@pytest.mark.database
def test_search_file(filesdb):
    """Test search_file method."""
    assert not filesdb.search_file("ethtool")
    pisi.api.install(["ethtool"])
    found = filesdb.search_file("ethtool")
    pkg, files_list = found[0]
    assert set(files_list) == set(["usr/bin/ethtool"])
    pisi.api.remove(["ethtool"])
