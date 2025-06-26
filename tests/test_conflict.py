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

import pytest
import pisi
import pisi.context as ctx
import pisi.conflict


@pytest.mark.integration
def test_installed_package_conflicts():
    """Test installed package conflicts."""
    pisi.api.install(["ethtool"])
    confinfo = pisi.conflict.Conflict()
    confinfo.package = "ethtool"
    confinfo.version = "6"
    confinfo.release = "1"
    assert not pisi.conflict.installed_package_conflicts(confinfo)
    pisi.api.remove(["ethtool"])


@pytest.mark.integration
def test_calculate_conflicts():
    """Test conflict calculation."""
    packagedb = pisi.db.packagedb.PackageDB()
    packages = ["ethtool", "zlib", "ctorrent"]
    assert pisi.conflict.calculate_conflicts(packages, packagedb)


@pytest.mark.integration
def test_conflict_check():
    """Test conflict checking between packages."""
    # In our sample repo1, spam conflicts with bar.
    # If this fails, it may affect database test case results.
    pisi.api.add_repo("repo1", "repos/repo1-bin/pisi-index.xml")
    pisi.api.update_repo("repo1")
    pisi.api.install(["spam"])
    myconflict = pisi.conflict.Conflict()
    myconflict.package = "bar"
    myconflict.version = "0.3"
    myconflict.release = "1"
    pisi.api.install(["bar"])
    assert "bar" in pisi.api.list_installed()
    assert "spam" not in pisi.api.list_installed()
    pisi.api.remove(["bar"])
    pisi.api.remove_repo("repo1")


@pytest.mark.integration
def test_inter_repo_cross_conflicts():
    """Test inter-repository cross conflicts."""
    # If this fails, it may affect database test case results
    pisi.api.add_repo("repo1", "repos/repo1-bin/pisi-index.xml")
    pisi.api.update_repo("repo1")
    pisi.api.install(["spam", "foo"])
    before = pisi.api.list_installed()
    pisi.api.remove_repo("repo1")
    pisi.api.add_repo("repo2", "repos/repo2-bin/pisi-index.xml")
    pisi.api.update_repo("repo2")
    pisi.api.upgrade(["spam"])
    after = pisi.api.list_installed()
    assert set(before) == set(after)
    idb = pisi.db.installdb.InstallDB()
    assert 3 == int(idb.get_package("foo").release)
    pisi.api.remove(["foo"])
    pisi.api.remove(["spam"])
    pisi.api.remove_repo("repo2")
