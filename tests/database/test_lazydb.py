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
import pisi.db.lazydb as lazydb


class TestLazyDB(lazydb.LazyDB):
    """Test implementation of LazyDB."""
    
    def init(self):
        self.testfield = True

    def getTestField(self):
        return self.testfield


@pytest.fixture
def test_db():
    """Provide a TestLazyDB instance."""
    return TestLazyDB()


@pytest.mark.database
def test_database_method_forcing_init(test_db):
    """Test database method that forces initialization."""
    assert test_db.getTestField()
    assert "testfield" in test_db.__dict__
    test_db._delete()


@pytest.mark.database
def test_database_without_init():
    """Test database without initialization."""
    db = TestLazyDB()
    assert "testfield" not in db.__dict__
    db._delete()


@pytest.mark.database
def test_singleton_behaviour():
    """Test singleton behavior."""
    db = TestLazyDB()
    db2 = TestLazyDB()
    assert id(db) == id(db2)
