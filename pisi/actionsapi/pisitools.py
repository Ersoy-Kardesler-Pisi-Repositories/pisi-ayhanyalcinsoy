#-*- coding: utf-8 -*-
#
# Copyright (C) 2005-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.

'''supports globs in sourceFile arguments'''


# Standart Python Modules
import os
import glob
import sys
import fileinput
import re
import filecmp

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

# Pisi Modules
import pisi.context as ctx
from pisi.util import join_path, remove_prefix, uncompress

# ActionsAPI Modules
import pisi.actionsapi
import pisi.actionsapi.get as get
from pisi.actionsapi.pisitoolsfunctions import *
from pisi.actionsapi.shelltools import *

from pisi.actionsapi import error

def dobin(sourceFile, destinationDirectory='/usr/bin'):
    '''insert an executable file into /bin or /usr/bin'''
    ''' example call: pisitools.dobin("bin/xloadimage", "/bin", "xload") '''
    executable_insinto(join_path(get.installDIR(), destinationDirectory), sourceFile)

def dopixmaps(sourceFile, destinationDirectory='/usr/share/pixmaps'):
    '''insert a data file into /usr/share/pixmaps'''
    ''' example call: pisitools.dopixmaps("/usr/share/pixmaps/firefox", "firefox") '''
    readable_insinto(join_path(get.installDIR(), destinationDirectory), sourceFile)

def dodir(destinationDirectory):
    '''creates a directory tree'''
    makedirs(join_path(get.installDIR(), destinationDirectory))

def dodoc(*sourceFiles, **kw):
    '''inserts the files in the list of files into /usr/share/doc/PACKAGE'''
    destDir = kw.get("destDir", get.srcNAME())
    readable_insinto(join_path(get.installDIR(), get.docDIR(), destDir), *sourceFiles)

def doexe(sourceFile, destinationDirectory):
    '''insert an executable file into destination directory'''

    ''' example call: pisitools.doexe("kde-3.4.sh", "/etc/X11/Sessions")'''
    executable_insinto(join_path(get.installDIR(), destinationDirectory), sourceFile)

def dohtml(*sourceFiles, **kw):
    '''inserts the files in the list of files into /usr/share/doc/PACKAGE/html'''

    ''' example call: pisitools.dohtml("doc/doxygen/html/*")'''
    destDir = kw.get("destDir", get.srcNAME())
    destinationDirectory = join_path(get.installDIR(), get.docDIR(), destDir, 'html')

    if not can_access_directory(destinationDirectory):
        makedirs(destinationDirectory)

    allowed_extensions = ['.png', '.gif', '.html', '.htm', '.jpg', '.css', '.js']
    disallowed_directories = ['CVS', '.git', '.svn', '.hg']

    for sourceFile in sourceFiles:
        sourceFileGlob = glob.glob(sourceFile)
        if len(sourceFileGlob) == 0:
            raise FileError(_("No file matched pattern \"%s\"") % sourceFile)

        for source in sourceFileGlob:
            if os.path.isfile(source) and os.path.splitext(source)[1] in allowed_extensions:
                os.system('install -m0644 "%s" %s' % (source, destinationDirectory))
            if os.path.isdir(source) and os.path.basename(source) not in disallowed_directories:
                eraser = os.path.split(source)[0]
                for root, dirs, files in os.walk(source):
                    newRoot = remove_prefix(eraser, root)
                    for sourcename in files:
                        if os.path.splitext(sourcename)[1] in allowed_extensions:
                            makedirs(join_path(destinationDirectory, newRoot))
                            os.system('install -m0644 %s %s' % (join_path(root, sourcename), join_path(destinationDirectory, newRoot, sourcename)))

def doinfo(*sourceFiles):
    '''inserts the into files in the list of files into /usr/share/info'''
    readable_insinto(join_path(get.installDIR(), get.infoDIR()), *sourceFiles)

def dolib(sourceFile, destinationDirectory='/usr/lib'):
    '''insert the library into /usr/lib'''

    '''example call: pisitools.dolib("libz.a")'''
    '''example call: pisitools.dolib("libz.so")'''
    sourceFile = join_path(os.getcwd(), sourceFile)
    destinationDirectory = join_path(get.installDIR(), destinationDirectory)

    lib_insinto(sourceFile, destinationDirectory, 0o755)

def dolib_a(sourceFile, destinationDirectory='/usr/lib'):
    '''insert the static library into /usr/lib with permission 0644'''

    '''example call: pisitools.dolib_a("staticlib/libvga.a")'''
    sourceFile = join_path(os.getcwd(), sourceFile)
    destinationDirectory = join_path(get.installDIR(), destinationDirectory)

    lib_insinto(sourceFile, destinationDirectory, 0o644)

