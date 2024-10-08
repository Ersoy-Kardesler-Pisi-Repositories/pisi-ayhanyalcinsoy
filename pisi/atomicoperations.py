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

"""Atomic package operations such as install/remove/upgrade"""

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext  # Python 3'te ugettext yerine gettext kullanılmalıdır

import os
import shutil
import zipfile

import pisi
import pisi.context as ctx
import pisi.util as util
import pisi.metadata
import pisi.files
import pisi.uri
import pisi.ui
import pisi.version
import pisi.operations.delta
import pisi.db

class Error(pisi.Error):
    pass

class NotfoundError(pisi.Error):
    pass

# single package operations

class AtomicOperation(object):

    def __init__(self, ignore_dep=None):
        # self.package = package
        if ignore_dep is None:
            self.ignore_dep = ctx.config.get_option('ignore_dependency')
        else:
            self.ignore_dep = ignore_dep

        self.historydb = pisi.db.historydb.HistoryDB()

    def run(self, package):
        "perform an atomic package operation"
        pass

# possible paths of install operation
(INSTALL, REINSTALL, UPGRADE, DOWNGRADE, REMOVE) = range(5)
opttostr = {
    INSTALL: "install",
    REMOVE: "remove",
    REINSTALL: "reinstall",
    UPGRADE: "upgrade",
    DOWNGRADE: "downgrade"
}

