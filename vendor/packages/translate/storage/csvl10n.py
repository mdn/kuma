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
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""classes that hold units of comma-separated values (.csv) files (csvunit)
or entire files (csvfile) for use with localisation
"""

import codecs
import csv
from cStringIO import StringIO

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


class DefaultDialect(csv.excel):
    skipinitialspace = True
    quoting = csv.QUOTE_NONNUMERIC
    escapechar = '\\'

csv.register_dialect('default', DefaultDialect)


def from_unicode(text, encoding='utf-8'):
    if encoding == 'auto':
        encoding = 'utf-8'
    if isinstance(text, unicode):
        return text.encode(encoding)
    return text


def to_unicode(text, encoding='utf-8'):
    if encoding == 'auto':
        encoding = 'utf-8'
    if isinstance(text, unicode):
        return text
    return text.decode(encoding)


class csvunit(base.TranslationUnit):
    spreadsheetescapes = [("+", "\\+"), ("-", "\\-"), ("=", "\\="), ("'", "\\'")]

    def __init__(self, source=None):
        super(csvunit, self).__init__(source)
        self.location = ""
        self.source = source or ""
        self.target = ""
        self.id = ""
        self.fuzzy = 'False'
        self.developer_comments = ""
        self.translator_comments = ""
        self.context = ""

    def getid(self):
        if self.id:
            return self.id

        result = self.source
        context = self.context
        if context:
            result = u"%s\04%s" % (context, result)

        return result

    def setid(self, value):
        self.id = value

    def getlocations(self):
        #FIXME: do we need to support more than one location
        return [self.location]

    def addlocation(self, location):
        self.location = location

    def getcontext(self):
        return self.context

    def setcontext(self, value):
        self.context = value

    def getnotes(self, origin=None):
        if origin is None:
            result = self.translator_comments
            if self.developer_comments:
                if result:
                    result += '\n' + self.developer_comments
                else:
                    result = self.developer_comments
            return result
        elif origin == "translator":
            return self.translator_comments
        elif origin in ('programmer', 'developer', 'source code'):
            return self.developer_comments
        else:
            raise ValueError("Comment type not valid")

    def addnote(self, text, origin=None, position="append"):
        if origin in ('programmer', 'developer', 'source code'):
            if position == 'append' and self.developer_comments:
                self.developer_comments += '\n' + text
            elif position == 'prepend' and self.developer_comments:
                self.developer_comments = text + '\n' + self.developer_comments
            else:
                self.developer_comments = text
        else:
            if position == 'append' and self.translator_comments:
                self.translator_comments += '\n' + text
            elif position == 'prepend' and self.translator_comments:
                self.translator_comments = self.translator_comments + '\n' + text
            else:
                self.translator_comments = text

    def removenotes(self):
        self.translator_comments = u''

    def isfuzzy(self):
        if self.fuzzy.lower() in ('1', 'x', 'true', 'yes', 'fuzzy'):
            return True
        return False

    def markfuzzy(self, value=True):
        if value:
            self.fuzzy = 'True'
        else:
            self.fuzzy = 'False'

    def match_header(self):
        """see if unit might be a header"""
        some_value = False
        for key, value in self.todict().iteritems():
            if value:
                some_value = True
            if key.lower() != 'fuzzy' and value and key.lower() != value.lower():
                return False
        return some_value

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

    def fromdict(self, cedict, encoding='utf-8'):
        for key, value in cedict.iteritems():
            rkey = fieldname_map.get(key, key)
            if value is None or key is None or key == EXTRA_KEY:
                continue
            value = to_unicode(value, encoding)
            if rkey == "id":
                self.id = value
            elif rkey == "source":
                self.source = value
            elif rkey == "target":
                self.target = value
            elif rkey == "location":
                self.location = value
            elif rkey == "fuzzy":
                self.fuzzy = value
            elif rkey == "context":
                self.context = value
            elif rkey == "translator_comments":
                self.translator_comments = value
            elif rkey == "developer_comments":
                self.developer_comments = value

        #self.source, self.target = self.remove_spreadsheet_escapes(self.source, self.target)

    def todict(self, encoding='utf-8'):
        #FIXME: use apis?
        #source, target = self.add_spreadsheet_escapes(self.source, self.target)
        source = self.source
        target = self.target
        output = {
            'location': from_unicode(self.location, encoding),
            'source': from_unicode(source, encoding),
            'target': from_unicode(target, encoding),
            'id': from_unicode(self.id, encoding),
            'fuzzy': str(self.fuzzy),
            'context': from_unicode(self.context, encoding),
            'translator_comments': from_unicode(self.translator_comments, encoding),
            'developer_comments': from_unicode(self.developer_comments, encoding),
        }

        return output

    def __str__(self):
        return str(self.todict())

canonical_field_names = ('location', 'source', 'target', 'id', 'fuzzy', 'context', 'translator_comments', 'developer_comments')
fieldname_map = {
    'original': 'source',
    'untranslated': 'source',
    'translated': 'target',
    'translation': 'target',
    'identified': 'id',
    'key': 'id',
    'label': 'id',
    'transaltor comments': 'translator_comments',
    'notes': 'translator_comments',
    'developer comments': 'developer_comments',
    'state': 'fuzzy',
}


EXTRA_KEY = '__CSVL10N__EXTRA__'


def try_dialects(inputfile, fieldnames, dialect):
    #FIXME: does it verify at all if we don't actually step through the file?
    try:
        inputfile.seek(0)
        reader = csv.DictReader(inputfile, fieldnames=fieldnames, dialect=dialect, restkey=EXTRA_KEY)
    except csv.Error:
        try:
            inputfile.seek(0)
            reader = csv.DictReader(inputfile, fieldnames=fieldnames, dialect='default', restkey=EXTRA_KEY)
        except csv.Error:
            inputfile.seek(0)
            reader = csv.DictReader(inputfile, fieldnames=fieldnames, dialect='excel', restkey=EXTRA_KEY)
    return reader


def valid_fieldnames(fieldnames):
    """check if fieldnames are valid"""
    for fieldname in fieldnames:
        if fieldname in canonical_field_names and fieldname == 'source':
            return True
        elif fieldname in fieldname_map and fieldname_map[fieldname] == 'source':
            return True
    return False


def detect_header(sample, dialect, fieldnames):
    """Test if file has a header or not, also returns number of columns in first row"""
    inputfile = StringIO(sample)
    try:
        reader = csv.reader(inputfile, dialect)
    except csv.Error:
        try:
            inputfile.seek(0)
            reader = csv.reader(inputfile, 'default')
        except csv.Error:
            inputfile.seek(0)
            reader = csv.reader(inputfile, 'excel')

    header = reader.next()
    columncount = max(len(header), 3)
    if valid_fieldnames(header):
        return header
    return fieldnames[:columncount]


class csvfile(base.TranslationStore):
    """This class represents a .csv file with various lines.
    The default format contains three columns: location, source, target"""
    UnitClass = csvunit
    Name = "Comma Separated Value"
    Mimetypes = ['text/comma-separated-values', 'text/csv']
    Extensions = ["csv"]

    def __init__(self, inputfile=None, fieldnames=None, encoding="auto"):
        base.TranslationStore.__init__(self, unitclass=self.UnitClass)
        self.units = []
        self.encoding = encoding or 'utf-8'
        if not fieldnames:
            self.fieldnames = ['location', 'source', 'target', 'id', 'fuzzy', 'context', 'translator_comments', 'developer_comments']
        else:
            if isinstance(fieldnames, basestring):
                fieldnames = [fieldname.strip() for fieldname in fieldnames.split(",")]
            self.fieldnames = fieldnames
        self.filename = getattr(inputfile, 'name', '')
        self.dialect = 'default'
        if inputfile is not None:
            csvsrc = inputfile.read()
            inputfile.close()
            self.parse(csvsrc)

    def parse(self, csvsrc):
        text, encoding = self.detect_encoding(csvsrc, default_encodings=['utf-8', 'utf-16'])
        #FIXME: raise parse error if encoding detection fails?
        if encoding and encoding.lower() != 'utf-8':
            csvsrc = text.encode('utf-8').lstrip(codecs.BOM_UTF8)
        self.encoding = encoding or 'utf-8'

        sniffer = csv.Sniffer()
        # FIXME: maybe we should sniff a smaller sample
        sample = csvsrc[:1024]
        if isinstance(sample, unicode):
            sample = sample.encode('utf-8')

        try:
            self.dialect = sniffer.sniff(sample)
            if not self.dialect.escapechar:
                self.dialect.escapechar = '\\'
                if self.dialect.quoting == csv.QUOTE_MINIMAL:
                    #HACKISH: most probably a default, not real detection
                    self.dialect.quoting = csv.QUOTE_ALL
                    self.dialect.doublequote = True
        except csv.Error:
            self.dialect = 'default'

        try:
            fieldnames = detect_header(sample, self.dialect, self.fieldnames)
            self.fieldnames = fieldnames
        except csv.Error:
            pass

        inputfile = csv.StringIO(csvsrc)
        reader = try_dialects(inputfile, self.fieldnames, self.dialect)

        #reader = SimpleDictReader(csvfile, fieldnames=fieldnames, dialect=dialect)
        first_row = True
        for row in reader:
            newce = self.UnitClass()
            newce.fromdict(row)
            if not first_row or not newce.match_header():
                self.addunit(newce)
            first_row = False

    def __str__(self):
        """convert to a string. double check that unicode is handled somehow here"""
        source = self.getoutput()
        if not isinstance(source, unicode):
            source = source.decode('utf-8')
        if not self.encoding or self.encoding == 'auto':
            encoding = 'utf-8'
        else:
            encoding = self.encoding
        return source.encode(encoding)

    def getoutput(self):
        outputfile = StringIO()
        writer = csv.DictWriter(outputfile, self.fieldnames, extrasaction='ignore', dialect=self.dialect)
        # write header
        hdict = dict(map(None, self.fieldnames, self.fieldnames))
        writer.writerow(hdict)
        for ce in self.units:
            cedict = ce.todict()
            writer.writerow(cedict)
        return outputfile.getvalue()
