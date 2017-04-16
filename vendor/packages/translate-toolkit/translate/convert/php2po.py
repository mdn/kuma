#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2006 Zuza Software Foundation
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

"""convert PHP localization files to Gettext PO localization files

See: http://translate.sourceforge.net/wiki/toolkit/php2po for examples and
usage instructions
"""

import sys
from translate.storage import po
from translate.storage import php

class php2po:
    """convert a .php file to a .po file for handling the translation..."""
    def convertstore(self, inputstore, duplicatestyle="msgctxt"):
        """converts a .php file to a .po file..."""
        outputstore = po.pofile()
        outputheader = outputstore.init_headers(charset="UTF-8", encoding="8bit")
        outputheader.addnote("extracted from %s" % inputstore.filename, "developer")

        for inputunit in inputstore.units:
            outputunit = self.convertunit(inputunit, "developer")
            if outputunit is not None:
                outputstore.addunit(outputunit)
        outputstore.removeduplicates(duplicatestyle)
        return outputstore

    def mergestore(self, templatestore, inputstore, blankmsgstr=False, duplicatestyle="msgctxt"):
        """converts two .properties files to a .po file..."""
        outputstore = po.pofile()
        outputheader = outputstore.init_headers(charset="UTF-8", encoding="8bit")
        outputheader.addnote("extracted from %s, %s" % (templatestore.filename, inputstore.filename), "developer")

        inputstore.makeindex()
        # loop through the original file, looking at units one by one
        for templateunit in templatestore.units:
            outputunit = self.convertunit(templateunit, "developer")
            # try and find a translation of the same name...
            if templateunit.name in inputstore.locationindex:
                translatedinputunit = inputstore.locationindex[templateunit.name]
                # Need to check that this comment is not a copy of the developer comments
                translatedoutputunit = self.convertunit(translatedinputunit, "translator")
            else:
                translatedoutputunit = None
            # if we have a valid po unit, get the translation and add it...
            if outputunit is not None:
                if translatedoutputunit is not None and not blankmsgstr:
                    outputunit.target = translatedoutputunit.source
                outputstore.addunit(outputunit)
            elif translatedoutputunit is not None:
                print >> sys.stderr, "error converting original properties definition %s" % templateunit.name
        outputstore.removeduplicates(duplicatestyle)
        return outputstore

    def convertunit(self, inputunit, origin):
        """Converts a .php unit to a .po unit"""
        outputunit = po.pounit(encoding="UTF-8")
        outputunit.addnote(inputunit.getnotes(origin), origin)
        outputunit.addlocation("".join(inputunit.getlocations()))
        outputunit.source = inputunit.source
        outputunit.target = ""
        return outputunit

def convertphp(inputfile, outputfile, templatefile, pot=False, duplicatestyle="msgctxt"):
    """reads in inputfile using php, converts using php2po, writes to outputfile"""
    inputstore = php.phpfile(inputfile)
    convertor = php2po()
    if templatefile is None:
        outputstore = convertor.convertstore(inputstore, duplicatestyle=duplicatestyle)
    else:
        templatestore = php.phpfile(templatefile)
        outputstore = convertor.mergestore(templatestore, inputstore, blankmsgstr=pot, duplicatestyle=duplicatestyle)
    if outputstore.isempty():
        return 0
    outputfile.write(str(outputstore))
    return 1

def main(argv=None):
    from translate.convert import convert
    formats = {"php": ("po", convertphp), ("php", "php"): ("po", convertphp)}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, usepots=True, description=__doc__)
    parser.add_duplicates_option()
    parser.passthrough.append("pot")
    parser.run(argv)

if __name__ == '__main__':
    main()

