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

"""convert Gettext PO localization files to Mozilla .dtd and .properties files

see: http://translate.sourceforge.net/wiki/toolkit/po2moz for examples and 
usage instructions
"""

import os.path
from translate.convert import po2dtd
from translate.convert import po2prop
from translate.convert import prop2mozfunny
from translate.storage import xpi
from translate.convert import convert

class MozConvertOptionParser(convert.ArchiveConvertOptionParser):
    def __init__(self, formats, usetemplates=False, usepots=False, description=None):
        convert.ArchiveConvertOptionParser.__init__(self, formats, usetemplates, usepots, description=description, archiveformats={"xpi": xpi.XpiFile})

    def initoutputarchive(self, options):
        """creates an outputarchive if required"""
        if options.output and self.isarchive(options.output, 'output'):
            newlang = None
            newregion = None
            if options.locale is not None:
                if options.locale.count("-") > 1:
                    raise ValueError("Invalid locale: %s - should be of the form xx-YY" % options.locale)
                elif "-" in options.locale:
                    newlang, newregion = options.locale.split("-")
                else:
                    newlang, newregion = options.locale, ""
            if options.clonexpi is not None:
                originalxpi = xpi.XpiFile(options.clonexpi, "r")
                options.outputarchive = originalxpi.clone(options.output, "w", newlang=newlang, newregion=newregion)
            elif self.isarchive(options.template, 'template'):
                options.outputarchive = options.templatearchive.clone(options.output, "a", newlang=newlang, newregion=newregion)
            else:
                if os.path.exists(options.output):
                    options.outputarchive = xpi.XpiFile(options.output, "a", locale=newlang, region=newregion)
                else:
                    # FIXME: this is unlikely to work because it has no jar files
                    options.outputarchive = xpi.XpiFile(options.output, "w", locale=newlang, region=newregion)

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
        if self.isarchive(options.output, 'output'):
            if options.progress in ('console', 'verbose'):
                print "writing xpi file..."
            options.outputarchive.close()
        return result

def main(argv=None):
    # handle command line options
    formats = {("dtd.po", "dtd"): ("dtd", po2dtd.convertdtd),
               ("properties.po", "properties"): ("properties", po2prop.convertmozillaprop),
               ("it.po", "it"): ("it", prop2mozfunny.po2it),
               ("ini.po", "ini"): ("ini", prop2mozfunny.po2ini),
               ("inc.po", "inc"): ("inc", prop2mozfunny.po2inc),
               # (None, "*"): ("*", convert.copytemplate),
               ("*", "*"): ("*", convert.copyinput),
               "*": ("*", convert.copyinput)}
    # handle search and replace
    replacer = convert.Replacer("${locale}", None)
    for replaceformat in ("js", "rdf", "manifest"):
        formats[(None, replaceformat)] = (replaceformat, replacer.searchreplacetemplate)
        formats[(replaceformat, replaceformat)] = (replaceformat, replacer.searchreplaceinput)
        formats[replaceformat] = (replaceformat, replacer.searchreplaceinput)
    parser = MozConvertOptionParser(formats, usetemplates=True, description=__doc__)
    parser.add_option("-l", "--locale", dest="locale", default=None,
        help="set output locale (required as this sets the directory names)", metavar="LOCALE")
    parser.add_option("", "--clonexpi", dest="clonexpi", default=None,
        help="clone xpi structure from the given xpi file")
    parser.add_fuzzy_option()
    parser.replacer = replacer
    parser.run(argv)


if __name__ == '__main__':
    main()
