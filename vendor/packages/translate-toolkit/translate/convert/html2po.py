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
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""convert HTML files to Gettext PO localization files

See: http://translate.sourceforge.net/wiki/toolkit/html2po for examples and 
usage instructions
"""

from translate.storage import po
from translate.storage import html

class html2po:
    def convertfile(self, inputfile, filename, includeheader, includeuntagged=False, duplicatestyle="msgctxt", keepcomments=False):
        """converts a html file to .po format"""
        thetargetfile = po.pofile()
        htmlparser = html.htmlfile(includeuntaggeddata=includeuntagged, inputfile=inputfile)
        if includeheader:
            targetheader = thetargetfile.init_headers(charset="UTF-8", encoding="8bit")
        for htmlunit in htmlparser.units:
            thepo = thetargetfile.addsourceunit(htmlunit.source)
            thepo.addlocations(htmlunit.getlocations())
            if keepcomments:
                thepo.addnote(htmlunit.getnotes(), "developer")
        thetargetfile.removeduplicates(duplicatestyle)
        return thetargetfile

def converthtml(inputfile, outputfile, templates, includeuntagged=False, pot=False, duplicatestyle="msgctxt", keepcomments=False):
    """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
    convertor = html2po()
    outputfilepos = outputfile.tell()
    includeheader = outputfilepos == 0
    outputstore = convertor.convertfile(inputfile, getattr(inputfile, "name", "unknown"), includeheader, includeuntagged, duplicatestyle=duplicatestyle, keepcomments=keepcomments)
    outputfile.write(str(outputstore))
    return 1

def main(argv=None):
    from translate.convert import convert
    from translate.misc import stdiotell
    import sys
    sys.stdout = stdiotell.StdIOWrapper(sys.stdout)
    formats = {"html":("po", converthtml), "htm":("po", converthtml), "xhtml":("po", converthtml), None:("po", converthtml)}
    parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
    parser.add_option("-u", "--untagged", dest="includeuntagged", default=False, action="store_true",
            help="include untagged sections")
    parser.passthrough.append("includeuntagged")
    parser.add_option("--keepcomments", dest="keepcomments", default=False, action="store_true",
            help="preserve html comments as translation notes in the output")
    parser.passthrough.append("keepcomments")
    parser.add_duplicates_option()
    parser.passthrough.append("pot")
    parser.run(argv)


if __name__ == '__main__':
    main()
