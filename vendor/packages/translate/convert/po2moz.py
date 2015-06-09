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

"""Convert Gettext PO localization files to Mozilla .dtd and .properties files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/moz2po.html
for examples and usage instructions.
"""

import os.path

from translate.convert import (convert, po2dtd, po2mozlang, po2prop,
                               prop2mozfunny)


class MozConvertOptionParser(convert.ConvertOptionParser):

    def __init__(self, formats, usetemplates=False, usepots=False,
                 description=None):
        convert.ConvertOptionParser.__init__(self, formats, usetemplates, usepots,
                                             description=description)

    def splitinputext(self, inputpath):
        """splits a inputpath into name and extension"""
        # TODO: not sure if this should be here, was in po2moz
        d, n = os.path.dirname(inputpath), os.path.basename(inputpath)
        s = n.find(".")
        if s == -1:
            return (inputpath, "")
        root = os.path.join(d, n[:s])
        ext = n[s+1:]
        return (root, ext)

    def recursiveprocess(self, options):
        """recurse through directories and convert files"""
        self.replacer.replacestring = options.locale
        result = super(MozConvertOptionParser, self).recursiveprocess(options)
        return result


def main(argv=None):
    # handle command line options
    formats = {("dtd.po", "dtd"): ("dtd", po2dtd.convertdtd),
               ("properties.po", "properties"): ("properties",
                                                 po2prop.convertmozillaprop),
               ("it.po", "it"): ("it", prop2mozfunny.po2it),
               ("ini.po", "ini"): ("ini", prop2mozfunny.po2ini),
               ("inc.po", "inc"): ("inc", prop2mozfunny.po2inc),
               ("lang.po", "lang"): ("lang", po2mozlang.convertlang),
               # (None, "*"): ("*", convert.copytemplate),
               ("*", "*"): ("*", convert.copyinput),
               "*": ("*", convert.copyinput)}
    # handle search and replace
    replacer = convert.Replacer("${locale}", None)
    for replaceformat in ("js", "rdf", "manifest"):
        formats[(None, replaceformat)] = (replaceformat,
                                          replacer.searchreplacetemplate)
        formats[(replaceformat, replaceformat)] = (replaceformat,
                                                   replacer.searchreplaceinput)
        formats[replaceformat] = (replaceformat, replacer.searchreplaceinput)
    parser = MozConvertOptionParser(formats, usetemplates=True, description=__doc__)
    parser.add_option("-l", "--locale", dest="locale", default=None,
        help="set output locale (required as this sets the directory names)",
        metavar="LOCALE")
    parser.add_option("", "--removeuntranslated", dest="remove_untranslated",
            default=False, action="store_true",
            help="remove untranslated strings from output")
    parser.add_threshold_option()
    parser.add_fuzzy_option()
    parser.passthrough.append("remove_untranslated")
    parser.replacer = replacer
    parser.run(argv)


if __name__ == '__main__':
    main()
