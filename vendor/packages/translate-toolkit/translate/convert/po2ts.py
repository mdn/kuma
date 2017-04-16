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

"""convert Gettext PO localization files to Qt Linguist (.ts) files

see: http://translate.sourceforge.net/wiki/toolkit/po2ts for examples and 
usage instructions
"""

from translate.storage import po
from translate.storage import ts

class po2ts:
    def convertstore(self, inputstore, templatefile=None, context=None):
        """converts a .po file to .ts format (using a template .ts file if given)"""
        if templatefile is None: 
            tsfile = ts.QtTsParser()
        else:
            tsfile = ts.QtTsParser(templatefile)
        for inputunit in inputstore.units:
            if inputunit.isheader() or inputunit.isblank():
                continue
            source = inputunit.source
            translation = inputunit.target
            comment = inputunit.getnotes("translator")
            transtype = None
            if not inputunit.istranslated():
                transtype = "unfinished"
            elif inputunit.getnotes("developer") == "(obsolete)":
                transtype = "obsolete" 
            if isinstance(source, str):
                source = source.decode("utf-8")
            if isinstance(translation, str):
                translation = translation.decode("utf-8")
            for sourcelocation in inputunit.getlocations():
                if context is None:
                    if "#" in sourcelocation:
                        contextname = sourcelocation[:sourcelocation.find("#")]
                    else:
                        contextname = sourcelocation
                else:
                    contextname = context
                tsfile.addtranslation(contextname, source, translation, comment, transtype, createifmissing=True)
        return tsfile.getxml()

def convertpo(inputfile, outputfile, templatefile, context):
    """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
    inputstore = po.pofile(inputfile)
    if inputstore.isempty():
        return 0
    convertor = po2ts()
    outputstring = convertor.convertstore(inputstore, templatefile, context)
    outputfile.write(outputstring)
    return 1

def main(argv=None):
    from translate.convert import convert
    formats = {"po": ("ts", convertpo), ("po", "ts"): ("ts", convertpo)}
    parser = convert.ConvertOptionParser(formats, usepots=False, usetemplates=True, description=__doc__)
    parser.add_option("-c", "--context", dest="context", default=None,
                      help="use supplied context instead of the one in the .po file comment")
    parser.passthrough.append("context")
    parser.run(argv)


if __name__ == '__main__':
    main()
