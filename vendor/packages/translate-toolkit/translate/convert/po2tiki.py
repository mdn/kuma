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

""" Convert .po files to TikiWiki's language.php files. """

import sys
from translate.storage import tiki
from translate.storage import po

class po2tiki:
    def convertstore(self, thepofile):
        """Converts a given (parsed) po file to a tiki file.

        @param thepofile: a pofile pre-loaded with input data
        """
        thetargetfile = tiki.TikiStore()
        for unit in thepofile.units:
            if not (unit.isblank() or unit.isheader()):
                newunit = tiki.TikiUnit(unit.source)
                newunit.settarget(unit.target)
                locations = unit.getlocations()
                if locations:
                    newunit.addlocations(locations)
                # If a word is "untranslated" but the target isn't empty and isn't the same as the source
                # it's been translated and we switch it. This is an assumption but should remain true as long
                # as these scripts are used.
                if newunit.getlocations() == ["untranslated"] and unit.source != unit.target and unit.target != "":
                    newunit.location = []
                    newunit.addlocation("translated")

                thetargetfile.addunit(newunit)
        return thetargetfile

def convertpo(inputfile, outputfile, template=None):
    """Converts from po file format to tiki.

    @param inputfile: file handle of the source
    @param outputfile: file handle to write to
    @param template: unused
    """
    inputstore = po.pofile(inputfile)
    if inputstore.isempty():
        return False
    convertor = po2tiki()
    outputstore = convertor.convertstore(inputstore)
    outputfile.write(str(outputstore))
    return True

def main(argv=None):
    """Will convert from .po to tiki style .php"""
    from translate.convert import convert
    from translate.misc import stdiotell
    sys.stdout = stdiotell.StdIOWrapper(sys.stdout)

    formats = {"po":("tiki",convertpo)}

    parser = convert.ConvertOptionParser(formats, description=__doc__)
    parser.run(argv)

if __name__ == '__main__':
    main()
