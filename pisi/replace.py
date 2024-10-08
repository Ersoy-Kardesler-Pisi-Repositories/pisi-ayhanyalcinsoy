# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 - 2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext  # Updated from ugettext to gettext in Python 3

import pisi.relation

class Replace(pisi.relation.Relation):
    """Replace relation"""
    
    def __str__(self):
        s = self.package
        if self.versionFrom:
            s += _(" version >= ") + self.versionFrom
        if self.versionTo:
            s += _(" version <= ") + self.versionTo
        if self.version:
            s += _(" version ") + self.version
        if self.releaseFrom:
            s += _(" release >= ") + self.releaseFrom
        if self.releaseTo:
            s += _(" release <= ") + self.releaseTo
        if self.release:
            s += _(" release ") + self.release
        return s

def installed_package_replaced(repinfo):
    """Determine if an installed package in *repository* is replaced by
    the given package."""
    return pisi.relation.installed_package_satisfies(repinfo)
