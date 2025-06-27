# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os
import pickle  # Updated from cPickle to pickle
import time
import pisi.context as ctx
import pisi.util as util

import string

# lower borks for international locales. What we want is ascii lower.
lower_map = str.maketrans(string.ascii_uppercase, string.ascii_lowercase)

class Singleton(object):
    _the_instances = {}

    def __new__(cls):
        if cls.__name__ not in Singleton._the_instances:
            instance = super(Singleton, cls).__new__(cls)
            # Ensure initialized is set before any __getattr__ calls
            if not hasattr(instance, "initialized"):
                instance.initialized = False
            Singleton._the_instances[cls.__name__] = instance
        return Singleton._the_instances[cls.__name__]

    def _instance(self):
        return self._the_instances[type(self).__name__]

    def _delete(self):
        # FIXME: After invalidate, previously initialized db object becomes stale
        del self._the_instances[type(self).__name__]

class LazyDB(Singleton):

    cache_version = "3.0.0"

    def __init__(self, cacheable=False, cachedir=None):
        self.initialized = False  # Always set directly
        self.cacheable = cacheable
        self.cachedir = cachedir

    def is_initialized(self):
        return self.initialized

    def __cache_file(self):
        return util.join_path(ctx.config.cache_root_dir(), f"{self.__class__.__name__.translate(lower_map)}.cache")

    def __cache_version_file(self):
        return f"{self.__cache_file()}.version"

    def __cache_file_version(self):
        try:
            with open(self.__cache_version_file()) as f:
                return f.read().strip()
        except IOError:
            return "2.2"

    def cache_save(self):
        if os.access(ctx.config.cache_root_dir(), os.W_OK) and self.cacheable:
            with open(self.__cache_version_file(), "w") as f:
                f.write(LazyDB.cache_version)
                f.flush()
                os.fsync(f.fileno())
            with open(self.__cache_file(), 'wb') as f:
                pickle.dump(self._instance().__dict__, f, protocol=pickle.HIGHEST_PROTOCOL)

    def cache_valid(self):
        if not self.cachedir:
            return True
        if not os.path.exists(self.cachedir):
            return False
        if self.__cache_file_version() != LazyDB.cache_version:
            return False

        cache_modified = os.stat(self.__cache_file()).st_mtime
        cache_dir_modified = os.stat(self.cachedir).st_mtime
        return cache_modified > cache_dir_modified

    def cache_load(self):
        if os.path.exists(self.__cache_file()) and self.cache_valid():
            try:
                with open(self.__cache_file(), 'rb') as f:
                    self._instance().__dict__ = pickle.load(f)
                return True
            except (pickle.UnpicklingError, EOFError):
                if os.access(ctx.config.cache_root_dir(), os.W_OK):
                    os.unlink(self.__cache_file())
                return False
        return False

    def cache_flush(self):
        if os.path.exists(self.__cache_file()):
            os.unlink(self.__cache_file())

    def invalidate(self):
        self._delete()

    def cache_regenerate(self):
        try:
            self.this_attr_does_not_exist()
        except AttributeError:
            pass

    def __init(self):
        if not self.cache_load():
            self.init()

    def __getattr__(self, attr):
        if attr != "__setstate__" and ('initialized' not in self.__dict__ or not self.__dict__['initialized']):
            start = time.time()
            self.__init()
            end = time.time()
            ctx.ui.debug(f"{self.__class__.__name__} initialized in {end - start:.4f} seconds.")
            self.initialized = True

        if attr not in self.__dict__:
            raise AttributeError(attr)

        return self.__dict__[attr]
