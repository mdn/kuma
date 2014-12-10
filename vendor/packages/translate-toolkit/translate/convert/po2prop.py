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


"""convert Gettext PO localization files to Java/Mozilla .properties files

see: http://translate.sourceforge.net/wiki/toolkit/po2prop for examples and 
usage instructions
"""

from translate.misc import quote
from translate.storage import po

eol = "\n"

class reprop:
    def __init__(self, templatefile):
        self.templatefile = templatefile
        self.inputdict = {}

    def convertstore(self, inputstore, personality, includefuzzy=False):
        self.personality = personality
        self.inmultilinemsgid = False
        self.inecho = False
        self.makestoredict(inputstore, includefuzzy)
        outputlines = []
        for line in self.templatefile.readlines():
            outputstr = self.convertline(line)
            outputlines.append(outputstr)
        return outputlines

    def makestoredict(self, store, includefuzzy=False):
        # make a dictionary of the translations
        for unit in store.units:
            if includefuzzy or not unit.isfuzzy():
                # there may be more than one entity due to msguniq merge
                for entity in unit.getlocations():
                    propstring = unit.target
                    
                    # NOTE: triple-space as a string means leave it empty (special signal)
                    if len(propstring.strip()) == 0 and propstring != "   ":
                        propstring = unit.source
                    self.inputdict[entity] = propstring

    def convertline(self, line):
        returnline = ""
        # handle multiline msgid if we're in one
        if self.inmultilinemsgid:
            msgid = quote.rstripeol(line).strip()
            # see if there's more
            self.inmultilinemsgid = (msgid[-1:] == '\\')
            # if we're echoing...
            if self.inecho:
                returnline = line
        # otherwise, this could be a comment
        elif line.strip()[:1] == '#':
            returnline = quote.rstripeol(line)+eol
        else:
            line = quote.rstripeol(line)
            equalspos = line.find('=')
            # if no equals, just repeat it
            if equalspos == -1:
                returnline = quote.rstripeol(line)+eol
            # otherwise, this is a definition
            else:
                # backslash at end means carry string on to next line
                if quote.rstripeol(line)[-1:] == '\\':
                    self.inmultilinemsgid = True
                # now deal with the current string...
                key = line[:equalspos].strip()
                # Calculate space around the equal sign
                prespace = line.lstrip()[line.lstrip().find(' '):equalspos]
                postspacestart = len(line[equalspos+1:])
                postspaceend = len(line[equalspos+1:].lstrip())
                postspace = line[equalspos+1:equalspos+(postspacestart-postspaceend)+1]
                if self.inputdict.has_key(key):
                    self.inecho = False
                    value = self.inputdict[key]
                    if isinstance(value, str):
                        value = value.decode('utf8')
                    if self.personality == "mozilla" or self.personality == "skype":
                        returnline = key+prespace+"="+postspace+quote.mozillapropertiesencode(value)+eol
                    else:
                        returnline = key+prespace+"="+postspace+quote.javapropertiesencode(value)+eol
                else:
                    self.inecho = True
                    returnline = line+eol
        if isinstance(returnline, unicode):
            returnline = returnline.encode('utf-8')
        return returnline

def convertmozillaprop(inputfile, outputfile, templatefile, includefuzzy=False):
    """Mozilla specific convertor function"""
    return convertprop(inputfile, outputfile, templatefile, personality="mozilla", includefuzzy=includefuzzy)

def convertprop(inputfile, outputfile, templatefile, personality, includefuzzy=False):
    inputstore = po.pofile(inputfile)
    if templatefile is None:
        raise ValueError("must have template file for properties files")
        # convertor = po2prop()
    else:
        convertor = reprop(templatefile)
    outputproplines = convertor.convertstore(inputstore, personality, includefuzzy)
    outputfile.writelines(outputproplines)
    return 1

def main(argv=None):
    # handle command line options
    from translate.convert import convert
    formats = {("po", "properties"): ("properties", convertprop),
               ("po", "lang"): ("lang", convertprop),}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, description=__doc__)
    parser.add_option("", "--personality", dest="personality", default="java", type="choice",
            choices=["java", "mozilla", "skype"],
            help="set the output behaviour: java (default), mozilla, skype", metavar="TYPE")
    parser.add_fuzzy_option()
    parser.passthrough.append("personality")
    parser.run(argv)

if __name__ == '__main__':
    main()

