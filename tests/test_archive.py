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
import pisi
from pisi import util
from pisi import uri
from pisi import archive
from pisi import sourcearchive
from pisi import fetcher
from pisi.specfile import SpecFile
from os.path import join, exists


@pytest.mark.integration
def test_tar_unpack():
    """Test unpacking tar archives."""
    spec = SpecFile("repos/pardus-2007/system/base/curl/pspec.xml")
    target_dir = "/tmp/tests"
    archives = sourcearchive.SourceArchives(spec)
    archives.unpack(target_dir)

    for archive_obj in spec.source.archive:
        assert archive_obj.type == "targz"


@pytest.mark.integration
def test_unpack_tar_cond():
    """Test conditional tar unpacking."""
    spec = SpecFile("repos/pardus-2007/system/base/curl/pspec.xml")
    target_dir = "/tmp"
    archives = sourcearchive.SourceArchives(spec)

    for archive_obj in spec.source.archive:
        url = uri.URI(archive_obj.uri)
        file_path = join(pisi.context.config.archives_dir(), url.filename())
        if util.sha1_file(file_path) != archive_obj.sha1sum:
            fetch = fetcher.Fetcher(archive_obj.uri, target_dir)
            fetch.fetch()
        assert archive_obj.type == "targz"


@pytest.mark.integration
def test_zip_unpack():
    """Test unpacking zip archives."""
    spec = SpecFile("repos/pardus-2007/system/base/openssl/pspec.xml")
    target_dir = "/tmp/tests"
    archives = sourcearchive.SourceArchives(spec)
    archives.fetch()
    archives.unpack(target_dir)
    assert not exists(target_dir + "/openssl")


@pytest.mark.integration
def test_make_zip():
    """Test creating zip archives."""
    spec = SpecFile("repos/pardus-2007/system/base/openssl/pspec.xml")
    target_dir = "/tmp/tests"
    archives = sourcearchive.SourceArchives(spec)
    archives.fetch(interactive=False)
    archives.unpack(target_dir, clean_dir=True)
    del archives

    new_dir = target_dir + "/newZip"
    zip_archive = archive.ArchiveZip(new_dir, "zip", "w")
    source_dir = "/tmp/pisi-root"
    zip_archive.add_to_archive(source_dir)
    zip_archive.close()
