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

"""Archive module provides access to regular archive file types."""

# standard library modules
import os
import stat
import errno
import shutil
import tarfile
import zipfile

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

# PiSi modules
import pisi
import pisi.util as util
import pisi.context as ctx


class UnknownArchiveType(Exception):
    pass

class ArchiveHandlerNotInstalled(Exception):
    pass


# Proxy class inspired from tarfile._BZ2Proxy
class _LZMAProxy:

    blocksize = 16 * 1024

    def __init__(self, fileobj, mode):
        self.fileobj = fileobj
        self.mode = mode
        self.name = getattr(self.fileobj, "name", None)
        self.init()

    def init(self):
        import lzma
        self.pos = 0
        if self.mode == "r":
            self.lzmaobj = lzma.LZMADecompressor()
            self.buf = b""  # Use bytes for compatibility
        else:
            self.lzmaobj = lzma.LZMACompressor()

    def read(self, size):
        b = [self.buf]
        x = len(self.buf)
        while x < size:
            raw = self.fileobj.read(self.blocksize)
            if not raw:
                break
            try:
                data = self.lzmaobj.decompress(raw)
            except EOFError:
                break
            b.append(data)
            x += len(data)
        self.buf = b''.join(b)  # Use bytes join

        buf = self.buf[:size]
        self.buf = self.buf[size:]
        self.pos += len(buf)
        return buf

    def seek(self, pos):
        if pos < self.pos:
            self.init()
        self.read(pos - self.pos)

    def tell(self):
        return self.pos

    def write(self, data):
        self.pos += len(data)
        raw = self.lzmaobj.compress(data)
        self.fileobj.write(raw)

    def close(self):
        if self.mode == "w":
            raw = self.lzmaobj.flush()
            self.fileobj.write(raw)


class TarFile(tarfile.TarFile):

    @classmethod
    def lzmaopen(cls,
                 name=None,
                 mode="r",
                 fileobj=None,
                 compressformat="xz",
                 compresslevel=9,
                 **kwargs):
        """Open lzma/xz compressed tar archive name for reading or writing.
           Appending is not allowed.
        """

        if len(mode) > 1 or mode not in "rw":
            raise ValueError("mode must be 'r' or 'w'.")

        try:
            import lzma
        except ImportError:
            raise tarfile.CompressionError("lzma module is not available")

        if fileobj is not None:
            fileobj = _LZMAProxy(fileobj, mode)
        else:
            options = {"format": compressformat,
                       "level": compresslevel}
            fileobj = lzma.LZMAFile(name, mode, options=options)

        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except IOError:
            raise tarfile.ReadError("not a lzma file")
        t._extfileobj = False
        return t


class ArchiveBase:
    """Base class for Archive classes."""
    def __init__(self, file_path, atype):
        self.file_path = file_path
        self.type = atype

    def unpack(self, target_dir, clean_dir=False):
        self.target_dir = target_dir
        # first we check if we need to clean-up our working env.
        if os.path.exists(self.target_dir):
            if clean_dir:
                util.clean_dir(self.target_dir)

        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)


class ArchiveBinary(ArchiveBase):
    """ArchiveBinary handles binary archive files (usually distributed as
    .bin files)"""
    def __init__(self, file_path, arch_type="binary"):
        super().__init__(file_path, arch_type)

    def unpack(self, target_dir, clean_dir=False):
        super().unpack(target_dir, clean_dir)

        # we can't unpack .bin files. we'll just move them to target
        # directory and leave the dirty job to actions.py ;)
        target_file = os.path.join(target_dir,
                                    os.path.basename(self.file_path))
        shutil.copyfile(self.file_path, target_file)


class ArchiveBzip2(ArchiveBase):
    """ArchiveBzip2 handles Bzip2 archive files"""

    def __init__(self, file_path, arch_type="bz2"):
        super().__init__(file_path, arch_type)

    def unpack(self, target_dir, clean_dir=False):
        super().unpack(target_dir, clean_dir)
        self.unpack_dir(target_dir)

    def unpack_dir(self, target_dir):
        """Unpack Bzip2 archive to a given target directory(target_dir)."""

        output_path = util.join_path(target_dir,
                                      os.path.basename(self.file_path))
        if output_path.endswith(".bz2"):
            output_path = output_path[:-4]

        import bz2
        with bz2.open(self.file_path, "rb") as bz2_file:
            with open(output_path, "wb") as output:  # Use "wb" for binary writing
                output.write(bz2_file.read())


