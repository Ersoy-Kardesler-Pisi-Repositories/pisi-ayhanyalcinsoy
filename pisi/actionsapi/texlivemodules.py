# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.

# Standard python modules
import os
import glob
import shutil
import shlex
import gettext
from pathlib import Path

__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

# Pisi Modules
import pisi.context as ctx
import pisi.actionsapi
from pisi.actionsapi import get
from pisi.actionsapi.shelltools import *
from pisi.actionsapi.pisitools import dodoc, dodir, domove, dosym, insinto, removeDir

WorkDir = f"{get.srcNAME()}-{get.srcVERSION().split('_')[-1]}"

class CompileError(pisi.actionsapi.Error):
    def __init__(self, value=''):
        super().__init__(value)
        self.value = value
        ctx.ui.error(value)

class InstallError(pisi.actionsapi.Error):
    def __init__(self, value=''):
        super().__init__(value)
        self.value = value
        ctx.ui.error(value)

class RunTimeError(pisi.actionsapi.Error):
    def __init__(self, value=''):
        super().__init__(value)
        self.value = value
        ctx.ui.error(value)

def compile(parameters=''):
    '''Compiling texlive packages'''

    # Move sources according to tlpkg files
    if move_sources():
        raise CompileError(_('Moving source files failed'))

    # Generate config files
    if generate_config_files():
        raise CompileError(_('Generate config files failed'))

    # Build format files
    if build_format_files():
        raise CompileError(_('Building format files failed'))

def install(parameters=''):
    '''Installing texlive packages'''

    # Create symlinks from format to engines
    if create_symlinks_format_to_engines():
        raise InstallError(_('Creating symlinks from format to engines failed'))

    # Install documentation files
    if install_doc_files():
        raise InstallError(_('Installing docs failed'))

    # Install texmf, texmf-dist, tlpkg, texmf-var
    if install_texmf_files():
        raise InstallError(_('Installing texmf files failed'))

    # Install configuration files
    if install_config_files():
        raise InstallError(_('Installing config files failed'))

    # Handle configuration files
    if handle_config_files():
        raise InstallError(_('Handling config files failed'))

def create_symlinks_format_to_engines():
    '''Create symlinks from format to engines'''
    for formatfile in Path(f"{get.curDIR()}/texmf/fmtutil").glob("format*.cnf"):
        with formatfile.open("r") as symfile:
            for line in symfile:
                if not line.startswith("#"):
                    symbin = line.split()
                    if "cont-" in symbin[0] or "metafun" in symbin[0] or "mptopdf" in symbin[0]:
                        ctx.ui.info(_('Symlink %s skipped (special case)') % symbin[0])
                    elif "mf" in symbin[0]:
                        ctx.ui.info(_('Symlink %s -> %s skipped (texlive-core takes care of it.)') % (symbin[0], symbin[1]))
                    else:
                        if symbin[0] == symbin[1]:
                            ctx.ui.info(_('Symlink %s -> %s skipped.') % (symbin[0], symbin[1]))
                        elif can_access_file(f"{get.installDIR()}/usr/bin/{symbin[0]}"):
                            ctx.ui.info(_('Symlink %s skipped (file exists.)') % symbin[0])
                        else:
                            ctx.ui.info(_('Making symlink from %s to %s') % (symbin[0], symbin[1]))
                            dodir("/usr/bin")
                            sym(symbin[1], f"{get.installDIR()}/usr/bin/{symbin[0]}")

def install_doc_files():
    '''Installing docs'''
    if "documentation" in get.srcNAME():
        if Path(f"{get.curDIR()}/texmf-doc").is_dir():
            shutil.copytree(f"{get.curDIR()}/texmf-doc", f"{get.installDIR()}/usr/share/texmf-doc")
    else:
        for removedir in ["texmf", "texmf-dist"]:
            doc_path = Path(f"{get.curDIR()}/{removedir}/doc")
            if doc_path.is_dir():
                shutil.rmtree(doc_path)

