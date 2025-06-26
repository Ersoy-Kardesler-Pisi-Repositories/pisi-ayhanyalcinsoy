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
#
# installation database
#

import os
import re
import gettext
import time
import xml.etree.ElementTree as ET
import pisi
import pisi.context as ctx
import pisi.dependency
import pisi.files
import pisi.util
import pisi.db.lazydb as lazydb

__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext


class InstallDBError(pisi.Error):
    pass


class InstallInfo:
    state_map = {'i': _('installed'), 'ip': _('installed-pending')}

    def __init__(self, state: str, version: str, release: str, distribution: str, install_time: float):
        self.state = state
        self.version = version
        self.release = release
        self.distribution = distribution
        self.time = install_time

    def one_liner(self) -> str:
        time_str = time.strftime("%d %b %Y %H:%M", time.localtime(self.time))
        return f'{self.state:2}|{self.version:15}|{self.release:6}|{self.distribution:8}|{time_str:12}'

    def __str__(self) -> str:
        time_str = time.strftime("%d %b %Y %H:%M", time.localtime(self.time))
        return _(f"State: {InstallInfo.state_map[self.state]}\n"
                 f"Version: {self.version}, Release: {self.release}\n"
                 f"Distribution: {self.distribution}, Install Time: {time_str}\n")

