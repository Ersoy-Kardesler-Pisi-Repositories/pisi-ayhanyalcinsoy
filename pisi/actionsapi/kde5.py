# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.

# ActionsAPI Modules
from pisi.actionsapi import get
from pisi.actionsapi import cmaketools
from pisi.actionsapi import shelltools

basename = "kde5"

prefix = "/{}".format(get.defaultprefixDIR())
libdir = "{}/lib".format(prefix)
bindir = "{}/bin".format(prefix)
libexecdir = "{}/lib".format(prefix)
iconsdir = "{}/share/icons".format(prefix)
applicationsdir = "{}/share/applications/{}".format(prefix, basename)
mandir = "/{}".format(get.manDIR())
sharedir = "{}/share".format(prefix)
localedir = "{}/share/locale".format(prefix)
qmldir = "{}/lib/qt5/qml".format(prefix)
plugindir = "{}/lib/qt5/plugins".format(prefix)
moduledir = "{}/lib/qt5/mkspecs/modules".format(prefix)
pythondir = "{}/bin/python".format(prefix)
appsdir = "{}".format(sharedir)
sysconfdir = "/etc"
configdir = "{}/xdg".format(sysconfdir)
servicesdir = "{}/services".format(sharedir)
servicetypesdir = "{}/servicetypes".format(sharedir)
includedir = "{}/include".format(prefix)
docdir = "/{}/{}".format(get.docDIR(), basename)
htmldir = "{}/html".format(docdir)
wallpapersdir = "{}/share/wallpapers".format(prefix)

def configure(parameters='', installPrefix=prefix, sourceDir='..'):
    ''' parameters -DLIB_INSTALL_DIR="hede" -DSOMETHING_USEFUL=1'''

    shelltools.makedirs("build")
    shelltools.cd("build")

    cmaketools.configure("-DCMAKE_BUILD_TYPE=Release \
                          -DKDE_INSTALL_LIBEXECDIR={} \
                          -DCMAKE_INSTALL_LIBDIR=lib \
                          -DKDE_INSTALL_USE_QT_SYS_PATHS=ON \
                          -DKDE_INSTALL_QMLDIR={} \
                          -DKDE_INSTALL_SYSCONFDIR={} \
                          -DKDE_INSTALL_PLUGINDIR={} \
                          -DECM_MKSPECS_INSTALL_DIR={} \
                          -DBUILD_TESTING=OFF \
                          -DKDE_INSTALL_LIBDIR=lib \
                          -Wno-dev \
                          -DCMAKE_INSTALL_PREFIX={} {}".format(libexecdir, qmldir, sysconfdir, plugindir, moduledir, prefix, parameters), installPrefix, sourceDir)

    shelltools.cd("..")

def make(parameters=''):
    cmaketools.make('-C build {}'.format(parameters))

def install(parameters='', argument='install'):
    cmaketools.install('-C build {}'.format(parameters), argument)
