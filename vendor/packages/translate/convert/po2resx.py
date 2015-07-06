#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 Zuza Software Foundation
# Copyright 2015 Sarah Hale
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

"""Convert Gettext PO localisation files to .Net Resource (.resx) files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/resx2po.html
for examples and usage instructions.
"""

from translate.convert import convert
from translate.storage import factory, resx


class po2resx:
    def __init__(self, templatefile, inputstore):
        self.templatefile = templatefile
        self.templatestore = resx.RESXFile(templatefile)
        self.inputstore = inputstore

    def convertstore(self, includefuzzy=False):
        self.includefuzzy = includefuzzy
        self.inputstore.makeindex()

        for unit in self.templatestore.units:
            inputunit = self.inputstore.locationindex.get(unit.getid())

            if inputunit is not None:
                if inputunit.isfuzzy() and not self.includefuzzy:
                    unit.target = unit.source
                else:
                    unit.target = inputunit.target
            else:
                unit.target = unit.source

            if inputunit is not None:
                self.addcomments(inputunit, unit)

        return str(self.templatestore)

    def addcomments(self, inputunit, unit):
        comments = []

        # Handle #. automatic comments
        autocomment = inputunit.getnotes("developer")
        comments.append(autocomment)

        # Handle # comments
        transcomment = inputunit.getnotes("translator")
        if transcomment:
            comments.append("[Translator Comment: " + transcomment + "]")

        # Join automatic and translator comments with a newline as per
        # convention.
        combocomment = '\n'.join(comments)

        if combocomment:
            unit.addnote(combocomment)


def convertresx(inputfile, outputfile, templatefile, includefuzzy=False,
                outputthreshold=None):

    inputstore = factory.getobject(inputfile)

    if templatefile is None:
        raise ValueError("Must have template file for RESX files")
    else:
        convertor = po2resx(templatefile, inputstore)

    outputstring = convertor.convertstore(includefuzzy)
    outputfile.write(outputstring)
    return True


def main(argv=None):
    formats = {
        ("po", "resx"): ("resx", convertresx),
    }
    parser = convert.ConvertOptionParser(formats, usetemplates=True,
                                         description=__doc__)
    parser.add_fuzzy_option()
    parser.run(argv)


if __name__ == '__main__':
    main()
