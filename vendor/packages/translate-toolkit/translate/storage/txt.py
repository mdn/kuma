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

"""This class implements the functionality for handling plain text files, or 
similar wiki type files.

Supported formats are 
  - Plain text
  - dokuwiki
  - MediaWiki
""" 

from translate.storage import base
import re

dokuwiki = []
dokuwiki.append(("Dokuwiki heading", re.compile(r"( ?={2,6}[\s]*)(.+)"), re.compile("([\s]*={2,6}[\s]*)$")))
dokuwiki.append(("Dokuwiki bullet", re.compile(r"([\s]{2,}\*[\s]*)(.+)"), re.compile("[\s]+$")))
dokuwiki.append(("Dokuwiki numbered item", re.compile(r"([\s]{2,}-[\s]*)(.+)"), re.compile("[\s]+$")))

mediawiki = []
mediawiki.append(("MediaWiki heading", re.compile(r"(={2,5}[\s]*)(.+)"), re.compile("([\s]*={2,5}[\s]*)$")))
mediawiki.append(("MediaWiki bullet", re.compile(r"(\*+[\s]*)(.+)"), re.compile("[\s]+$")))
mediawiki.append(("MediaWiki numbered item", re.compile(r"(#+[\s]*)(.+)"), re.compile("[\s]+$")))

flavours = {
"dokuwiki": dokuwiki,
"mediawiki": mediawiki,
None: [],
"plain": []
}

class TxtUnit(base.TranslationUnit):
    """This class represents a block of text from a text file"""
    def __init__(self, source="", encoding="utf-8"):
        """Construct the txtunit"""
        self.encoding = encoding
        super(TxtUnit, self).__init__(source)
        self.source = source
        self.pretext = ""
        self.posttext = ""
        self.location = []

    def __str__(self):
        """Convert a txt unit to a string"""
        string = u"".join([self.pretext, self.source, self.posttext])
        if isinstance(string, unicode):
            return string.encode(self.encoding)
        return string

    # Note that source and target are equivalent for monolingual units
    def setsource(self, source):
        """Sets the definition to the quoted value of source"""
        if isinstance(source, str):
            source = source.decode(self.encoding)
        self._source = source

    def getsource(self):
        """gets the unquoted source string"""
        return self._source
    source = property(getsource, setsource)

    def settarget(self, target):
        """Sets the definition to the quoted value of target"""
        self.source = target

    def gettarget(self):
        """gets the unquoted target string"""
        return self.source
    target = property(gettarget, settarget)

    def addlocation(self, location):
        self.location.append(location)

    def getlocations(self):
        return self.location

class TxtFile(base.TranslationStore):
    """This class represents a text file, made up of txtunits"""
    UnitClass = TxtUnit
    def __init__(self, inputfile=None, flavour=None, encoding="utf-8"):
        base.TranslationStore.__init__(self, unitclass=self.UnitClass)
        self.filename = getattr(inputfile, 'name', '')
        self.flavour = flavours.get(flavour, [])
        if inputfile is not None:
            txtsrc = inputfile.readlines()
            self.parse(txtsrc)
        self.encoding = encoding

    def parse(self, lines):
        """Read in text lines and create txtunits from the blocks of text"""
        block = []
        startline = 0
        pretext = ""
        posttext = ""
        if not isinstance(lines, list):
            lines = lines.split("\n")
        for linenum in range(len(lines)):
            line = lines[linenum].rstrip("\n").rstrip("\r")
            for rule, prere, postre in self.flavour:
                match = prere.match(line)
                if match:
                    pretext, source = match.groups()
                    postmatch = postre.search(source)
                    if postmatch:
                        posttext = postmatch.group()
                        source = source[:postmatch.start()]
                    block.append(source)
                    isbreak = True
                    break
            else:
                isbreak = not line.strip()
            if isbreak and block:
                unit = self.addsourceunit("\n".join(block))
                unit.addlocation("%s:%d" % (self.filename, startline + 1))
                unit.pretext = pretext
                unit.posttext = posttext
                pretext = ""
                posttext = ""
                block = []
            elif not isbreak:
                if not block:
                    startline = linenum
                block.append(line)
        if block:
            unit = self.addsourceunit("\n".join(block))
            unit.addlocation("%s:%d" % (self.filename, startline + 1))

    def __str__(self):
        source = self.getoutput()
        if isinstance(source, unicode):
            return source.encode(getattr(self, "encoding", "UTF-8"))
        return source

    def getoutput(self):
        """Convert the units back to blocks"""
        blocks = [str(unit) for unit in self.units]
        string = "\n\n".join(blocks)
        return string
