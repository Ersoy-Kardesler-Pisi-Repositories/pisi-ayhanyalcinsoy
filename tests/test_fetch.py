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
import base64
import pisi.context as ctx
import pisi.api
from pisi.specfile import SpecFile
from pisi.fetcher import Fetcher
from pisi import util
from pisi import uri


@pytest.fixture
def fetch_setup():
    """Setup for fetch tests."""
    spec = SpecFile()
    spec.read("repos/pardus-2007/system/base/curl/pspec.xml")
    url = uri.URI(spec.source.archive[0].uri)
    url.set_auth_info(("user", "pass"))
    destpath = ctx.config.archives_dir()
    fetch = Fetcher(url, destpath)
    return {"spec": spec, "url": url, "destpath": destpath, "fetch": fetch}


@pytest.mark.integration
def test_fetch(fetch_setup):
    """Test file fetching."""
    fetch_setup["fetch"].fetch()
    fetched_file = os.path.join(fetch_setup["destpath"], fetch_setup["url"].filename())
    if os.access(fetched_file, os.R_OK):
        assert (
            util.sha1_file(fetched_file)
            == fetch_setup["spec"].source.archive[0].sha1sum
        )
    os.remove(fetched_file)


@pytest.mark.unit
def test_fetcher_functions(fetch_setup):
    """Test fetcher utility functions."""
    enc = base64.encodestring("%s:%s" % fetch_setup["url"].auth_info())
    assert fetch_setup["fetch"]._get_http_headers() == (
        (
            "Authorization",
            "Basic %s" % enc,
        )
    )
    assert not fetch_setup["fetch"]._get_ftp_headers()
