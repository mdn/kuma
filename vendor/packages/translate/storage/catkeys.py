#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Manage the Haiku catkeys translation format

The Haiku catkeys format is the translation format used for localisation of
the `Haiku <http://www.haiku-os.org/>`_ operating system.

It is a bilingual base class derived format with :class:`CatkeysFile` and
:class:`CatkeysUnit` providing file and unit level access.  The file format is
described here:
http://www.haiku-os.org/blog/pulkomandy/2009-09-24_haiku_locale_kit_translator_handbook

Implementation
    The implementation covers the full requirements of a catkeys file. The
    files are simple Tab Separated Value (TSV) files that can be read
    by Microsoft Excel and other spreadsheet programs. They use the .txt
    extension which does make it more difficult to automatically identify
    such files.

    The dialect of the TSV files is specified by :class:`CatkeysDialect`.

Encoding
    The files are UTF-8 encoded.

Header
    :class:`CatkeysHeader` provides header management support.

Escaping
    catkeys seem to escape things like in C++ (strings are just extracted from
    the source code unchanged, it seems.

    Functions allow for :func:`._escape` and :func:`._unescape`.
"""

import csv

from translate.lang import data
from translate.storage import base


FIELDNAMES_HEADER = ["version", "language", "mimetype", "checksum"]
"""Field names for the catkeys header"""

FIELDNAMES = ["source", "context", "comment", "target"]
"""Field names for a catkeys TU"""

FIELDNAMES_HEADER_DEFAULTS = {
    "version": "1",
    "language": "",
    "mimetype": "",
    "checksum": "",
}
"""Default or minimum header entries for a catkeys file"""

_unescape_map = {"\\r": "\r", "\\t": "\t", '\\n': '\n', '\\\\': '\\'}
_escape_map = dict([(value, key) for (key, value) in _unescape_map.items()])
# We don't yet do escaping correctly, just for lack of time to do it.  The
# current implementation is just based on something simple that will work with
# investaged files.  The only escapes found were "\n", "\t", "\\n"


def _escape(string):
    if string:
        string = string.replace(r"\n", r"\\n").replace("\n", "\\n").replace("\t", "\\t")
    return string


def _unescape(string):
    if string:
        string = string.replace("\\n", "\n").replace("\\t", "\t").replace(r"\n", r"\\n")
    return string


class CatkeysDialect(csv.Dialect):
    """Describe the properties of a catkeys generated TAB-delimited file."""
    delimiter = "\t"
    lineterminator = "\n"
    quoting = csv.QUOTE_NONE
csv.register_dialect("catkeys", CatkeysDialect)


class CatkeysHeader(object):
    """A catkeys translation memory header"""

    def __init__(self, header=None):
        self._header_dict = {}
        if not header:
            self._header_dict = self._create_default_header()
        elif isinstance(header, dict):
            self._header_dict = header

    def _create_default_header(self):
        """Create a default catkeys header"""
        defaultheader = FIELDNAMES_HEADER_DEFAULTS.copy()
        return defaultheader

    def settargetlanguage(self, newlang):
        """Set a human readable target language"""
        if not newlang or newlang not in data.languages:
            return
        #XXX assumption about the current structure of the languages dict in data
        self._header_dict['language'] = data.languages[newlang][0].lower()
    targetlanguage = property(None, settargetlanguage)


class CatkeysUnit(base.TranslationUnit):
    """A catkeys translation memory unit"""

    def __init__(self, source=None):
        self._dict = {}
        if source:
            self.source = source
        super(CatkeysUnit, self).__init__(source)

    def getdict(self):
        """Get the dictionary of values for a catkeys line"""
        return self._dict

    def setdict(self, newdict):
        """Set the dictionary of values for a catkeys line

        :param newdict: a new dictionary with catkeys line elements
        :type newdict: Dict
        """
        # TODO First check that the values are OK
        self._dict = newdict
    dict = property(getdict, setdict)

    def _get_source_or_target(self, key):
        if self._dict.get(key, None) is None:
            return None
        elif self._dict[key]:
            return _unescape(self._dict[key]).decode('utf-8')
        else:
            return ""

    def _set_source_or_target(self, key, newvalue):
        if newvalue is None:
            self._dict[key] = None
        if isinstance(newvalue, unicode):
            newvalue = newvalue.encode('utf-8')
        newvalue = _escape(newvalue)
        if not key in self._dict or newvalue != self._dict[key]:
            self._dict[key] = newvalue

    def getsource(self):
        return self._get_source_or_target('source')

    def setsource(self, newsource):
        self._rich_source = None
        return self._set_source_or_target('source', newsource)
    source = property(getsource, setsource)

    def gettarget(self):
        return self._get_source_or_target('target')

    def settarget(self, newtarget):
        self._rich_target = None
        return self._set_source_or_target('target', newtarget)
    target = property(gettarget, settarget)

    def getnotes(self, origin=None):
        if not origin or origin in ["programmer", "developer", "source code"]:
            return self._dict["comment"].decode('utf-8')
        return u""

    def getcontext(self):
        return self._dict["context"].decode('utf-8')

    def getid(self):
        context = self.getcontext()
        notes = self.getnotes()
        id = self.source
        if notes:
            id = u"%s\04%s" % (notes, id)
        if context:
            id = u"%s\04%s" % (context, id)
        return id

    def markfuzzy(self, present=True):
        if present:
            self.target = u""

    def settargetlang(self, newlang):
        self._dict['target-lang'] = newlang
    targetlang = property(None, settargetlang)

    def __str__(self):
        return str(self._dict)

    def istranslated(self):
        if not self._dict.get('source', None):
            return False
        return bool(self._dict.get('target', None))

    def merge(self, otherunit, overwrite=False, comments=True,
              authoritative=False):
        """Do basic format agnostic merging."""
        # We can't go fuzzy, so just do nothing
        if self.source != otherunit.source or self.getcontext() != otherunit.getcontext() or otherunit.isfuzzy():
            return
        if not self.istranslated() or overwrite:
            self.rich_target = otherunit.rich_target


class CatkeysFile(base.TranslationStore):
    """A catkeys translation memory file"""
    Name = "Haiku catkeys file"
    Mimetypes = ["application/x-catkeys"]
    Extensions = ["catkeys"]

    def __init__(self, inputfile=None, unitclass=CatkeysUnit):
        """Construct a catkeys store, optionally reading in from inputfile."""
        self.UnitClass = unitclass
        base.TranslationStore.__init__(self, unitclass=unitclass)
        self.filename = ''
        self.header = CatkeysHeader()
        self._encoding = 'utf-8'
        if inputfile is not None:
            self.parse(inputfile)

    def settargetlanguage(self, newlang):
        self.header.settargetlanguage(newlang)

    def parse(self, input):
        """parsse the given file or file source string"""
        if hasattr(input, 'name'):
            self.filename = input.name
        elif not getattr(self, 'filename', ''):
            self.filename = ''
        if hasattr(input, "read"):
            tmsrc = input.read()
            input.close()
            input = tmsrc
        for header in csv.DictReader(input.split("\n")[:1], fieldnames=FIELDNAMES_HEADER, dialect="catkeys"):
            self.header = CatkeysHeader(header)
        lines = csv.DictReader(input.split("\n")[1:], fieldnames=FIELDNAMES, dialect="catkeys")
        for line in lines:
            newunit = CatkeysUnit()
            newunit.dict = line
            self.addunit(newunit)

    def __str__(self):
        output = csv.StringIO()
        writer = csv.DictWriter(output, fieldnames=FIELDNAMES_HEADER, dialect="catkeys")
        writer.writerow(self.header._header_dict)
        writer = csv.DictWriter(output, fieldnames=FIELDNAMES, dialect="catkeys")
        for unit in self.units:
            writer.writerow(unit.dict)
        return output.getvalue()
