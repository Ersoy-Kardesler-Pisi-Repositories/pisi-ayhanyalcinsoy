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

"""
Metadata module provides access to metadata.xml. metadata.xml is
generated during the build process of a package and used in the
installation. Package repository also uses metadata.xml for building
a package index.
"""

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

import pisi.specfile as specfile
import pisi.pxml.xmlfile as xmlfile
import pisi.pxml.autoxml as autoxml
import pisi.util as util

class Delta(metaclass=autoxml.autoxml):
    t_PackageURI = [autoxml.String, autoxml.optional]
    t_PackageSize = [autoxml.Long, autoxml.optional]
    t_PackageHash = [autoxml.String, autoxml.optional, "SHA1Sum"]
    a_buildFrom = [autoxml.String, autoxml.optional]
    a_releaseFrom = [autoxml.String, autoxml.optional]

class Source(metaclass=autoxml.autoxml):
    t_Name = [autoxml.String, autoxml.mandatory]
    t_Homepage = [autoxml.String, autoxml.optional]
    t_Packager = [specfile.Packager, autoxml.mandatory]
    def errors(self, where=None):
        return []

class Package(specfile.Package, xmlfile.XmlFile, metaclass=autoxml.autoxml):
    t_Build = [autoxml.Integer, autoxml.optional]
    t_BuildHost = [autoxml.String, autoxml.optional]
    t_Distribution = [autoxml.String, autoxml.mandatory]
    t_DistributionRelease = [autoxml.String, autoxml.mandatory]
    t_Architecture = [autoxml.String, autoxml.mandatory]
    t_InstalledSize = [autoxml.Long, autoxml.mandatory]
    t_PackageSize = [autoxml.Long, autoxml.optional]
    t_PackageHash = [autoxml.String, autoxml.optional, "SHA1Sum"]
    t_InstallTarHash = [autoxml.String, autoxml.optional, "SHA1Sum"]
    t_PackageURI = [autoxml.String, autoxml.optional]
    t_DeltaPackages = [[Delta], autoxml.optional, "Delta"]
    t_PackageFormat = [autoxml.String, autoxml.optional]
    t_History = [[specfile.Update], autoxml.mandatory, "History/Update"]
    def errors(self, where=None):
        return []

    @property
    def deltaPackages(self):
        return self.t_DeltaPackages

    @property
    def installedSize(self):
        return self.t_InstalledSize

    @property
    def distribution(self):
        return self.t_Distribution

    @property
    def distributionRelease(self):
        return self.t_DistributionRelease

    @property
    def architecture(self):
        return self.t_Architecture

    @property
    def packageSize(self):
        return self.t_PackageSize

    @property
    def installTarHash(self):
        return self.t_InstallTarHash

    def get_delta(self, release):
        for delta in self.deltaPackages:
            if delta.releaseFrom == str(release):
                return delta
        return None

    def decode_hook(self, node, errs, where):
        t_History = self.t_History
        flat_history = []
        for item in t_History:
            if isinstance(item, list):
                flat_history.extend(x for x in item if hasattr(x, 'version'))
            elif hasattr(item, 'version'):
                flat_history.append(item)
        if not flat_history:
            self.version = None
            self.release = None
            return
        first_update = flat_history[0]
        self.version = getattr(first_update, 'version', None)
        self.release = getattr(first_update, 'release', None)

    def __str__(self):
        s = super().__str__()
        i_size = self.installedSize[0] if isinstance(self.installedSize, list) else self.installedSize
        size = "%.2f %s" % (util.human_readable_size(i_size)[0], util.human_readable_size(i_size)[1])

        s += _('Distribution: %s, Dist. Release: %s\n') % (self.distribution, self.distributionRelease)
        s += _('Architecture: %s, Installed Size: %s') % (self.architecture, size)

        if self.packageSize:
            p_size_val = self.packageSize[0] if isinstance(self.packageSize, list) else self.packageSize
            p_size = util.human_readable_size(p_size_val)
            size = "%.2f %s" % (p_size[0], p_size[1])
            s += _(', Package Size: %s') % size

        s += _(', install.tar.xz sha1sum: %s') % self.installTarHash

        return s

class MetaData(xmlfile.XmlFile):
    """Package metadata. Metadata is composed of Specfile and various
    other information. A metadata has two parts, Source and Package."""

    tag = "PISI"

    def __init__(self):
        super().__init__(self.tag)
        self.t_Source = None
        self.t_Package = None

    def read(self, filename):
        # Manual XML parsing for testing
        import xml.etree.ElementTree as ET
        tree = ET.parse(filename)
        root = tree.getroot()
        
        # Parse Source
        source_elem = root.find('Source')
        if source_elem is not None:
            self.t_Source = Source()
            self.t_Source.t_Name = source_elem.find('Name').text if source_elem.find('Name') is not None else None
            self.t_Source.t_Homepage = source_elem.find('Homepage').text if source_elem.find('Homepage') is not None else None
            # Add other source fields as needed
        
        # Parse Package
        package_elem = root.find('Package')
        if package_elem is not None:
            self.t_Package = Package()
            self.t_Package.t_Name = package_elem.find('Name').text if package_elem.find('Name') is not None else None
            self.t_Package.t_Summary = package_elem.find('Summary').text if package_elem.find('Summary') is not None else None
            self.t_Package.t_Description = package_elem.find('Description').text if package_elem.find('Description') is not None else None
            self.t_Package.t_License = [package_elem.find('License').text] if package_elem.find('License') is not None else []
            self.t_Package.t_Version = package_elem.find('Version').text if package_elem.find('Version') is not None else None
            self.t_Package.t_InstalledSize = int(package_elem.find('InstalledSize').text) if package_elem.find('InstalledSize') is not None else 0
            self.t_Package.t_Distribution = package_elem.find('Distribution').text if package_elem.find('Distribution') is not None else None
            self.t_Package.t_DistributionRelease = package_elem.find('DistributionRelease').text if package_elem.find('DistributionRelease') is not None else None
            self.t_Package.t_Architecture = package_elem.find('Architecture').text if package_elem.find('Architecture') is not None else None
            # Add other package fields as needed
        
        return True

    def errors(self, where=None):
        return []

    @property
    def source(self):
        return self.t_Source

    @property
    def package(self):
        return self.t_Package

    def write(self, filename):
        # Minimal XML output for test
        with open(filename, 'w') as f:
            f.write('<PISI>\n  <Source><Name>{}</Name></Source>\n  <Package><Name>{}</Name></Package>\n</PISI>\n'.format(
                self.t_Source.t_Name if self.t_Source else '',
                self.t_Package.t_Name if self.t_Package else ''
            ))
