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
import pisi.replace
import pisi.relation


@pytest.mark.unit
def testInstalledPackageReplaced():
    pisi.api.install(["ethtool"])
    relation = pisi.relation.Relation()
    relation.package = "ethtool"
    relation.version = "6"
    relation.release = "1"

    replace = pisi.replace.Replace(relation)
    replace.package = "zlib"
    # Check if the replaced package is installed
    self.assert_(pisi.replace.installed_package_replaced(replace))
    repinfo = pisi.replace.Replace(relation)
    repinfo.package = "ctorrent"
    assert not pisi.replace.installed_package_replaced(repinfo)

    pisi.api.remove(["ethtool"])
