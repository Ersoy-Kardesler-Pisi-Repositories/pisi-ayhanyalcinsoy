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

import os
import shutil
import pytest
import tempfile

import pisi
import pisi.context as ctx


@pytest.fixture(scope="session", autouse=True)
def setup_pisi_environment():
    """Setup PiSi environment for all tests."""
    options = pisi.config.Options()
    options.destdir = "repos/tmp"
    pisi.api.set_options(options)
    pisi.api.set_comar(False)

    ctx.config.values.general.distribution = "Pardus"
    ctx.config.values.general.distribution_release = "2007"

    # Setup test repositories if they don't exist
    if not pisi.api.list_repos():
        pisi.api.add_repo("pardus-2007", "repos/pardus-2007-bin/pisi-index.xml")
        pisi.api.add_repo("contrib-2007", "repos/contrib-2007-bin/pisi-index.xml")
        pisi.api.add_repo("pardus-2007-src", "repos/pardus-2007/pisi-index.xml")
        pisi.api.update_repo("pardus-2007")
        pisi.api.update_repo("contrib-2007")
        pisi.api.update_repo("pardus-2007-src")

    yield

    # Cleanup after all tests
    if os.path.exists("repos/tmp"):
        shutil.rmtree("repos/tmp")


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def clean_repos():
    """Clean and recreate test repositories."""
    if os.path.exists("repos/tmp"):
        shutil.rmtree("repos/tmp")

    # Recreate test repositories
    os.system("cd repos && python createrepos.py")

    yield

    # Cleanup
    if os.path.exists("repos/tmp"):
        shutil.rmtree("repos/tmp")
