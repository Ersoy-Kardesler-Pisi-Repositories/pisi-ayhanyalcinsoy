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
from pisi.specfile import SpecFile
from pisi import uri
from pisi.file import File


@pytest.mark.unit
def test_make_uri():
    """Test URI creation from spec file."""
    spec = SpecFile("repos/pardus-2007/system/base/curl/pspec.xml")
    url = uri.URI(spec.source.archive[0].uri)
    assert File.make_uri(url)


@pytest.mark.unit
def test_choose_method():
    """Test compression method selection."""
    compress = File("repos/contrib-2007/pisi-index.xml", File.read)
    assert File.choose_method("pisi.conf", compress)


@pytest.mark.unit
def test_decompress():
    """Test file decompression."""
    localfile = File("repos/pardus-2007/system/base/curl/pspec.xml", File.read)
    compress = File("repos/contrib-2007/pisi-index.xml", File.read)
    assert File.decompress(localfile, compress)


@pytest.mark.unit
def test_local_file():
    """Test local file reading."""
    f = File("repos/pardus-2007/system/base/curl/pspec.xml", File.read)
    r = f.readlines()
    assert len(r) > 0


@pytest.mark.integration
def test_remote_read():
    """Test remote file reading."""
    f = File(
        "http://www.pardus.org.tr/urunler/pardus-2009.2-Geronticus_eremita-surum-notlari-tr.html",
        File.read,
    )
    r = f.readlines()
    assert len(r) > 0
