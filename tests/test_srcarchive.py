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
import pisi.sourcearchive
from pisi.specfile import SpecFile


@pytest.mark.unit
def testFetch():
    spec = SpecFile("repos/pardus-2007/system/base/curl/pspec.xml")
    srcarch = pisi.sourcearchive.SourceArchive(spec.source.archive[0])
    self.assert_(not srcarch.fetch())


@pytest.mark.unit
def testIscached():
    spec = SpecFile("repos/pardus-2007/system/base/curl/pspec.xml")
    srcarch = pisi.sourcearchive.SourceArchive(spec.source.archive[0])
    assert srcarch.is_cached()


@pytest.mark.unit
def testIscached():
    spec = SpecFile("repos/pardus-2007/system/base/curl/pspec.xml")
    targetDir = "/tmp/tests"
    srcarch = pisi.sourcearchive.SourceArchive(spec.source.archive[0])
    self.assert_(not srcarch.unpack(targetDir))


@pytest.mark.unit
def testUnpack():
    spec = SpecFile("repos/pardus-2007/system/base/curl/pspec.xml")
    targetDir = "/tmp/tests"
    srcarch = pisi.sourcearchive.SourceArchive(spec.source.archive[0])
    srcarch.unpack(targetDir)
