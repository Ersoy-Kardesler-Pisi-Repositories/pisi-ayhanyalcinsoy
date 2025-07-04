# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import pisi
import pisi.context as ctx

class Error(pisi.Error):
    pass

class Exception(pisi.Error):
    pass

def error(msg):
    if ctx.config.get_option('ignore_action_errors'):
        ctx.ui.error(msg)
    else:
        raise Error(msg)
