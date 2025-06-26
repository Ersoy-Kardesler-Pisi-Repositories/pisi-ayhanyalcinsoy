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
import gettext

# gettext setup
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

# Pisi Modules
import pisi.context as ctx
from pisi.util import join_path

# ActionsAPI Modules
import pisi.actionsapi
import pisi.actionsapi.get as get
from pisi.actionsapi.shelltools import system, can_access_file, unlink

class ConfigureError(pisi.actionsapi.Error):
    def __init__(self, value=''):
        super().__init__(value)
        self.value = value
        ctx.ui.error(value)
        if can_access_file('config.log'):
            ctx.ui.error(_('Please attach the config.log to your bug report:\n%s/config.log') % os.getcwd())

class MakeError(pisi.actionsapi.Error):
    def __init__(self, value=''):
        super().__init__(value)
        self.value = value
        ctx.ui.error(value)

class InstallError(pisi.actionsapi.Error):
    def __init__(self, value=''):
        super().__init__(value)
        self.value = value
        ctx.ui.error(value)

class RunTimeError(pisi.actionsapi.Error):
    def __init__(self, value=''):
        super().__init__(value)
        self.value = value
        ctx.ui.error(value)

def configure(parameters='', installPrefix='/%s' % get.defaultprefixDIR(), sourceDir='.'):
    '''Configure source with given cmake parameters = "-DCMAKE_BUILD_TYPE -DCMAKE_CXX_FLAGS ... "'''
    if can_access_file(join_path(sourceDir, 'CMakeLists.txt')):
        args = f'cmake -DCMAKE_INSTALL_PREFIX={installPrefix} ' \
               f'-DCMAKE_C_FLAGS="{get.CFLAGS()}" ' \
               f'-DCMAKE_CXX_FLAGS="{get.CXXFLAGS()}" ' \
               f'-DCMAKE_LD_FLAGS="{get.LDFLAGS()}" ' \
               f'-DCMAKE_BUILD_TYPE=RelWithDebInfo {parameters} {sourceDir}'

        if system(args):
            raise ConfigureError(_('Configure failed.'))
    else:
        raise ConfigureError(_('No configure script found for cmake.'))

def make(parameters=''):
    '''Build source with given parameters'''
    if ctx.config.get_option("verbose") and ctx.config.get_option("debug"):
        command = f'make VERBOSE=1 {get.makeJOBS()} {parameters}'
    else:
        command = f'make {get.makeJOBS()} {parameters}'

    if system(command):
        raise MakeError(_('Make failed.'))

def fixInfoDir():
    infoDir = f'{get.installDIR()}/usr/share/info/dir'
    if can_access_file(infoDir):
        unlink(infoDir)

def install(parameters='', argument='install'):
    '''Install source into install directory with given parameters'''
    # You can't squeeze unix paths with things like 'bindir', 'datadir', etc with CMake
    # http://public.kitware.com/pipermail/cmake/2006-August/010748.html
    args = f'make DESTDIR="{get.installDIR()}" {parameters} {argument}'

    if system(args):
        raise InstallError(_('Install failed.'))
    else:
        fixInfoDir()

def rawInstall(parameters='', argument='install'):
    '''Install source into install directory with given parameters = PREFIX=%s % get.installDIR()'''
    if can_access_file('makefile') or can_access_file('Makefile') or can_access_file('GNUmakefile'):
        if system(f'make {parameters} {argument}'):
            raise InstallError(_('Install failed.'))
        else:
            fixInfoDir()
    else:
        raise InstallError(_('No Makefile found.'))
