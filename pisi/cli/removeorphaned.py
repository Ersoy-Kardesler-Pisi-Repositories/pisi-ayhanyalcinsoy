# -*- coding:utf-8 -*-
#
# Copyright (C) 2014, marcin.bojara (at) gmail.com
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import optparse

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext  # Python 3'te ugettext yerine gettext kullanılır

import pisi.cli.command as command
import pisi.context as ctx
import pisi.api
import pisi.db

class RemoveOrphaned(command.PackageOp, metaclass=command.autocommand):
    __doc__ = _("""Remove orphaned packages

Usage: remove-orphaned

Remove all orphaned packages from the system.
""")

    def __init__(self, args):
        super().__init__(args)  # Python 3'te super() kullanımı
        self.installdb = pisi.db.installdb.InstallDB()

    name = ("remove-orphaned", "ro")

    def options(self):
        group = optparse.OptionGroup(self.parser, _("remove-orphaned options"))

        super().options(group)  # Python 3'te super() kullanımı
        group.add_option("-x", "--exclude", action="append",
                         default=None, help=_("When removing orphaned, ignore packages and components whose basenames match pattern."))

        self.parser.add_option_group(group)

    def run(self):
        self.init(database=True, write=False)
        orphaned = self.installdb.get_orphaned()
        if ctx.get_option('exclude'):
            orphaned = pisi.blacklist.exclude(orphaned, ctx.get_option('exclude')) 

        pisi.api.remove(orphaned)
