# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 - 2011, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import re
import gzip
import xml.etree.ElementTree as ET

import pisi
import pisi.specfile
import pisi.db.lazydb as lazydb

class SourceDB(lazydb.LazyDB):

    def __init__(self):
        super().__init__(cacheable=True)

    def init(self):
        self.__source_nodes = {}
        self.__pkgstosrc = {}
        self.__revdeps = {}

        repodb = pisi.db.repodb.RepoDB()

        for repo in repodb.list_repos():
            doc = repodb.get_repo_doc(repo)
            self.__source_nodes[repo], self.__pkgstosrc[repo] = self.__generate_sources(doc)
            self.__revdeps[repo] = self.__generate_revdeps(doc)

        self.sdb = pisi.db.itembyrepo.ItemByRepo(self.__source_nodes, compressed=True)
        self.psdb = pisi.db.itembyrepo.ItemByRepo(self.__pkgstosrc)
        self.rvdb = pisi.db.itembyrepo.ItemByRepo(self.__revdeps)

    def __generate_sources(self, doc):
        sources = {}
        pkgstosrc = {}

        for spec in doc.findall("SpecFile"):
            src_name = spec.find("Source").findtext("Name")
            sources[src_name] = gzip.compress(ET.tostring(spec, encoding='utf-8'))
            for package in spec.findall("Package"):
                pkgstosrc[package.findtext("Name")] = src_name

        return sources, pkgstosrc

    def __generate_revdeps(self, doc):
        revdeps = {}
        for spec in doc.findall("SpecFile"):
            name = spec.find("Source").findtext("Name")
            deps = spec.find("Source").find("BuildDependencies")
            if deps is not None:
                for dep in deps.findall("Dependency"):
                    dep_name = dep.text
                    dep_xml = ET.tostring(dep, encoding='utf-8')
                    revdeps.setdefault(dep_name, set()).add((name, dep_xml))
        return revdeps

    def list_sources(self, repo=None):
        return self.sdb.get_item_keys(repo)

    def which_repo(self, name):
        return self.sdb.which_repo(self.pkgtosrc(name))

    def which_source_repo(self, name):
        source = self.pkgtosrc(name)
        return source, self.sdb.which_repo(source)

    def has_spec(self, name, repo=None):
        return self.sdb.has_item(name, repo)

    def get_spec(self, name, repo=None):
        spec, repo = self.get_spec_repo(name, repo)
        return spec

    def search_spec(self, terms, lang=None, repo=None, fields=None, cs=False):
        resum = '<Summary xml:lang=.(%s|en).>.*?%s.*?</Summary>'
        redesc = '<Description xml:lang=.(%s|en).>.*?%s.*?</Description>'
        if not fields:
            fields = {'name': True, 'summary': True, 'desc': True}
        if not lang:
            # Use a simple fallback for language detection
            import locale
            try:
                lang = locale.getlocale()[0][:2] if locale.getlocale()[0] else 'en'
            except:
                lang = 'en'
        found = []
        for name, xml in self.sdb.get_items_iter(repo):
            if isinstance(xml, bytes):
                xml = xml.decode('utf-8')
            if terms == [term for term in terms if (fields['name'] and
                    re.compile(term, re.I).search(name)) or
                    (fields['summary'] and
                    re.compile(resum % (lang, term), 0 if cs else re.I).search(xml)) or
                    (fields['desc'] and
                    re.compile(redesc % (lang, term), 0 if cs else re.I).search(xml))]:
                found.append(name)
        return found

    def get_spec_repo(self, name, repo=None):
        src, repo = self.sdb.get_item_repo(name, repo)
        spec = pisi.specfile.SpecFile()
        spec.parse(src.decode('utf-8'))
        return spec, repo

    def pkgtosrc(self, name, repo=None):
        return self.psdb.get_item(name, repo)

    def get_rev_deps(self, name, repo=None):
        try:
            rvdb = self.rvdb.get_item(name, repo)
        except Exception as e:  # Catch the specific exception you expect
            return []

        rev_deps = []
        for pkg, dep in rvdb:
            node = ET.fromstring(dep)
            dependency = pisi.dependency.Dependency()
            dependency.package = node.text
            if node.attrib:
                for attr, value in node.attrib.items():
                    dependency.__dict__[attr] = value
            rev_deps.append((pkg, dependency))
        return rev_deps
