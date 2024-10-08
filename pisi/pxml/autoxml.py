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

"""
 autoxml is a metaclass for automatic XML translation, using
 a miniature type system. (w00t!) This is based on an excellent
 high-level XML processing prototype that Gurer prepared.

 Method names are mixedCase for compatibility with minidom,
 an old library.
"""

# System
import locale
import types
import sys
import inspect
import re
from io import StringIO  # Update for Python 3

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.gettext  # ugettext is gettext in Python 3

# PiSi
import pisi
import pisi.pxml.xmlext as xmlext
import pisi.pxml.xmlfile as xmlfile
import pisi.context as ctx
import pisi.util as util
import pisi.oo as oo

class Error(pisi.Error):
    pass

# requirement specs

mandatory, optional = range(2)  # poor man's enum

# basic types

String = str  # Python 3 uses str for both string and unicode
Text = str
Integer = int
Long = int  # Python 3 has no LongType
Float = float

class LocalText(dict):
    """Handles XML tags with localized text"""

    def __init__(self, tag="", req=optional):
        self.tag = tag
        self.req = req
        dict.__init__(self)

    def decode(self, node, errs, where=""):
        # flags, tag name, instance attribute
        assert self.tag != ''
        nodes = xmlext.getAllNodes(node, self.tag)
        if not nodes:
            if self.req == mandatory:
                errs.append(where + ': ' + _("At least one '%s' tag should have local text") %
                            self.tag)
        else:
            for node in nodes:
                lang = xmlext.getNodeAttribute(node, 'xml:lang')
                c = xmlext.getNodeText(node)
                if not c:
                    errs.append(where + ': ' + _("'%s' language of tag '%s' is empty") %
                                (lang, self.tag))
                # FIXME: check for dups and 'en'
                if not lang:
                    lang = 'en'
                self[lang] = c

    def encode(self, node, errs):
        assert self.tag != ''
        for key in self.keys():
            newnode = xmlext.addNode(node, self.tag)
            xmlext.setNodeAttribute(newnode, 'xml:lang', key)
            xmlext.addText(newnode, '', self[key])

    @staticmethod
    def get_lang():
        try:
            (lang, encoding) = locale.getlocale()
            if not lang:
                (lang, encoding) = locale.getdefaultlocale()
            if lang is None:  # C locale fallback
                return 'en'
            else:
                return lang[0:2]
        except KeyboardInterrupt:
            raise
        except Exception as e:  # Use Python 3 exception syntax
            raise Error(_('LocalText: unable to get either current or default locale'))

    def errors(self, where=str()):
        errs = []
        langs = [LocalText.get_lang(), 'en', 'tr']
        if self.keys() and not any(lambda x: x in self, langs):
            errs.append(where + ': ' + _("Tag should have at least the current locale, or failing that an English or Turkish version"))
        return errs

    def format(self, f, errs):
        L = LocalText.get_lang()
        if L in self:
            f.add_flowing_data(self[L])
        elif 'en' in self:
            f.add_flowing_data(self['en'])
        elif 'tr' in self:
            f.add_flowing_data(self['tr'])
        else:
            errs.append(_("Tag should have at least the current locale, or failing that an English or Turkish version"))

    # FIXME: factor out these common routines
    def print_text(self, file=sys.stdout):
        # Writer sınıfı yerine direkt dosyaya yazıyoruz
        w = Writer(file)  # Writer sınıfı, dosyaya yazmayı yönetir
        errs = []
        self.format(w, errs)  # Burada formatlama işlemi yapılıyor
        if errs:
            for x in errs:
                ctx.ui.warning(x)  # Hataları uyarı olarak gösterir

    def __str__(self):
        L = LocalText.get_lang()  # Dil seçimi
        if L in self:
            return str(self[L])  # Dil seçimine uygun metni döndür
        elif 'en' in self:
            # Fallback to English
            return str(self['en'])
        elif 'tr' in self:
            # Fallback to Turkish
            return str(self['tr'])
        else:
            return ""  # Boş string döndür

class Writer:
    """UTF-8 desteği sağlayan basit bir Writer sınıfı"""

    def __init__(self, file=None, maxcol=78):
        self.file = file if file is not None else sys.stdout  # Varsayılan olarak sys.stdout kullanılır
        self.maxcol = maxcol
        self.col = 0  # Sütun sayısı

    def send_literal_data(self, data):
        # Python 3'te stringler zaten Unicode, encode etmeye gerek yok
        self.file.write(data)  # Veriyi doğrudan yaz
        
        i = data.rfind('\n')  # Son satır sonunu bul
        if i >= 0:
            self.col = 0  # Yeni satıra geçildiğinde sütun sıfırlanır
            data = data[i+1:]
        
        data = data.expandtabs()  # Tab genişletme
        self.col += len(data)  # Sütun sayısını güncelle
        self.atbreak = 0  # Satır sonu bayrağı sıfırlanır

