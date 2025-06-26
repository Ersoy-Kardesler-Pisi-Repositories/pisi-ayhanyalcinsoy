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
import pisi.configfile
import pisi.context as ctx


@pytest.mark.unit
def test_config_file_loading():
    """Test loading configuration files."""
    # Test that config file can be loaded
    assert ctx.config is not None


@pytest.mark.unit
def test_config_sections():
    """Test that configuration sections are properly defined."""
    # Test that general section exists
    assert hasattr(ctx.config.values, "general")

    # Test that distribution is set
    assert ctx.config.values.general.distribution == "Pardus"
    assert ctx.config.values.general.distribution_release == "2007"


@pytest.mark.unit
def test_config_defaults():
    """Test configuration default values."""
    # Test that config has expected structure
    assert ctx.config is not None
    assert hasattr(ctx.config.values, "general")
