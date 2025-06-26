# -*- coding: utf-8 -*-
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

import os
import re
import shelve
import hashlib

import pisi
import pisi.context as ctx
import pisi.db.lazydb as lazydb

# FIXME:
# We could traverse through files.xml files of the packages to find the path and
# the package - a linear search - as some well known package managers do. But the current 
# file conflict mechanism of pisi prevents this and needs a fast has_file function. 
# So currently filesdb is the only db and we cant still get rid of rebuild-db :/

class FilesDB(lazydb.LazyDB):

    def __init__(self):
        super().__init__()
        self.initialized = False

    def init(self):
        self.filesdb = {}
        self.__check_filesdb()
        self.initialized = True

    def has_file(self, path):
        return hashlib.md5(path.encode('utf-8')).digest() in self.filesdb  # Python 3'te 'has_key' yerine 'in' kullanıldı

    def get_file(self, path):
        return self.filesdb[hashlib.md5(path.encode('utf-8')).digest()], path  # Python 3'te 'str' objeleri 'bytes' olarak kodlanmalı

    def search_file(self, term):
        if self.has_file(term):
            pkg, path = self.get_file(term)
            return [(pkg, [path])]

        installdb = pisi.db.installdb.InstallDB()
        found = []
        for pkg in installdb.list_installed():
            files_xml_path = os.path.join(installdb.package_path(pkg), ctx.const.files_xml)
            with open(files_xml_path, 'r', encoding='utf-8') as files_xml:  # Dosyayı okurken kodlamayı belirtmek için
                paths = re.compile('<Path>(.*?%s.*?)</Path>' % re.escape(term), re.I).findall(files_xml.read())
            if paths:
                found.append((pkg, paths))
        return found

    def add_files(self, pkg, files):
        self.__check_filesdb()
        for f in files.list:
            self.filesdb[hashlib.md5(f.path.encode('utf-8')).digest()] = pkg  # 'path' kodlanmalı

    def remove_files(self, files):
        for f in files:
            file_hash = hashlib.md5(f.path.encode('utf-8')).digest()
            if file_hash in self.filesdb:
                del self.filesdb[file_hash]

    def destroy(self):
        files_db_path = os.path.join(ctx.config.info_dir(), ctx.const.files_db)
        if os.path.exists(files_db_path):
            os.unlink(files_db_path)

    def close(self):
        if isinstance(self.filesdb, shelve.DbfilenameShelf):
            self.filesdb.close()

    def __check_filesdb(self):
        if isinstance(self.filesdb, shelve.DbfilenameShelf):
            return

        files_db_path = os.path.join(ctx.config.info_dir(), ctx.const.files_db)

        if not os.path.exists(files_db_path):
            flag = "n"
        elif os.access(files_db_path, os.W_OK):
            flag = "w"
        else:
            flag = "r"

        self.filesdb = shelve.open(files_db_path, flag)
