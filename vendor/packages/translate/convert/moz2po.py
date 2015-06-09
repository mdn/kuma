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
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Convert Mozilla .dtd and .properties files to Gettext PO localization files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/moz2po.html
for examples and usage instructions.
"""

from translate.convert import (convert, dtd2po, mozfunny2prop, mozlang2po,
                               prop2po)


def main(argv=None):
    formats = {
        (None, "*"): ("*", convert.copytemplate),
        ("*", "*"): ("*", convert.copyinput),
        "*": ("*", convert.copyinput),
    }
    # handle formats that convert to .po files
    converters = [
        ("dtd", dtd2po.convertdtd),
        ("properties", prop2po.convertmozillaprop),
        ("it", mozfunny2prop.it2po),
        ("ini", mozfunny2prop.ini2po),
        ("inc", mozfunny2prop.inc2po),
        ("lang", mozlang2po.convertlang),
    ]
    for format, converter in converters:
        formats[(format, format)] = (format + ".po", converter)
        formats[format] = (format + ".po", converter)
    # handle search and replace
    replacer = convert.Replacer("en-US", "${locale}")
    for replaceformat in ("js", "rdf", "manifest"):
        formats[(None, replaceformat)] = (replaceformat,
                                          replacer.searchreplacetemplate)
        formats[(replaceformat, replaceformat)] = (replaceformat,
                                                   replacer.searchreplaceinput)
        formats[replaceformat] = (replaceformat, replacer.searchreplaceinput)
    parser = convert.ConvertOptionParser(formats, usetemplates=True,
                                         usepots=True,
                                         description=__doc__)
    parser.add_duplicates_option()
    parser.passthrough.append("pot")
    parser.run(argv)


if __name__ == '__main__':
    main()
