# -*- coding:utf-8 -*-
#
# Copyright (C) 2005 - 2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext  # Python 3'te ugettext yerine gettext kullanılır

import pisi.cli.command as command
import pisi.api

class RemoveRepo(command.Command):
    __doc__ = _("""Remove repositories

Usage: remove-repo <repo1> <repo2> ... <repon>

Remove all repository information from the system.
""")
    __metaclass__ = command.autocommand

    def __init__(self, args):
        super().__init__(args)  # Python 3'te super() kullanımı

    name = ("remove-repo", "rr")

    def run(self):
        if len(self.args) >= 1:
            self.init()
            for repo in self.args:
                pisi.api.remove_repo(repo)
        else:
            self.help()
