#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2003-2006 Zuza Software Foundation
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

"""Convert Gettext PO localization files to Comma-Separated Value (.csv) files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/csv2po.html
for examples and usage instructions.
"""

from translate.storage import csvl10n, po


class po2csv:

    def convertcomments(self, inputunit):
        return " ".join(inputunit.getlocations())

    def convertunit(self, inputunit):
        csvunit = csvl10n.csvunit()
        if inputunit.isheader():
            return None
            #csvunit.location = "location"
            #csvunit.source = "source"
            #csvunit.target = "target"
        elif inputunit.isblank():
            return None
        else:
            csvunit.location = self.convertcomments(inputunit)
            csvunit.source = inputunit.source
            csvunit.target = inputunit.target
        return csvunit

    def convertplurals(self, inputunit):
        """Convert PO plural units

        We only convert the first plural form.  So languages with multiple
        plurals are not handled.  For single plural languages we simply
        skip this plural extraction.
        """
        if len(inputunit.target.strings) == 1:  # No plural forms
            return None
        csvunit = csvl10n.csvunit()
        csvunit.location = self.convertcomments(inputunit)
        csvunit.source = inputunit.source.strings[1]
        csvunit.target = inputunit.target.strings[1]
        return csvunit

    def convertstore(self, inputstore, columnorder=None):
        if columnorder is None:
            columnorder = ['location', 'source', 'target']
        outputstore = csvl10n.csvfile(fieldnames=columnorder)
        for inputunit in inputstore.units:
            outputunit = self.convertunit(inputunit)
            if outputunit is not None:
                outputstore.addunit(outputunit)
            if inputunit.hasplural():
                outputunit = self.convertplurals(inputunit)
                if outputunit is not None:
                    outputstore.addunit(outputunit)
        return outputstore


def convertcsv(inputfile, outputfile, templatefile, columnorder=None):
    """reads in inputfile using po, converts using po2csv, writes to outputfile"""
    # note that templatefile is not used, but it is required by the converter...
    inputstore = po.pofile(inputfile)
    if inputstore.isempty():
        return 0
    convertor = po2csv()
    outputstore = convertor.convertstore(inputstore, columnorder)
    outputfile.write(str(outputstore))
    return 1


def main(argv=None):
    from translate.convert import convert
    formats = {"po": ("csv", convertcsv)}
    parser = convert.ConvertOptionParser(formats, description=__doc__)
    parser.add_option("", "--columnorder", dest="columnorder", default=None,
        help="specify the order and position of columns (location,source,target)")
    parser.passthrough.append("columnorder")
    parser.run(argv)


if __name__ == '__main__':
    main()
