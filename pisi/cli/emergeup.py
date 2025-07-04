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

import optparse

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext  # Python 3'te ugettext yerine gettext kullanılır

import pisi.cli.command as command
import pisi.cli.build as build
import pisi.context as ctx
import pisi.api

class EmergeUp(build.Build, metaclass=command.autocommand):
    __doc__ = _("""Build and install PiSi source packages from repository

Usage: emergeup ...

You should give the name of a source package to be
downloaded from a repository containing sources.

You can also give the name of a component.
""")

    def __init__(self, args):
        super(EmergeUp, self).__init__(args)
        self.comar = True

    name = ("emergeup", "emup")

    def options(self):
        group = optparse.OptionGroup(self.parser, _("emergeup options"))
        super(EmergeUp, self).options()  # Super ile options çağrısı
        group.add_option("-c", "--component", action="store",
                         default=None, help=_("Emerge available packages under given component"))
        group.add_option("--ignore-file-conflicts", action="store_true",
                         default=False, help=_("Ignore file conflicts"))
        group.add_option("--ignore-package-conflicts", action="store_true",
                         default=False, help=_("Ignore package conflicts"))
        group.add_option("--ignore-comar", action="store_true",
                         default=False, help=_("Bypass comar configuration agent"))
        self.parser.add_option_group(group)

    def run(self):
        self.init(database=True)

        source = pisi.db.sourcedb.SourceDB()
        imdb = pisi.db.installdb.InstallDB()

        installed_emerge_packages = imdb.list_installed_with_build_host("localhost")

        emerge_up_list = []

        for package in installed_emerge_packages:
            if source.has_spec(package):
                spec = source.get_spec(package)
                if spec.getSourceRelease() > imdb.get_version(package)[1]:
                    emerge_up_list.append(package)

        if ctx.get_option('output_dir'):
            ctx.ui.info(_('Output directory: %s') % ctx.config.options.output_dir)
        else:
            ctx.ui.info(_('Outputting binary packages in the package cache.'))
            ctx.config.options.output_dir = ctx.config.cached_packages_dir()

        repos = pisi.api.list_repos()
        pisi.api.update_repos(repos, ctx.get_option('force'))
        
        pisi.api.emerge(emerge_up_list)
