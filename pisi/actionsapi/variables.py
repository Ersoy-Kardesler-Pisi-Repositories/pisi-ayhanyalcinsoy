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

# Standard Python Modules
import os

# Pisi-Core Modules
import pisi.context as ctx


def export_flags() -> None:
    """Set general flags used in actions API."""
    # First, reset environment
    os.environ.clear()
    os.environ.update(ctx.config.environ)

    # Build systems depend on these environment variables.
    values = ctx.config.values
    os.environ.update({
        'HOST': values.build.host,
        'CFLAGS': values.build.cflags,
        'CXXFLAGS': values.build.cxxflags,
        'LDFLAGS': values.build.ldflags,
        'USER_LDFLAGS': values.build.ldflags,
        'JOBS': values.build.jobs,
        'CC': f"{values.build.host}-gcc",
        'CXX': f"{values.build.host}-g++"
    })


class Env:
    """General environment variables used in actions API."""
    
    def __init__(self):
        export_flags()
        self.__vars = {
            'pkg_dir': 'PKG_DIR',
            'work_dir': 'WORK_DIR',
            'install_dir': 'INSTALL_DIR',
            'build_type': 'PISI_BUILD_TYPE',
            'src_name': 'SRC_NAME',
            'src_version': 'SRC_VERSION',
            'src_release': 'SRC_RELEASE',
            'host': 'HOST',
            'cflags': 'CFLAGS',
            'cxxflags': 'CXXFLAGS',
            'ldflags': 'LDFLAGS',
            'jobs': 'JOBS'
        }

    def __getattr__(self, attr: str) -> str:
        """Get environment variable by attribute name."""
        return os.getenv(self.__vars.get(attr))


class Dirs:
    """General directories used in actions API."""
    
    def __init__(self):
        self.values = ctx.config.values
        self.doc = 'usr/share/doc'
        self.sbin = 'usr/sbin'
        self.man = 'usr/share/man'
        self.info = 'usr/share/info'
        self.data = 'usr/share'
        self.conf = 'etc'
        self.localstate = 'var'
        self.libexec = 'usr/libexec'
        self.defaultprefix = 'usr'
        self.emul32prefix = 'emul32'
        self.kde = self.values.dirs.kde_dir
        self.qt = self.values.dirs.qt_dir


class Generals:
    """General information from /etc/pisi/pisi.conf."""
    
    def __init__(self):
        self.values = ctx.config.values
        self.architecture = self.values.general.architecture
        self.distribution = self.values.general.distribution
        self.distribution_release = self.values.general.distribution_release


# Global variable for context
glb = None


def init_variables() -> None:
    """Initialize global variables."""
    global glb
    ctx.env = Env()
    ctx.dirs = Dirs()
    ctx.generals = Generals()
    glb = ctx
