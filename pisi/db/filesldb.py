# -*- coding: utf-8 -*-
#
# Copyright (C) 2014, Marcin Bojara
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os
import re
try:
    import plyvel
    PLYVEL_AVAILABLE = True
except ImportError:
    PLYVEL_AVAILABLE = False
    plyvel = None
import hashlib

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

import pisi
import pisi.context as ctx

class FilesLDB():
    def __init__(self):
        if not PLYVEL_AVAILABLE:
            raise ImportError("plyvel is required for FilesLDB functionality")
        self.files_ldb_path = os.path.join(ctx.config.info_dir(), ctx.const.files_ldb)
        self.filesdb = plyvel.DB(self.files_ldb_path, create_if_missing=True)
        # .ldb uzantılı dosyaların varlığını kontrol et
        if not [f for f in os.listdir(self.files_ldb_path) if f.endswith('.ldb')]:
            if ctx.comar: 
                self.destroy()
            self.create_filesdb()

    def __del__(self):
        self.close()

    def create_filesdb(self):
        ctx.ui.info(pisi.util.colorize(_('Creating files database...'), 'green'))
        installdb = pisi.db.installdb.InstallDB()
        for pkg in installdb.list_installed():
            ctx.ui.info(_('Adding \'%s\' to db... ') % pkg, noln=True)
            files = installdb.get_files(pkg)
            self.add_files(pkg, files)
            ctx.ui.info(_('OK.'))
        ctx.ui.info(pisi.util.colorize(_('done.'), 'green'))

    def get_file(self, path):
        # Path için MD5 hash hesaplayarak dosyayı al
        pkg = self.filesdb.get(hashlib.md5(path.encode('utf-8')).digest())
        return pkg, path

    def search_file(self, term):
        pkg, path = self.get_file(term)
        if pkg:
            return [(pkg.decode('utf-8'), [path])]  # Python 3'te bytes türünden string'e çevirme

        installdb = pisi.db.installdb.InstallDB()
        found = []
        for pkg in installdb.list_installed():
            files_xml_path = os.path.join(installdb.package_path(pkg), ctx.const.files_xml)
            with open(files_xml_path, 'r', encoding='utf-8') as files_xml:  # Dosya açarken kodlama belirtildi
                paths = re.compile('<Path>(.*?%s.*?)</Path>' % re.escape(term), re.I).findall(files_xml.read())
            if paths:
                found.append((pkg, paths))
        return found

    def add_files(self, pkg, files):
        for f in files.list:
            self.filesdb.put(hashlib.md5(f.path.encode('utf-8')).digest(), pkg.encode('utf-8'))  # Python 3'te string'leri encode et

    def remove_files(self, files):
        for f in files:
            self.filesdb.delete(hashlib.md5(f.path.encode('utf-8')).digest())

    def destroy(self):
        ctx.ui.info(pisi.util.colorize(_('Cleaning files database folder... '), 'green'), noln=True)
        for f in os.listdir(self.files_ldb_path):
            os.unlink(os.path.join(self.files_ldb_path, f))
        ctx.ui.info(pisi.util.colorize(_('done.'), 'green'))

    def close(self):
        if not self.filesdb.closed: 
            self.filesdb.close()
