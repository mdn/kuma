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
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Convert Gettext PO localization files to iCal files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/ical2po.html
for examples and usage instructions.
"""

from translate.convert import convert
from translate.storage import factory, ical


class reical:

    def __init__(self, templatefile, inputstore):
        self.templatefile = templatefile
        self.templatestore = ical.icalfile(templatefile)
        self.inputstore = inputstore

    def convertstore(self, includefuzzy=False):
        self.includefuzzy = includefuzzy
        self.inputstore.makeindex()
        for unit in self.templatestore.units:
            for location in unit.getlocations():
                if location in self.inputstore.locationindex:
                    inputunit = self.inputstore.locationindex[location]
                    if inputunit.isfuzzy() and not self.includefuzzy:
                        unit.target = unit.source
                    else:
                        unit.target = inputunit.target
                else:
                    unit.target = unit.source
        return str(self.templatestore)


def convertical(inputfile, outputfile, templatefile, includefuzzy=False,
                outputthreshold=None):
    inputstore = factory.getobject(inputfile)

    if not convert.should_output_store(inputstore, outputthreshold):
        return False

    if templatefile is None:
        raise ValueError("must have template file for iCal files")
    else:
        convertor = reical(templatefile, inputstore)
    outputstring = convertor.convertstore(includefuzzy)
    outputfile.write(outputstring)
    return 1


def main(argv=None):
    # handle command line options
    formats = {("po", "ics"): ("ics", convertical)}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, description=__doc__)
    parser.add_threshold_option()
    parser.add_fuzzy_option()
    parser.run(argv)


if __name__ == '__main__':
    main()