class Install(AtomicOperation):
    "Install class, provides install routines for pisi packages"

    @staticmethod
    def from_name(name, ignore_dep=None):
        packagedb = pisi.db.packagedb.PackageDB()
        # download package and return an installer object
        # find package in repository
        repo = packagedb.which_repo(name)
        if repo:
            repodb = pisi.db.repodb.RepoDB()
            ctx.ui.info(_("Package %s found in repository %s") % (name, repo))

            repo = repodb.get_repo(repo)
            pkg = packagedb.get_package(name)
            delta = None

            installdb = pisi.db.installdb.InstallDB()
            # Package is installed. This is an upgrade. Check delta.
            if installdb.has_package(pkg.name):
                (version, release, build, distro, distro_release) = installdb.get_version_and_distro_release(pkg.name)
                # pisi distro upgrade should not use delta support
                if distro == pkg.distribution and distro_release == pkg.distributionRelease:
                    delta = pkg.get_delta(release)

            ignore_delta = ctx.config.values.general.ignore_delta

            # If delta exists then use the delta uri.
            if delta and not ignore_delta:
                pkg_uri = delta.packageURI
                pkg_hash = delta.packageHash
            else:
                pkg_uri = pkg.packageURI
                pkg_hash = pkg.packageHash

            uri = pisi.uri.URI(pkg_uri)
            if uri.is_absolute_path():
                pkg_path = str(pkg_uri)
            else:
                pkg_path = os.path.join(os.path.dirname(repo.indexuri.get_uri()), str(uri.path()))

            ctx.ui.info(_("Package URI: %s") % pkg_path, verbose=True)

            # Bug 4113
            cached_file = pisi.package.Package.is_cached(pkg_path)
            if cached_file and util.sha1_file(cached_file) != pkg_hash:
                os.unlink(cached_file)
                cached_file = None

            install_op = Install(pkg_path, ignore_dep)

            # Bug 4113
            if not cached_file:
                downloaded_file = install_op.package.filepath
                if pisi.util.sha1_file(downloaded_file) != pkg_hash:
                    raise pisi.Error(_("Download Error: Package does not match the repository package."))

            return install_op
        else:
            raise Error(_("Package %s not found in any active repository.") % name)

    def __init__(self, package_fname, ignore_dep=None, ignore_file_conflicts=None):
        if not ctx.filesdb:
            ctx.filesdb = pisi.db.filesldb.FilesLDB()
        "initialize from a file name"
        super(Install, self).__init__(ignore_dep)
        if ignore_file_conflicts is None:
            ignore_file_conflicts = ctx.get_option('ignore_file_conflicts')
        self.ignore_file_conflicts = ignore_file_conflicts
        self.package_fname = package_fname
        try:
            self.package = pisi.package.Package(package_fname)
            self.package.read()
        except zipfile.BadZipFile:
            raise zipfile.BadZipFile(self.package_fname)
        self.metadata = self.package.metadata
        self.files = self.package.files
        self.pkginfo = self.metadata.package
        self.installdb = pisi.db.installdb.InstallDB()
        self.operation = INSTALL
        self.store_old_paths = None

    def install(self, ask_reinstall=True):

        # Any package should remove the package it replaces before
        self.check_replaces()

        ctx.ui.status(_('Installing %s, version %s, release %s') %
                       (self.pkginfo.name, self.pkginfo.version,
                        self.pkginfo.release))
        ctx.ui.notify(pisi.ui.installing, package=self.pkginfo, files=self.files)

        self.ask_reinstall = ask_reinstall
        self.check_requirements()
        self.check_versioning(self.pkginfo.version, self.pkginfo.release)
        self.check_relations()
        self.check_operation()

        ctx.disable_keyboard_interrupts()

        self.extract_install()
        self.store_pisi_files()
        self.postinstall()
        self.update_databases()

        ctx.enable_keyboard_interrupts()

        ctx.ui.close()
        if self.operation == UPGRADE:
            event = pisi.ui.upgraded
        else:
            event = pisi.ui.installed
        ctx.ui.notify(event, package=self.pkginfo, files=self.files)

    def check_requirements(self):
        """check system requirements"""
        # TODO: IS THERE ENOUGH SPACE?
        # what to do if / is split into /usr, /var, etc.
        # check comar
        if self.metadata.package.providesComar and ctx.comar:
            import pisi.comariface as comariface
            comariface.get_link()

    def check_replaces(self):
        for replaced in self.pkginfo.replaces:
            if self.installdb.has_package(replaced.package):
                pisi.operations.remove.remove_replaced_packages([replaced.package])

    def check_versioning(self, version, release):
        try:
            int(release)
            pisi.version.make_version(version)
        except (ValueError, pisi.version.InvalidVersionError):
            raise Error(_("%s-%s is not a valid PiSi version format") % (version, release))

    def check_relations(self):
        # check dependencies
        if not ctx.config.get_option('ignore_dependency'):
            if not self.pkginfo.installable():
                raise Error(_("%s package cannot be installed unless the dependencies are satisfied") %
                            self.pkginfo.name)

        # If it is explicitly specified that package conflicts with this package and also
        # we passed check_conflicts tests in operations.py than this means a non-conflicting
        # pkg is in "order" to be installed that has no file conflict problem with this package.
        # PS: we need this because "order" generating code does not consider conflicts.
        def really_conflicts(pkg):
            if not self.pkginfo.conflicts:
                return True

            return not pkg in map(lambda x: x.package, self.pkginfo.conflicts)

        # check file conflicts
        file_conflicts = []
        for f in self.files.list:
            pkg, existing_file = ctx.filesdb.get_file(f.path)
            if pkg:
                dst = pisi.util.join_path(ctx.config.dest_dir(), f.path)
                if pkg != self.pkginfo.name and not os.path.isdir(dst) and really_conflicts(pkg):
                    file_conflicts.append((pkg, existing_file))
        if file_conflicts:
            file_conflicts_str = ""
            for (pkg, existing_file) in file_conflicts:
                file_conflicts_str += _("/%s from %s package\n") % (existing_file, pkg)
            msg = _('File conflicts:\n%s') % file_conflicts_str
            if self.ignore_file_conflicts:
                ctx.ui.warning(msg)
            else:
                raise Error(msg)

    def check_operation(self):

        self.old_pkginfo = None
        pkg = self.pkginfo

        if self.installdb.has_package(pkg.name):  # is this a reinstallation?
            ipkg = self.installdb.get_package(pkg.name)
            (iversion_s, irelease_s, ibuild) = self.installdb.get_version(pkg.name)

            # determine if same version
            if pkg.release == irelease_s:
                if self.ask_reinstall:
                    if not ctx.ui.confirm(_('Re-install same version package?')):
                        raise Error(_('Package re-install declined'))
                self.operation = REINSTALL
                self.old_pkginfo = ipkg

            elif pisi.version.compare(pkg.version, iversion_s) > 0:  # upgrade
                self.operation = UPGRADE

            elif pisi.version.compare(pkg.version, iversion_s) < 0:  # downgrade
                self.operation = DOWNGRADE

            # if package is not upgraded nor downgraded nor reinstalled
            else:
                raise Error(_('No update found for %s') % pkg.name)

        # if it is a new package
        else:
            self.operation = INSTALL

    def postinstall(self):
        "runs post-install commands"
        try:
            for cmd in self.metadata.post_install:
                ctx.run_command(cmd, self.pkginfo)
        except pisi.Error as e:
            ctx.ui.warning(_("Postinstall Error: %s") % e)

    def extract_install(self):
        "extracts files from the package"
        dest_dir = ctx.config.dest_dir()
        # print("DESTDIR: %s" % dest_dir)
        self.package.extract(dest_dir)

    def store_pisi_files(self):
        """stores new package files in database"""
        ctx.ui.info(_('Storing installed files in database...'))
        self.installdb.add_package(self.pkginfo, self.package_fname)
        ctx.filesdb.add_files(self.files)

    def update_databases(self):
        """updates various databases"""
        ctx.ui.info(_('Updating databases...'))
        # package files, and others
        # update packages.db
        # remove installed package (if it is removed)
        if self.old_pkginfo:
            self.installdb.remove_package(self.old_pkginfo.name)

        # update historydb
        self.historydb.insert(self.pkginfo, self.operation, self.package_fname)
        self.historydb.write()
        ctx.ui.info(_('Database update complete.'))

def install_single(pkg, upgrade=False):
    """Install a single package from a file or repository"""
    if os.path.exists(pkg):
        install_op = Install(pkg)
    else:
        install_op = Install.from_name(pkg)
    install_op.install(ask_reinstall=not upgrade)

def install_single_file(pkg_location, upgrade):
    """install from a file location"""
    install_single(pkg_location, upgrade)

