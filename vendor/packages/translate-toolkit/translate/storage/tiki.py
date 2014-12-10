#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Mozilla Corporation, Zuza Software Foundation
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

"""Class that manages TikiWiki files for translation.  Tiki files are <strike>ugly and
inconsistent</strike> formatted as a single large PHP array with several special 
sections identified by comments.  Example current as of 2008-12-01::

  <?php
    // Many comments at the top
    $lang=Array(
    // ### Start of unused words
    "aaa" => "zzz",
    // ### end of unused words
    
    // ### start of untranslated words
    // "bbb" => "yyy",
    // ### end of untranslated words
    
    // ### start of possibly untranslated words
    "ccc" => "xxx",
    // ### end of possibly untranslated words
    
    "ddd" => "www",
    "###end###"=>"###end###");
  ?>

In addition there are several auto-generated //-style comments scattered through the 
page and array, some of which matter when being parsed.

This has all been gleaned from the 
U{TikiWiki source<http://tikiwiki.svn.sourceforge.net/viewvc/tikiwiki/trunk/get_strings.php?view=markup>}.
As far as I know no detailed documentation exists for the tiki language.php files.

"""

from translate.storage import base
from translate.misc import wStringIO
import re
import datetime

class TikiUnit(base.TranslationUnit):
    """A tiki unit entry."""
    def __init__(self, source=None, encoding="UTF-8"):
        self.location = []
        super(TikiUnit, self).__init__(source)

    def __unicode__(self):
        """Returns a string formatted to be inserted into a tiki language.php file."""
        ret = u'"%s" => "%s",' % (self.source, self.target)
        if self.location == ["untranslated"]:
            ret = u'// ' + ret
        return ret + "\n"

    def addlocation(self, location):
        """Location is defined by the comments in the file. This function will only
        set valid locations.
        
        @param location: Where the string is located in the file.  Must be a valid location.
        """
        if location in ['unused', 'untranslated', 'possiblyuntranslated', 'translated']:
            self.location.append(location)

    def getlocations(self):
        """Returns the a list of the location(s) of the string."""
        return self.location

class TikiStore(base.TranslationStore):
    """Represents a tiki language.php file."""
    def __init__(self, inputfile=None):
        """If an inputfile is specified it will be parsed.

        @param inputfile: Either a string or a filehandle of the source file
        """
        base.TranslationStore.__init__(self, TikiUnit)
        self.units = []
        self.filename = getattr(inputfile, 'name', '')
        if inputfile is not None:
            self.parse(inputfile)

    def __str__(self):
        """Will return a formatted tiki-style language.php file."""
        _unused = []
        _untranslated = []
        _possiblyuntranslated = []
        _translated = []

        output = self._tiki_header()

        # Reorder all the units into their groups
        for unit in self.units:
            if unit.getlocations() == ["unused"]:
                _unused.append(unit)
            elif unit.getlocations() == ["untranslated"]:
                _untranslated.append(unit)
            elif unit.getlocations() == ["possiblyuntranslated"]:
                _possiblyuntranslated.append(unit)
            else:
                _translated.append(unit)

        output += "// ### Start of unused words\n"
        for unit in _unused:
            output += unicode(unit)
        output += "// ### end of unused words\n\n"
        output += "// ### start of untranslated words\n"
        for unit in _untranslated:
            output += unicode(unit)
        output += "// ### end of untranslated words\n\n"
        output += "// ### start of possibly untranslated words\n"
        for unit in _possiblyuntranslated:
            output += unicode(unit)
        output += "// ### end of possibly untranslated words\n\n"
        for unit in _translated:
            output += unicode(unit)

        output += self._tiki_footer()
        return output.encode('UTF-8')

    def _tiki_header(self):
        """Returns a tiki-file header string."""
        return u"<?php // -*- coding:utf-8 -*-\n// Generated from po2tiki on %s\n\n$lang=Array(\n" % datetime.datetime.now()

    def _tiki_footer(self):
        """Returns a tiki-file footer string."""
        return u'"###end###"=>"###end###");\n?>'

    def parse(self, input):
        """Parse the given input into source units.
        
        @param input: the source, either a string or filehandle
        """
        if hasattr(input, "name"):
            self.filename = input.name

        if isinstance(input, str):
            input = wStringIO.StringIO(input)

        _split_regex = re.compile(r"^(?:// )?\"(.*)\" => \"(.*)\",$", re.UNICODE)

        try:
            _location = "translated"

            for line in input:
                # The tiki file fails to identify each section so we have to look for start and end
                # points and if we're outside of them we assume the string is translated
                if line.count("### Start of unused words"):
                    _location = "unused"
                elif line.count("### start of untranslated words"):
                    _location = "untranslated"
                elif line.count("### start of possibly untranslated words"):
                    _location = "possiblyuntranslated"
                elif line.count("### end of unused words"):
                    _location = "translated"
                elif line.count("### end of untranslated words"):
                    _location = "translated"
                elif line.count("### end of possibly untranslated words"):
                    _location = "translated"

                match = _split_regex.match(line)

                if match:
                    unit = self.addsourceunit("".join(match.group(1)))
                    # Untranslated words get an empty msgstr
                    if not _location == "untranslated":
                        unit.settarget(match.group(2))
                    unit.addlocation(_location)
        finally:
            input.close()