def install_texmf_files():
    '''Installing texmf, texmf-dist, tlpkg, texmf-var'''
    for installdoc in ["texmf", "texmf-dist", "tlpkg", "texmf-var"]:
        installdoc_path = Path(f"{get.curDIR()}/{installdoc}")
        if installdoc_path.is_dir():
            if installdoc != "texmf-var":
                shutil.copytree(installdoc_path, f"{get.installDIR()}/usr/share/{installdoc}")
            else:
                shutil.copytree(installdoc_path, f"{get.installDIR()}/var/lib/texmf")

def install_config_files():
    '''Installing config files'''
    src_name = get.srcNAME()
    for config_file in [
        f"{src_name}.cfg",
        f"{src_name}-config.ps",
        f"{src_name}-config",
        f"language.{src_name}.def",
        f"language.{src_name}.dat"
    ]:
        if can_access_file(f"{get.curDIR()}/{config_file}"):
            target_dir = {
                f"{src_name}.cfg": "/etc/texmf/updmap.d",
                f"{src_name}-config.ps": "/etc/texmf/dvips.d",
                f"{src_name}-config": "/etc/texmf/dvipdfm/config",
                f"language.{src_name}.def": "/etc/texmf/language.def.d",
                f"language.{src_name}.dat": "/etc/texmf/language.dat.d",
            }[config_file]
            insinto(target_dir, f"{get.curDIR()}/{config_file}")

def handle_config_files():
    '''Handling config files'''
    for root, dirs, files in os.walk(f"{get.installDIR()}/usr/share/texmf"):
        if not ("config" in root or "doc" in root):
            for config_file in files:
                if config_file.endswith(("cfg", "cnf")):
                    dirname = Path(root).name
                    config_dir = f"{get.installDIR()}/etc/texmf/{dirname}.d"
                    if not os.path.isdir(config_dir):
                        ctx.ui.info(_('Creating %s') % config_dir)
                        dodir(config_dir)
                    ctx.ui.info(_('Moving (and symlinking) /usr/share/texmf/%s to %s.d') % (config_file, dirname))
                    domove(f"/usr/share/texmf/{dirname}/{config_file}", config_dir)
                    dosym(f"{config_dir}/{config_file}", f"/usr/share/texmf/{dirname}/{config_file}")

def add_format(parameters):
    '''Add format files'''
    fmtutil_dir = Path(f"{get.curDIR()}/texmf/fmtutil")
    fmtutil_dir.mkdir(exist_ok=True)

    cnf_file_path = fmtutil_dir / f"format.{get.srcNAME()}.cnf"
    if not cnf_file_path.is_file():
        with cnf_file_path.open("w") as cnf_file:
            cnf_file.write(f"# Generated for {get.srcNAME()} by actionsapi/texlivemodules.py\n")

    parameters = " ".join(parameters.split())  # Removing white-space characters
    parameters = shlex.split(parameters)  # Split parameters until the value "option"

    para_dict = {}
    for option in parameters:
        pair = option.strip().split("=", 1)  # Split just once
        if len(pair) == 2:
            para_dict[pair[0]] = pair[1]
            if pair[0] == "patterns" and pair[1] == '':
                para_dict["patterns"] = '-'
            elif pair[0] != 'patterns':
                para_dict["patterns"] = '-'

    with cnf_file_path.open('a') as cnf_file:
        cnf_file.write(f"{para_dict['name']}\t{para_dict['engine']}\t{para_dict['patterns']}\t{para_dict['options']}\n")

def move_sources():
    reloc = "texmf-dist"

    for tlpobjfile in os.listdir("tlpkg/tlpobj/"):
        with open(f"tlpkg/tlpobj/{tlpobjfile}", "r") as jobsfile:
            for line in jobsfile:
                if "RELOC" in line:
                    path = line.split("/", 1)[-1].strip()
                    dirname = os.path.dirname(path)
                    if not os.path.isdir(f"{reloc}/{dirname}"):
                        os.makedirs(f"{reloc}/{dirname}", exist_ok=True)
                    shutil.move(path, f"{reloc}/{dirname}")

