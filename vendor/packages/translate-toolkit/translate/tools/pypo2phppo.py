#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Mozilla Corporation, Zuza Software Foundation
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

""" Convert Python format .po files to PHP format .po files """

import re
import sys
from translate.storage import po
from translate.misc.multistring import multistring

class pypo2phppo:
    def convertstore(self, inputstore):
        """Converts a given .po file (Python Format) to a PHP format .po file, the difference being
            how variable substitutions work.  PHP uses a %1$s format, and Python uses
            a {0} format (zero indexed).  This method will convert, e.g.:
                I have {1} apples and {0} oranges
                    to
                I have %2$s apples and %1$s oranges
            This method ignores strings with %s as both languages will recognize that.
        """
        thetargetfile = po.pofile(inputfile="")

        for unit in inputstore.units:
            newunit = self.convertunit(unit)
            thetargetfile.addunit(newunit)
        return thetargetfile

    def convertunit(self, unit):
        unit.automaticcomments = self.convertstrings(unit.automaticcomments)
        unit.othercomments = self.convertstrings(unit.othercomments)
        unit.source = self.convertstrings(unit.source)
        unit.target = self.convertstrings(unit.target)
        return unit

    def convertstrings(self, input):
        if isinstance(input, multistring):
            strings = input.strings
        elif isinstance(input, list):
            strings = input
        else:
            strings = [input]

        for index, string in enumerate(strings):
            strings[index] = re.sub('\{(\d)\}', lambda x: "%%%d$s" % (int(x.group(1))+1), string)
        return strings[0] if len(strings) == 1 else strings

def convertpy2php(inputfile, outputfile, template=None):
    """Converts from Python .po to PHP .po

    @param inputfile: file handle of the source
    @param outputfile: file handle to write to
    @param template: unused
    """
    convertor = pypo2phppo()
    inputstore = po.pofile(inputfile)
    outputstore = convertor.convertstore(inputstore)
    if outputstore.isempty():
        return False
    outputfile.write(str(outputstore))
    return True

def main(argv=None):
    """Converts from Python .po to PHP .po"""
    from translate.convert import convert

    formats = {"po":("po",convertpy2php)}
    parser = convert.ConvertOptionParser(formats, description=__doc__)
    parser.run(argv)

if __name__ == '__main__':
    main()
