#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2006,2008-2009 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
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

"""Convert Gettext PO localization files back to Windows Resource (.rc) files

See: http://translate.sourceforge.net/wiki/toolkit/po2rc for examples and
usage instructions.
"""

from translate.storage import po
from translate.storage import rc

class rerc:
    def __init__(self, templatefile, charset="utf-8", lang=None, sublang=None):
        self.templatefile = templatefile
        self.templatestore = rc.rcfile(templatefile)
        self.inputdict = {}
        self.charset = charset
        self.lang = lang
        self.sublang = sublang

    def convertstore(self, inputstore, includefuzzy=False):
        self.makestoredict(inputstore, includefuzzy)
        outputblocks = []
        for block in self.templatestore.blocks:
            outputblocks.append(self.convertblock(block))
        if self.charset == "utf-8":
            outputblocks.insert(0, "#pragma code_page(65001)\n")
            outputblocks.append("#pragma code_page(default)")
        return outputblocks

    def makestoredict(self, store, includefuzzy=False):
        """ make a dictionary of the translations"""
        for unit in store.units:
            if includefuzzy or not unit.isfuzzy():
                for location in unit.getlocations():
                    rcstring = unit.target
                    if len(rcstring.strip()) == 0:
                        rcstring = unit.source
                    self.inputdict[location] = rc.escape_to_rc(rcstring).encode(self.charset)

    def convertblock(self, block):
        newblock = block
        if isinstance(newblock, unicode):
            newblock = newblock.encode('utf-8')
        if newblock.startswith("LANGUAGE"):
            return "LANGUAGE %s, %s" % (self.lang, self.sublang)
        for unit in self.templatestore.units:
            location = unit.getlocations()[0]
            if self.inputdict.has_key(location):
                if self.inputdict[location] != unit.match.groupdict()['value']:
                    newmatch = unit.match.group().replace(unit.match.groupdict()['value'], self.inputdict[location])
                    newblock = newblock.replace(unit.match.group(), newmatch)
        if isinstance(newblock, unicode):
            newblock = newblock.encode(self.charset)
        return newblock

def convertrc(inputfile, outputfile, templatefile, includefuzzy=False, charset=None, lang=None, sublang=None):
    inputstore = po.pofile(inputfile)
    if not lang:
        raise ValueError("must specify a target language")
    if templatefile is None:
        raise ValueError("must have template file for rc files")
        # convertor = po2rc()
    else:
        convertor = rerc(templatefile, charset, lang, sublang)
    outputrclines = convertor.convertstore(inputstore, includefuzzy)
    outputfile.writelines(outputrclines)
    return 1

def main(argv=None):
    # handle command line options
    from translate.convert import convert
    formats = {("po", "rc"): ("rc", convertrc)}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, description=__doc__)
    defaultcharset = "utf-8"
    parser.add_option("", "--charset", dest="charset", default=defaultcharset,
        help="charset to use to decode the RC files (default: %s)" % defaultcharset, metavar="CHARSET")
    parser.add_option("-l", "--lang", dest="lang", default=None,
        help="LANG entry", metavar="LANG")
    defaultsublang="SUBLANG_DEFAULT"
    parser.add_option("", "--sublang", dest="sublang", default=defaultsublang,
        help="SUBLANG entry (default: %s)" % defaultsublang, metavar="SUBLANG")
    parser.passthrough.append("charset")
    parser.passthrough.append("lang")
    parser.passthrough.append("sublang")
    parser.add_fuzzy_option()
    parser.run(argv)

if __name__ == '__main__':
    main()
