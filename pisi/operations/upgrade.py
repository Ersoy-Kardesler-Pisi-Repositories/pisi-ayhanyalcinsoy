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

import sys
import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

import pisi
import pisi.ui as ui
import pisi.context as ctx
import pisi.pgraph as pgraph
import pisi.atomicoperations as atomicoperations
import pisi.operations as operations
import pisi.util as util
import pisi.db
import pisi.blacklist

def check_update_actions(packages):
    installdb = pisi.db.installdb.InstallDB()
    packagedb = pisi.db.packagedb.PackageDB()

    actions = {}

    for package in packages:
        if not installdb.has_package(package):
            continue

        pkg = packagedb.get_package(package)
        version, release, build = installdb.get_version(package)
        pkg_actions = pkg.get_update_actions(release)

        for action_name, action_targets in pkg_actions.items():
            item = actions.setdefault(action_name, [])
            for action_target in action_targets:
                item.append((package, action_target))

    has_actions = False

    if "serviceRestart" in actions:
        has_actions = True
        ctx.ui.warning(_("You must restart the following service(s) manually "
                         "for the updated software to take effect:"))
        for package, target in actions["serviceRestart"]:
            ctx.ui.info("    - %s" % target)

    if "systemRestart" in actions:
        has_actions = True
        ctx.ui.warning(_("You must restart your system for the updates "
                         "in the following package(s) to take effect:"))
        for package, target in actions["systemRestart"]:
            ctx.ui.info("    - %s" % package)

    return has_actions

def find_upgrades(packages, replaces):
    packagedb = pisi.db.packagedb.PackageDB()
    installdb = pisi.db.installdb.InstallDB()

    debug = ctx.config.get_option("debug")
    security_only = ctx.get_option('security_only')
    comparesha1sum = ctx.get_option('compare_sha1sum')

    Ap = []
    ds = []
    for i_pkg in packages:

        if i_pkg in replaces.keys():
            continue

        if i_pkg.endswith(ctx.const.package_suffix):
            ctx.ui.debug(_("Warning: package *name* ends with '.pisi'"))

        if not installdb.has_package(i_pkg):
            ctx.ui.info(_('Package %s is not installed.') % i_pkg, True)
            continue

        if not packagedb.has_package(i_pkg):
            ctx.ui.info(_('Package %s is not available in repositories.') % i_pkg, True)
            continue

        pkg = packagedb.get_package(i_pkg)
        hash = installdb.get_install_tar_hash(i_pkg)
        (version, release, build, distro, distro_release) = installdb.get_version_and_distro_release(i_pkg)

        if security_only and not pkg.has_update_type("security", release):
            continue

        if pkg.distribution == distro and \
                pisi.version.make_version(pkg.distributionRelease) > pisi.version.make_version(distro_release):
            Ap.append(i_pkg)

        else:
            if int(release) < int(pkg.release):
                Ap.append(i_pkg)
            elif comparesha1sum and \
                int(release) == int(pkg.release) and \
                not pkg.installTarHash == hash:
                Ap.append(i_pkg)
                ds.append(i_pkg)
            else:
                ctx.ui.info(_('Package %s is already at the latest release %s.')
                            % (pkg.name, pkg.release), True)

    if debug and ds:
        ctx.ui.status(_('The following packages have different sha1sum:'))
        ctx.ui.info(util.format_by_columns(sorted(ds)))

    return Ap

