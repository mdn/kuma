#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2007 Zuza Software Foundation
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

"""Manage the Wordfast Translation Memory format

   Wordfast TM format is the Translation Memory format used by the 
   U{Wordfast<http://www.wordfast.net/>} computer aided translation tool.

   It is a bilingual base class derived format with L{WordfastTMFile}
   and L{WordfastUnit} providing file and unit level access.

   Wordfast tools
   ==============
   Wordfast is a computer aided translation tool.  It is an application
   built on top of Microsoft Word and is implemented as a rather 
   sophisticated set of macros.  Understanding that helps us understand
   many of the seemingly strange choices around this format including:
   encoding, escaping and file naming.

   Implementation
   ==============
   The implementation covers the full requirements of a Wordfast TM file.
   The files are simple Tab Separated Value (TSV) files that can be read 
   by Microsoft Excel and other spreadsheet programs.  They use the .txt 
   extension which does make it more difficult to automatically identify 
   such files.

   The dialect of the TSV files is specified by L{WordfastDialect}.

   Encoding
   --------
   The files are UTF-16 or ISO-8859-1 (Latin1) encoded.  These choices
   are most likely because Microsoft Word is the base editing tool for
   Wordfast.

   The format is tab separated so we are able to detect UTF-16 vs Latin-1 
   by searching for the occurance of a UTF-16 tab character and then
   continuing with the parsing.

   Timestamps
   ----------
   L{WordfastTime} allows for the correct management of the Wordfast
   YYYYMMDD~HHMMSS timestamps.  However, timestamps on individual units are 
   not updated when edited.

   Header
   ------
   L{WordfastHeader} provides header management support.  The header 
   functionality is fully implemented through observing the behaviour of the
   files in real use cases, input from the Wordfast programmers and 
   public documentation.

   Escaping
   --------
   Wordfast TM implements a form of escaping that covers two aspects:
     1. Placeable: bold, formating, etc.  These are left as is and ignored.
        It is up to the editor and future placeable implementation to manage
        these.
     2. Escapes: items that may confuse Excel or translators are 
        escaped as &'XX;. These are fully implemented and are converted to
        and from Unicode.  By observing behaviour and reading documentation
        we where able to observe all possible escapes. Unfortunately the
        escaping differs slightly between Windows and Mac version.  This
        might cause errors in future.
   Functions allow for L{conversion to Unicode<_wf_to_char>} and L{back to 
   Wordfast escapes<_char_to_wf>}.

   Extended Attributes
   -------------------
   The last 4 columns allow users to define and manage extended attributes.
   These are left as is and are not directly managed byour implemenation.
"""

import csv
import sys
import time
from translate.storage import base

WF_TIMEFORMAT = "%Y%m%d~%H%M%S"
"""Time format used by Wordfast"""

WF_FIELDNAMES_HEADER = ["date", "userlist", "tucount", "src-lang", "version", "target-lang", "license", "attr1list", "attr2list", "attr3list", "attr4list", "attr5list"]
"""Field names for the Wordfast header"""

WF_FIELDNAMES = ["date", "user", "reuse", "src-lang", "source", "target-lang", "target", "attr1", "attr2", "attr3", "attr4"]
"""Field names for a Wordfast TU"""

WF_FIELDNAMES_HEADER_DEFAULTS = {
"date": "%19000101~121212", 
"userlist": "%User ID,TT,TT Translate-Toolkit", 
"tucount": "%TU=00000001", 
"src-lang": "%EN-US", 
"version": "%Wordfast TM v.5.51w9/00", 
"target-lang": "", 
"license": "%---00000001", 
"attr1list": "", 
"attr2list": "", 
"attr3list": "", 
"attr4list": "" }
"""Default or minimum header entries for a Wordfast file"""

