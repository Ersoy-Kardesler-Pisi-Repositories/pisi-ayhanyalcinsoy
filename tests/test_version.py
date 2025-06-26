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
from pisi.version import Version


@pytest.mark.unit
def test_version_single():
    """Test single version comparison."""
    v1 = Version("103")
    v2 = Version("90")
    assert v1 > v2


@pytest.mark.unit
def test_version_ops_numerical():
    """Test numerical version operations."""
    v1 = Version("0.3.1")
    v2 = Version("0.3.5")
    v3 = Version("1.5.2")
    v4 = Version("0.3.1")
    v5 = Version("2.07")

    assert v1 < v2
    assert v3 > v2
    assert v1 <= v3
    assert v4 >= v4
    assert v5 > v3


@pytest.mark.unit
def test_version_ops_keywords():
    """Test version operations with keywords."""
    # with keywords
    v1 = Version("2.23_pre10")
    v2 = Version("2.23")
    v3 = Version("2.21")
    v4 = Version("2.23_p1")
    v5 = Version("2.23_beta1")
    v6 = Version("2.23_m1")
    v7 = Version("2.23_rc1")
    v8 = Version("2.23_rc2")

    assert v1 < v2
    assert v1 > v3
    assert v1 < v4
    assert v1 > v5
    assert v2 < v4
    assert v2 > v5
    assert v6 < v4
    assert v6 > v5
    assert v7 > v5
    assert v8 > v7

    v1 = Version("1.0_alpha1")
    v2 = Version("1.0_alpha2")
    assert v2 > v1


@pytest.mark.unit
def test_version_ops_characters():
    """Test version operations with characters."""
    # with character
    v1 = Version("2.10a")
    v2 = Version("2.10")
    v3 = Version("2.10d")

    assert v1 > v2
    assert v1 < v3
    assert v2 < v3


@pytest.mark.unit
def test_version_ge_bug():
    """Test version greater than or equal bug (bug 603)."""
    v1 = Version("1.8.0")
    v2 = Version("1.9.1")
    assert not v1 > v2
    assert not v1 >= v2
