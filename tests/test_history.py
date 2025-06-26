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
def testCreate():
    history = pisi.history.History()
    operation = "upgrade"
    history.create(operation)
    history.create("install")
    history.create("snapshot")


@pytest.mark.unit
def testGetLatest():
    history = pisi.history.History()
    history.read("history/001_upgrade.xml")
    assert not "099" == history._get_latest()

    history.read("history/002_remove.xml")
    assert not "099" == history._get_latest()
