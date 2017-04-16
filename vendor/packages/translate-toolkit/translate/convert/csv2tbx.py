#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2006-2007 Zuza Software Foundation
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

"""convert Comma-Separated Value (.csv) files to a TermBase eXchange (.tbx) glossary file"""

from translate.misc import sparse
from translate.storage import tbx
from translate.storage import csvl10n

class csv2tbx:
    """a class that takes translations from a .csv file and puts them in a .tbx file"""
    def __init__(self, charset=None):
        """construct the converter..."""
        self.charset = charset

    def convertfile(self, thecsvfile):
        """converts a csvfile to a tbxfile, and returns it. uses templatepo if given at construction"""
        mightbeheader = True
        self.tbxfile = tbx.tbxfile()
        for thecsv in thecsvfile.units:
            if mightbeheader:
                # ignore typical header strings...
                mightbeheader = False
                if [item.strip().lower() for item in thecsv.comment, thecsv.source, thecsv.target] == \
                     ["comment", "original", "translation"]:
                    continue
                if len(thecsv.comment.strip()) == 0 and thecsv.source.find("Content-Type:") != -1:
                    continue
            term = tbx.tbxunit.buildfromunit(thecsv)
            # TODO: we might want to get the location or other information from CSV
            self.tbxfile.addunit(term)
        return self.tbxfile

def convertcsv(inputfile, outputfile, templatefile, charset=None, columnorder=None):
    """reads in inputfile using csvl10n, converts using csv2tbx, writes to outputfile"""
    inputstore = csvl10n.csvfile(inputfile, fieldnames=columnorder)
    convertor = csv2tbx(charset=charset)
    outputstore = convertor.convertfile(inputstore)
    if len(outputstore.units) == 0:
        return 0
    outputfile.write(str(outputstore))
    return 1

def main():
    from translate.convert import convert
    formats = {("csv", "tbx"): ("tbx", convertcsv), ("csv", None): ("tbx", convertcsv)}
    parser = convert.ConvertOptionParser(formats, usetemplates=False, description=__doc__)
    parser.add_option("", "--charset", dest="charset", default=None,
        help="set charset to decode from csv files", metavar="CHARSET")
    parser.add_option("", "--columnorder", dest="columnorder", default=None,
        help="specify the order and position of columns (comment,source,target)")
    parser.passthrough.append("charset")
    parser.passthrough.append("columnorder")
    parser.run()



if __name__ == '__main__':
    main()
