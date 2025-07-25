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

"""
generic file abstraction that allows us to use URIs for everything
we support only the simple read case ATM
we are just encapsulating a common pattern in our program, nothing big.
like all pisi classes, it has been programmed in a non-restrictive way
"""

import os
import shutil

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext

import pisi
import pisi.uri
import pisi.util
import pisi.fetcher
import pisi.context as ctx

class AlreadyHaveException(Exception):
    def __init__(self, url, localfile):
        Exception.__init__(self, _("URL %s already downloaded as %s")
                                      % (url, localfile))
        self.url = url
        self.localfile = localfile

class NoSignatureFound(Exception):
    def __init__(self, url):
        Exception.__init__(self, _("No signature found for %s") % url)
        self.url = url

class Error(Exception):
    pass

class InvalidSignature(Error):
    def __init__(self, url):
        Exception.__init__(self, _(" invalid for %s") % url)
        self.url = url

class File:

    # Compression types
    COMPRESSION_TYPE_AUTO = 0
    COMPRESSION_TYPE_BZ2 = 1
    COMPRESSION_TYPE_XZ = 2

    (read, write) = range(2)            # modes
    (detached, whatelse) = range(2)

    __compressed_file_extensions = {".xz": COMPRESSION_TYPE_XZ,
                                    ".bz2": COMPRESSION_TYPE_BZ2}

    @staticmethod
    def make_uri(uri):
        "handle URI arg"
        if isinstance(uri, str):
            uri = pisi.uri.URI(uri)
        elif not isinstance(uri, pisi.uri.URI):
            raise Error(_("uri must have type either URI or string"))
        return uri

    @staticmethod
    def choose_method(filename, compress):
        if compress == File.COMPRESSION_TYPE_AUTO:
            for ext, method in File.__compressed_file_extensions.items():
                if filename.endswith(ext):
                    return method

            return None
        else:
            return compress

    @staticmethod
    def is_compressed(filename):
        return filename.endswith(tuple(File.__compressed_file_extensions))

    @staticmethod
    def decompress(localfile, compress):
        compress = File.choose_method(localfile, compress)
        if compress == File.COMPRESSION_TYPE_XZ:
            import lzma
            open(localfile[:-3], "w").write(lzma.LZMAFile(localfile).read().decode())
            localfile = localfile[:-3]
        elif compress == File.COMPRESSION_TYPE_BZ2:
            import bz2
            open(localfile[:-4], "w").write(bz2.BZ2File(localfile).read().decode())
            localfile = localfile[:-4]
        return localfile

    @staticmethod
    def download(uri, transfer_dir = "/tmp", sha1sum = False,
                 compress = None, sign = None, copylocal = False):

        assert isinstance(uri, pisi.uri.URI)

        pisi.util.ensure_dirs(transfer_dir)

        # Check file integrity before saving?
        check_integrity = sha1sum or sign

        origfile = pisi.util.join_path(transfer_dir, uri.filename())

        if sha1sum:
            sha1filename = File.download(pisi.uri.URI(uri.get_uri() + '.sha1sum'), transfer_dir)
            sha1f = open(sha1filename)
            newsha1 = sha1f.read().split("\n")[0]

        if uri.is_remote_file() or copylocal:
            tmpfile = check_integrity and uri.filename() + ctx.const.temporary_suffix
            localfile = pisi.util.join_path(transfer_dir, tmpfile or uri.filename())

            if sha1sum and os.path.exists(origfile):
                oldsha1 = pisi.util.sha1_file(origfile)
                if (newsha1 == oldsha1):
                    # early terminate, we already got it ;)
                    raise AlreadyHaveException(uri, origfile)

            if uri.is_remote_file():
                ctx.ui.info(_("Fetching %s") % uri.get_uri(), verbose=True)
                pisi.fetcher.fetch_url(uri, transfer_dir, ctx.ui.Progress, tmpfile)
            else:
                ctx.ui.info(_("Copying %s to transfer dir") % uri.get_uri(), verbose=True)
                shutil.copy(uri.get_uri(), localfile)
        else:
            localfile = uri.get_uri()
            if not os.path.exists(localfile):
                raise IOError(_("File '%s' not found.") % localfile)
            if not os.access(localfile, os.W_OK):
                oldfn = localfile
                localfile = pisi.util.join_path(transfer_dir, os.path.basename(localfile))
                shutil.copy(oldfn, localfile)

        def clean_temporary():
            temp_files = []
            if sha1sum:
                temp_files.append(sha1filename)
            if check_integrity:
                temp_files.append(localfile)
            for filename in temp_files:
                try:
                    os.unlink(filename)
                except OSError:
                    pass

        if sha1sum:
            if (pisi.util.sha1_file(localfile) != newsha1):
                clean_temporary()
                raise Error(_("File integrity of %s compromised.") % uri)

        if check_integrity:
            shutil.move(localfile, origfile)
            localfile = origfile

        localfile = File.decompress(localfile, compress)

        return localfile


    def __init__(self, uri, mode, transfer_dir = "/tmp",
                 sha1sum = False, compress = None, sign = None):
        "it is pointless to open a file without a URI and a mode"

        self.transfer_dir = transfer_dir
        self.sha1sum = sha1sum
        self.compress = compress
        self.sign = sign

        uri = File.make_uri(uri)
        if mode==File.read or mode==File.write:
            self.mode = mode
        else:
            raise Error(_("File mode must be either File.read or File.write"))
        if uri.is_remote_file():
            if self.mode == File.read:
                localfile = File.download(uri, transfer_dir, sha1sum, compress, sign)
            else:
                raise Error(_("Remote write not implemented"))
        else:
            localfile = uri.get_uri()
            if self.mode == File.read:
                localfile = File.decompress(localfile, self.compress)

        if self.mode == File.read:
            access = 'r'
        else:
            access = 'w'
        self.__file__ = open(localfile, access)
        self.localfile = localfile

    def local_file(self):
        "returns the underlying file object"
        return self.__file__

    def close(self, delete_transfer = False):
        "this method must be called at the end of operation"
        self.__file__.close()
        if self.mode == File.write:
            compressed_files = []
            ctypes = self.compress or 0
            if ctypes & File.COMPRESSION_TYPE_XZ:
                import lzma
                compressed_file = self.localfile + ".xz"
                compressed_files.append(compressed_file)
                options = {"level": 9}
                lzma_file = lzma.LZMAFile(compressed_file, "w",
                                          options=options)
                lzma_file.write(open(self.localfile, "r").read().encode())
                lzma_file.close()

            if ctypes & File.COMPRESSION_TYPE_BZ2:
                import bz2
                compressed_file = self.localfile + ".bz2"
                compressed_files.append(compressed_file)
                bz2.BZ2File(compressed_file, "w").write(open(self.localfile, "r").read().encode())

            if self.sha1sum:
                sha1 = pisi.util.sha1_file(self.localfile)
                cs = open(self.localfile + '.sha1sum', 'w')
                cs.write(sha1)
                cs.close()
                for compressed_file in compressed_files:
                    sha1 = pisi.util.sha1_file(compressed_file)
                    cs = open(compressed_file + '.sha1sum', 'w')
                    cs.write(sha1)
                    cs.close()

            if self.sign==File.detached:
                if pisi.util.run_batch('gpg --detach-sig ' + self.localfile)[0]:
                    raise Error(_("ERROR: gpg --detach-sig %s failed") % self.localfile)
                for compressed_file in compressed_files:
                    if pisi.util.run_batch('gpg --detach-sig ' + compressed_file)[0]:
                        raise Error(_("ERROR: gpg --detach-sig %s failed") % compressed_file)

    @staticmethod
    def check_signature(uri, transfer_dir, sign=detached):
        if sign==File.detached:
            try:
                sigfilename = File.download(pisi.uri.URI(uri + '.sig'), transfer_dir)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                raise NoSignatureFound(uri)
            if os.system('gpg --verify ' + sigfilename) != 0:
                raise InvalidSignature(uri)

    def flush(self):
        self.__file__.flush()

    def fileno(self):
        return self.__file__.fileno()

    def isatty(self):
        return self.__file__.isatty()

    def __next__(self):
        return next(self.__file__)

    def read(self, size = None):
        if size:
            return self.__file__.read(size)
        else:
            return self.__file__.read()

    def readline(self, size = None):
        if size:
            return self.__file__.readline(size)
        else:
            return self.__file__.readline()

    def readlines(self, size = None):
        if size:
            return self.__file__.readlines(size)
        else:
            return self.__file__.readlines()

    def seek(self, offset, whence=0):
        self.__file__.seek(offset, whence)

    def tell(self):
        return self.__file__.tell()

    def truncate(self):
        self.__file__.truncate()

    def write(self, string):
        self.__file__.write(string)

    def writelines(self, sequence):
        self.__file__.writelines(sequence)
