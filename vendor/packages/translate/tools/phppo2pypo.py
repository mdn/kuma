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
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Convert PHP format .po files to Python format .po files.
"""

import re

from translate.misc.multistring import multistring
from translate.storage import po


class phppo2pypo:

    def convertstore(self, inputstore):
        """Converts a given .po file (PHP Format) to a Python format .po file, the difference being
            how variable substitutions work.  PHP uses a %1$s format, and Python uses
            a {0} format (zero indexed).  This method will convert, e.g.:
                I have %2$s apples and %1$s oranges
                    to
                I have {1} apples and {0} oranges
            This method ignores strings with %s as both languages will recognize that.
        """
        thetargetfile = po.pofile(inputfile="")

        for unit in inputstore.units:
            newunit = self.convertunit(unit)
            thetargetfile.addunit(newunit)
        return thetargetfile

    def convertunit(self, unit):
        developer_notes = unit.getnotes(origin="developer")
        translator_notes = unit.getnotes(origin="translator")
        unit.removenotes()
        unit.addnote(self.convertstrings(developer_notes))
        unit.addnote(self.convertstrings(translator_notes))
        unit.source = self.convertstrings(unit.source)
        unit.target = self.convertstrings(unit.target)
        return unit

    def convertstring(self, input):
        return re.sub('%(\d)\$s', lambda x: "{%d}" % (int(x.group(1)) - 1), input)

    def convertstrings(self, input):
        if isinstance(input, multistring):
            strings = input.strings
        elif isinstance(input, list):
            strings = input
        else:
            return self.convertstring(input)
        for index, string in enumerate(strings):
            strings[index] = re.sub('%(\d)\$s', lambda x: "{%d}" % (int(x.group(1)) - 1), string)
        return multistring(strings)


def convertphp2py(inputfile, outputfile, template=None):
    """Converts from PHP .po format to Python .po format

    :param inputfile: file handle of the source
    :param outputfile: file handle to write to
    :param template: unused
    """
    convertor = phppo2pypo()
    inputstore = po.pofile(inputfile)
    outputstore = convertor.convertstore(inputstore)
    if outputstore.isempty():
        return False
    outputfile.write(str(outputstore))
    return True


def main(argv=None):
    """Converts PHP .po files to Python .po files."""
    from translate.convert import convert

    formats = {"po": ("po", convertphp2py)}
    parser = convert.ConvertOptionParser(formats, description=__doc__)
    parser.run(argv)


if __name__ == '__main__':
    main()
