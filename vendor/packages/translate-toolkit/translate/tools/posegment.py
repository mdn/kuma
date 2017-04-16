#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

"""Segment Gettext PO, XLIFF and TMX localization files at the sentence level.

See: http://translate.sourceforge.net/wiki/toolkit/posegment for examples and
usage instructions
"""

from translate.storage import factory
from translate.lang import factory as lang_factory

class segment:

    def __init__(self, sourcelang, targetlang, stripspaces=True):
        self.sourcelang = sourcelang
        self.targetlang = targetlang
        self.stripspaces = stripspaces

    def segmentunit(self, unit):
        if unit.isheader() or unit.hasplural():
            return [unit]
        sourcesegments = self.sourcelang.sentences(unit.source, strip=self.stripspaces)
        targetsegments = self.targetlang.sentences(unit.target, strip=self.stripspaces)
        if unit.istranslated() and (len(sourcesegments) != len(targetsegments)):
            return [unit]
        # We could do more here to check if the lengths correspond more or less,
        # certain quality checks are passed, etc.  But for now this is a good
        # start.
        units = []
        for i in range(len(sourcesegments)):
            newunit = unit.copy()
            newunit.source = sourcesegments[i]
            if not unit.istranslated():
                newunit.target = ""
            else:
                newunit.target = targetsegments[i]
            units.append(newunit)
        return units

    def convertstore(self, fromstore):
        tostore = type(fromstore)()
        for unit in fromstore.units:
            newunits = self.segmentunit(unit)
            for newunit in newunits:
                tostore.addunit(newunit)
        return tostore

def segmentfile(inputfile, outputfile, templatefile, sourcelanguage="en", targetlanguage=None, stripspaces=True):
    """reads in inputfile, segments it then, writes to outputfile"""
    # note that templatefile is not used, but it is required by the converter...
    inputstore = factory.getobject(inputfile)
    if inputstore.isempty():
        return 0
    sourcelang = lang_factory.getlanguage(sourcelanguage)
    targetlang = lang_factory.getlanguage(targetlanguage)
    convertor = segment(sourcelang, targetlang, stripspaces=stripspaces)
    outputstore = convertor.convertstore(inputstore)
    outputfile.write(str(outputstore))
    return 1

def main():
    from translate.convert import convert
    formats = {"po":("po", segmentfile), "xlf":("xlf", segmentfile), "tmx": ("tmx", segmentfile)}
    parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
    parser.add_option("-l", "--language", dest="targetlanguage", default=None,
            help="the target language code", metavar="LANG")
    parser.add_option("", "--source-language", dest="sourcelanguage", default=None, 
            help="the source language code (default 'en')", metavar="LANG")
    parser.passthrough.append("sourcelanguage")
    parser.passthrough.append("targetlanguage")
    parser.add_option("", "--keepspaces", dest="stripspaces", action="store_false",
            default=True, help="Disable automatic stripping of whitespace")
    parser.passthrough.append("stripspaces")
    parser.run()


if __name__ == '__main__':
    main()
