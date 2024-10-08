# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.

class AnotherInstanceError(Exception):
    """Raised when an attempt is made to start another instance of a program that should be singleton."""
    pass

class PrivilegeError(Exception):
    """Raised when an operation requires higher privileges than those available to the current user."""
    pass
