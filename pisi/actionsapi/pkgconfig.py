# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.

# Standart Python Modules
import subprocess

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

# PiSi Modules
import pisi.context as ctx
import pisi.actionsapi

class PkgconfigError(pisi.actionsapi.Error):
    def __init__(self, value=''):
        super().__init__(value)
        self.value = value
        ctx.ui.error(value)

def getVariableForLibrary(library, variable):
    # Returns a specific variable provided in the library .pc file
    try:
        proc = subprocess.Popen(["pkg-config",
                                 f"--variable={variable}",
                                 library],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        return_code = proc.wait()
    except OSError as exception:
        if exception.errno == 2:
            raise PkgconfigError(_("pkg-config is not installed on your system."))
    else:
        if return_code == 0 and proc.stdout:
            return proc.stdout.read().strip().decode('utf-8')
        else:
            # Command failed
            raise PkgconfigError(proc.stderr.read().strip().decode('utf-8'))

def getLibraryVersion(library):
    """Returns the module version provided in the library .pc file."""
    try:
        proc = subprocess.Popen(["pkg-config",
                                 "--modversion",
                                 library],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        return_code = proc.wait()
    except OSError as exception:
        if exception.errno == 2:
            raise PkgconfigError(_("pkg-config is not installed on your system."))
    else:
        if return_code == 0 and proc.stdout:
            return proc.stdout.read().strip().decode('utf-8')
        else:
            # Command failed
            raise PkgconfigError(proc.stderr.read().strip().decode('utf-8'))

def getLibraryCFLAGS(library):
    """Returns compiler flags for compiling with this library.
    Ex: -I/usr/include/nss"""
    try:
        proc = subprocess.Popen(["pkg-config",
                                 "--cflags",
                                 library],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        return_code = proc.wait()
    except OSError as exception:
        if exception.errno == 2:
            raise PkgconfigError(_("pkg-config is not installed on your system."))
    else:
        if return_code == 0 and proc.stdout:
            return proc.stdout.read().strip().decode('utf-8')
        else:
            # Command failed
            raise PkgconfigError(proc.stderr.read().strip().decode('utf-8'))

def getLibraryLIBADD(library):
    """Returns linker flags for linking with this library.
    Ex: -lpng14"""
    try:
        proc = subprocess.Popen(["pkg-config",
                                 "--libs",
                                 library],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        return_code = proc.wait()
    except OSError as exception:
        if exception.errno == 2:
            raise PkgconfigError(_("pkg-config is not installed on your system."))
    else:
        if return_code == 0 and proc.stdout:
            return proc.stdout.read().strip().decode('utf-8')
        else:
            # Command failed
            raise PkgconfigError(proc.stderr.read().strip().decode('utf-8'))

def runManualCommand(*args):
    """Runs the given command and returns the output."""
    cmd = ["pkg-config"]
    cmd.extend(args)
    try:
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        return_code = proc.wait()
    except OSError as exception:
        if exception.errno == 2:
            raise PkgconfigError(_("pkg-config is not installed on your system."))
    else:
        if return_code == 0 and proc.stdout:
            return proc.stdout.read().strip().decode('utf-8')
        else:
            # Command failed
            raise PkgconfigError(proc.stderr.read().strip().decode('utf-8'))

def libraryExists(library):
    """Returns True if the library provides a .pc file."""
    result = None
    try:
        result = subprocess.call(["pkg-config",
                                   "--exists",
                                   library])
    except OSError as exception:
        if exception.errno == 2:
            raise PkgconfigError(_("pkg-config is not installed on your system."))
    else:
        return result == 0
