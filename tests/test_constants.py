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
import pisi.constants
import pisi.context as ctx


@pytest.mark.unit
def test_constants():
    """Test that PiSi constants are correctly defined."""
    constants = ctx.const
    const_dict = {"actions": "actions.py", "setup": "setup", "metadata": "metadata.xml"}

    for key, expected_value in const_dict.items():
        if hasattr(constants, key):
            value = getattr(constants, key)
            assert (
                value == expected_value
            ), f"Constant {key} should be {expected_value}, got {value}"