# TODO Needs validation.  The following need to be checked against a WF TM file to ensure 
# that the correct Unicode values have been chosen for the characters. For now these look
# correct and have been taken from Windows CP1252 and Macintosh code points found for
# the respective character sets on Linux.
WF_ESCAPE_MAP = (
              ("&'26;", u"\u0026"), # & - Ampersand (must be first to prevent escaping of escapes)
              ("&'82;", u"\u201A"), # ‚ - Single low-9 quotation mark
              ("&'85;", u"\u2026"), # … - Elippsis
              ("&'91;", u"\u2018"), # ‘ - left single quotation mark
              ("&'92;", u"\u2019"), # ’ - right single quotation mark
              ("&'93;", u"\u201C"), # “ - left double quotation mark
              ("&'94;", u"\u201D"), # ” - right double quotation mark
              ("&'96;", u"\u2013"), # – - en dash (validate)
              ("&'97;", u"\u2014"), # — - em dash (validate)
              ("&'99;", u"\u2122"), # ™ - Trade mark
              # Windows only
              ("&'A0;", u"\u00A0"), #   - Non breaking space
              ("&'A9;", u"\u00A9"), # © - Copyright
              ("&'AE;", u"\u00AE"), # ® - Registered
              ("&'BC;", u"\u00BC"), # ¼
              ("&'BD;", u"\u00BD"), # ½
              ("&'BE;", u"\u00BE"), # ¾
              # Mac only
              ("&'A8;", u"\u00AE"), # ® - Registered
              ("&'AA;", u"\u2122"), # ™ - Trade mark
              ("&'C7;", u"\u00AB"), # « - Left-pointing double angle quotation mark
              ("&'C8;", u"\u00BB"), # » - Right-pointing double angle quotation mark
              ("&'C9;", u"\u2026"), # … - Horizontal Elippsis
              ("&'CA;", u"\u00A0"), #   - Non breaking space
              ("&'D0;", u"\u2013"), # – - en dash (validate)
              ("&'D1;", u"\u2014"), # — - em dash (validate)
              ("&'D2;", u"\u201C"), # “ - left double quotation mark
              ("&'D3;", u"\u201D"), # ” - right double quotation mark
              ("&'D4;", u"\u2018"), # ‘ - left single quotation mark
              ("&'D5;", u"\u2019"), # ’ - right single quotation mark
              ("&'E2;", u"\u201A"), # ‚ - Single low-9 quotation mark
              ("&'E3;", u"\u201E"), # „ - Double low-9 quotation mark
              # Other markers
              #("&'B;", u"\n"), # Soft-break - XXX creates a problem with roundtripping could also be represented by \u2028
             )
"""Mapping of Wordfast &'XX; escapes to correct Unicode characters"""

TAB_UTF16 = "\x00\x09"
"""The tab \\t character as it would appear in UTF-16 encoding"""

def _char_to_wf(string):
    """Char -> Wordfast &'XX; escapes
    
       Full roundtripping is not possible because of the escaping of NEWLINE \\n 
       and TAB \\t"""
    # FIXME there is no platform check to ensure that we use Mac encodings when running on a Mac
    if string:
        for code, char in WF_ESCAPE_MAP:
            string = string.replace(char.encode('utf-8'), code)
        string = string.replace("\n", "\\n").replace("\t", "\\t")
    return string

def _wf_to_char(string):
    """Wordfast &'XX; escapes -> Char"""
    if string:
        for code, char in WF_ESCAPE_MAP:
            string = string.replace(code, char.encode('utf-8'))
        string = string.replace("\\n", "\n").replace("\\t", "\t")
    return string

class WordfastDialect(csv.Dialect):
    """Describe the properties of a Wordfast generated TAB-delimited file."""
    delimiter = "\t"
    lineterminator = "\r\n"
    quoting = csv.QUOTE_NONE
    if sys.version_info < (2, 5, 0):
        # We need to define the following items for csv in Python < 2.5
        quoting = csv.QUOTE_MINIMAL   # Wordfast does not quote anything, since we escape
                                      # \t anyway in _char_to_wf this should not be a problem
        doublequote = False
        skipinitialspace = False
        escapechar = None
        quotechar = '"'
csv.register_dialect("wordfast", WordfastDialect)

class WordfastTime(object):
    """Manages time stamps in the Wordfast format of YYYYMMDD~hhmmss"""
    def __init__(self, newtime=None):
        self._time = None
        if not newtime:
            self.time = None
        elif isinstance(newtime, basestring):
            self.timestring = newtime
        elif isinstance(newtime, time.struct_time):
            self.time = newtime

    def get_timestring(self):
        """Get the time in the Wordfast time format"""
        if not self._time:
            return None
        else:
            return time.strftime(WF_TIMEFORMAT, self._time)

    def set_timestring(self, timestring):
        """Set the time_sturct object using a Wordfast time formated string

        @param timestring: A Wordfast time string (YYYMMDD~hhmmss)
        @type timestring: String
        """
        self._time = time.strptime(timestring, WF_TIMEFORMAT)
    timestring = property(get_timestring, set_timestring)

    def get_time(self):
        """Get the time_struct object"""
        return self._time

    def set_time(self, newtime):
        """Set the time_struct object
        
        @param newtime: a new time object
        @type newtime: time.time_struct
        """
        if newtime and isinstance(newtime, time.struct_time):
            self._time = newtime
        else:
            self._time = None
    time = property(get_time, set_time)

    def __str__(self):
        if not self.timestring:
            return ""
        else:
            return self.timestring