def dolib_so(sourceFile, destinationDirectory='/usr/lib'):
    '''insert the dynamic library into /usr/lib with permission 0755'''

    '''example call: pisitools.dolib_so("pppd/plugins/minconn.so")'''
    sourceFile = join_path(os.getcwd(), sourceFile)
    destinationDirectory = join_path(get.installDIR(), destinationDirectory)

    lib_insinto(sourceFile, destinationDirectory, 0o755)

def doman(*sourceFiles):
    '''inserts the man pages in the list of files into /usr/share/man/'''

    '''example call: pisitools.doman("man.1", "pardus.*")'''
    manDIR = join_path(get.installDIR(), get.manDIR())
    if not can_access_directory(manDIR):
        makedirs(manDIR)

    for sourceFile in sourceFiles:
        sourceFileGlob = glob.glob(sourceFile)
        if len(sourceFileGlob) == 0:
            raise FileError(_("No file matched pattern \"%s\"") % sourceFile)

        for source in sourceFileGlob:
            compressed = source.endswith("gz") and source
            if compressed:
                source = source[:-3]
            try:
                pageName, pageDirectory = source[:source.rindex('.')], \
                                          source[source.rindex('.')+1:]
            except ValueError:
                error(_('ActionsAPI [doman]: Wrong man page file: %s') % (source))

            manPDIR = join_path(manDIR, '/man%s' % pageDirectory)
            makedirs(manPDIR)
            if not compressed:
                os.system('install -m0644 %s %s' % (source, manPDIR))
            else:
                uncompress(compressed, targetDir=manPDIR)

def domo(sourceFile, locale, destinationFile, localeDirPrefix='/usr/share/locale'):
    '''inserts the mo files in the list of files into /usr/share/locale/LOCALE/LC_MESSAGES'''

    '''example call: pisitools.domo("po/tr.po", "tr", "pam_login.mo")'''

    os.system('msgfmt %s' % sourceFile)
    makedirs('%s%s/%s/LC_MESSAGES/' % (get.installDIR(), localeDirPrefix, locale))
    move('messages.mo', '%s%s/%s/LC_MESSAGES/%s' % (get.installDIR(), localeDirPrefix, locale, destinationFile))

def domove(sourceFile, destination, destinationFile=''):
    '''moves sourceFile/Directory into destinationFile/Directory'''

    ''' example call: pisitools.domove("/usr/bin/bash", "/bin/bash")'''
    ''' example call: pisitools.domove("/usr/bin/", "/usr/sbin")'''
    makedirs(join_path(get.installDIR(), destination))

    sourceFileGlob = glob.glob(join_path(get.installDIR(), sourceFile))
    if len(sourceFileGlob) == 0:
        raise FileError(_("No file matched pattern \"%s\". 'domove' operation failed.") % sourceFile)

    for filePath in sourceFileGlob:
        if not destinationFile:
            move(filePath, join_path(get.installDIR(), join_path(destination, os.path.basename(filePath))))
        else:
            move(filePath, join_path(get.installDIR(), join_path(destination, destinationFile)))

def rename(sourceFile, destinationFile):
    ''' renames sourceFile as destinationFile'''

    ''' example call: pisitools.rename("/usr/bin/bash", "bash.old") '''
    ''' the result of the previous example would be "/usr/bin/bash.old" '''

    baseDir = os.path.dirname(sourceFile)

    try:
        os.rename(join_path(get.installDIR(), sourceFile), join_path(get.installDIR(), baseDir, destinationFile))
    except OSError as e:
        error(_('ActionsAPI [rename]: %s: %s') % (e, sourceFile))

def dosed(sources, findPattern, replacePattern='', filePattern='', deleteLine=False, level=-1):
    '''replaces patterns in sources'''

    def get_files(path, pattern, level):
        res = []
        if path.endswith("/"): 
            path = path[:-1]
        for root, dirs, files in os.walk(path):
            currentLevel = len(root.split("/")) - len(path.split("/"))
            if level != -1 and currentLevel > level: 
                continue
            for f in files:
                if re.search(pattern, f):
                    res.append(f"{root}/{f}")
        return res

    backupExtension = ".pisi-backup"
    sourceFiles = []
    sourcesGlob = glob.glob(sources)
    
    for source in sourcesGlob:
        if os.path.isdir(source):
            sourceFiles.extend(get_files(source, filePattern, level))
        else:
            sourceFiles.append(source)

    if len(sourceFiles) == 0:
        raise FileError(_('No such file matching pattern: "%s". \'dosed\' operation failed.') % (filePattern if filePattern else sources))

    for sourceFile in sourceFiles:
        if can_access_file(sourceFile):
            backupFile = f"{sourceFile}{backupExtension}"
            for line in fileinput.input(sourceFile, inplace=True, backup=backupExtension):
                if re.search(findPattern, line):
                    line = "" if deleteLine else re.sub(findPattern, replacePattern, line)  
                sys.stdout.write(line)
            if can_access_file(backupFile):
                if filecmp.cmp(sourceFile, backupFile, shallow=False):
                    ctx.ui.warning(_('dosed method has not changed file \'%s\'.') % sourceFile)
                else: 
                    ctx.ui.info(f"{sourceFile} has been changed by dosed method.", verbose=True)
                os.unlink(backupFile)
        else:
            raise FileError(_('File does not exist or permission denied: %s') % sourceFile)

