# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2011, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

"""
 Specfile module is our handler for PSPEC files. PSPEC (PiSi SPEC)
 files are specification files for PiSi source packages. This module
 provides read and write routines for PSPEC files.
"""

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

# standard python modules
import os.path
import piksemel

# pisi modules
import pisi.pxml.xmlfile as xmlfile
import pisi.pxml.autoxml as autoxml
import pisi.context as ctx
import pisi.dependency
import pisi.replace
import pisi.conflict
import pisi.component as component
import pisi.group as group
import pisi.util as util
import pisi.db

class Error(pisi.Error):
    pass

__metaclass__ = autoxml.autoxml

class Packager:

    t_Name = [autoxml.Text, autoxml.mandatory]
    t_Email = [autoxml.String, autoxml.mandatory]

    def __str__(self):
        s = f"{self.name} <{self.email}>"
        return s


class AdditionalFile:

    s_Filename = [autoxml.String, autoxml.mandatory]
    a_target = [autoxml.String, autoxml.mandatory]
    a_permission = [autoxml.String, autoxml.optional]
    a_owner = [autoxml.String, autoxml.optional]
    a_group = [autoxml.String, autoxml.optional]

    def __str__(self):
        s = f"{self.filename} -> {self.target} "
        if self.permission:
            s += f'({self.permission})'
        return s

class Type:

    s_type = [autoxml.String, autoxml.mandatory]
    a_package = [autoxml.String, autoxml.optional]

class Action:

    # Valid actions:
    #
    # reverseDependencyUpdate
    # systemRestart
    # serviceRestart

    s_action  = [autoxml.String, autoxml.mandatory]
    a_package = [autoxml.String, autoxml.optional]
    a_target  = [autoxml.String, autoxml.optional]

    def __str__(self):
        return self.action

class Patch:

    s_Filename = [autoxml.String, autoxml.mandatory]
    a_compressionType = [autoxml.String, autoxml.optional]
    a_level = [autoxml.Integer, autoxml.optional]
    a_reverse = [autoxml.String, autoxml.optional]

    # FIXME: what's the cleanest way to give a default value for reading level?
    # def decode_hook(self, node, errs, where):
    #    if self.level is None:
    #        self.level = 0

    def __str__(self):
        s = self.filename
        if self.compressionType:
            s += f' ({self.compressionType})'
        if self.level:
            s += f' level:{self.level}'
        return s

class Update:

    a_release = [autoxml.String, autoxml.mandatory]
    # 'type' attribute is here to keep backward compatibility
    a_type = [autoxml.String, autoxml.optional]
    t_types = [[Type], autoxml.optional, "Type"]
    t_Date = [autoxml.String, autoxml.mandatory]
    t_Version = [autoxml.String, autoxml.mandatory]
    t_Comment = [autoxml.String, autoxml.optional]
    t_Name = [autoxml.Text, autoxml.optional]
    t_Email = [autoxml.String, autoxml.optional]
    t_Requires = [[Action], autoxml.optional]

    def __str__(self):
        s = self.date
        s += f", ver={self.version}"
        s += f", rel={self.release}"
        if self.type:
            s += f", type={self.type}"
        return s

class Path:

    s_Path = [autoxml.String, autoxml.mandatory]
    a_fileType =  [autoxml.String, autoxml.optional]
    a_permanent =  [autoxml.String, autoxml.optional]

    def __str__(self):
        s = self.path
        s += f", type={self.fileType}"
        return s


class ComarProvide:

    s_om = [autoxml.String, autoxml.mandatory]
    a_script = [autoxml.String, autoxml.mandatory]
    a_name = [autoxml.String, autoxml.optional]

    def __str__(self):
        # FIXME: descriptive enough?
        s = self.script
        s += f' ({self.om}{" for " + self.name if self.name else ""})'
        return s


class Archive:
    s_uri = [autoxml.String, autoxml.mandatory]
    a_type = [autoxml.String, autoxml.optional]
    a_sha1sum = [autoxml.String, autoxml.mandatory]
    a_target = [autoxml.String, autoxml.optional]
    a_name = [autoxml.String, autoxml.optional]

    def decode_hook(self, node, errs, where):
        if not self.name:
            self.name = os.path.basename(self.uri)

    def __str__(self):
        s = _('URI: %s, type: %s, sha1sum: %s') % (self.uri, self.type, self.sha1sum)
        return s

