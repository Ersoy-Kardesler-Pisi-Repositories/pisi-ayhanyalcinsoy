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


@pytest.mark.unit
def testInstalledPackageSatisfies():
    pisi.api.install(["ethtool"])
    relation = pisi.relation.Relation()

    relation.package = "ethtool"
    # Test version = X
    relation.version = "0.3"
    assert pisi.relation.installed_package_satisfies(relation)
    relation.version = None

    # Test versionFrom = X
    relation.versionFrom = "0.3"
    assert pisi.relation.installed_package_satisfies(relation)
    relation.versionFrom = "8"
    assert not pisi.relation.installed_package_satisfies(relation)
    relation.versionFrom = None

    # Test versionTo = X
    relation.versionTo = "8"
    assert pisi.relation.installed_package_satisfies(relation)
    relation.versionTo = "0.1"
    assert not pisi.relation.installed_package_satisfies(relation)
    relation.versionTo = None

    # Test release = X
    relation.release = "3"
    assert not pisi.relation.installed_package_satisfies(relation)
    relation.release = "1"
    assert pisi.relation.installed_package_satisfies(relation)
    relation.release = None

    # test releaseFrom = X
    relation.releaseFrom = "1"
    assert pisi.relation.installed_package_satisfies(relation)
    relation.releaseFrom = "7"
    assert not pisi.relation.installed_package_satisfies(relation)
    relation.releaseFrom = None

    # test releaseTo = X
    relation.releaseTo = "7"
    assert pisi.relation.installed_package_satisfies(relation)
    relation.releaseTo = "0"
    assert not pisi.relation.installed_package_satisfies(relation)
    relation.releaseTo = None

    pisi.api.remove(["ethtool"])