def build_format_files():
    '''Build format files'''
    fmtutil_dir = Path(f"{get.curDIR()}/texmf/fmtutil/")
    if fmtutil_dir.is_dir():
        for formatfile in fmtutil_dir.glob("format*.cnf"):
            web2c_dir = Path(f"{get.curDIR()}/texmf-var/web2c/")
            web2c_dir.mkdir(parents=True, exist_ok=True)
            ctx.ui.info(_('Building format file %s') % formatfile)
            export("TEXMFHOME", f"{get.curDIR()}/texmf:/%stexmf-dist:{get.curDIR()}/texmf-var")
            export("VARTEXFONTS", "fonts")
            system(f"env -u TEXINPUTS fmtutil --cnffile {formatfile} --fmtdir {web2c_dir} --all")

def add_language_dat(parameter):
    '''Create language.*.dat files'''
    para_dict = {key: value for key, value in (opt.split("=") for opt in parameter.split()) if "=" in opt}

    # Using 'with' statement to ensure the file is properly closed after writing
    with open(f'{get.curDIR()}/language.{get.srcNAME()}.dat', 'a') as language_dat:
        language_dat.write(f"{para_dict['name']}\t{para_dict['file']}\n")

        if "synonyms" in para_dict:
            language_dat.write(f"={para_dict['synonyms']}\n")

import os
from pathlib import Path
import gettext

__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

def add_language_def(parameter):
    '''Create language.*.def files'''
    # Split the parameters and build a dictionary from them
    para_dict = dict(pair.split("=") for pair in parameter.split() if "=" in pair)

    # Set defaults for lefthyphenmin and righthyphenmin if they are not provided
    para_dict.setdefault("lefthyphenmin", "2")
    para_dict.setdefault("righthyphenmin", "3")

    # Using context manager for file handling
    def_file_path = Path(f"{get.curDIR()}/language.{get.srcNAME()}.def")
    with open(def_file_path, 'a') as language_def:
        language_def.write("\\addlanguage{%s}{%s}{}{%s}{%s}\n" % (
            para_dict["name"],
            para_dict["file"],
            para_dict["lefthyphenmin"],
            para_dict["righthyphenmin"],
        ))

        if "synonyms" in para_dict:
            language_def.write("\\addlanguage{%s}{%s}{}{%s}{%s}\n" % (
                para_dict["synonyms"],
                para_dict["file"],
                para_dict["lefthyphenmin"],
                para_dict["righthyphenmin"],
            ))

def generate_config_files():
    '''Generate config files'''
    for tlpobjfile in ls(f"{get.curDIR()}/tlpkg/tlpobj/*"):
        with open(tlpobjfile, 'r') as jobsfile:
            for line in jobsfile:
                splitline = line.split(" ", 2)
                if splitline[0] == "execute":
                    command = splitline[1]
                    parameter = splitline[2].strip()
                    handle_command(command, parameter)

def handle_command(command, parameter):
    '''Handle commands for generating config files'''
    if command == "addMap":
        echo(f"{get.curDIR()}/{get.srcNAME()}.cfg", f"Map {parameter}")
        ctx.ui.info(_('Map %s is added to %s/%s.cfg') % (parameter, get.curDIR(), get.srcNAME()))
    elif command == "addMixedMap":
        echo(f"{get.curDIR()}/{get.srcNAME()}.cfg", f"MixedMap {parameter}")
        ctx.ui.info(_('MixedMap %s is added to %s/%s.cfg') % (parameter, get.curDIR(), get.srcNAME()))
    elif command == "addDvipsMap":
        echo(f"{get.curDIR()}/{get.srcNAME()}-config.ps", f"p +{parameter}")
        ctx.ui.info(_('p +%s is added to %s/%s-config.ps') % (parameter, get.curDIR(), get.srcNAME()))
    elif command == "addDvipdfmMap":
        echo(f"{get.curDIR()}/{get.srcNAME()}-config", f"f {parameter}")
        ctx.ui.info(_('f %s is added to %s/%s-config') % (parameter, get.curDIR(), get.srcNAME()))
    elif command == "AddHyphen":
        addLanguageDat(parameter)
        add_language_def(parameter)
    elif command == "AddFormat":
        addFormat(parameter)
    elif command == "BuildFormat":
        ctx.ui.info(_('Language file %s already generated.') % parameter)
    elif command == "BuildLanguageDat":
        ctx.ui.info(_('No rule to process %s. Please file a bug.') % command)


