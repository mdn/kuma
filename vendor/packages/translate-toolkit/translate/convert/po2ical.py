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


"""convert Gettext PO localization files to iCal files"""

from translate.storage import factory
from translate.storage import ical

class reical:
    def __init__(self, templatefile):
        self.templatefile = templatefile
        self.templatestore = ical.icalfile(templatefile)
        self.inputdict = {}

    def convertstore(self, inputstore, includefuzzy=False):
        self.makestoredict(inputstore, includefuzzy)
        for unit in self.templatestore.units:
            for location in unit.getlocations():
                if self.inputdict.has_key(location):
                    unit.target = self.inputdict[location]
                else:
                    unit.target = unit.source
        return str(self.templatestore)

    def makestoredict(self, store, includefuzzy=False):
        # make a dictionary of the translations
        for unit in store.units:
            if includefuzzy or not unit.isfuzzy():
                # there may be more than one entity due to msguniq merge
                for location in unit.getlocations():
                    inistring = unit.target
                    if len(inistring.strip()) == 0:
                        inistring = unit.source
                    self.inputdict[location] = inistring

def convertical(inputfile, outputfile, templatefile, includefuzzy=False):
    inputstore = factory.getobject(inputfile)
    if templatefile is None:
        raise ValueError("must have template file for iCal files")
    else:
        convertor = reical(templatefile)
    outputstring = convertor.convertstore(inputstore, includefuzzy)
    outputfile.write(outputstring)
    return 1

def main(argv=None):
    # handle command line options
    from translate.convert import convert
    formats = {("po", "ics"): ("ics", convertical)}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, description=__doc__)
    parser.add_fuzzy_option()
    parser.run(argv)

if __name__ == '__main__':
    main()

