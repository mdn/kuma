#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008, 2011 Zuza Software Foundation
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

# Original Author: Dan Schafer <dschafer@mozilla.com>
# Date: 10 Jun 2008

"""A class to manage Mozilla .lang files."""

from translate.storage import base, txt


class LangUnit(base.TranslationUnit):
    """This is just a normal unit with a weird string output"""

    def __init__(self, source=None):
        self.locations = []
        base.TranslationUnit.__init__(self, source)

    def __str__(self):
        if self.source == self.target:
            unchanged = " {ok}"
        else:
            unchanged = ""
        if not self.istranslated():
            target = self.source
        else:
            target = self.target
        if self.getnotes():
            notes = ('\n').join(["# %s" % note for note in self.getnotes('developer').split("\n")])
            return u"%s\n;%s\n%s%s" % (notes, self.source, target, unchanged)
        return u";%s\n%s%s" % (self.source, target, unchanged)

    def getlocations(self):
        return self.locations

    def addlocation(self, location):
        self.locations.append(location)


class LangStore(txt.TxtFile):
    """We extend TxtFile, since that has a lot of useful stuff for encoding"""
    UnitClass = LangUnit

    Name = "Mozilla .lang"
    Extensions = ['lang']

    def __init__(self, inputfile=None, flavour=None, encoding="utf-8", mark_active=False):
        self.is_active = False
        self.mark_active = mark_active
        super(LangStore, self).__init__(inputfile, flavour, encoding)

    def parse(self, lines):
        #Have we just seen a ';' line, and so are ready for a translation
        readyTrans = False
        comment = ""

        if not isinstance(lines, list):
            lines = lines.split("\n")
        for lineoffset, line in enumerate(lines):
            line = line.decode(self.encoding).rstrip("\n").rstrip("\r")

            if lineoffset == 0 and line == "## active ##":
                self.is_active = True
                continue

            if len(line) == 0 and not readyTrans:  # Skip blank lines
                continue

            if readyTrans:  # If we are expecting a translation, set the target
                if line != u.source:
                    u.target = line.replace(" {ok}", "")
                else:
                    u.target = ""
                readyTrans = False  # We already have our translation
                continue

            if line.startswith('#'):  # A comment
                comment += line[1:].strip() + "\n"

            if line.startswith(';'):
                u = self.addsourceunit(line[1:])
                readyTrans = True  # Now expecting a translation on the next line
                u.addlocation("%s:%d" % (self.filename, lineoffset + 1))
                if comment is not None:
                    u.addnote(comment[:-1], 'developer')
                    comment = ""

    def __str__(self):
        ret_string = ""
        if self.is_active or self.mark_active:
            ret_string += "## active ##\n"
        ret_string += u"\n\n\n".join([unicode(unit) for unit in self.units]).encode('utf-8')
        ret_string += "\n"
        return ret_string
