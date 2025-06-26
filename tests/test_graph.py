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
import pisi
from pisi import graph


@pytest.fixture
@pytest.mark.unit
def test_graphs():
    """Setup test graphs."""
    g0 = pisi.graph.Digraph()
    g0.add_edge(1, 2)
    g0.add_edge(1, 3)
    g0.add_edge(2, 3)
    g0.add_edge(3, 4)
    g0.add_edge(4, 1)
    g1 = pisi.graph.Digraph()
    g1.add_edge(0, 2)
    g1.add_edge(0, 3)
    g1.add_edge(2, 4)
    g1.add_edge(3, 4)
    return g0, g1


@pytest.mark.unit
def test_has_vertex(test_graphs):
    """Test vertex existence checking."""
    g0, g1 = test_graphs
    assert not g0.has_vertex(5)
    assert not g1.has_vertex(1)


@pytest.mark.unit
def test_has_edge(test_graphs):
    """Test edge existence checking."""
    g0, g1 = test_graphs
    assert not g0.has_edge(5, 6)
    assert not g0.has_edge(3, 5)
    assert not g1.has_edge(2, 3)


@pytest.mark.unit
def test_cycle(test_graphs):
    """Test cycle detection."""
    g0, g1 = test_graphs
    assert not g0.cycle_free()
    assert g1.cycle_free()


@pytest.mark.unit
def test_topological_sort(test_graphs):
    """Test topological sorting."""
    g0, g1 = test_graphs
    order = g1.topological_sort()
    assert order[0] == 0
    assert order[-1] == 4