class WordfastHeader(object):
    """A wordfast translation memory header"""
    def __init__(self, header=None):
        self._header_dict = []
        if not header:
            self.header = self._create_default_header()
        elif isinstance(header, dict):
            self.header = header

    def _create_default_header(self):
        """Create a default Wordfast header with the date set to the current time"""
        defaultheader = WF_FIELDNAMES_HEADER_DEFAULTS
        defaultheader['date'] = '%%%s' % WordfastTime(time.localtime()).timestring
        return defaultheader

    def getheader(self):
        """Get the header dictionary"""
        return self._header_dict

    def setheader(self, newheader):
        self._header_dict = newheader
    header = property(getheader, setheader)

    def settargetlang(self, newlang):
        self._header_dict['target-lang'] = '%%%s' % newlang
    targetlang = property(None, settargetlang)

    def settucount(self, count):
        self._header_dict['tucount'] = '%%TU=%08d' % count
    tucount = property(None, settucount)

class WordfastUnit(base.TranslationUnit):
    """A Wordfast translation memory unit"""
    def __init__(self, source=None):
        self._dict = {}
        if source:
            self.source = source
        super(WordfastUnit, self).__init__(source)

    def _update_timestamp(self):
        """Refresh the timestamp for the unit"""
        self._dict['date'] = WordfastTime(time.localtime()).timestring

    def getdict(self):
        """Get the dictionary of values for a Wordfast line"""
        return self._dict

    def setdict(self, newdict):
        """Set the dictionary of values for a Wordfast line

        @param newdict: a new dictionary with Wordfast line elements
        @type newdict: Dict
        """
        # TODO First check that the values are OK
        self._dict = newdict
    dict = property(getdict, setdict)

    def _get_source_or_target(self, key):
        if self._dict.get(key, None) is None:
            return None
        elif self._dict[key]:
            return _wf_to_char(self._dict[key]).decode('utf-8')
        else:
            return ""

    def _set_source_or_target(self, key, newvalue):
        if newvalue is None:
            self._dict[key] = None
        if isinstance(newvalue, unicode):
            newvalue = newvalue.encode('utf-8')
        newvalue = _char_to_wf(newvalue)
        if not key in self._dict or newvalue != self._dict[key]:
            self._dict[key] = newvalue
            self._update_timestamp()

    def getsource(self):
        return self._get_source_or_target('source')

    def setsource(self, newsource):
        return self._set_source_or_target('source', newsource)
    source = property(getsource, setsource)

    def gettarget(self):
        return self._get_source_or_target('target')

    def settarget(self, newtarget):
        return self._set_source_or_target('target', newtarget)
    target = property(gettarget, settarget)

    def settargetlang(self, newlang):
        self._dict['target-lang'] = newlang
    targetlang = property(None, settargetlang)

    def __str__(self):
        return str(self._dict)

    def istranslated(self):
        if not self._dict.get('source', None):
            return False
        return bool(self._dict.get('target', None))


class WordfastTMFile(base.TranslationStore):
    """A Wordfast translation memory file"""
    Name = _("Wordfast Translation Memory")
    Mimetypes  = ["application/x-wordfast"]
    Extensions = ["txt"]
    def __init__(self, inputfile=None, unitclass=WordfastUnit):
        """construct a Wordfast TM, optionally reading in from inputfile."""
        self.UnitClass = unitclass
        base.TranslationStore.__init__(self, unitclass=unitclass)
        self.filename = ''
        self.header = WordfastHeader()
        self._encoding = 'iso-8859-1'
        if inputfile is not None:
            self.parse(inputfile)

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
        if TAB_UTF16 in input.split("\n")[0]:
            self._encoding = 'utf-16'
        else:
            self._encoding = 'iso-8859-1'
        try:
            input = input.decode(self._encoding).encode('utf-8')
        except:
            raise ValueError("Wordfast files are either UTF-16 (UCS2) or ISO-8859-1 encoded")
        for header in csv.DictReader(input.split("\n")[:1], fieldnames=WF_FIELDNAMES_HEADER, dialect="wordfast"):
            self.header = WordfastHeader(header)
        lines = csv.DictReader(input.split("\n")[1:], fieldnames=WF_FIELDNAMES, dialect="wordfast")
        for line in lines:
            newunit = WordfastUnit()
            newunit.dict = line
            self.addunit(newunit)

    def __str__(self):
        output = csv.StringIO()
        header_output = csv.StringIO()
        writer = csv.DictWriter(output, fieldnames=WF_FIELDNAMES, dialect="wordfast")
        unit_count = 0
        for unit in self.units:
            if unit.istranslated():
                unit_count += 1
                writer.writerow(unit.dict)
        if unit_count == 0:
            return ""
        output.reset()
        self.header.tucount = unit_count
        outheader = csv.DictWriter(header_output, fieldnames=WF_FIELDNAMES_HEADER, dialect="wordfast")
        outheader.writerow(self.header.header)
        header_output.reset()
        decoded = "".join(header_output.readlines() + output.readlines()).decode('utf-8')
        try:
            return decoded.encode(self._encoding)
        except UnicodeEncodeError:
            return decoded.encode('utf-16')
        

