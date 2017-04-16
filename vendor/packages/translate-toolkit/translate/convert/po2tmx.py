#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2005, 2006 Zuza Software Foundation
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
#

"""convert Gettext PO localization files to a TMX (Translation Memory eXchange) file

see: http://translate.sourceforge.net/wiki/toolkit/po2tmx for examples and 
usage instructions
"""

from translate.storage import po
from translate.storage import tmx
from translate.convert import convert
from translate.misc import wStringIO
import os

class po2tmx:
    def convertfile(self, inputfile, sourcelanguage='en', targetlanguage=None):
        """converts a .po file to TMX file"""
        # TODO: This seems to not be used... remove it
        inputstore = inputfile
        for inunit in inputstore.units:
            if inunit.isheader() or inunit.isblank() or not inunit.istranslated() or inunit.isfuzzy():
                continue
            source = inunit.source
            translation = inunit.target
            # TODO place source location in comments
            tmxfile.addtranslation(source, sourcelanguage, translation, targetlanguage)
        return str(tmxfile)
    
    def convertfiles(self, inputfile, tmxfile, sourcelanguage='en', targetlanguage=None):
        """converts a .po file (possibly many) to TMX file"""
        inputstore = po.pofile(inputfile)
        for inunit in inputstore.units:
            if inunit.isheader() or inunit.isblank() or not inunit.istranslated() or inunit.isfuzzy():
                continue
            source = inunit.source
            translation = inunit.target
            # TODO place source location in comments
            tmxfile.addtranslation(source, sourcelanguage, translation, targetlanguage)

def convertpo(inputfile, outputfile, templatefile, sourcelanguage='en', targetlanguage=None):
    """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
    convertor = po2tmx()
    convertor.convertfiles(inputfile, outputfile.tmxfile, sourcelanguage, targetlanguage)
    return 1

class tmxmultifile:
    def __init__(self, filename, mode=None):
        """initialises tmxmultifile from a seekable inputfile or writable outputfile"""
        self.filename = filename
        if mode is None:
            if os.path.exists(filename):
                mode = 'r'
            else:
                mode = 'w'
        self.mode = mode
#        self.multifilestyle = multifilestyle
        self.multifilename = os.path.splitext(filename)[0]
#        self.multifile = open(filename, mode)
        self.tmxfile = tmx.tmxfile()

    def openoutputfile(self, subfile):
        """returns a pseudo-file object for the given subfile"""
        def onclose(contents):
            pass
        outputfile = wStringIO.CatchStringOutput(onclose)
        outputfile.filename = subfile
        outputfile.tmxfile = self.tmxfile
        return outputfile


class TmxOptionParser(convert.ArchiveConvertOptionParser):
    def recursiveprocess(self, options):
        if not options.targetlanguage:
            raise ValueError("You must specify the target language")
        super(TmxOptionParser, self).recursiveprocess(options)
        self.output = open(options.output, 'w')
        options.outputarchive.tmxfile.setsourcelanguage(options.sourcelanguage)
        self.output.write(str(options.outputarchive.tmxfile))

def main(argv=None):
    formats = {"po": ("tmx", convertpo), ("po", "tmx"): ("tmx", convertpo)}
    archiveformats = {(None, "output"): tmxmultifile, (None, "template"): tmxmultifile}
    parser = TmxOptionParser(formats, usepots=False, usetemplates=False, description=__doc__, archiveformats=archiveformats)
    parser.add_option("-l", "--language", dest="targetlanguage", default=None, 
            help="set target language code (e.g. af-ZA) [required]", metavar="LANG")
    parser.add_option("", "--source-language", dest="sourcelanguage", default='en', 
            help="set source language code (default: en)", metavar="LANG")
    parser.passthrough.append("sourcelanguage")
    parser.passthrough.append("targetlanguage")
    parser.run(argv)


if __name__ == '__main__':
    main()