def upgrade(A=None, repo=None):
    """Re-installs packages from the repository, trying to perform
    a minimum or maximum number of upgrades according to options."""

    packagedb = pisi.db.packagedb.PackageDB()
    installdb = pisi.db.installdb.InstallDB()
    replaces = packagedb.get_replaces()
    if A is None:
        # if A is empty, then upgrade all packages
        A = installdb.list_installed()

    if repo:
        repo_packages = set(packagedb.list_packages(repo))
        A = set(A).intersection(repo_packages)

    A_0 = A = set(A)
    Ap = find_upgrades(A, replaces)
    A = set(Ap)

    A |= set(pisi.util.flatten_list(replaces.values()))
    A |= upgrade_base(A)

    A = pisi.blacklist.exclude_from(A, ctx.const.blacklist)

    if ctx.get_option('exclude_from'):
        A = pisi.blacklist.exclude_from(A, ctx.get_option('exclude_from'))

    if ctx.get_option('exclude'):
        A = pisi.blacklist.exclude(A, ctx.get_option('exclude'))

    ctx.ui.debug('A = %s' % str(A))

    if len(A) == 0:
        ctx.ui.info(_('No packages to upgrade.'))
        return True

    ctx.ui.debug('A = %s' % str(A))

    if not ctx.config.get_option('ignore_dependency'):
        G_f, order = plan_upgrade(A, replaces=replaces)
    else:
        G_f = None
        order = list(A)

    componentdb = pisi.db.componentdb.ComponentDB()

    # Bug 4211
    if componentdb.has_component('system.base'):
        order = operations.helper.reorder_base_packages(order)

    ctx.ui.status(_('The following packages will be upgraded:'))
    ctx.ui.info(util.format_by_columns(sorted(order)))

    total_size, cached_size = operations.helper.calculate_download_sizes(order)
    total_size, symbol = util.human_readable_size(total_size)
    ctx.ui.info(util.colorize(_('Total size of package(s): %.2f %s') % (total_size, symbol), "yellow"))

    needs_confirm = check_update_actions(order)

    if set(order) - A_0 - set(pisi.util.flatten_list(replaces.values())):
        ctx.ui.warning(_("There are extra packages due to dependencies."))
        needs_confirm = True

    if ctx.get_option('dry_run'):
        return

    if needs_confirm and \
            not ctx.ui.confirm(_("Do you want to continue?")):
        return False

    ctx.ui.notify(ui.packagestogo, order=order)

    conflicts = []
    if not ctx.get_option('ignore_package_conflicts'):
        conflicts = operations.helper.check_conflicts(order, packagedb)

    paths = []
    for x in order:
        ctx.ui.info(util.colorize(_("Downloading %d / %d") % (order.index(x) + 1, len(order)), "yellow"))
        install_op = atomicoperations.Install.from_name(x)
        paths.append(install_op.package_fname)

    # fetch to be upgraded packages but do not install them.
    if ctx.get_option('fetch_only'):
        return

    if conflicts:
        operations.remove.remove_conflicting_packages(conflicts)

    operations.remove.remove_obsoleted_packages()

    for path in paths:
        ctx.ui.info(util.colorize(_("Installing %d / %d") % (paths.index(path) + 1, len(paths)), "yellow"))
        install_op = atomicoperations.Install(path, ignore_file_conflicts=True)
        install_op.install(not ctx.get_option('compare_sha1sum'))

def plan_upgrade(A, force_replaced=True, replaces=None):
    # FIXME: remove force_replaced
    # try to construct a pisi graph of packages to
    # install / reinstall

    packagedb = pisi.db.packagedb.PackageDB()

    G_f = pgraph.PGraph(packagedb)               # construct G_f

    A = set(A)

    if force_replaced:
        if replaces is None:
            replaces = packagedb.get_replaces()
        A |= set(pisi.util.flatten_list(replaces.values()))

    for x in A:
        G_f.add_package(x)

    installdb = pisi.db.installdb.InstallDB()

    def add_runtime_deps(pkg, Bp):
        for dep in pkg.runtimeDependencies():
            if installdb.has_package(dep.package) and dep.satisfied_by_installed():
                continue

            if dep.satisfied_by_repo():
                if dep.package not in G_f.vertices():
                    Bp.add(str(dep.package))

                G_f.add_dep(pkg.name, dep)
            else:
                ctx.ui.error(_('Dependency %s of %s cannot be satisfied') % (dep, pkg.name))
                raise Exception(_("Upgrade is not possible."))

    def add_resolvable_conflicts(pkg, Bp):
        """Try to resolve conflicts by upgrading"""

        for conflict in pkg.conflicts:
            if conflict.package in G_f.vertices():
                continue

            if not pisi.conflict.installed_package_conflicts(conflict):
                continue

            if not packagedb.has_package(conflict.package):
                continue

            new_pkg = packagedb.get_package(conflict.package)
            if conflict.satisfies_relation(new_pkg.version, new_pkg.release):
                continue

            Bp.add(conflict.package)
            G_f.add_package(conflict.package)

    def add_broken_rev_deps(pkg, Bp):
        """Add broken reverse dependencies if possible"""

        for rdep in pkg.reverseDependencies():
            if rdep.package in G_f.vertices():
                continue

            if not installdb.has_package(rdep.package):
                continue

            if pisi.conflict.installed_package_conflicts(pkg):
                Bp.add(pkg.name)

            G_f.add_dep(rdep.package, pkg)

    Bp = set()
    for x in A:
        pkg = packagedb.get_package(x)

        add_runtime_deps(pkg, Bp)
        add_resolvable_conflicts(pkg, Bp)
        add_broken_rev_deps(pkg, Bp)

    if Bp:
        ctx.ui.warning(_('The following packages will be upgraded too:'))
        ctx.ui.info(util.format_by_columns(sorted(Bp)))

    return G_f, list(A)

def upgrade_base(A):
    """returns additional packages that need to be upgraded"""
    base = []
    if ctx.config.get_option('upgrade_base'):
        base += [pkg for pkg in ctx.const.base if not pkg in A and pisi.db.installdb.InstallDB().has_package(pkg)]
    return base
