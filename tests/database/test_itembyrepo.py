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
import pisi.db.itembyrepo


@pytest.fixture
def testdb():
    """Provide test database with sample data."""
    packages = {}
    obsoletes = {}

    packages["pardus-2007"] = {
        "aggdraw": "package aggdraw",
        "acpica": "package acpica",
    }
    packages["contrib-2007"] = {
        "kdiff3": "package kdiff3",
        "kmess": "package kmess",
    }

    obsoletes["pardus-2007"] = ["wengophone", "rar"]
    obsoletes["contrib-2007"] = ["xara"]

    tdb = pisi.db.itembyrepo.ItemByRepo(packages)
    odb = pisi.db.itembyrepo.ItemByRepo(obsoletes)

    # original item_repos in ItemByRepo uses repodb.list_repos
    def item_repos(repo=None):
        repos = ["pardus-2007", "contrib-2007"]
        if repo:
            repos = [repo]
        return repos

    tdb.item_repos = item_repos
    odb.item_repos = item_repos
    
    return {"tdb": tdb, "odb": odb}


@pytest.mark.database
def test_has_repository(testdb):
    """Test has_repo method."""
    assert testdb["tdb"].has_repo("pardus-2007")
    assert testdb["tdb"].has_repo("contrib-2007")
    assert not testdb["tdb"].has_repo("hedehodo")


@pytest.mark.database
def test_has_item(testdb):
    """Test has_item method."""
    assert testdb["tdb"].has_item("kdiff3", "contrib-2007")
    assert not testdb["tdb"].has_item("kdiff3", "pardus-2007")
    assert testdb["tdb"].has_item("acpica")


@pytest.mark.database
def test_which_repo(testdb):
    """Test which_repo method."""
    assert testdb["tdb"].which_repo("aggdraw") == "pardus-2007"
    assert testdb["tdb"].which_repo("kmess") == "contrib-2007"


@pytest.mark.database
def test_get_item_and_repository(testdb):
    """Test get_item_repo method."""
    pkg, repo = testdb["tdb"].get_item_repo("acpica")
    assert pkg == "package acpica"
    assert repo == "pardus-2007"

    pkg, repo = testdb["tdb"].get_item_repo("kmess")
    assert pkg == "package kmess"
    assert repo == "contrib-2007"


@pytest.mark.database
def test_item_repos():
    """Test item_repos method."""
    db = pisi.db.itembyrepo.ItemByRepo({})
    assert db.item_repos("caracal") == ["caracal"]
    # repos were created by testcase.py
    assert db.item_repos() == ["pardus-2007", "contrib-2007", "pardus-2007-src"]


@pytest.mark.database
def test_get_item(testdb):
    """Test get_item method."""
    assert testdb["tdb"].get_item("acpica") == "package acpica"
    assert testdb["tdb"].get_item("kmess") == "package kmess"


@pytest.mark.database
def test_get_item_of_repository(testdb):
    """Test get_item with repository parameter."""
    assert testdb["tdb"].get_item("acpica", "pardus-2007") == "package acpica"
    assert testdb["tdb"].get_item("kmess", "contrib-2007") == "package kmess"


@pytest.mark.database
def test_get_item_keys(testdb):
    """Test get_item_keys method."""
    assert set(testdb["tdb"].get_item_keys("pardus-2007")) == set(
        ["aggdraw", "acpica"]
    )
    assert set(testdb["tdb"].get_item_keys("contrib-2007")) == set(
        ["kdiff3", "kmess"]
    )
    assert set(testdb["tdb"].get_item_keys()) == set(
        ["kdiff3", "kmess", "aggdraw", "acpica"]
    )


@pytest.mark.database
def test_get_list_item(testdb):
    """Test get_list_item method."""
    assert set(testdb["odb"].get_list_item("pardus-2007")) == set(
        ["rar", "wengophone"]
    )
    assert set(testdb["odb"].get_list_item("contrib-2007")) == set(["xara"])
    assert set(testdb["odb"].get_list_item()) == set(
        ["rar", "xara", "wengophone"]
    )
