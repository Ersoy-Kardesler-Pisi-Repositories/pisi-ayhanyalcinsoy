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

import re
import gettext

__trans = gettext.translation('pisi', fallback=True)
_ = __trans.ugettext

import pisi
import pisi.db.repodb
import pisi.db.itembyrepo
import pisi.component
import pisi.db.lazydb as lazydb

class ComponentDB(lazydb.LazyDB):

    def __init__(self):
        super().__init__(cacheable=True)  # Python 3'te super() kullanımında argüman yok.

    def init(self):
        component_nodes = {}
        component_packages = {}
        component_sources = {}

        repodb = pisi.db.repodb.RepoDB()

        for repo in repodb.list_repos():
            doc = repodb.get_repo_doc(repo)
            component_nodes[repo] = self.__generate_components(doc)
            component_packages[repo] = self.__generate_packages(doc)
            component_sources[repo] = self.__generate_sources(doc)

        self.cdb = pisi.db.itembyrepo.ItemByRepo(component_nodes)
        self.cpdb = pisi.db.itembyrepo.ItemByRepo(component_packages)
        self.csdb = pisi.db.itembyrepo.ItemByRepo(component_sources)

    def __generate_packages(self, doc):
        components = {}
        for pkg in doc.tags("Package"):
            components.setdefault(pkg.getTagData("PartOf"), []).append(pkg.getTagData("Name"))
        return components

    def __generate_sources(self, doc):
        components = {}
        for spec in doc.tags("SpecFile"):
            src = spec.getTag("Source")
            components.setdefault(src.getTagData("PartOf"), []).append(src.getTagData("Name"))
        return components

    def __generate_components(self, doc):
        return {x.getTagData("Name"): x.toString() for x in doc.tags("Component")}  # Dictionary comprehension kullanıldı

    def has_component(self, name, repo=None):
        return self.cdb.has_item(name, repo)

    def list_components(self, repo=None):
        return self.cdb.get_item_keys(repo)

    def search_component(self, terms, lang=None, repo=None):
        rename = '<LocalName xml:lang="(%s|en)">.*?%s.*?</LocalName>'
        resum = '<Summary xml:lang="(%s|en)">.*?%s.*?</Summary>'
        redesc = '<Description xml:lang="(%s|en)">.*?%s.*?</Description>'

        if not lang:
            lang = pisi.pxml.autoxml.LocalText.get_lang()
        found = []
        for name, xml in self.cdb.get_items_iter(repo):
            if name not in found and any(
                re.compile(rename % (lang, term), re.I).search(xml) or
                re.compile(resum % (lang, term), re.I).search(xml) or
                re.compile(redesc % (lang, term), re.I).search(xml)
                for term in terms):
                found.append(name)
        return found

    def get_component(self, component_name, repo=None):
        if not self.has_component(component_name, repo):
            raise Exception(_('Component %s not found') % component_name)

        component = pisi.component.Component()
        component.parse(self.cdb.get_item(component_name, repo))

        try:
            component.packages = self.cpdb.get_item(component_name, repo)
        except Exception:  # Hata türünü belirlemeyi gerektirir.
            pass

        try:
            component.sources = self.csdb.get_item(component_name, repo)
        except Exception:  # Hata türünü belirlemeyi gerektirir.
            pass

        return component

    def get_union_component(self, component_name):
        component = pisi.component.Component()
        component.parse(self.cdb.get_item(component_name))
        
        for repo in pisi.db.repodb.RepoDB().list_repos():
            try:
                component.packages.extend(self.cpdb.get_item(component_name, repo))
            except Exception:  # Hata türünü belirlemeyi gerektirir.
                pass

            try:
                component.sources.extend(self.csdb.get_item(component_name, repo))
            except Exception:  # Hata türünü belirlemeyi gerektirir.
                pass
            
        return component

    def get_packages(self, component_name, repo=None, walk=False):
        component = self.get_component(component_name, repo)
        if not walk:
            return component.packages

        packages = list(component.packages)  # Liste kopyası oluşturuldu.

        sub_components = [x for x in self.list_components(repo) if x.startswith(component_name + ".")]
        for sub in sub_components:
            try:
                packages.extend(self.get_component(sub, repo).packages)
            except Exception:  # Hata türünü belirlemeyi gerektirir.
                pass

        return packages

    def get_union_packages(self, component_name, walk=False):
        component = self.get_union_component(component_name)
        if not walk:
            return component.packages

        packages = list(component.packages)

        sub_components = [x for x in self.list_components() if x.startswith(component_name + ".")]
        for sub in sub_components:
            try:
                packages.extend(self.get_union_component(sub).packages)
            except Exception:  # Hata türünü belirlemeyi gerektirir.
                pass

        return packages

    def get_sources(self, component_name, repo=None, walk=False):
        component = self.get_component(component_name, repo)
        if not walk:
            return component.sources

        sources = list(component.sources)

        sub_components = [x for x in self.list_components(repo) if x.startswith(component_name + ".")]
        for sub in sub_components:
            try:
                sources.extend(self.get_component(sub, repo).sources)
            except Exception:  # Hata türünü belirlemeyi gerektirir.
                pass

        return sources

    def get_union_sources(self, component_name, walk=False):
        component = self.get_union_component(component_name)
        if not walk:
            return component.sources

        sources = list(component.sources)

        sub_components = [x for x in self.list_components() if x.startswith(component_name + ".")]
        for sub in sub_components:
            try:
                sources.extend(self.get_union_component(sub).sources)
            except Exception:  # Hata türünü belirlemeyi gerektirir.
                pass

        return sources
