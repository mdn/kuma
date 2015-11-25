#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2006 Zuza Software Foundation
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

"""Convert Gettext PO localization files to HTML files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/html2po.html
for examples and usage instructions.
"""

from translate.convert import convert
from translate.storage import html, po


class po2html:
    """po2html can take a po file and generate html. best to give it a
    template file otherwise will just concat msgstrs"""

    def lookup(self, string):
        unit = self.inputstore.sourceindex.get(string, None)
        if unit is None:
            return string
        unit = unit[0]
        if unit.istranslated():
            return unit.target
        if self.includefuzzy and unit.isfuzzy():
            return unit.target
        return unit.source

    def mergestore(self, inputstore, templatetext, includefuzzy):
        """converts a file to .po format"""
        self.inputstore = inputstore
        self.inputstore.makeindex()
        self.includefuzzy = includefuzzy
        output_store = html.htmlfile(inputfile=templatetext, callback=self.lookup)
        return output_store.filesrc


def converthtml(inputfile, outputfile, templatefile, includefuzzy=False,
                outputthreshold=None):
    """reads in stdin using fromfileclass, converts using convertorclass,
    writes to stdout"""
    inputstore = po.pofile(inputfile)

    if not convert.should_output_store(inputstore, outputthreshold):
        return False

    convertor = po2html()
    if templatefile is None:
        raise ValueError("must have template file for HTML files")
    else:
        outputstring = convertor.mergestore(inputstore, templatefile,
                                            includefuzzy)
    outputfilepos = outputfile.tell()
    outputfile.write(outputstring.encode('utf-8'))
    return 1


def main(argv=None):
    from translate.misc import stdiotell
    import sys
    sys.stdout = stdiotell.StdIOWrapper(sys.stdout)
    formats = {
        ("po", "htm"): ("htm", converthtml),
        ("po", "html"): ("html", converthtml),
        ("po", "xhtml"): ("xhtml", converthtml),
        ("po"): ("html", converthtml),
    }
    parser = convert.ConvertOptionParser(formats, usetemplates=True,
                                         description=__doc__)
    parser.add_threshold_option()
    parser.add_fuzzy_option()
    parser.run(argv)


if __name__ == '__main__':
    main()
