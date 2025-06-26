# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2010, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import re
import time
import gzip
import zlib
import gettext
import datetime
import xml.etree.ElementTree as ET
import locale
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

import pisi.db
import pisi.metadata
import pisi.dependency
import pisi.db.itembyrepo
import pisi.db.lazydb as lazydb

def get_lang():
    try:
        lang, encoding = locale.getlocale()
        if not lang:
            lang, encoding = locale.getdefaultlocale()
        if lang is None:
            return 'en'
        else:
            return lang[0:2]
    except Exception:
        return 'en'

class PackageDB(lazydb.LazyDB):

    def __init__(self):
        super().__init__(cacheable=True)

    def init(self):
        self.__package_nodes = {}  # Packages
        self.__revdeps = {}        # Reverse dependencies
        self.__obsoletes = {}      # Obsoletes
        self.__replaces = {}       # Replaces

        repodb = pisi.db.repodb.RepoDB()

        for repo in repodb.list_repos():
            doc = repodb.get_repo_doc(repo)
            self.__package_nodes[repo] = self.__generate_packages(doc)
            self.__revdeps[repo] = self.__generate_revdeps(doc)
            self.__obsoletes[repo] = self.__generate_obsoletes(doc)
            self.__replaces[repo] = self.__generate_replaces(doc)

        self.pdb = pisi.db.itembyrepo.ItemByRepo(self.__package_nodes, compressed=True)
        self.rvdb = pisi.db.itembyrepo.ItemByRepo(self.__revdeps)
        self.odb = pisi.db.itembyrepo.ItemByRepo(self.__obsoletes)
        self.rpdb = pisi.db.itembyrepo.ItemByRepo(self.__replaces)

    def __generate_replaces(self, doc):
        return [pkg.findtext("Name") for pkg in doc.findall("Package") if pkg.find("Replaces") is not None]

    def __generate_obsoletes(self, doc):
        distribution = doc.find("Distribution")
        obsoletes = distribution.find("Obsoletes") if distribution is not None else None
        src_repo = doc.find("SpecFile") is not None

        if obsoletes is None or src_repo:
            return []

        return [pkg.text for pkg in obsoletes.findall("Package")]

    def __generate_packages(self, doc):
        return {pkg.findtext("Name"): zlib.compress(ET.tostring(pkg, encoding='utf-8')) for pkg in doc.findall("Package")}

    def __generate_revdeps(self, doc):
        revdeps = {}
        for node in doc.findall("Package"):
            name = node.findtext('Name')
            deps = node.find("RuntimeDependencies")
            if deps is not None:
                for dep in deps.findall("Dependency"):
                    dep_name = dep.text
                    dep_xml = ET.tostring(dep, encoding='utf-8')
                    revdeps.setdefault(dep_name, set()).add((name, dep_xml))
        return revdeps

    def has_package(self, name, repo=None):
        return self.pdb.has_item(name, repo)

    def get_package(self, name, repo=None):
        pkg, repo = self.get_package_repo(name, repo)
        return pkg

    def ensure_str(self, s):
        if isinstance(s, bytes):
            return s.decode('utf-8')
        return s

    def search_in_packages(self, packages, terms, lang=None):
        resum = r'<Summary xml:lang=.(%s|en).>.*?%s.*?</Summary>'
        redesc = r'<Description xml:lang=.(%s|en).>.*?%s.*?</Description>'
        if lang is None:
            lang = get_lang()
        found = []
        for name in packages:
            xml = self.ensure_str(self.pdb.get_item(name))
            if terms == list(filter(lambda term: re.compile(term, re.I).search(name) or 
                                            re.compile(resum % (lang, term), re.I).search(xml) or 
                                            re.compile(redesc % (lang, term), re.I).search(xml), terms)):
                found.append(name)
        return found

    def search_package(self, terms, lang=None, repo=None, fields=None, cs=False):
        resum = r'<Summary xml:lang=.(%s|en).>.*?%s.*?</Summary>'
        redesc = r'<Description xml:lang=.(%s|en).>.*?%s.*?</Description>'
        if lang is None:
            lang = get_lang()
        if fields is None:
            fields = {'name': True, 'summary': True, 'desc': True}
        found = []
        for name, xml in self.pdb.get_items_iter(repo):
            xml = self.ensure_str(xml)
            if terms == list(filter(lambda term: (fields['name'] and 
                    re.compile(term, re.I).search(name)) or 
                    (fields['summary'] and 
                    re.compile(resum % (lang, term), 0 if cs else re.I).search(xml)) or 
                    (fields['desc'] and 
                    re.compile(redesc % (lang, term), 0 if cs else re.I).search(xml)), terms)):
                found.append(name)
        return found

    def __get_version(self, meta_doc):
        history = meta_doc.getTag("History")
        version = history.getTag("Update").getTagData("Version")
        release = history.getTag("Update").getAttribute("release")

        # TODO Remove None
        return version, release, None

    def __get_distro_release(self, meta_doc):
        distro = meta_doc.getTagData("Distribution")
        release = meta_doc.getTagData("DistributionRelease")

        return distro, release

    def get_version_and_distro_release(self, name, repo):
        if not self.has_package(name, repo):
            raise Exception(_('Package %s not found.') % name)

        pkg_doc = ET.fromstring(self.pdb.get_item(name, repo).decode('utf-8'))
        return self.__get_version(pkg_doc) + self.__get_distro_release(pkg_doc)

    def get_version(self, name, repo):
        if not self.has_package(name, repo):
            raise Exception(_('Package %s not found.') % name)

        pkg_doc = ET.fromstring(self.pdb.get_item(name, repo).decode('utf-8'))
        return self.__get_version(pkg_doc)

    def get_package_repo(self, name, repo=None):
        pkg, repo = self.pdb.get_item_repo(name, repo)
        package = pisi.metadata.Package()
        package.parse(pkg.decode('utf-8'))
        return package, repo

    def which_repo(self, name):
        return self.pdb.which_repo(name)

    def get_obsoletes(self, repo=None):
        return self.odb.get_list_item(repo)

    def get_isa_packages(self, isa):
        repodb = pisi.db.repodb.RepoDB()

        packages = set()
        for repo in repodb.list_repos():
            doc = repodb.get_repo_doc(repo)
            for package in doc.tags("Package"):
                if package.getTagData("IsA"):
                    for node in package.tags("IsA"):
                        if node.firstChild().data() == isa:
                            packages.add(package.getTagData("Name"))
        return list(packages)

    def get_rev_deps(self, name, repo=None):
        try:
            rvdb = self.rvdb.get_item(name, repo)
        except Exception:  # FIXME: what exception could we catch here, replace with that.
            return []

        rev_deps = []
        for pkg, dep in rvdb:
            node = ET.fromstring(dep)
            dependency = pisi.dependency.Dependency()
            dependency.package = node.findtext(".")
            if node.attrib:
                for attr, value in node.attrib.items():
                    dependency.__dict__[attr] = value
            rev_deps.append((pkg, dependency))
        return rev_deps

    # replacesdb holds the info about the replaced packages (ex. gaim -> pidgin)
    def get_replaces(self, repo=None):
        pairs = {}

        for pkg_name in self.rpdb.get_list_item():
            xml = self.pdb.get_item(pkg_name, repo)
            package = ET.fromstring(xml.decode('utf-8'))
            replaces_tag = package.find("Replaces")
            if replaces_tag is not None:
                for node in replaces_tag.findall("Package"):
                    r = pisi.relation.Relation()
                    r.decode(node, [])
                    if pisi.replace.installed_package_replaced(r):
                        pairs.setdefault(r.package, []).append(pkg_name)

        return pairs

    def list_packages(self, repo):
        return self.pdb.get_item_keys(repo)

    def list_newest(self, repo, since=None):
        packages = []
        historydb = pisi.db.historydb.HistoryDB()
        if since:
            since_date = datetime.datetime(*time.strptime(since, "%Y-%m-%d")[0:6])
        else:
            since_date = datetime.datetime(*time.strptime(historydb.get_last_repo_update(), "%Y-%m-%d")[0:6])

        for pkg in self.list_packages(repo):
            enter_date = datetime.datetime(*time.strptime(self.get_package(pkg).history[-1].date, "%Y-%m-%d")[0:6])
            if enter_date >= since_date:
                packages.append(pkg)
        return packages
