#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2002-2006 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""classes that hold units of comma-separated values (.csv) files (csvunit)
or entire files (csvfile) for use with localisation
"""

import csv

from translate.misc import sparse
from translate.storage import base

class SimpleDictReader:
    def __init__(self, fileobj, fieldnames):
        self.fieldnames = fieldnames
        self.contents = fileobj.read()
        self.parser = sparse.SimpleParser(defaulttokenlist=[",", "\n"], whitespacechars="\r")
        self.parser.stringescaping = 0
        self.parser.quotechars = '"'
        self.tokens = self.parser.tokenize(self.contents)
        self.tokenpos = 0

    def __iter__(self):
        return self

    def getvalue(self, value):
        """returns a value, evaluating strings as neccessary"""
        if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
            return sparse.stringeval(value)
        else:
            return value

    def next(self):
        lentokens = len(self.tokens)
        while self.tokenpos < lentokens and self.tokens[self.tokenpos] == "\n":
            self.tokenpos += 1
        if self.tokenpos >= lentokens:
            raise StopIteration()
        thistokens = []
        while self.tokenpos < lentokens and self.tokens[self.tokenpos] != "\n":
            thistokens.append(self.tokens[self.tokenpos])
            self.tokenpos += 1
        while self.tokenpos < lentokens and self.tokens[self.tokenpos] == "\n":
            self.tokenpos += 1
        fields = []
        # patch together fields since we can have quotes inside a field
        currentfield = ''
        fieldparts = 0
        for token in thistokens:
            if token == ',':
                # a field is only quoted if the whole thing is quoted
                if fieldparts == 1:
                    currentfield = self.getvalue(currentfield)
                fields.append(currentfield)
                currentfield = ''
                fieldparts = 0
            else:
                currentfield += token
                fieldparts += 1
        # things after the last comma...
        if fieldparts:
            if fieldparts == 1:
                currentfield = self.getvalue(currentfield)
            fields.append(currentfield)
        values = {}
        for fieldnum in range(len(self.fieldnames)):
            if fieldnum >= len(fields):
                values[self.fieldnames[fieldnum]] = ""
            else:
                values[self.fieldnames[fieldnum]] = fields[fieldnum]
        return values

class csvunit(base.TranslationUnit):
    spreadsheetescapes = [("+", "\\+"), ("-", "\\-"), ("=", "\\="), ("'", "\\'")]
    def __init__(self, source=None):
        super(csvunit, self).__init__(source)
        self.comment = ""
        self.source = source
        self.target = ""

    def add_spreadsheet_escapes(self, source, target):
        """add common spreadsheet escapes to two strings"""
        for unescaped, escaped in self.spreadsheetescapes:
            if source.startswith(unescaped):
                source = source.replace(unescaped, escaped, 1)
            if target.startswith(unescaped):
                target = target.replace(unescaped, escaped, 1)
        return source, target

    def remove_spreadsheet_escapes(self, source, target):
        """remove common spreadsheet escapes from two strings"""
        for unescaped, escaped in self.spreadsheetescapes:
            if source.startswith(escaped):
                source = source.replace(escaped, unescaped, 1)
            if target.startswith(escaped):
                target = target.replace(escaped, unescaped, 1)
        return source, target

    def fromdict(self, cedict):
        self.comment = cedict.get('location', '').decode('utf-8')
        self.source = cedict.get('source', '').decode('utf-8')
        self.target = cedict.get('target', '').decode('utf-8')
        if self.comment is None:
            self.comment = ''
        if self.source is None:
            self.source = ''
        if self.target is None:
            self.target = ''
        self.source, self.target = self.remove_spreadsheet_escapes(self.source, self.target)

    def todict(self, encoding='utf-8'):
        comment, source, target = self.comment, self.source, self.target
        source, target = self.add_spreadsheet_escapes(source, target)
        if isinstance(comment, unicode):
            comment = comment.encode(encoding)
        if isinstance(source, unicode):
            source = source.encode(encoding)
        if isinstance(target, unicode):
            target = target.encode(encoding)
        return {'location':comment, 'source': source, 'target': target}

class csvfile(base.TranslationStore):
    """This class represents a .csv file with various lines. 
    The default format contains three columns: location, source, target"""
    UnitClass = csvunit
    Name = _("Comma Separated Value")
    Mimetypes  = ['text/comma-separated-values', 'text/csv']
    Extensions = ["csv"]
    def __init__(self, inputfile=None, fieldnames=None):
        base.TranslationStore.__init__(self, unitclass = self.UnitClass)
        self.units = []
        if fieldnames is None:
            self.fieldnames = ['location', 'source', 'target']
        else:
            if isinstance(fieldnames, basestring):
                fieldnames = [fieldname.strip() for fieldname in fieldnames.split(",")]
            self.fieldnames = fieldnames
        self.filename = getattr(inputfile, 'name', '')
        if inputfile is not None:
            csvsrc = inputfile.read()
            inputfile.close()
            self.parse(csvsrc)

    def parse(self, csvsrc):
        csvfile = csv.StringIO(csvsrc)
        reader = SimpleDictReader(csvfile, self.fieldnames)
        for row in reader:
            newce = self.UnitClass()
            newce.fromdict(row)
            self.addunit(newce)

    def __str__(self):
        """convert to a string. double check that unicode is handled somehow here"""
        source = self.getoutput()
        if isinstance(source, unicode):
            return source.encode(getattr(self, "encoding", "UTF-8"))
        return source

    def getoutput(self):
        csvfile = csv.StringIO()
        writer = csv.DictWriter(csvfile, self.fieldnames)
        for ce in self.units:
            cedict = ce.todict()
            writer.writerow(cedict)
        csvfile.reset()
        return "".join(csvfile.readlines())

