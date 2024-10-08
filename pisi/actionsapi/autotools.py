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
_ = __trans.ugettext

# Pisi Modules
import pisi.context as ctx

# ActionsAPI Modules
import pisi.actionsapi
import pisi.actionsapi.get as get
from pisi.actionsapi.shelltools import system, can_access_file, unlink, isDirectory, ls
from pisi.actionsapi.libtools import gnuconfig_update
from pisi.actionsapi.pisitools import dosed, removeDir

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

def configure(parameters=''):
    '''Configure source with given parameters = "--with-nls --with-libusb --with-something-useful"'''

    if can_access_file('configure'):
        gnuconfig_update()

        prefix = get.emul32prefixDIR() if get.buildTYPE() == "emul32" else get.defaultprefixDIR()
        args = f'./configure --prefix=/{prefix} --build={get.HOST()} --mandir=/{get.manDIR()} ' \
               f'--infodir=/{get.infoDIR()} --datadir=/{get.dataDIR()} ' \
               f'--sysconfdir=/{get.confDIR()} --localstatedir=/{get.localstateDIR()} ' \
               f'--libexecdir=/{get.libexecDIR()} ' \
               f'{"--libdir=/usr/lib32 " if get.buildTYPE() == "emul32" else ""}{parameters}'

        if system(args):
            raise ConfigureError(_('Configure failed.'))
    else:
        raise ConfigureError(_('No configure script found.'))

def rawConfigure(parameters=''):
    '''Configure source with given parameters = "--prefix=/usr --libdir=/usr/lib --with-nls"'''
    if can_access_file('configure'):
        gnuconfig_update()

        if system(f'./configure {parameters}'):
            raise ConfigureError(_('Configure failed.'))
    else:
        raise ConfigureError(_('No configure script found.'))

def compile(parameters=''):
    system(f'{get.CC()} {get.CFLAGS()} {parameters}')

def make(parameters=''):
    '''Make source with given parameters = "all" || "doc" etc.'''
    if system(f'make {get.makeJOBS()} {parameters}'):
        raise MakeError(_('Make failed.'))

def fixInfoDir():
    infoDir = f'{get.installDIR()}/usr/share/info/dir'
    if can_access_file(infoDir):
        unlink(infoDir)

def fixpc():
    '''Fix .pc files in installDIR()/usr/lib32/pkgconfig'''
    path = f"{get.installDIR()}/usr/lib32/pkgconfig"
    if isDirectory(path):
        for f in ls(f"{path}/*.pc"):
            dosed(f, get.emul32prefixDIR(), get.defaultprefixDIR())

def install(parameters='', argument='install'):
    '''Install source into install directory with given parameters'''
    args = f'make prefix={get.installDIR()}/{get.defaultprefixDIR()} ' \
           f'datadir={get.installDIR()}/{get.dataDIR()} ' \
           f'infodir={get.installDIR()}/{get.infoDIR()} ' \
           f'localstatedir={get.installDIR()}/{get.localstateDIR()} ' \
           f'mandir={get.installDIR()}/{get.manDIR()} ' \
           f'sysconfdir={get.installDIR()}/{get.confDIR()} ' \
           f'{parameters} {argument}'

    if system(args):
        raise InstallError(_('Install failed.'))
    else:
        fixInfoDir()

    if get.buildTYPE() == "emul32":
        fixpc()
        if isDirectory(f"{get.installDIR()}/emul32"):
            removeDir("/emul32")

def rawInstall(parameters='', argument='install'):
    '''Install source into install directory with given parameters = PREFIX=%s % get.installDIR()'''
    if system(f'make {parameters} {argument}'):
        raise InstallError(_('Install failed.'))
    else:
        fixInfoDir()

    if get.buildTYPE() == "emul32":
        fixpc()
        if isDirectory(f"{get.installDIR()}/emul32"):
            removeDir("/emul32")

def aclocal(parameters=''):
    '''Generates an aclocal.m4 based on the contents of configure.in.'''
    if system(f'aclocal {parameters}'):
        raise RunTimeError(_('Running aclocal failed.'))

def autoconf(parameters=''):
    '''Generates a configure script'''
    if system(f'autoconf {parameters}'):
        raise RunTimeError(_('Running autoconf failed.'))

def autoreconf(parameters=''):
    '''Re-generates a configure script'''
    if system(f'autoreconf {parameters}'):
        raise RunTimeError(_('Running autoreconf failed.'))

def automake(parameters=''):
    '''Generates a makefile'''
    if system(f'automake {parameters}'):
        raise RunTimeError(_('Running automake failed.'))

def autoheader(parameters=''):
    '''Generates templates for configure'''
    if system(f'autoheader {parameters}'):
        raise RunTimeError(_('Running autoheader failed.'))
