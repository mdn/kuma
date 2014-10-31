#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of translate.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# (c) 2009 Dominic König (dominic@nursix.org)
#

"""convert web2py translation dictionaries (.py) to GNU/gettext PO files"""

from translate.storage import po

class web2py2po:
    def __init__(self, pofile=None):
        self.mypofile = pofile

    def convertunit(self, source_str, target_str):
        pounit = po.pounit(encoding="UTF-8")
        pounit.setsource( source_str )
        if target_str:
            pounit.settarget( target_str )
        return pounit

    def convertstore(self, mydict):

        targetheader = self.mypofile.init_headers(charset="UTF-8", encoding="8bit")
        targetheader.addnote("extracted from web2py", "developer")

        for source_str in mydict.keys():
            target_str = mydict[source_str]
            if target_str.startswith('*** '):
                target_str = ''
            pounit = self.convertunit(source_str, target_str)
            self.mypofile.addunit(pounit)

        return self.mypofile

def convertpy(inputfile, outputfile, encoding="UTF-8"):

    new_pofile = po.pofile()
    convertor = web2py2po(new_pofile)

    mydict = eval(inputfile.read())
    if not isinstance(mydict, dict):
        return 0

    outputstore = convertor.convertstore(mydict)

    if outputstore.isempty():
        return 0

    outputfile.write(str(outputstore))
    return 1

def main(argv=None):
    from translate.convert import convert
    formats = {("py", "po"): ("po", convertpy), ("py", None): ("po", convertpy)}
    parser = convert.ConvertOptionParser(formats, usetemplates=False, description=__doc__)
    parser.run(argv)

if __name__ == '__main__':
    main()
