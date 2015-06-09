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

"""Convert Mozilla .lang files to Gettext PO localization files.
"""

from translate.storage import mozilla_lang as lang, po


class lang2po:

    def __init__(self, duplicatestyle="msgctxt"):
        self.duplicatestyle = duplicatestyle

    def convertstore(self, thelangfile):
        """converts a file to .po format"""
        thetargetfile = po.pofile()

        # Set up the header
        targetheader = thetargetfile.header()
        targetheader.addnote("extracted from %s" %
                             thelangfile.filename, "developer")

        # For each lang unit, make the new po unit accordingly
        for langunit in thelangfile.units:
            newunit = thetargetfile.addsourceunit(langunit.source)
            newunit.settarget(langunit.target)
            newunit.addlocations(langunit.getlocations())
            newunit.addnote(langunit.getnotes(), 'developer')

        # Remove duplicates, because we can
        thetargetfile.removeduplicates(self.duplicatestyle)
        return thetargetfile


def convertlang(inputfile, outputfile, templates, pot=False,
                duplicatestyle="msgctxt", encoding="utf-8"):
    """reads in stdin using fromfileclass, converts using convertorclass,
    writes to stdout"""
    inputstore = lang.LangStore(inputfile, encoding=encoding)
    convertor = lang2po(duplicatestyle=duplicatestyle)
    outputstore = convertor.convertstore(inputstore)
    if outputstore.isempty():
        return 0
    outputfile.write(str(outputstore))
    return 1


formats = {
    "lang": ("po", convertlang)
}


def main(argv=None):
    from translate.convert import convert
    from translate.misc import stdiotell
    import sys
    sys.stdout = stdiotell.StdIOWrapper(sys.stdout)
    parser = convert.ConvertOptionParser(formats, usepots=True,
                                           description=__doc__)
    parser.add_option("", "--encoding", dest="encoding", default='utf-8',
    help="The encoding of the input file (default: UTF-8)")
    parser.passthrough.append("encoding")
    parser.add_duplicates_option()
    parser.run(argv)


if __name__ == '__main__':
    main()