class ArchiveGzip(ArchiveBase):
    """ArchiveGzip handles Gzip archive files"""

    def __init__(self, file_path, arch_type="gz"):
        super().__init__(file_path, arch_type)

    def unpack(self, target_dir, clean_dir=False):
        super().unpack(target_dir, clean_dir)
        self.unpack_dir(target_dir)

    def unpack_dir(self, target_dir):
        """Unpack Gzip archive to a given target directory(target_dir)."""

        output_path = util.join_path(target_dir,
                                      os.path.basename(self.file_path))
        if output_path.endswith(".gz"):
            output_path = output_path[:-3]

        import gzip
        with gzip.open(self.file_path, "rb") as gzip_file:
            with open(output_path, "wb") as output:  # Use "wb" for binary writing
                output.write(gzip_file.read())


class ArchiveLzma(ArchiveBase):
    """ArchiveLzma handles LZMA archive files"""

    def __init__(self, file_path, arch_type="lzma"):
        super().__init__(file_path, arch_type)

    def unpack(self, target_dir, clean_dir=False):
        super().unpack(target_dir, clean_dir)
        self.unpack_dir(target_dir)

    def unpack_dir(self, target_dir):
        """Unpack LZMA archive to a given target directory(target_dir)."""

        output_path = util.join_path(target_dir,
                                      os.path.basename(self.file_path))
        ext = ".lzma" if self.type == "lzma" else ".xz"
        if output_path.endswith(ext):
            output_path = output_path[:-len(ext)]

        import lzma
        with lzma.open(self.file_path, "rb") as lzma_file:
            with open(output_path, "wb") as output:  # Use "wb" for binary writing
                output.write(lzma_file.read())

