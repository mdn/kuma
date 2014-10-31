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

"""Builds a new translation file with the target of the input language as 
source language.

Ensure that the two po files correspond 100% to the same pot file before using
this.

To translate Kurdish (ku) through French::
    po2swap -i fr/ -t ku -o fr-ku

To convert the fr-ku files back to en-ku::
    po2swap --reverse -i fr/ -t fr-ku -o en-ku

See: http://translate.sourceforge.net/wiki/toolkit/poswap for further examples and
usage instructions
"""

from translate.storage import po
from translate.convert import convert

def swapdir(store):
    """Swap the source and target of each unit."""
    for unit in store.units:
        if unit.isheader():
            continue
        if not unit.target or unit.isfuzzy():
            unit.target = unit.source
        else:
            unit.source, unit.target = unit.target, unit.source

def convertpo(inputpofile, outputpotfile, template, reverse=False):
    """reads in inputpofile, removes the header, writes to outputpotfile."""
    inputpo = po.pofile(inputpofile)
    templatepo = po.pofile(template)
    if reverse:
        swapdir(inputpo)
    templatepo.makeindex()
    header = inputpo.header()
    if header:
        inputpo.units = inputpo.units[1:]

    for i, unit in enumerate(inputpo.units):
        for location in unit.getlocations():
            templateunit = templatepo.locationindex.get(location, None)
            if templateunit and templateunit.source == unit.source:
                break
        else:
            templateunit = templatepo.findunit(unit.source)

        unit.othercomments = []
        if unit.target and not unit.isfuzzy():
            unit.source = unit.target
        elif not reverse:
            if inputpo.filename:
                unit.addnote("No translation found in %s" % inputpo.filename, origin="programmer")
            else:
                unit.addnote("No translation found in the supplied source language", origin="programmer")
        unit.target = ""
        unit.markfuzzy(False)
        if templateunit:
            unit.addnote(templateunit.getnotes(origin="translator"))
            unit.markfuzzy(templateunit.isfuzzy())
            unit.target = templateunit.target
        if unit.isobsolete():
            del inputpo.units[i]
    outputpotfile.write(str(inputpo))
    return 1

def main(argv=None):
    formats = {("po", "po"): ("po", convertpo), ("po", "pot"): ("po", convertpo), "po": ("po", convertpo)}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, description=__doc__)
    parser.add_option("", "--reverse", dest="reverse", default=False, action="store_true",
                    help="reverse the process of intermediate language conversion")
    parser.passthrough.append("reverse")
    parser.run(argv)

if __name__ == '__main__':
    main()

