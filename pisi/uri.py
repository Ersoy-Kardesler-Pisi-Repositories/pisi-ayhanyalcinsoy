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

"""Simplifies working with URLs, purl module provides common URL
parsing and processing"""

import urllib.parse as urlparse
import os.path
import gettext

__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext  # Değişiklik yapıldı, ugettext yerine gettext kullanıldı.

class URI:
    """URI class provides a URL parser and simplifies working with
    URLs."""

    def __init__(self, uri=None):
        if uri:
            self.set_uri(str(uri))
        else:
            self.__scheme = None
            self.__location = None
            self.__path = None
            self.__filename = None
            self.__params = None
            self.__query = None
            self.__fragment = None
            self.__uri = None

        self.__authinfo = None

    def get_uri(self):
        return self.__uri if self.__uri else None

    def set_uri(self, uri):
        # (scheme, location, path, params, query, fragment)
        uri = str(uri)
        u = urlparse.urlparse(uri, "file")
        self.__scheme = u.scheme
        self.__location = u.netloc
        self.__path = u.path
        self.__filename = os.path.basename(self.__path)
        self.__params = u.params
        self.__query = u.query
        self.__fragment = u.fragment

        self.__uri = uri

    def is_local_file(self):
        return self.scheme() == "file"

    def is_remote_file(self):
        return not self.is_local_file()

    def is_absolute_path(self):
        return os.path.isabs(self.__path)

    def is_relative_path(self):
        return not self.is_absolute_path()

    def set_auth_info(self, auth_tuple):
        if not isinstance(auth_tuple, tuple):
            raise Exception(_("set_auth_info needs a tuple (user, pass)"))
        self.__authinfo = auth_tuple

    def auth_info(self):
        return self.__authinfo

    def scheme(self):
        return self.__scheme

    def location(self):
        return self.__location

    def path(self):
        return self.__path

    def filename(self):
        return self.__filename

    def params(self):
        return self.__params

    def query(self):
        return self.__query

    def fragment(self):
        return self.__fragment

    def __str__(self):
        return self.get_uri()

    uri = property(get_uri, set_uri)
