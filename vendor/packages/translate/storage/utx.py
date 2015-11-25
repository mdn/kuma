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

"""Manage the Universal Terminology eXchange (UTX) format

UTX is a format for terminology exchange, designed it seems with Machine
Translation (MT) as it's primary consumer.  The format is created by
the Asia-Pacific Association for Machine Translation (AAMT).

It is a bilingual base class derived format with :class:`UtxFile`
and :class:`UtxUnit` providing file and unit level access.

The format can manage monolingual dictionaries but these classes don't
implement that.

Specification
    The format is implemented according to UTX v1.0 (No longer available from
    their website. The current `UTX version
    <http://www.aamt.info/english/utx/#Download>`_ may be downloaded instead).

Format Implementation
    The UTX format is a Tab Seperated Value (TSV) file in UTF-8.  The
    first two lines are headers with subsequent lines containing a
    single source target definition.

Encoding
    The files are UTF-8 encoded with no BOM and CR+LF line terminators.
"""

import csv
import time

from translate.storage import base


class UtxDialect(csv.Dialect):
    """Describe the properties of an UTX generated TAB-delimited dictionary
    file."""
    delimiter = "\t"
    # The spec says \r\n but there are older version < 1.0 with just \n
    # FIXME if we find older specs then lets see if we can support these
    # differences
    lineterminator = "\r\n"
    quoting = csv.QUOTE_NONE
csv.register_dialect("utx", UtxDialect)


class UtxHeader:
    """A UTX header entry

    A UTX header is a single line that looks like this::
        #UTX-S <version>; < source language >/< target language>;
        <date created>; <optional fields (creator, license, etc.)>

    Where::
        - UTX-S version is currently 1.00.
        - Source language/target language: ISO 639, 3166 formats.
          In the case of monolingual dictionary, target language should be
          omitted.
        - Date created: ISO 8601 format
        - Optional fields (creator, license, etc.)
    """


class UtxUnit(base.TranslationUnit):
    """A UTX dictionary unit"""

    def __init__(self, source=None):
        self._dict = {}
        if source:
            self.source = source
        super(UtxUnit, self).__init__(source)

    def getdict(self):
        """Get the dictionary of values for a UTX line"""
        return self._dict

    def setdict(self, newdict):
        """Set the dictionary of values for a UTX line

        :param newdict: a new dictionary with UTX line elements
        :type newdict: Dict
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
        # FIXME update the header date
        if newvalue is None:
            self._dict[key] = None
        if isinstance(newvalue, unicode):
            newvalue = newvalue.encode('utf-8')
        if not key in self._dict or newvalue != self._dict[key]:
            self._dict[key] = newvalue

    def getnotes(self, origin=None):
        return self._get_field('comment')

    def addnote(self, text, origin=None, position="append"):
        currentnote = self._get_field('comment')
        if (position == "append" and
            currentnote is not None and
            currentnote != u''):
            self._set_field('comment', currentnote + '\n' + text)
        else:
            self._set_field('comment', text)

    def removenotes(self):
        self._set_field('comment', u'')

    def getsource(self):
        return self._get_field('src')

    def setsource(self, newsource):
        self._rich_source = None
        return self._set_field('src', newsource)
    source = property(getsource, setsource)

    def gettarget(self):
        return self._get_field('tgt')

    def settarget(self, newtarget):
        self._rich_target = None
        return self._set_field('tgt', newtarget)
    target = property(gettarget, settarget)

    def settargetlang(self, newlang):
        self._dict['target-lang'] = newlang
    targetlang = property(None, settargetlang)

    def __str__(self):
        return str(self._dict)

    def istranslated(self):
        return bool(self._dict.get('tgt', None))


class UtxFile(base.TranslationStore):
    """A UTX dictionary file"""
    Name = "UTX Dictionary"
    Mimetypes = ["text/x-utx"]
    Extensions = ["utx"]

    def __init__(self, inputfile=None, unitclass=UtxUnit):
        """Construct an UTX dictionary, optionally reading in from
        inputfile."""
        self.UnitClass = unitclass
        base.TranslationStore.__init__(self, unitclass=unitclass)
        self.filename = ''
        self.extension = ''
        self._fieldnames = ['src', 'tgt', 'src:pos']
        self._header = {
            "version": "1.00",
             "source_language": "en",
             "date_created": time.strftime("%FT%TZ%z",
                                           time.localtime(time.time()))
        }
        if inputfile is not None:
            self.parse(inputfile)

    def _read_header(self, header=None):
        """Read a UTX header"""
        if header is None:
            self._fieldnames = ['src', 'tgt', 'src:pos']
            # FIXME make the header properly
            self._header = {"version": "1.00"}
            return
        header_lines = []
        for line in header.split(UtxDialect.lineterminator):
            if line.startswith("#"):
                header_lines.append(line)
            else:
                break
        self._header = {}
        header_components = []
        for line in header_lines[:-1]:
            header_components += line[1:].split(";")
        self._header["version"] = header_components[0].replace("UTX-S ", "")
        languages = header_components[1].strip().split("/")
        self._header["source_language"] = languages[0]
        self._header["target_language"] = languages[1] or None
        self._header["date_created"] = header_components[2].strip()
        for data in header_components[3:]:
            key, value = data.strip().split(":")
            self._header[key] = value.strip()
        self._fieldnames = header_lines[-1:][0].replace("#", ""). split('\t')
        return len(header_lines)

    def _write_header(self):
        """Create a UTX header"""
        header = "#UTX-S %(version)s; %(src)s/%(tgt)s; %(date)s" % {
                    "version": self._header["version"],
                    "src": self._header["source_language"],
                    "tgt": self._header.get("target_language", ""),
                    "date": self._header["date_created"],
                 }
        items = []
        for key, value in self._header.iteritems():
            if key in ["version", "source_language",
                       "target_language", "date_created"]:
                continue
            items.append("%s: %s" % (key, value))
        if len(items):
            items = "; ".join(items)
            header += "; " + items
        header += UtxDialect.lineterminator
        header += "#" + "\t".join(self._fieldnames) + UtxDialect.lineterminator
        return header

    def getsourcelanguage(self):
        return self._header.get("source_language", None)

    def setsourcelanguage(self, sourcelanguage):
        self._header["source_language"] = sourcelanguage

    def gettargetlanguage(self):
        return self._header.get("target_language", None)

    def settargetlanguage(self, targetlanguage):
        self._header["target_language"] = targetlanguage

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
            header_length = self._read_header(input)
        except:
            raise base.ParseError("Cannot parse header")
        lines = csv.DictReader(
                    input.split(UtxDialect.lineterminator)[header_length:],
                    fieldnames=self._fieldnames,
                    dialect="utx")
        for line in lines:
            newunit = UtxUnit()
            newunit.dict = line
            self.addunit(newunit)

    def __str__(self):
        output = csv.StringIO()
        writer = csv.DictWriter(output, fieldnames=self._fieldnames,
                                dialect="utx")
        unit_count = 0
        for unit in self.units:
            if unit.istranslated():
                unit_count += 1
                writer.writerow(unit.dict)
        if unit_count == 0:
            return ""
        output.reset()
        return self._write_header() + "".join(output.readlines())
