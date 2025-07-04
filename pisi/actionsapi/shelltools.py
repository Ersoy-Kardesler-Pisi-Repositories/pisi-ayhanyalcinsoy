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
import glob
import shutil
import string
import pwd
import grp

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

# Pisi Modules
import pisi.context as ctx

# ActionsAPI Modules
import pisi.actionsapi
import pisi.actionsapi.get

from pisi.actionsapi import error
from pisi.util import run_logged
from pisi.util import join_path

def can_access_file(filePath):
    '''test the existence of file'''
    return os.access(filePath, os.F_OK)

def can_access_directory(destinationDirectory):
    '''test readability, writability and executability of directory'''
    return os.access(destinationDirectory, os.R_OK | os.W_OK | os.X_OK)

def makedirs(destinationDirectory):
    '''recursive directory creation function'''
    try:
        if not os.access(destinationDirectory, os.F_OK):
            os.makedirs(destinationDirectory)
    except OSError:
        error(_('Cannot create directory %s') % destinationDirectory)

def echo(destinationFile, content):
    try:
        with open(destinationFile, 'a') as f:
            f.write('%s\n' % content)
    except IOError:
        error(_('ActionsAPI [echo]: Can\'t append to file %s.') % (destinationFile))

def chmod(filePath, mode=0o755):
    '''change the mode of filePath to the mode'''
    filePathGlob = glob.glob(filePath)
    if len(filePathGlob) == 0:
        error(_("ActionsAPI [chmod]: No file matched pattern \"%s\".") % filePath)

    for fileName in filePathGlob:
        if can_access_file(fileName):
            try:
                os.chmod(fileName, mode)
            except OSError:
                ctx.ui.error(_('ActionsAPI [chmod]: Operation not permitted: %s (mode: 0%o)') % (fileName, mode))
        else:
            ctx.ui.error(_('ActionsAPI [chmod]: File %s doesn\'t exists.') % (fileName))

def chown(filePath, uid='root', gid='root'):
    '''change the owner and group id of filePath to uid and gid'''
    if can_access_file(filePath):
        try:
            os.chown(filePath, pwd.getpwnam(uid)[2], grp.getgrnam(gid)[2])
        except OSError:
            ctx.ui.error(_('ActionsAPI [chown]: Operation not permitted: %s (uid: %s, gid: %s)') % (filePath, uid, gid))
    else:
        ctx.ui.error(_('ActionsAPI [chown]: File %s doesn\'t exists.') % filePath)

def sym(source, destination):
    '''creates symbolic link'''
    try:
        os.symlink(source, destination)
    except OSError:
        ctx.ui.error(_('ActionsAPI [sym]: Permission denied: %s to %s') % (source, destination))

def unlink(pattern):
    '''remove the file path'''
    filePathGlob = glob.glob(pattern)
    if len(filePathGlob) == 0:
        ctx.ui.error(_("No file matched pattern \"%s\". Remove operation failed.") % pattern)
        return

    for filePath in filePathGlob:
        if isFile(filePath) or isLink(filePath):
            try:
                os.unlink(filePath)
            except OSError:
                ctx.ui.error(_('ActionsAPI [unlink]: Permission denied: %s.') % (filePath))
        elif isDirectory(filePath):
            pass
        else:
            ctx.ui.error(_('ActionsAPI [unlink]: File %s doesn\'t exists.') % (filePath))

def unlinkDir(sourceDirectory):
    '''delete an entire directory tree'''
    if isDirectory(sourceDirectory) or isLink(sourceDirectory):
        try:
            shutil.rmtree(sourceDirectory)
        except OSError:
            error(_('ActionsAPI [unlinkDir]: Operation not permitted: %s') % (sourceDirectory))
    elif isFile(sourceDirectory):
        pass
    else:
        error(_('ActionsAPI [unlinkDir]: Directory %s doesn\'t exists.') % (sourceDirectory))

