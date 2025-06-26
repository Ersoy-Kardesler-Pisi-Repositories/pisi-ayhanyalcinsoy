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

# Standart Python Modules
import os
import sys
import gettext

__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

# PiSi Modules
import pisi.actionsapi
import pisi.context as ctx

# ActionsAPI Modules
import pisi.actionsapi.variables

class BinutilsError(pisi.actionsapi.Error):
    def __init__(self, value=''):
        pisi.actionsapi.Error.__init__(self, value)
        self.value = value
        ctx.ui.error(value)

# Globals
env = pisi.actionsapi.variables.glb.env
dirs = pisi.actionsapi.variables.glb.dirs
generals = pisi.actionsapi.variables.glb.generals

def curDIR():
    '''Returns current work directory's path.'''
    return os.getcwd()

def curKERNEL():
    '''Returns currently running kernel's version.'''
    return os.uname()[2]

def curPYTHON():
    '''Returns currently used python's version.'''
    (a, b, c, x, y) = sys.version_info
    return 'python{}.{},'.format(a, b)

def curPERL():
    '''Returns currently used perl's version.'''
    perl_path = '/usr/bin/perl'
    if os.path.exists(perl_path):
        return os.path.realpath(perl_path).split('perl')[1]
    return None

def ENV(environ):
    '''Returns any given environment variable.'''
    return os.environ.get(environ)

# PİSİ Related Functions

def pkgDIR():
    '''Returns the path of binary packages.'''
    '''Default: /var/cache/pisi/packages'''
    return env.pkg_dir

def workDIR():
    return env.work_dir

def installDIR():
    '''Returns the path of binary packages.'''
    return env.install_dir

# Pardus Related Functions

def lsbINFO():
    """Returns a dictionary filled through /etc/lsb-release."""
    try:
        with open("/etc/lsb-release", "r") as f:
            return {l.split("=")[0]: l.split("=")[1].strip("'\"") for l in f.read().strip().split("\n") if "=" in l}
    except FileNotFoundError:
        return {}

# PSPEC Related Functions

def srcNAME():
    return env.src_name

def srcVERSION():
    return env.src_version

def srcRELEASE():
    return env.src_release

def srcTAG():
    return '{}-{}-{}'.format(env.src_name, env.src_version, env.src_release)

def srcDIR():
    return '{}-{}'.format(env.src_name, env.src_version)

# Build Related Functions

def ARCH():
    return generals.architecture

def HOST():
    return env.host

def CHOST():
    # FIXME: Currently behaves the same as HOST,
    # but will be used for cross-compiling when pisi is ready...
    return env.host

def CFLAGS():
    return env.cflags

def CXXFLAGS():
    return env.cxxflags

def LDFLAGS():
    return env.ldflags

def makeJOBS():
    return env.jobs

def buildTYPE():
    '''Returns the current build type.'''
    return env.build_type

# Directory Related Functions

def docDIR():
    return dirs.doc

def sbinDIR():
    return dirs.sbin

def infoDIR():
    return dirs.info

def manDIR():
    return dirs.man

def dataDIR():
    return dirs.data

def confDIR():
    return dirs.conf

def localstateDIR():
    return dirs.localstate

def libexecDIR():
    return dirs.libexec

def defaultprefixDIR():
    return dirs.defaultprefix

def emul32prefixDIR():
    return dirs.emul32prefix

def kdeDIR():
    return dirs.kde

def qtDIR():
    return dirs.qt

# Binutils Variables

def existBinary(bin):
    '''Determine if path has binary.'''
    path = os.environ['PATH'].split(':')
    for directory in path:
        if os.path.exists(os.path.join(directory, bin)):
            return True
    return False

def getBinutilsInfo(util):
    cross_build_name = '{}-{}'.format(HOST(), util)
    if not existBinary(cross_build_name):
        if not existBinary(util):
            raise BinutilsError(_('Util {} cannot be found').format(util))
        else:
            ctx.ui.debug(_('Warning: {} does not exist, using plain name {}').format(cross_build_name, util))
            return util
    else:
        return cross_build_name

def AR():
    return getBinutilsInfo('ar')

def AS():
    return getBinutilsInfo('as')

def CC():
    return getBinutilsInfo('gcc')

def CXX():
    return getBinutilsInfo('g++')

def LD():
    return getBinutilsInfo('ld')

def NM():
    return getBinutilsInfo('nm')

def RANLIB():
    return getBinutilsInfo('ranlib')

def F77():
    return getBinutilsInfo('g77')

def GCJ():
    return getBinutilsInfo('gcj')