class ArchiveTar(ArchiveBase):
    """ArchiveTar handles tar archives depending on the compression
    type. Provides access to tar, tar.gz and tar.bz2 files.

    This class provides the unpack magic for tar archives."""
    def __init__(self, file_path=None, arch_type="tar",
                 no_same_permissions=True,
                 no_same_owner=True,
                 fileobj=None):
        super(ArchiveTar, self).__init__(file_path, arch_type)
        self.tar = None
        self.no_same_permissions = no_same_permissions
        self.no_same_owner = no_same_owner
        self.fileobj = fileobj

    def unpack(self, target_dir, clean_dir=False):
        """Unpack tar archive to a given target directory(target_dir)."""
        super(ArchiveTar, self).unpack(target_dir, clean_dir)
        self.unpack_dir(target_dir)

    def unpack_dir(self, target_dir, callback=None):
        rmode = ""
        self.tar = None
        if self.type == 'tar':
            rmode = 'r:'
        elif self.type == 'targz':
            rmode = 'r:gz'
        elif self.type == 'tarbz2':
            rmode = 'r:bz2'
        elif self.type in ('tarlzma', 'tarxz'):
            self.tar = tarfile.lzmaopen(self.file_path, fileobj=self.fileobj)
        else:
            raise UnknownArchiveType()

        if self.tar is None:
            self.tar = tarfile.open(self.file_path, rmode, fileobj=self.fileobj)

        oldwd = None
        try:
            # Don't fail if CWD doesn't exist (#6748)
            oldwd = os.getcwd()
        except OSError:
            pass
        os.chdir(target_dir)

        uid = os.getuid()
        gid = os.getgid()

        for tarinfo in self.tar:
            if callback:
                callback(tarinfo, extracted=False)

            startservices = []
            if tarinfo.issym() and \
                    os.path.isdir(tarinfo.name) and \
                    not os.path.islink(tarinfo.name):
                # Changing a directory with a symlink. tarfile module
                # cannot handle this case.

                if os.path.isdir(tarinfo.linkname):
                    # Symlink target is a directory. Move old directory's
                    # content to this directory.
                    for filename in os.listdir(tarinfo.name):
                        old_path = util.join_path(tarinfo.name, filename)
                        new_path = util.join_path(tarinfo.linkname, filename)

                        if os.path.lexists(new_path):
                            if not os.path.isdir(new_path):
                                # A file with the same name exists in the
                                # target. Remove the one in the old directory.
                                os.remove(old_path)
                            continue

                        # try as up to this time
                        try:
                            os.renames(old_path, new_path)
                        except OSError as e:
                            # something gone wrong? [Errno 18] Invalid cross-device link?
                            # try in other way
                            if e.errno == errno.EXDEV:
                                if tarinfo.linkname.startswith(".."):
                                    new_path = util.join_path(os.path.normpath(os.path.join(os.path.dirname(tarinfo.name), tarinfo.linkname)), filename)
                                if not old_path.startswith("/"):
                                    old_path = "/" + old_path
                                if not new_path.startswith("/"):
                                    new_path = "/" + new_path
                                print("Moving:", old_path, " -> ", new_path)
                                os.system(f"mv -f {old_path} {new_path}")
                            else:
                                raise
                    try:
                        os.rmdir(tarinfo.name)
                    except OSError as e:
                        # hmmm, not empty dir? try rename it adding .old extension.
                        if e.errno == errno.ENOTEMPTY:
                            # if directory with dbus/pid file was moved we have to restart dbus
                            for (path, dirs, files) in os.walk(tarinfo.name):
                                if path.endswith("dbus") and "pid" in files:
                                    startservices.append("dbus")
                                    for service in ("NetworkManager", "connman", "wicd"):
                                        if os.path.isfile(f"/etc/mudur/services/enabled/{service}"):
                                            startservices.append(service)
                                            os.system(f"service {service} stop")
                                    os.system("service dbus stop")
                                    break
                            os.system(f"mv -f {tarinfo.name} {tarinfo.name}.old")
                        else:
                            raise

                elif not os.path.lexists(tarinfo.linkname):
                    # Symlink target does not exist. Assume the old
                    # directory is moved to another place in package.
                    os.renames(tarinfo.name, tarinfo.linkname)

                else:
                    # This should not happen. Probably a packaging error.
                    # Try to rename directory
                    try:
                        os.rename(tarinfo.name, f"{tarinfo.name}.renamed-by-pisi")
                    except:
                        # If fails, try to remove it
                        shutil.rmtree(tarinfo.name)

            try:
                self.tar.extract(tarinfo)
                for service in startservices: 
                    os.system(f"service {service} start")
            except OSError as e:
                # Handle the case where an upper directory cannot
                # be created because of a conflict with an existing
                # regular file or symlink. In this case, remove
                # the old file and retry extracting.

                if e.errno != errno.EEXIST:
                    raise

                # For the path "a/b/c", upper_dirs will be ["a", "a/b"].
                upper_dirs = []
                head, tail = os.path.split(tarinfo.name)

                while head and tail:
                    upper_dirs.insert(0, head)
                    head, tail = os.path.split(head)

                for path in upper_dirs:
                    if not os.path.lexists(path):
                        break

                    if not os.path.isdir(path):
                        # A file with the same name exists.
                        # Remove the existing file.
                        os.remove(path)
                        break
                else:
                    # No conflicts detected! This is probably not the case
                    # mentioned here. Raise the same exception.
                    raise

                # Try to extract again.
                self.tar.extract(tarinfo)

            except IOError as e:
                # Handle the case where new path is file, but old path is directory
                # due to not possible touch file c in /a/b if directory /a/b/c exists.
                if not e.errno == errno.EISDIR:
                    path = tarinfo.name
                    found = False
                    while path:
                        if os.path.isfile(path):
                            os.unlink(path)
                            found = True
                            break
                        else:
                            path = "/".join(path.split("/")[:-1])
                    if not found: 
                        raise
                    # Try to extract again.
                    self.tar.extract(tarinfo)
                else:
                    shutil.rmtree(tarinfo.name)
                    # Try to extract again.
                    self.tar.extract(tarinfo)

            # tarfile.extract does not honor umask. It must be honored
            # explicitly. See --no-same-permissions option of tar(1),
            # which is the default behaviour.
            #
            # Note: This is no good while installing a pisi package.
            # That's why this is optional.
            if self.no_same_permissions and not os.path.islink(tarinfo.name):
                os.chmod(tarinfo.name, tarinfo.mode & ~ctx.const.umask)

            if self.no_same_owner:
                if not os.path.islink(tarinfo.name):
                    os.chown(tarinfo.name, uid, gid)
                else:
                    os.lchown(tarinfo.name, uid, gid)

            if callback:
                callback(tarinfo, extracted=True)

        try:
            if oldwd:
                os.chdir(oldwd)
        # Bug #6748
        except OSError:
            pass
        self.close()

    def add_to_archive(self, file_name, arc_name=None):
        """Add file or directory path to the tar archive"""
        if not self.tar:
            if self.type == 'tar':
                wmode = 'w:'
            elif self.type == 'targz':
                wmode = 'w:gz'
            elif self.type == 'tarbz2':
                wmode = 'w:bz2'
            else:
                raise UnknownArchiveType()
            self.tar = tarfile.open(self.file_path, wmode)

        # Add file or directory to the archive
        self.tar.add(file_name, arcname=arc_name)
    
    def close(self):
        if self.tar is not None:
            self.tar.close()