class Source:

    t_Name = [autoxml.String, autoxml.mandatory]
    t_Homepage = [autoxml.String, autoxml.optional]
    t_Packager = [Packager, autoxml.mandatory]
    t_ExcludeArch = [[autoxml.String], autoxml.optional]
    t_License = [[autoxml.String], autoxml.mandatory]
    t_IsA = [[autoxml.String], autoxml.optional]
    t_PartOf = [autoxml.String, autoxml.optional]
    t_Summary = [autoxml.LocalText, autoxml.mandatory]
    t_Description = [autoxml.LocalText, autoxml.mandatory]
    t_Icon = [autoxml.String, autoxml.optional]
    t_Archive = [[Archive], autoxml.mandatory, "Archive"]
    t_AdditionalFiles = [[AdditionalFile], autoxml.optional]
    t_BuildDependencies = [[pisi.dependency.Dependency], autoxml.optional]
    t_Patches = [[Patch], autoxml.optional]
    t_Version = [autoxml.String, autoxml.optional]
    t_Release = [autoxml.String, autoxml.optional]
    t_SourceURI = [autoxml.String, autoxml.optional]  # used in index

    def buildtimeDependencies(self):
        return self.buildDependencies

class AnyDependency:
    t_Dependencies = [[pisi.dependency.Dependency], autoxml.optional, "Dependency"]

    def __str__(self):
        return f"{{{' or '.join([str(dep) for dep in self.dependencies])}}}"

    def name(self):
        return f"{{{' or '.join([dep.package for dep in self.dependencies])}}}"

    def decode_hook(self, node, errs, where):
        self.package = self.dependencies[0].package

    def satisfied_by_dict_repo(self, dict_repo):
        for dependency in self.dependencies:
            if dependency.satisfied_by_dict_repo(dict_repo):
                return True
        return False

    def satisfied_by_any_installed_other_than(self, package):
        for dependency in self.dependencies:
            if dependency.package != package and dependency.satisfied_by_installed():
                return True
        return False

    def satisfied_by_installed(self):
        for dependency in self.dependencies:
            if dependency.satisfied_by_installed():
                return True
        return False

    def satisfied_by_repo(self):
        for dependency in self.dependencies:
            if dependency.satisfied_by_repo():
                return True
        return False

class Package:

    t_Name = [autoxml.String, autoxml.mandatory]
    t_Summary = [autoxml.LocalText, autoxml.optional]
    t_Description = [autoxml.LocalText, autoxml.optional]
    t_IsA = [[autoxml.String], autoxml.optional]
    t_PartOf = [autoxml.String, autoxml.optional]
    t_License = [[autoxml.String], autoxml.optional]
    t_Icon = [autoxml.String, autoxml.optional]
    t_BuildFlags = [[autoxml.String], autoxml.optional, "BuildFlags/Flag"]
    t_BuildType = [autoxml.String, autoxml.optional]
    t_BuildDependencies = [[pisi.dependency.Dependency], autoxml.optional]
    t_AdditionalFiles = [[AdditionalFile], autoxml.optional]
    t_Provides = [[pisi.replace.Replacement], autoxml.optional]
    t_Conflicts = [[pisi.conflict.Conflict], autoxml.optional]
    t_Requires = [[AnyDependency], autoxml.optional]
    t_Sources = [[Source], autoxml.optional]

    def buildtimeDependencies(self):
        return self.buildDependencies

    def satisfied_by_installed(self):
        for dependency in self.requires:
            if not dependency.satisfied_by_installed():
                return False
        return True

    def satisfied_by_repo(self):
        for dependency in self.requires:
            if not dependency.satisfied_by_repo():
                return False
        return True

    def __str__(self):
        return f"{self.name}"

class Specfile(xmlfile.XMLFile):

    t_Name = [autoxml.String, autoxml.mandatory]
    t_Version = [autoxml.String, autoxml.mandatory]
    t_Release = [autoxml.String, autoxml.mandatory]
    t_Sources = [[Source], autoxml.optional]
    t_Packages = [[Package], autoxml.optional]
    t_Updates = [[Update], autoxml.optional]

    def __init__(self, **kwargs):
        self.__super.__init__(**kwargs)

    def find_package(self, package):
        for pkg in self.packages:
            if pkg.name == package:
                return pkg
        return None

    def find_source(self, name):
        for src in self.sources:
            if src.name == name:
                return src
        return None

    def has_packages(self):
        return len(self.packages) > 0

    def has_sources(self):
        return len(self.sources) > 0

    def last_update(self):
        if not self.updates:
            return None
        return self.updates[-1]

    def last_version(self):
        return self.version

    def last_release(self):
        return self.release

    def source(self):
        if self.has_sources():
            return self.sources[0]
        return None
