#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2008 Zuza Software Foundation
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

"""Convert Gettext PO localization files to PHP localization files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/php2po.html
for examples and usage instructions.
"""

from translate.convert import convert
from translate.misc import quote
from translate.storage import php, po


eol = "\n"


class rephp:

    def __init__(self, templatefile, inputstore):
        self.templatefile = templatefile
        self.inputstore = inputstore
        self.inmultilinemsgid = False
        self.inecho = False
        self.inarray = False
        self.equaldel = "="
        self.enddel = ";"
        self.prename = ""
        self.quotechar = ""

    def convertstore(self, includefuzzy=False):
        self.includefuzzy = includefuzzy
        self.inputstore.makeindex()
        outputlines = []
        for line in self.templatefile.readlines():
            outputstr = self.convertline(line)
            outputlines.append(outputstr)
        return outputlines

    def convertline(self, line):
        line = unicode(line, 'utf-8')
        returnline = ""
        # handle multiline msgid if we're in one
        if self.inmultilinemsgid:
            # see if there's more
            endpos = line.rfind("%s%s" % (self.quotechar, self.enddel))
            # if there was no '; or the quote is escaped, we have to continue
            if endpos >= 0 and line[endpos-1] != '\\':
                self.inmultilinemsgid = False
            # if we're echoing...
            if self.inecho:
                returnline = line
        # otherwise, this could be a comment
        elif line.strip()[:2] == '//' or line.strip()[:2] == '/*':
            returnline = quote.rstripeol(line) + eol
        elif line.find('array(') != -1:
            self.inarray = True
            self.prename = line[:line.find('=')].strip() + "->"
            self.equaldel = "=>"
            self.enddel = ","
            returnline = quote.rstripeol(line) + eol
        elif self.inarray and line.find(');') != -1:
            self.inarray = False
            self.equaldel = "="
            self.enddel = ";"
            self.prename = ""
            returnline = quote.rstripeol(line) + eol
        else:
            line = quote.rstripeol(line)
            equalspos = line.find(self.equaldel)
            hashpos = line.find("#")
            # if no equals, just repeat it
            if equalspos == -1:
                returnline = quote.rstripeol(line) + eol
            elif 0 <= hashpos < equalspos:
                # Assume that this is a '#' comment line
                returnline = quote.rstripeol(line) + eol
            # otherwise, this is a definition
            else:
                # now deal with the current string...
                key = line[:equalspos].rstrip()
                lookupkey = self.prename + key.lstrip()
                # Calculate space around the equal sign
                prespace = line[len(line[:equalspos].rstrip()):equalspos]
                postspacestart = len(line[equalspos+len(self.equaldel):])
                postspaceend = len(line[equalspos+len(self.equaldel):].lstrip())
                postspace = line[equalspos+len(self.equaldel):equalspos+(postspacestart-postspaceend)+len(self.equaldel)]
                self.quotechar = line[equalspos+(postspacestart-postspaceend)+len(self.equaldel)]
                inlinecomment_pos = line.rfind("%s%s" % (self.quotechar,
                                                         self.enddel))
                if inlinecomment_pos > -1:
                    inlinecomment = line[inlinecomment_pos+2:]
                else:
                    inlinecomment = ""
                if lookupkey in self.inputstore.locationindex:
                    unit = self.inputstore.locationindex[lookupkey]
                    if (unit.isfuzzy() and not self.includefuzzy) or len(unit.target) == 0:
                        value = unit.source
                    else:
                        value = unit.target
                    value = php.phpencode(value, self.quotechar)
                    self.inecho = False
                    if isinstance(value, str):
                        value = value.decode('utf8')
                    returnline = "%(key)s%(pre)s%(del)s%(post)s%(quote)s%(value)s%(quote)s%(enddel)s%(comment)s%(eol)s" % {
                                     "key": key,
                                     "pre": prespace, "del": self.equaldel,
                                     "post": postspace,
                                     "quote": self.quotechar, "value": value,
                                     "enddel": self.enddel,
                                     "comment": inlinecomment, "eol": eol,
                                  }
                else:
                    self.inecho = True
                    returnline = line + eol
                # no string termination means carry string on to next line
                endpos = line.rfind("%s%s" % (self.quotechar, self.enddel))
                # if there was no '; or the quote is escaped, we have to
                # continue
                if endpos == -1 or line[endpos-1] == '\\':
                    self.inmultilinemsgid = True
        if isinstance(returnline, unicode):
            returnline = returnline.encode('utf-8')
        return returnline


def convertphp(inputfile, outputfile, templatefile, includefuzzy=False,
               outputthreshold=None):
    inputstore = po.pofile(inputfile)

    if not convert.should_output_store(inputstore, outputthreshold):
        return False

    if templatefile is None:
        raise ValueError("must have template file for php files")
        # convertor = po2php()
    else:
        convertor = rephp(templatefile, inputstore)
    outputphplines = convertor.convertstore(includefuzzy)
    outputfile.writelines(outputphplines)
    return 1


def main(argv=None):
    # handle command line options
    formats = {
            ("po", "php"): ("php", convertphp),
            ("po", "html"): ("html", convertphp),
    }
    parser = convert.ConvertOptionParser(formats, usetemplates=True,
                                         description=__doc__)
    parser.add_threshold_option()
    parser.add_fuzzy_option()
    parser.run(argv)

if __name__ == '__main__':
    main()