class InstallDB(lazydb.LazyDB):

    def __init__(self):
        super().__init__(cacheable=True, cachedir=ctx.config.packages_dir())

    def init(self):
        self.installed_db = self.__generate_installed_pkgs()
        self.rev_deps_db = self.__generate_revdeps()
        self.installed_extra = self.__generate_installed_extra()

    def __generate_installed_extra(self):
        ie = []
        ie_path = os.path.join(ctx.config.info_dir(), ctx.const.installed_extra)
        if os.path.isfile(ie_path):
            with open(ie_path) as ie_file:
                ie.extend(ie_file.read().strip().split("\n"))
        return ie

    def __generate_installed_pkgs(self):
        def split_name(dirname):
            name, version, release = dirname.rsplit("-", 2)
            return name, f"{version}-{release}"

        return dict(map(split_name, os.listdir(ctx.config.packages_dir())))

    def __get_marked_packages(self, _type):
        info_path = os.path.join(ctx.config.info_dir(), _type)
        if os.path.exists(info_path):
            with open(info_path, "r") as file:
                return file.read().split()
        return []

    def __add_to_revdeps(self, package, revdeps):
        metadata_xml = os.path.join(self.package_path(package), ctx.const.metadata_xml)
        try:
            tree = ET.parse(metadata_xml)
            root = tree.getroot()
            pkg = root.find("Package")
        except Exception:
            pkg = None

        if pkg is None:
            # If package info is broken or not available, skip it.
            ctx.ui.warning(_(f"Installation info for package '{package}' is broken. "
                             "Reinstall it to fix this problem."))
            del self.installed_db[package]
            return

        deps = pkg.find('RuntimeDependencies')
        if deps is not None:
            for dep in deps.findall("Dependency"):
                dep_name = dep.text
                dep_xml = ET.tostring(dep, encoding='utf-8')
                revdep = revdeps.setdefault(dep_name, {})
                revdep[package] = dep_xml
            for anydep in deps.findall("AnyDependency"):
                for dep in anydep.findall("Dependency"):
                    dep_name = dep.text
                    dep_xml = ET.tostring(anydep, encoding='utf-8')
                    revdep = revdeps.setdefault(dep_name, {})
                    revdep[package] = dep_xml

    def __generate_revdeps(self):
        revdeps = {}
        for package in self.list_installed():
            self.__add_to_revdeps(package, revdeps)
        return revdeps

    def list_installed(self):
        return list(self.installed_db.keys())

    def has_package(self, package):
        return package in self.installed_db

    def list_installed_with_build_host(self, build_host):
        build_host_re = re.compile("<BuildHost>(.*?)</BuildHost>")
        found = []
        for name in self.list_installed():
            xml_path = os.path.join(self.package_path(name), ctx.const.metadata_xml)
            with open(xml_path) as xml_file:
                xml = xml_file.read()
                matched = build_host_re.search(xml)
                if matched:
                    if build_host != matched.groups()[0]:
                        continue
                elif build_host:
                    continue

                found.append(name)

        return found

    def __get_version(self, meta_doc):
        pkg = meta_doc.find("Package")
        history = pkg.find("History")
        version = history.find("Update").findtext("Version")
        release = history.find("Update").get("release")
        return version, release, None

    def __get_distro_release(self, meta_doc):
        pkg = meta_doc.find("Package")
        distro = pkg.findtext("Distribution")
        release = pkg.findtext("DistributionRelease")
        return distro, release

    def __get_install_tar_hash(self, meta_doc):
        return meta_doc.find("Package").findtext("InstallTarHash")

    def get_install_tar_hash(self, package):
        metadata_xml = os.path.join(self.package_path(package), ctx.const.metadata_xml)
        tree = ET.parse(metadata_xml)
        root = tree.getroot()
        return self.__get_install_tar_hash(root)

    def get_version_and_distro_release(self, package):
        metadata_xml = os.path.join(self.package_path(package), ctx.const.metadata_xml)
        tree = ET.parse(metadata_xml)
        root = tree.getroot()
        return self.__get_version(root) + self.__get_distro_release(root)

    def get_version(self, package):
        metadata_xml = os.path.join(self.package_path(package), ctx.const.metadata_xml)
        tree = ET.parse(metadata_xml)
        root = tree.getroot()
        return self.__get_version(root)

    def get_files(self, package):
        files = pisi.files.Files()
        files_xml = os.path.join(self.package_path(package), ctx.const.files_xml)
        files.read(files_xml)
        return files

    def get_config_files(self, package):
        files = self.get_files(package)
        return [file for file in files.list if file.type == 'config']

    def search_package(self, terms, lang=None, fields=None, cs=False):
        resum = r'<Summary xml:lang=.(%s|en).>.*?%s.*?</Summary>'
        redesc = r'<Description xml:lang=.(%s|en).>.*?%s.*?</Description>'
        if fields is None:
            fields = {'name': True, 'summary': True, 'desc': True}
        if lang is None:
            # Use a simple fallback for language detection
            import locale
            try:
                lang = locale.getlocale()[0][:2] if locale.getlocale()[0] else 'en'
            except:
                lang = 'en'
        found = []
        for name in self.list_installed():
            xml_path = os.path.join(self.package_path(name), ctx.const.metadata_xml)
            with open(xml_path) as xml_file:
                xml = xml_file.read()
                if terms == [term for term in terms if (fields['name'] and
                        re.compile(term, re.I).search(name)) or
                        (fields['summary'] and
                        re.compile(resum % (lang, term), 0 if cs else re.I).search(xml)) or
                        (fields['desc'] and
                        re.compile(redesc % (lang, term), 0 if cs else re.I).search(xml))]:
                    found.append(name)
        return found

    def get_isa_packages(self, isa):
        risa = f'<IsA>{isa}</IsA>'
        packages = []
        for name in self.list_installed():
            xml_path = os.path.join(self.package_path(name), ctx.const.metadata_xml)
            with open(xml_path) as xml_file:
                xml = xml_file.read()
                if re.compile(risa).search(xml):
                    packages.append(name)
        return packages

    def get_info(self, package):
        files_xml = os.path.join(self.package_path(package), ctx.const.files_xml)
        ctime = pisi.util.creation_time(files_xml)
        pkg = self.get_package(package)
        state = "i"
        if pkg.name in self.list_pending():
            state = "ip"

        return InstallInfo(state, pkg.version, pkg.release, pkg.distribution, ctime)

    def __make_dependency(self, depStr):
        node = ET.fromstring(depStr)
        dependency = pisi.dependency.Dependency()
        dependency.package = node.text
        if node.attrib:
            for attr, value in node.attrib.items():
                dependency.__dict__[attr] = value
        return dependency

    def __create_dependency(self, depStr):
        if "<AnyDependency>" in depStr:
            anydependency = pisi.specfile.AnyDependency()
            for dep in re.findall(r'(<Dependency .*?>.*?</Dependency>)', depStr):
                anydependency.dependencies.append(self.__make_dependency(dep))
            return anydependency
        else:
            return self.__make_dependency(depStr)

    def get_rev_deps(self, name):
        rev_deps = []
        package_revdeps = self.rev_deps_db.get(name)
        if package_revdeps:
            for pkg, dep in package_revdeps.items():
                dependency = self.__create_dependency(dep)
                rev_deps.append((pkg, dependency))
        return rev_deps

    def get_orphaned(self):
        """Get list of packages installed as extra dependencies, but without reverse dependencies now."""
        return [x for x in self.installed_extra if not self.get_rev_deps(x)]

    def get_no_rev_deps(self):
        """Get installed packages list which haven't reverse dependencies."""
        return [x for x in self.installed_db if not self.get_rev_deps(x)]

    def pkg_dir(self, pkg, version, release):
        return pisi.util.join_path(ctx.config.packages_dir(), f"{pkg}-{version}-{release}")

    def get_package(self, package):
        metadata = pisi.metadata.MetaData()
        metadata_xml = os.path.join(self.package_path(package), ctx.const.metadata_xml)
        metadata.read(metadata_xml)
        return metadata.package

    def __mark_package(self, _type, package):
        packages = self.__get_marked_packages(_type)
        if package not in packages:
            packages.append(package)
            self.__write_marked_packages(_type, packages)

    def mark_pending(self, package):
        self.__mark_package(ctx.const.config_pending, package)

    def mark_needs_restart(self, package):
        self.__mark_package(ctx.const.needs_restart, package)

    def mark_needs_reboot(self, package):
        self.__mark_package(ctx.const.needs_reboot, package)

    def add_package(self, pkginfo):
        # Cleanup old revdep info
        for revdep_info in self.rev_deps_db.values():
            revdep_info.pop(pkginfo.name, None)

        self.installed_db[pkginfo.name] = f"{pkginfo.version}-{pkginfo.release}"
        self.__add_to_revdeps(pkginfo.name, self.rev_deps_db)

    def remove_package(self, package_name):
        if package_name in self.installed_db:
            del self.installed_db[package_name]

        # Cleanup revdep info
        for revdep_info in self.rev_deps_db.values():
            revdep_info.pop(package_name, None)

        self.clear_pending(package_name)

    def list_pending(self):
        return self.__get_marked_packages(ctx.const.config_pending)

    def list_needs_restart(self):
        return self.__get_marked_packages(ctx.const.needs_restart)

    def list_needs_reboot(self):
        return self.__get_marked_packages(ctx.const.needs_reboot)

    def __write_marked_packages(self, _type, packages):
        info_file = os.path.join(ctx.config.info_dir(), _type)
        with open(info_file, "w") as config:
            for pkg in set(packages):
                config.write(f"{pkg}\n")

    def __clear_marked_packages(self, _type, package):
        if package == "*":
            self.__write_marked_packages(_type, [])
            return
        packages = self.__get_marked_packages(_type)
        if package in packages:
            packages.remove(package)
            self.__write_marked_packages(_type, packages)

    def clear_pending(self, package):
        self.__clear_marked_packages(ctx.const.config_pending, package)

    def clear_needs_restart(self, package):
        self.__clear_marked_packages(ctx.const.needs_restart, package)

    def clear_needs_reboot(self, package):
        self.__clear_marked_packages(ctx.const.needs_reboot, package)

    def package_path(self, package):
        if package in self.installed_db:
            return os.path.join(ctx.config.packages_dir(), f"{package}-{self.installed_db[package]}")
        raise Exception(_('Package %s is not installed') % package)
