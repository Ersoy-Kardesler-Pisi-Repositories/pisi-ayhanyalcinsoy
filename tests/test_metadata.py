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
import os

from pisi import metadata
from pisi import util


@pytest.mark.unit
def test_read():
    """Test reading metadata."""
    md = metadata.MetaData()
    md.read("metadata.xml")
    assert md.package.license == ["As-Is"]
    assert md.package.version == "1.7"
    assert md.package.installedSize == 149691
    return md


@pytest.mark.unit
def test_verify():
    """Test metadata verification."""
    md = test_read()
    if md.errors():
        pytest.fail()


@pytest.mark.unit
def test_write():
    """Test metadata writing."""
    md = test_read()
    md.write("/tmp/metadata-write.xml")
