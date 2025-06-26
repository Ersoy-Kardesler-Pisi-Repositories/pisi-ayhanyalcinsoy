# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 - 2010, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

import os
import xml.etree.ElementTree as ET
import pisi
import pisi.uri
import pisi.util
import pisi.context as ctx
import pisi.db.lazydb as lazydb
from pisi.file import File

class RepoError(pisi.Error):
    pass

class IncompatibleRepoError(RepoError):
    pass

class Repo:
    def __init__(self, indexuri):
        self.indexuri = indexuri

medias = (cd, usb, remote, local) = range(4)

class RepoOrder:

    def __init__(self):
        self._doc = None
        self.repos = self._get_repos()

    def add(self, repo_name, repo_url, repo_type="remote"):
        repo_doc = self._get_doc()

        try:
            repos = repo_doc.findall("Repo")
            if repos:
                repo_node = ET.SubElement(repo_doc, "Repo")
            else:
                repo_node = ET.SubElement(repo_doc, "Repo")
        except IndexError:
            repo_node = ET.SubElement(repo_doc, "Repo")

        name_node = ET.SubElement(repo_node, "Name")
        name_node.text = repo_name

        url_node = ET.SubElement(repo_node, "Url")
        url_node.text = repo_url

        status_node = ET.SubElement(repo_node, "Status")
        status_node.text = "active"

        media_node = ET.SubElement(repo_node, "Media")
        media_node.text = repo_type

        self._update(repo_doc)

    def set_status(self, repo_name, status):
        repo_doc = self._get_doc()

        for r in repo_doc.findall("Repo"):
            if r.findtext("Name") == repo_name:
                status_node = r.find("Status")
                if status_node is not None:
                    status_node.text = status
                else:
                    status_node = ET.SubElement(r, "Status")
                    status_node.text = status

        self._update(repo_doc)

    def get_status(self, repo_name):
        repo_doc = self._get_doc()
        for r in repo_doc.findall("Repo"):
            if r.findtext("Name") == repo_name:
                status_node = r.find("Status")
                if status_node is not None:
                    status = status_node.text
                    if status in ["active", "inactive"]:
                        return status
        return "inactive"

    def remove(self, repo_name):
        repo_doc = self._get_doc()

        for r in repo_doc.findall("Repo"):
            if r.findtext("Name") == repo_name:
                repo_doc.remove(r)

        self._update(repo_doc)

    def get_order(self):
        order = []

        # FIXME: get media order from pisi.conf
        for m in ["cd", "usb", "remote", "local"]:
            if m in self.repos:
                order.extend(self.repos[m])

        return order

    def _update(self, doc):
        repos_file = os.path.join(ctx.config.info_dir(), ctx.const.repos)
        tree = ET.ElementTree(doc)
        tree.write(repos_file, encoding='utf-8', xml_declaration=True)
        self._doc = None
        self.repos = self._get_repos()

    def _get_doc(self):
        if self._doc is None:
            repos_file = os.path.join(ctx.config.info_dir(), ctx.const.repos)
            if os.path.exists(repos_file):
                tree = ET.parse(repos_file)
                self._doc = tree.getroot()
            else:
                self._doc = ET.Element("REPOS")

        return self._doc

    def _get_repos(self):
        repo_doc = self._get_doc()
        order = {}

        for r in repo_doc.findall("Repo"):
            media = r.findtext("Media")
            name = r.findtext("Name")
            status = r.findtext("Status")
            order.setdefault(media, []).append(name)

        return order

class RepoDB(lazydb.LazyDB):

    def init(self):
        self.repoorder = RepoOrder()

    def has_repo(self, name):
        return name in self.list_repos(only_active=False)

    def has_repo_url(self, url, only_active=True):
        return url in self.list_repo_urls(only_active)

    def get_repo_doc(self, repo_name):
        repo = self.get_repo(repo_name)

        index_path = repo.indexuri.get_uri()

        # FIXME Local index files should also be cached.
        if File.is_compressed(index_path) or repo.indexuri.is_remote_file():
            index = os.path.basename(index_path)
            index_path = pisi.util.join_path(ctx.config.index_dir(),
                                             repo_name, index)

            if File.is_compressed(index_path):
                index_path = os.path.splitext(index_path)[0]

        if not os.path.exists(index_path):
            ctx.ui.warning(_("%s repository needs to be updated") % repo_name)
            return ET.Element("PISI")

        try:
            tree = ET.parse(index_path)
            return tree.getroot()
        except Exception as e:
            raise RepoError(_("Error parsing repository index information. Index file does not exist or is malformed."))

    def get_repo(self, repo):
        return Repo(pisi.uri.URI(self.get_repo_url(repo)))

    # FIXME: this method is a quick hack around repo_info.indexuri.get_uri()
    def get_repo_url(self, repo):
        urifile_path = pisi.util.join_path(ctx.config.index_dir(), repo, "uri")
        with open(urifile_path, "r") as f:
            uri = f.read()
        return uri.rstrip()

    def add_repo(self, name, repo_info, at=None):
        repo_path = pisi.util.join_path(ctx.config.index_dir(), name)
        os.makedirs(repo_path)
        urifile_path = pisi.util.join_path(ctx.config.index_dir(), name, "uri")
        with open(urifile_path, "w") as f:
            f.write(repo_info.indexuri.get_uri())
        self.repoorder.add(name, repo_info.indexuri.get_uri())

    def remove_repo(self, name):
        pisi.util.clean_dir(os.path.join(ctx.config.index_dir(), name))
        self.repoorder.remove(name)

    def get_source_repos(self, only_active=True):
        repos = []
        for r in self.list_repos(only_active):
            if self.get_repo_doc(r).findtext("SpecFile"):
                repos.append(r)
        return repos

    def get_binary_repos(self, only_active=True):
        repos = []
        for r in self.list_repos(only_active):
            if not self.get_repo_doc(r).findtext("SpecFile"):
                repos.append(r)
        return repos

    def list_repos(self, only_active=True):
        return [x for x in self.repoorder.get_order() if not only_active or self.repo_active(x)]

    def list_repo_urls(self, only_active=True):
        repos = []
        for r in self.list_repos(only_active):
            repos.append(self.get_repo_url(r))
        return repos

    def get_repo_by_url(self, url):
        if not self.has_repo_url(url):
            return None

        for r in self.list_repos(only_active=False):
            if self.get_repo_url(r) == url:
                return r

    def activate_repo(self, name):
        self.repoorder.set_status(name, "active")

    def deactivate_repo(self, name):
        self.repoorder.set_status(name, "inactive")

    def repo_active(self, name):
        return self.repoorder.get_status(name) == "active"

    def get_distribution(self, name):
        doc = self.get_repo_doc(name)
        distro = doc.find("Distribution")
        return distro and distro.findtext("SourceName")

    def get_distribution_release(self, name):
        doc = self.get_repo_doc(name)
        distro = doc.find("Distribution")
        return distro and distro.findtext("Version")

    def check_distribution(self, name):
        if ctx.get_option('ignore_check'):
            return

        dist_name = self.get_distribution(name)
        if dist_name is None:
            return

        compatible = dist_name == ctx.config.values.general.distribution

        dist_release = self.get_distribution_release(name)
        if dist_release is not None:
            compatible &= dist_release == ctx.config.values.general.distribution_release

        if not compatible:
            self.deactivate_repo(name)
            raise IncompatibleRepoError(
                _("Repository '%s' is not compatible with your "
                  "distribution. Repository is disabled.") % name)
