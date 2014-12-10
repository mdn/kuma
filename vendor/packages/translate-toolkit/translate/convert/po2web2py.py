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

"""convert GNU/gettext PO files to web2py translation dictionaries (.py)"""

from translate.storage import factory

class po2pydict:
    def __init__(self):
        return

    def convertstore(self, inputstore, includefuzzy):
        from StringIO import StringIO
        str_obj = StringIO()
        
        mydict = dict()
        for unit in inputstore.units:
            if unit.isheader():
                continue
            if unit.istranslated() or (includefuzzy and unit.isfuzzy()):
                mydict[unit.source] = unit.target
            else:
                mydict[unit.source] = '*** ' + unit.source
        
        str_obj.write('{\n')
        for source_str in mydict:
            str_obj.write("%s:%s,\n" % (repr(str(source_str)),repr(str(mydict[source_str]))))
        str_obj.write('}\n')
        str_obj.seek(0)
        return str_obj

def convertpy(inputfile, outputfile, templatefile=None, includefuzzy=False):
    inputstore = factory.getobject(inputfile)
    convertor = po2pydict()
    outputstring = convertor.convertstore(inputstore, includefuzzy)
    outputfile.write(outputstring.read())
    return 1

def main(argv=None):
    from translate.convert import convert
    from translate.misc import stdiotell
    import sys
    sys.stdout = stdiotell.StdIOWrapper(sys.stdout)
    formats = {("po", "py"):("py", convertpy), ("po"):("py", convertpy)}
    parser = convert.ConvertOptionParser(formats, usetemplates=False, description=__doc__)
    parser.add_fuzzy_option()
    parser.run(argv)

if __name__ == '__main__':
    main()
