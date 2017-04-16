#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

"""Manage the OmegaT glossary format

   OmegaT glossary format is used by the
   U{OmegaT<http://www.omegat.org/en/omegat.html>} computer aided
   translation tool.

   It is a bilingual base class derived format with L{OmegaTFile}
   and L{OmegaTUnit} providing file and unit level access.

   Format Implementation
   =====================
   The OmegaT glossary format is a simple Tab Separated Value (TSV) file
   with the columns: source, target, comment.

   The dialect of the TSV files is specified by L{OmegaTDialect}.

   Encoding
   --------
   The files are either UTF-8 or encoded using the system default.  UTF-8
   encoded files use the .utf8 extension while system encoded files use
   the .tab extension.
"""

import csv
import locale
import os.path
import sys
import time
from translate.storage import base

OMEGAT_FIELDNAMES = ["source", "target", "comment"]
"""Field names for an OmegaT glossary unit"""


class OmegaTDialect(csv.Dialect):
    """Describe the properties of an OmegaT generated TAB-delimited file."""
    delimiter = "\t"
    lineterminator = "\r\n"
    quoting = csv.QUOTE_NONE
    if sys.version_info < (2, 5, 0):
        # We need to define the following items for csv in Python < 2.5
        quoting = csv.QUOTE_MINIMAL   # OmegaT does not quote anything FIXME So why MINIMAL?
        doublequote = False
        skipinitialspace = False
        escapechar = None
        quotechar = '"'
csv.register_dialect("omegat", OmegaTDialect)

class OmegaTUnit(base.TranslationUnit):
    """An OmegaT translation memory unit"""
    def __init__(self, source=None):
        self._dict = {}
        if source:
            self.source = source
        super(OmegaTUnit, self).__init__(source)

    def getdict(self):
        """Get the dictionary of values for a OmegaT line"""
        return self._dict

    def setdict(self, newdict):
        """Set the dictionary of values for a OmegaT line

        @param newdict: a new dictionary with OmegaT line elements
        @type newdict: Dict
        """
        # TODO First check that the values are OK
        self._dict = newdict
    dict = property(getdict, setdict)

    def _get_field(self, key):
        if key not in self._dict:
            return None
        elif self._dict[key]:
            return self._dict[key].decode('utf-8')
        else:
            return ""

    def _set_field(self, key, newvalue):
        if newvalue is None:
            self._dict[key] = None
        if isinstance(newvalue, unicode):
            newvalue = newvalue.encode('utf-8')
        if not key in self._dict or newvalue != self._dict[key]:
            self._dict[key] = newvalue

    def getnotes(self, origin=None):
        return self._get_field('comment')

    def getsource(self):
        return self._get_field('source')

    def setsource(self, newsource):
        self._rich_source = None
        return self._set_field('source', newsource)
    source = property(getsource, setsource)

    def gettarget(self):
        return self._get_field('target')

    def settarget(self, newtarget):
        self._rich_target = None
        return self._set_field('target', newtarget)
    target = property(gettarget, settarget)

    def settargetlang(self, newlang):
        self._dict['target-lang'] = newlang
    targetlang = property(None, settargetlang)

    def __str__(self):
        return str(self._dict)

    def istranslated(self):
        return bool(self._dict.get('target', None))


class OmegaTFile(base.TranslationStore):
    """An OmegaT translation memory file"""
    Name = _("OmegaT Glossary")
    Mimetypes  = ["application/x-omegat-glossary"]
    Extensions = ["utf8"]
    def __init__(self, inputfile=None, unitclass=OmegaTUnit):
        """Construct an OmegaT glossary, optionally reading in from inputfile."""
        self.UnitClass = unitclass
        base.TranslationStore.__init__(self, unitclass=unitclass)
        self.filename = ''
        self.extension = ''
        self._encoding = self._get_encoding()
        if inputfile is not None:
            self.parse(inputfile)

    def _get_encoding(self):
        return 'utf-8'

    def parse(self, input):
        """parsese the given file or file source string"""
        if hasattr(input, 'name'):
            self.filename = input.name
        elif not getattr(self, 'filename', ''):
            self.filename = ''
        if hasattr(input, "read"):
            tmsrc = input.read()
            input.close()
            input = tmsrc
        try:
            input = input.decode(self._encoding).encode('utf-8')
        except:
            raise ValueError("OmegaT files are either UTF-8 encoded or use the default system encoding")
        lines = csv.DictReader(input.split("\n"), fieldnames=OMEGAT_FIELDNAMES, dialect="omegat")
        for line in lines:
            newunit = OmegaTUnit()
            newunit.dict = line
            self.addunit(newunit)

    def __str__(self):
        output = csv.StringIO()
        writer = csv.DictWriter(output, fieldnames=OMEGAT_FIELDNAMES, dialect="omegat")
        unit_count = 0
        for unit in self.units:
            if unit.istranslated():
                unit_count += 1
                writer.writerow(unit.dict)
        if unit_count == 0:
            return ""
        output.reset()
        decoded = "".join(output.readlines()).decode('utf-8')
        try:
            return decoded.encode(self._encoding)
        except UnicodeEncodeError:
            return decoded.encode('utf-8')

class OmegaTFileTab(OmegaTFile):
    """An OmegT translation memory file in the default system encoding"""
    # FIXME: uncomment this when we next open from string freeze
    #Name = _("OmegaT Glossary")
    Name = None
    Mimetypes  = ["application/x-omegat-glossary"]
    Extensions = ["tab"]

    def _get_encoding(self):
        return locale.getdefaultlocale()[1]