def install_single_name(name, upgrade):
    """install by name"""
    install_single(name, upgrade)

class Remove(AtomicOperation):

    def __init__(self, package_name, ignore_dep=None, store_old_paths=None):
        if not ctx.filesdb:
            ctx.filesdb = pisi.db.filesldb.FilesLDB()
        super(Remove, self).__init__(ignore_dep)
        self.installdb = pisi.db.installdb.InstallDB()
        self.package_name = package_name
        self.package = self.installdb.get_package(self.package_name)
        self.store_old_paths = store_old_paths
        try:
            self.files = self.installdb.get_files(self.package_name)
        except pisi.Error as e:
            # for some reason file was deleted, we still allow removes!
            ctx.ui.error(str(e))
            ctx.ui.warning(_('File list could not be read for package %s, continuing removal.') % package_name)
            self.files = pisi.files.Files()

    def run(self):
        """Remove a single package"""

        ctx.ui.status(_('Removing package %s') % self.package_name)
        ctx.ui.notify(pisi.ui.removing, package=self.package, files=self.files)
        if not self.installdb.has_package(self.package_name):
            raise Exception(_('Trying to remove nonexistent package ') + self.package_name)

        self.check_dependencies()

        self.run_preremove()
        for fileinfo in self.files.list:
            self.remove_file(fileinfo, self.package_name, True)

        self.run_postremove()

        self.update_databases()

        self.remove_pisi_files()
        ctx.ui.close()
        ctx.ui.notify(pisi.ui.removed, package=self.package, files=self.files)

    def check_dependencies(self):
        # FIXME: why is this not implemented? -- exa
        # we only have to check the dependencies to ensure the
        # system will be consistent after this removal
        pass
        # is there any package who depends on this package?

    @staticmethod
    def remove_file(fileinfo, package_name, remove_permanent=False, store_old_paths=None):

        if fileinfo.permanent and not remove_permanent:
            return

        fpath = pisi.util.join_path(ctx.config.dest_dir(), fileinfo.path)

        historydb = pisi.db.historydb.HistoryDB()
        # we should check if the file belongs to another
        # package (this can legitimately occur while upgrading
        # two packages such that a file has moved from one package to
        # another as in #2911)
        pkg, existing_file = ctx.filesdb.get_file(fileinfo.path)
        if pkg and pkg != package_name:
            ctx.ui.warning(_('Not removing conflicted file : %s') % fpath)
            return

        if fileinfo.type == ctx.const.conf:
            # config files are precious, leave them as they are
            # unless they are the same as provided by package.
            # remove symlinks as they are, cause if the hash of the
            # file it links has changed, it will be kept as is,
            # and when the package is reinstalled the symlink will
            # link to that changed file again.
            try:
                if os.path.islink(fpath) or pisi.util.sha1_file(fpath) == fileinfo.hash:
                    os.unlink(fpath)
                else:
                    # keep changed file in history
                    historydb.save_config(package_name, fpath)

                    # after saving to history db, remove the config file any way
                    if ctx.get_option("purge"):
                        os.unlink(fpath)
            except pisi.util.FileError:
                pass
        else:
            if os.path.isfile(fpath) or os.path.islink(fpath):
                os.unlink(fpath)
                if store_old_paths:
                    with open(store_old_paths, "a") as f:
                        f.write("%s\n" % fpath)
            elif os.path.isdir(fpath) and not os.listdir(fpath):
                os.rmdir(fpath)
            else:
                ctx.ui.warning(_('Installed file %s does not exist on system [Probably you manually deleted]') % fpath)
                return

        # remove emptied directories
        dpath = os.path.dirname(fpath)
        while dpath != '/' and not os.listdir(dpath):
            os.rmdir(dpath)
            dpath = os.path.dirname(dpath)

    def run_preremove(self):
        if ctx.comar:
            import pisi.comariface
            pisi.comariface.pre_remove(
                self.package_name,
                os.path.join(self.package.pkg_dir(), ctx.const.metadata_xml),
                os.path.join(self.package.pkg_dir(), ctx.const.files_xml),
            )

    def run_postremove(self):
        if ctx.comar:
            import pisi.comariface
            pisi.comariface.post_remove(
                self.package_name,
                os.path.join(self.package.pkg_dir(), ctx.const.metadata_xml),
                os.path.join(self.package.pkg_dir(), ctx.const.files_xml),
                provided_scripts=self.package.providesComar,
            )

    def update_databases(self):
        self.remove_db()
        self.historydb.add_and_update(pkgBefore=self.package, operation="remove")

    def remove_pisi_files(self):
        util.clean_dir(self.package.pkg_dir())

    def remove_db(self):
        self.installdb.remove_package(self.package_name)
        ctx.filesdb.remove_files(self.files.list)
        # FIX:DB
        # FIXME: something goes wrong here, if we use ctx operations ends up with segmentation fault!
        # pisi.db.packagedb.remove_tracking_package(self.package_name)


def remove_single(package_name):
    Remove(package_name).run()

def build(package):
    # wrapper for build op
    import pisi.operations.build
    return pisi.operations.build.build(package)