def move(source, destination):
    '''recursively move a "source" file or directory to "destination"'''
    sourceGlob = glob.glob(source)
    if len(sourceGlob) == 0:
        error(_("ActionsAPI [move]: No file matched pattern \"%s\".") % source)

    for filePath in sourceGlob:
        if isFile(filePath) or isLink(filePath) or isDirectory(filePath):
            try:
                shutil.move(filePath, destination)
            except OSError:
                error(_('ActionsAPI [move]: Permission denied: %s to %s') % (filePath, destination))
        else:
            error(_('ActionsAPI [move]: File %s doesn\'t exists.') % (filePath))

# FIXME: instead of passing a sym parameter, split copy and copytree into 4 different function
def copy(source, destination, sym=True):
    '''recursively copy a "source" file or directory to "destination"'''
    sourceGlob = glob.glob(source)
    if len(sourceGlob) == 0:
        error(_("ActionsAPI [copy]: No file matched pattern \"%s\".") % source)

    for filePath in sourceGlob:
        if isFile(filePath) and not isLink(filePath):
            try:
                shutil.copy(filePath, destination)
            except IOError:
                error(_('ActionsAPI [copy]: Permission denied: %s to %s') % (filePath, destination))
        elif isLink(filePath) and sym:
            if isDirectory(destination):
                os.symlink(os.readlink(filePath), join_path(destination, os.path.basename(filePath)))
            else:
                if isFile(destination):
                    os.remove(destination)
                os.symlink(os.readlink(filePath), destination)
        elif isLink(filePath) and not sym:
            if isDirectory(filePath):
                copytree(filePath, destination)
            else:
                shutil.copy(filePath, destination)
        elif isDirectory(filePath):
            copytree(filePath, destination, sym)
        else:
            error(_('ActionsAPI [copy]: File %s does not exist.') % filePath)

def copytree(source, destination, sym=True):
    '''recursively copy an entire directory tree rooted at source'''
    if isDirectory(source):
        if os.path.exists(destination):
            if isDirectory(destination):
                copytree(source, join_path(destination, os.path.basename(source.strip('/'))))
                return
            else:
                copytree(source, join_path(destination, os.path.basename(source)))
                return
        try:
            shutil.copytree(source, destination, symlinks=sym)
        except OSError as e:
            error(_('ActionsAPI [copytree] %s to %s: %s') % (source, destination, e))
    else:
        error(_('ActionsAPI [copytree]: Directory %s doesn\'t exists.') % (source))

def touch(filePath):
    '''changes the access time of the 'filePath', or creates it if it does not exist'''
    filePathGlob = glob.glob(filePath)

    if filePathGlob:
        if len(filePathGlob) == 0:
            error(_("ActionsAPI [touch]: No file matched pattern \"%s\".") % filePath)

        for f in filePathGlob:
            os.utime(f, None)
    else:
        try:
            with open(filePath, 'w'):
                pass
        except IOError:
            error(_('ActionsAPI [touch]: Permission denied: %s') % (filePath))

def cd(directoryName=''):
    '''change directory'''
    current = os.getcwd()
    if directoryName:
        os.chdir(directoryName)
    else:
        os.chdir(os.path.dirname(current))

def ls(source):
    '''listdir'''
    if os.path.isdir(source):
        return os.listdir(source)
    else:
        return glob.glob(source)

def export(key, value):
    '''export environ variable'''
    os.environ[key] = value

def isLink(filePath):
    '''return True if filePath refers to a symbolic link'''
    return os.path.islink(filePath)

def isFile(filePath):
    '''return True if filePath is an existing regular file'''
    return os.path.isfile(filePath)

def isDirectory(filePath):
    '''Return True if filePath is an existing directory'''
    return os.path.isdir(filePath)

def isEmpty(filePath):
    '''Return True if filePath is an empty file'''
    return os.path.getsize(filePath) == 0

def realPath(filePath):
    '''return the canonical path of the specified filename, eliminating any symbolic links encountered in the path'''
    return os.path.realpath(filePath)

def baseName(filePath):
    '''return the base name of pathname filePath'''
    return os.path.basename(filePath)

def dirName(filePath):
    '''return the directory name of pathname path'''
    return os.path.dirname(filePath)

def system(command):
    command = ' '.join(command.split())
    retValue = run_logged(command)

    # if return value is different than 0, it means error, raise exception
    if retValue != 0:
        error(_("Command \"%s\" failed, return value was %d.") % (command, retValue))

    return retValue
