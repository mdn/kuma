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
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Produces a clean file from an unclean file (Trados/Wordfast) by stripping
out the tw4win indicators.

This does not convert an RTF file to PO/XLIFF, but produces the target file
with only the target text in from a text version of the RTF.
"""

import re

from translate.misc.multistring import multistring
from translate.storage import factory


tw4winre = re.compile(r"\{0>.*?<\}\d{1,3}\{>(.*?)<0\}", re.M | re.S)


def cleanunit(unit):
    """cleans the targets in the given unit"""
    if isinstance(unit.target, multistring):
        strings = unit.target.strings
    else:
        strings = [unit.target]
    for index, string in enumerate(strings):
        string = string.replace("\par", "")
        strings[index] = tw4winre.sub(r"\1", string)
    if len(strings) == 1:
        unit.target = strings[0]
    else:
        unit.target = strings


def cleanfile(thefile):
    """cleans the given file"""
    for unit in thefile.units:
        cleanunit(unit)
    return thefile


def runclean(inputfile, outputfile, templatefile):
    """reads in inputfile, cleans, writes to outputfile"""
    fromfile = factory.getobject(inputfile)

    cleanfile(fromfile)
#    if fromfile.isempty():
#        return False
    outputfile.write(str(fromfile))
    return True


def main():
    from translate.convert import convert
    formats = {"po": ("po", runclean), "xlf": ("xlf", runclean), None: ("po", runclean)}
    parser = convert.ConvertOptionParser(formats, usetemplates=False, description=__doc__)
    parser.run()


if __name__ == '__main__':
    main()
