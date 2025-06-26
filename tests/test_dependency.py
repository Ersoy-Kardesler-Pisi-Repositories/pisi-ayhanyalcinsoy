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
import pisi.relation
import pisi.dependency


@pytest.mark.unit
def testDictSatisfiesDep():
    pisi.api.install(["ethtool"])
    relation = pisi.relation.Relation()
    relation.package = "ethtool"

    pisi.api.install(["zlib"])
    rel = pisi.relation.Relation()
    rel.package = "zlib"

    depinfo = pisi.dependency.Dependency(relation)
    dictionary = {"ethtool": [" "], "zlib": ["a", "b"], "ctorrent": ["c"]}
    assert not depinfo.satisfied_by_dict_repo(dictionary)
    depinf = pisi.dependency.Dependency(rel)
    assert not depinf.satisfied_by_dict_repo(dictionary)


@pytest.mark.unit
def testInstalledSatisfiesDep():
    pisi.api.install(["ctorrent"])
    relation = pisi.relation.Relation()
    relation.package = "ctorrent"
    depinfo = pisi.dependency.Dependency(relation)
    assert not depinfo.satisfied_by_installed()


@pytest.mark.unit
def testRepoSatisfiesDependency():
    pisi.api.install(["ethtool"])
    relation = pisi.relation.Relation()
    relation.package = "ctorrent"
    depinfo = pisi.dependency.Dependency(relation)
    assert not depinfo.satisfied_by_repo()