class autoxml(type):
    """High-level automatic XML transformation interface for xmlfile.
    
    The idea is to declare a class for each XML tag. Inside the
    class the tags and attributes nested in the tag are further
    elaborated. A simple example follows:

    class Employee:
         __metaclass__ = autoxml
         t_Name = [xmlfile.Text, xmlfile.mandatory]
         a_Type = [xmlfile.Integer, xmlfile.optional]

    This class defines a tag and an attribute nested in Employee
    class. Name is a string and type is an integer, called basic
    types. While the tag is mandatory, the attribute may be left out.
    """

    def __init__(cls, name, bases, dct):
        super(autoxml, cls).__init__(name, bases, dct)

        xmlfile_support = xmlfile.XmlFile in bases

        cls.autoxml_bases = list(filter(lambda base: isinstance(base, autoxml), bases))

        if 'tag' not in dct:
            cls.tag = name

        names = []
        inits = []
        decoders = []
        encoders = []
        errorss = []
        formatters = []

        try:
            fn = re.compile(r'\s*([tas]_[a-zA-Z]+).*').findall
            inspect.linecache.clearcache()
            lines = list(filter(fn, inspect.getsourcelines(cls)[0]))
            decl_order = list(map(lambda x: x.split()[0], lines))
        except IOError:
            decl_order = list(dct.keys())

        order = list(filter(lambda x: not x.startswith('s_'), decl_order))

        str_members = list(filter(lambda x: x.startswith('s_'), decl_order))
        if len(str_members) > 1:
            raise Error('Only one str member can be defined')
        elif len(str_members) == 1:
            order.insert(0, str_members[0])

        for var in order:
            if var.startswith('t_') or var.startswith('a_') or var.startswith('s_'):
                name = var[2:]
                if var.startswith('a_'):
                    x = autoxml.gen_attr_member(cls, name)
                elif var.startswith('t_'):
                    x = autoxml.gen_tag_member(cls, name)
                elif var.startswith('s_'):
                    x = autoxml.gen_str_member(cls, name)
                (name, init, decoder, encoder, errors, format_x) = x
                names.append(name)
                inits.append(init)
                decoders.append(decoder)
                encoders.append(encoder)
                errorss.append(errors)
                formatters.append(format_x)

        cls.initializers = inits

        def initialize(self, uri=None, keepDoc=False, tmpDir='/tmp', **args):
            if xmlfile_support:
                if 'tag' in args:
                    xmlfile.XmlFile.__init__(self, tag=args['tag'])
                else:
                    xmlfile.XmlFile.__init__(self, tag=cls.tag)
            for base in cls.autoxml_bases:
                base.__init__(self)
            for init in inits:
                init(self)
            for x in args.keys():
                setattr(self, x, args[x])
            if hasattr(self, 'init'):
                self.init(cls.tag)
            if xmlfile_support and uri:
                self.read(uri, keepDoc, tmpDir)

        cls.__init__ = initialize

        cls.decoders = decoders
        def decode(self, node, errs, where=str(cls.tag)):
            for base in cls.autoxml_bases:
                base.decode(self, node, errs, where)
            for decode_member in decoders:
                decode_member(self, node, errs, where)
            if hasattr(self, 'decode_hook'):
                self.decode_hook(node, errs, where)
        cls.decode = decode

        cls.encoders = encoders
        def encode(self, node, errs):
            for base in cls.autoxml_bases:
                base.encode(self, node, errs)
            for encode_member in encoders:
                encode_member(self, node, errs)
            if hasattr(self, 'encode_hook'):
                self.encode_hook(node, errs)
        cls.encode = encode

        cls.errorss = errorss
        def errors(self, where=str(cls.tag)):
            errs = []
            for base in cls.autoxml_bases:
                errs.extend(base.errors(self, where))
            for errors in errorss:
                errs.extend(errors(self, where))
            if hasattr(self, 'errors_hook'):
                errs.extend(self.errors_hook(where))
            return errs
        cls.errors = errors

        def check(self):
            errs = self.errors()
            if errs:
                errs.append("autoxml.check: '%s' errors" % len(errs))
                raise Error(*errs)
        cls.check = check

        cls.formatters = formatters
        def format(self, w, errs):
            for base in cls.autoxml_bases:
                self.base.format(w, errs)
            for formatter in formatters:
                self.formatter.format(w, errs)
        cls.format = format

        def print_text(self, file=sys.stdout):
            w = Writer(file)
            errs = []
            self.format(w, errs)
            if errs:
                for x in errs:
                    sys.stderr.write(x)
        cls.print_text = print_text

        if '__str__' not in dct:
            def __str__(self):
                strfile = io.StringIO()
                self.print_text(strfile)
                result = strfile.getvalue()
                strfile.close()
                return result
            cls.__str__ = __str__

        if '__eq__' not in dct:
            def __eq__(self, other):
                if other is None:
                    return False
                for name in names:
                    try:
                        if getattr(self, name) != getattr(other, name):
                            return False
                    except Exception as e:
                        return False
                return True

            def __ne__(self, other):
                return not self.__eq__(other)
            cls.__eq__ = __eq__
            cls.__ne__ = __ne__

        if xmlfile_support:
            def parse(self, xml, keepDoc=False):
                self.parsexml(xml)
                errs = []
                self.decode(self.rootNode(), errs)
                if errs:
                    errs.append("autoxml.parse: String '%s' has errors" % xml)
                    raise Error(*errs)
                if hasattr(self, 'read_hook'):
                    self.read_hook(errs)

                if not keepDoc:
                    self.unlink()

                errs = self.errors()
                if errs:
                    errs.append("autoxml.parse: String '%s' has errors" % xml)

            def read(self, uri, keepDoc=False, tmpDir='/tmp', sha1sum=False, compress=None, sign=None, copylocal=False, nodecode=False):
                read_xml = self.readxml(uri, tmpDir, sha1sum=sha1sum, compress=compress, sign=sign, copylocal=copylocal)

                if nodecode:
                    return read_xml

                errs = []
                self.decode(self.rootNode(), errs)
                if errs:
                    errs.append("autoxml.read: File '%s' has errors" % uri)
                    raise Error(*errs)
                if hasattr(self, 'read_hook'):
                    self.read_hook(errs)

                if not keepDoc:
                    self.unlink()

                errs = self.errors()
                if errs:
                    errs.append("autoxml.read: File '%s' has errors" % uri)
                    raise Error(*errs)

            def write(self, uri, keepDoc=False, tmpDir='/tmp', sha1sum=False, compress=None, sign=None):
                errs = self.errors()
                if errs:
                    errs.append("autoxml.write: object validation has failed")
                    raise Error(*errs)
                errs = []
                self.newDocument()
                self.encode(self.rootNode(), errs)
                if hasattr(self, 'write_hook'):
                    self.write_hook(errs)
                if errs:
                    errs.append("autoxml.write: File encoding '%s' has errors" % uri)
                    raise Error(*errs)
                self.writexml(uri, tmpDir, sha1sum=sha1sum, compress=compress, sign=sign)
                if not keepDoc:
                    self.unlink()

            cls.read = read
            cls.write = write
            cls.parse = parse

    @staticmethod
    def gen_attr_member(cls, attr):
        spec = getattr(cls, 'a_' + attr)
        tag_type = spec[0]
        assert isinstance(tag_type, type)

        def readtext(node, attr):
            return xmlext.getNodeAttribute(node, attr)

        def writetext(node, attr, text):
            return xmlext.setNodeAttribute(node, attr, text)

        def init(self):
            setattr(self, attr, None)

        def decode(self, node, errs, where=str(cls.tag)):
            value = readtext(node, attr)
            if value is not None:
                try:
                    setattr(self, attr, tag_type(value))
                except Exception as e:
                    errs.append("invalid value for attribute '%s' in %s: '%s'" % (attr, where, value))

        def encode(self, node, errs):
            value = getattr(self, attr)
            if value is not None:
                writetext(node, attr, str(value))

        def errors(self, where=str(cls.tag)):
            errs = []
            value = getattr(self, attr)
            if mandatory in spec and value is None:
                errs.append("attribute '%s' missing in %s" % (attr, where))
            elif value is not None:
                try:
                    tag_type(value)
                except Exception as e:
                    errs.append("invalid value for attribute '%s' in %s: '%s'" % (attr, where, value))
            return errs

        def format(self, f, errs):
            value = getattr(self, attr)
            if value is not None:
                f.add_literal_data(' %s="%s"' % (attr, str(value)))

        return (attr, init, decode, encode, errors, format)

    @staticmethod
    def gen_tag_member(cls, tag):
        spec = getattr(cls, 't_' + tag)
        tag_type = spec[0]
        assert isinstance(tag_type, type)

        def readtext(node, tag):
            return xmlext.getSubNodeText(node, tag)

        def writetext(node, tag, text):
            return xmlext.setSubNodeText(node, tag, text)

        def init(self):
            setattr(self, tag, None)

        def decode(self, node, errs, where=str(cls.tag)):
            value = readtext(node, tag)
            if value is not None:
                try:
                    setattr(self, tag, tag_type(value))
                except Exception as e:
                    errs.append("invalid value for tag '%s' in %s: '%s'" % (tag, where, value))

        def encode(self, node, errs):
            value = getattr(self, tag)
            if value is not None:
                writetext(node, tag, str(value))

        def errors(self, where=str(cls.tag)):
            errs = []
            value = getattr(self, tag)
            if mandatory in spec and value is None:
                errs.append("tag '%s' missing in %s" % (tag, where))
            elif value is not None:
                try:
                    tag_type(value)
                except Exception as e:
                    errs.append("invalid value for tag '%s' in %s: '%s'" % (tag, where, value))
            return errs

        def format(self, f, errs):
            value = getattr(self, tag)
            if value is not None:
                f.add_literal_data('<%s>%s</%s>' % (tag, str(value), tag))

        return (tag, init, decode, encode, errors, format)

    @staticmethod
    def gen_str_member(cls, tag):
        spec = getattr(cls, 's_' + tag)

        def init(self):
            setattr(self, tag, None)

        def decode(self, node, errs, where=str(cls.tag)):
            text = xmlext.getSubNodeText(node, tag)
            setattr(self, tag, text)

        def encode(self, node, errs):
            text = getattr(self, tag)
            if text is not None:
                xmlext.setSubNodeText(node, tag, text)

        def errors(self, where=str(cls.tag)):
            errs = []
            text = getattr(self, tag)
            if mandatory in spec and text is None:
                errs.append("str '%s' missing in %s" % (tag, where))
            return errs

        def format(self, f, errs):
            text = getattr(self, tag)
            if text is not None:
                f.add_literal_data(text)

        return (tag, init, decode, encode, errors, format)

    @classmethod
    def mixed_case(cls, identifier):
        """helper function to turn token name into mixed case"""
        if identifier == "":
            return ""
        else:
            if identifier[0] == 'I':
                lowly = 'i'   # because of locale considerations in lowercasing
            else:
                lowly = identifier[0].lower()
            return lowly + identifier[1:]

    @classmethod
    def tagpath_head_last(cls, tagpath):
        "returns split of the tag path into last tag and the rest"
        try:
            lastsep = tagpath.rindex('/')
        except ValueError as e:
            return ('', tagpath)
        return (tagpath[:lastsep], tagpath[lastsep+1:])

    @classmethod
    def parse_spec(cls, token, spec):
        """decompose member specification"""
        name = cls.mixed_case(token)
        token_type = spec[0]
        req = spec[1]

        if len(spec) >= 3:
            path = spec[2]  # an alternative path specified
        elif isinstance(token_type, list):
            if isinstance(token_type[0], autoxml):
                # if list of class, by default nested like in most PSPEC
                path = token + '/' + token_type[0].tag
            else:
                # if list of ordinary type, just take the name
                path = token
        elif isinstance(token_type, autoxml):
            # if a class, by default its tag
            path = token_type.tag
        else:
            path = token  # otherwise it's the same name as the token

        return name, token_type, req, path

    @classmethod
    def gen_anon_basic(cls, token, spec, readtext, writetext):
        """Generate a tag or attribute with one of the basic types like integer."""
        name, token_type, req, tagpath = cls.parse_spec(token, spec)

        def initialize():
            """default value for all basic types is None"""
            return None

        def decode(node, errs, where):
            """decode from DOM node, the value, watching the spec"""
            text = readtext(node, token)
            if text:
                try:
                    value = autoxml.basic_cons_map[token_type](text)
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    value = None
                    errs.append(f"{where}: Type mismatch: read text cannot be decoded")
                return value
            else:
                if req == 'mandatory':
                    errs.append(f"{where}: Mandatory token {token} not available")
                return None

        def encode(node, value, errs):
            """encode given value inside DOM node"""
            if value is not None:
                writetext(node, token, str(value))
            else:
                if req == 'mandatory':
                    errs.append(f"Mandatory token {token} not available")

        def errors(value, where):
            errs = []
            if value and not isinstance(value, token_type):
                errs.append(f"{where}: Type mismatch. Expected {token_type}, got {type(value)}")
            return errs

        def format(value, f, errs):
            """format value for pretty printing"""
            f.add_literal_data(str(value))

        return initialize, decode, encode, errors, format

    @classmethod
    def gen_class_tag(cls, tag, spec):
        """generate a class datatype"""
        name, tag_type, req, path = cls.parse_spec(tag, spec)

        def make_object():
            obj = tag_type.__new__(tag_type)
            obj.__init__(tag=tag, req=req)
            return obj

        def init():
            return make_object()

        def decode(node, errs, where):
            node = xmlext.getNode(node, tag)
            if node:
                try:
                    obj = make_object()
                    obj.decode(node, errs, where)
                    return obj
                except Error:
                    errs.append(f"{where}: Type mismatch: DOM cannot be decoded")
            else:
                if req == 'mandatory':
                    errs.append(f"{where}: Mandatory argument not available")
            return None

        def encode(node, obj, errs):
            if node and obj:
                try:
                    classnode = xmlext.newNode(node, tag)
                    obj.encode(classnode, errs)
                    xmlext.addNode(node, '', classnode)
                except Error:
                    if req == 'mandatory':
                        errs.append("Object cannot be encoded")
            else:
                if req == 'mandatory':
                    errs.append("Mandatory argument not available")

        def errors(obj, where):
            return obj.errors(where)

        def format(obj, f, errs):
            if obj:
                try:
                    obj.format(f, errs)
                except Error:
                    if req == 'mandatory':
                        errs.append("Object cannot be formatted")
            else:
                if req == 'mandatory':
                    errs.append("Mandatory argument not available")

        return init, decode, encode, errors, format

    @classmethod
    def gen_list_tag(cls, tag, spec):
        """generate a list datatype. stores comps in tag/comp_tag"""
        name, tag_type, req, path = cls.parse_spec(tag, spec)

        pathcomps = path.split('/')
        comp_tag = pathcomps.pop()
        list_tagpath = util.makepath(pathcomps, sep='/', relative=True)

        if len(tag_type) != 1:
            raise Error("List type must contain only one element")

        x = cls.gen_tag(comp_tag, [tag_type[0], 'mandatory'])
        (init_item, decode_item, encode_item, errors_item, format_item) = x

        def init():
            return []

        def decode(node, errs, where):
            l = []
            nodes = xmlext.getAllNodes(node, path)
            if len(nodes) == 0 and req == 'mandatory':
                errs.append(f"{where}: Mandatory list \"{path}\" under \"{node.name()}\" node is empty.")
            ix = 1
            for node in nodes:
                dummy = xmlext.newNode(node, "Dummy")
                xmlext.addNode(dummy, '', node)
                l.append(decode_item(dummy, errs, f"{where}[{ix}]"))
                ix += 1
            return l

        def encode(node, l, errs):
            if l:
                for item in l:
                    if list_tagpath:
                        listnode = xmlext.addNode(node, list_tagpath, branch=False)
                    else:
                        listnode = node
                    encode_item(listnode, item, errs)
            else:
                if req == 'mandatory':
                    errs.append(f"Mandatory list \"{path}\" under \"{node.name()}\" node is empty.")

        def errors(l, where):
            errs = []
            ix = 1
            for node in l:
                errs.extend(errors_item(node, f"{where}[{ix}]"))
                ix += 1
            return errs

        def format(l, f, errs):
            l.sort()
            for node in l:
                format_item(node, f, errs)
                f.add_literal_data(' ')

        return init, decode, encode, errors, format

    @classmethod
    def gen_insetclass_tag(cls, tag, spec):
        """generate a class datatype that is highly integrated"""
        name, tag_type, req, path = cls.parse_spec(tag, spec)

        def make_object():
            obj = tag_type.__new__(tag_type)
            obj.__init__(tag=tag, req=req)
            return obj

        def init():
            return make_object()

        def decode(node, errs, where):
            if node:
                try:
                    obj = make_object()
                    obj.decode(node, errs, where)
                    return obj
                except Error:
                    errs.append(f"{where}: Type mismatch: DOM cannot be decoded")
            else:
                if req == 'mandatory':
                    errs.append(f"{where}: Mandatory argument not available")
            return None

        def encode(node, obj, errs):
            if node and obj:
                try:
                    obj.encode(node, errs)
                except Error:
                    if req == 'mandatory':
                        errs.append("Object cannot be encoded")
            else:
                if req == 'mandatory':
                    errs.append("Mandatory argument not available")

        def errors(obj, where):
            return obj.errors(where)

        def format(obj, f, errs):
            if obj:
                try:
                    obj.format(f, errs)
                except Error:
                    if req == 'mandatory':
                        errs.append("Object cannot be formatted")
            else:
                if req == 'mandatory':
                    errs.append("Mandatory argument not available")

        return init, decode, encode, errors, format

    basic_cons_map = {
        str: str,
        int: int,
        float: float
    }