def dosbin(sourceFile, destinationDirectory='/usr/sbin'):
    '''insert an executable file into /sbin or /usr/sbin'''
    executable_insinto(join_path(get.installDIR(), destinationDirectory), sourceFile)

def dosym(sourceFile, destinationFile):
    '''creates soft link between sourceFile and destinationFile'''
    makedirs(join_path(get.installDIR(), os.path.dirname(destinationFile)))

    try:
        os.symlink(sourceFile, join_path(get.installDIR(), destinationFile))
    except OSError:
        error(_('ActionsAPI [dosym]: File already exists: %s') % (destinationFile))

def insinto(destinationDirectory, sourceFile, destinationFile='', sym=True):
    '''insert a sourceFile into destinationDirectory as a destinationFile with same uid/guid/permissions'''
    makedirs(join_path(get.installDIR(), destinationDirectory))

    if not destinationFile:
        sourceFileGlob = glob.glob(sourceFile)
        if len(sourceFileGlob) == 0:
            raise FileError(_("No file matched pattern \"%s\".") % sourceFile)

        for filePath in sourceFileGlob:
            if can_access_file(filePath):
                copy(filePath, join_path(get.installDIR(), join_path(destinationDirectory, os.path.basename(filePath))), sym)
    else:
        copy(sourceFile, join_path(get.installDIR(), join_path(destinationDirectory, destinationFile)), sym)

def newdoc(sourceFile, destinationFile):
    '''inserts a sourceFile into /usr/share/doc/PACKAGE/ directory as a destinationFile'''
    destinationDirectory = os.path.dirname(destinationFile)
    destinationFile = os.path.basename(destinationFile)
    copy(sourceFile, destinationFile)
    readable_insinto(join_path(get.installDIR(), 'usr/share/doc', get.srcNAME(), destinationDirectory), destinationFile)

def newman(sourceFile, destinationFile):
    '''inserts a sourceFile into /usr/share/man/manPREFIX/ directory as a destinationFile'''
    copy(sourceFile, destinationFile)
    doman(destinationFile)

def remove(sourceFile):
    '''removes sourceFile'''
    sourceFileGlob = glob.glob(join_path(get.installDIR(), sourceFile))
    if len(sourceFileGlob) == 0:
        raise FileError(_("No file matched pattern \"%s\". Remove operation failed.") % sourceFile)

    for filePath in sourceFileGlob:
        unlink(filePath)

def removeDir(destinationDirectory):
    '''removes destinationDirectory and its subtrees'''
    destdirGlob = glob.glob(join_path(get.installDIR(), destinationDirectory))
    if len(destdirGlob) == 0:
        raise FileError(_("No directory matched pattern \"%s\". Remove directory operation failed.") % destinationDirectory)

    for directory in destdirGlob:
        unlinkDir(directory)

class Flags:
    def __init__(self, *evars):
        self.evars = evars

    def add(self, *flags):
        for evar in self.evars:
            os.environ[evar] = " ".join(os.environ[evar].split() + [f.strip() for f in flags])            

    def remove(self, *flags):
        for evar in self.evars:
            os.environ[evar] = " ".join([v for v in os.environ[evar].split() if v not in [f.strip() for f in flags]])

    def replace(self, old_val, new_val):
        for evar in self.evars:
            os.environ[evar] = " ".join([new_val if v == old_val else v for v in os.environ[evar].split()])

    def sub(self, pattern, repl, count=0, flags=0):
        for evar in self.evars:
            os.environ[evar] = re.sub(pattern, repl, os.environ[evar], count, flags)

    def reset(self):
        for evar in self.evars:
            os.environ[evar] = ""

cflags = Flags("CFLAGS")
ldflags = Flags("LDFLAGS")
cxxflags = Flags("CXXFLAGS")
flags = Flags("CFLAGS", "CXXFLAGS")