class ArchiveZip(ArchiveBase):
    """ArchiveZip handles zip archives and provides access to zip
    files. This class provides the unpack magic for zip archives."""
    def __init__(self, file_path=None, arch_type="zip", fileobj=None):
        super(ArchiveZip, self).__init__(file_path, arch_type)
        self.fileobj = fileobj
        self.zip = None

    def unpack(self, target_dir, clean_dir=False):
        """Unpack zip archive to a given target directory(target_dir)."""
        super(ArchiveZip, self).unpack(target_dir, clean_dir)
        self.unpack_dir(target_dir)

    def unpack_dir(self, target_dir, callback=None):
        """Unpack zip archive."""
        self.zip = zipfile.ZipFile(self.file_path, 'r', self.fileobj)

        for zipinfo in self.zip.infolist():
            if callback:
                callback(zipinfo, extracted=False)

            if zipinfo.filename.endswith('/'):
                # Skip directories
                continue

            try:
                self.zip.extract(zipinfo, target_dir)
            except Exception as e:
                print(f"Error extracting {zipinfo.filename}: {e}")

            if callback:
                callback(zipinfo, extracted=True)

    def add_to_archive(self, file_name, arc_name=None):
        """Add file or directory path to the zip archive"""
        if self.zip is None:
            self.zip = zipfile.ZipFile(self.file_path, 'w')

        self.zip.write(file_name, arcname=arc_name)

    def close(self):
        if self.zip is not None:
            self.zip.close()


class Archive7z(ArchiveBase):
    """Archive7z handles 7z archives. This class provides the
    unpack magic for 7z archives."""
    def __init__(self, file_path=None, arch_type="7z"):
        super(Archive7z, self).__init__(file_path, arch_type)

    def unpack(self, target_dir, clean_dir=False):
        """Unpack 7z archive to a given target directory(target_dir)."""
        # Implement the unpack logic for 7z archives.
        pass  # Placeholder for actual unpacking logic

    def add_to_archive(self, file_name, arc_name=None):
        """Add file or directory path to the 7z archive"""
        # Implement the logic to add files to 7z archives.
        pass  # Placeholder for actual logic

    def close(self):
        pass  # Placeholder for actual close logic


class Archive(ArchiveBase):
    """Archive serves as a factory for creating archive instances
    based on the provided file extension."""
    def __new__(cls, *args, **kwargs):
        ext = os.path.splitext(args[0])[1].lower()
        if ext in ['.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.tar.lzma', '.tar.xz']:
            return super(Archive, cls).__new__(ArchiveTar)
        elif ext in ['.zip']:
            return super(Archive, cls).__new__(ArchiveZip)
        elif ext in ['.7z']:
            return super(Archive, cls).__new__(Archive7z)
        else:
            raise UnknownArchiveType()

