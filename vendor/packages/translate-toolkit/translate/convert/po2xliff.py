#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2005, 2006 Zuza Software Foundation
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

"""convert Gettext PO localization files to XLIFF localization files

see: http://translate.sourceforge.net/wiki/toolkit/po2xliff for examples and 
usage instructions
"""

from translate.storage import po
from translate.storage import poxliff

class po2xliff:
    def convertunit(self, outputstore, inputunit, filename):
        """creates a transunit node"""
        source = inputunit.source
        target = inputunit.target
        if inputunit.isheader():
            unit = outputstore.addheaderunit(target, filename)
        else:
            unit = outputstore.addsourceunit(source, filename, True)
            unit.target = target
            #Explicitly marking the fuzzy state will ensure that normal (translated)
            #units in the PO file end up as approved in the XLIFF file.
            if target:
                unit.markfuzzy(inputunit.isfuzzy())
            else:
                unit.markapproved(False)
            
            #Handle #: location comments
            for location in inputunit.getlocations():
                unit.createcontextgroup("po-reference", self.contextlist(location), purpose="location")
            
            #Handle #. automatic comments
            comment = inputunit.getnotes("developer")
            if comment:
                unit.createcontextgroup("po-entry", [("x-po-autocomment", comment)], purpose="information")
                unit.addnote(comment, origin="developer")
        
            #TODO: x-format, etc.


        #Handle # other comments
        comment = inputunit.getnotes("translator")
        if comment:
            unit.createcontextgroup("po-entry", [("x-po-trancomment", comment)], purpose="information")
            unit.addnote(comment, origin="po-translator")
            
        return unit

    def contextlist(self, location):
        contexts = []
        if ":" in location:
            sourcefile, linenumber = location.split(":", 1)
        else:
            sourcefile, linenumber = location, None
        contexts.append(("sourcefile", sourcefile))
        if linenumber:
            contexts.append(("linenumber", linenumber))
        return contexts
        
    def convertstore(self, inputstore, templatefile=None, **kwargs):
        """converts a .po file to .xlf format"""
        if templatefile is None: 
            outputstore = poxliff.PoXliffFile(**kwargs)
        else:
            outputstore = poxliff.PoXliffFile(templatefile, **kwargs)
        filename = inputstore.filename
        for inputunit in inputstore.units:
            if inputunit.isblank():
                continue
            transunitnode = self.convertunit(outputstore, inputunit, filename)
        return str(outputstore)

def convertpo(inputfile, outputfile, templatefile):
    """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
    inputstore = po.pofile(inputfile)
    if inputstore.isempty():
        return 0
    convertor = po2xliff()
    outputstring = convertor.convertstore(inputstore, templatefile)
    outputfile.write(outputstring)
    return 1

def main(argv=None):
    from translate.convert import convert
    formats = {"po": ("xlf", convertpo), ("po", "xlf"): ("xlf", convertpo)}
    parser = convert.ConvertOptionParser(formats, usepots=True, usetemplates=True, description=__doc__)
    parser.run(argv)

if __name__ == '__main__':
    main()
