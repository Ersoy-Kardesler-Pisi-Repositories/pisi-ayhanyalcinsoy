# -*- coding:utf-8 -*-
#
# Copyright (C) 2009, TUBITAK/UEKAE
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

class EnableRepo(command.Command, metaclass=command.autocommand):
    __doc__ = _("""Enable repository

Usage: enable-repo [<repo1> <repo2> ... <repon>]

<repoi>: repository name

Disabled repositories are not taken into account in operations
""")

    def __init__(self, args):
        super(EnableRepo, self).__init__(args)
        self.repodb = pisi.db.repodb.RepoDB()

    name = ("enable-repo", "er")

    def run(self):
        self.init(database=True)

        if not self.args:
            self.help()
            return

        for repo in self.args:
            if self.repodb.has_repo(repo):
                pisi.api.set_repo_activity(repo, True)
