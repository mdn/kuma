#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2005-2007 Zuza Software Foundation
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

"""convert Gettext PO localization files to a Wordfast translation memory file

see: http://translate.sourceforge.net/wiki/toolkit/po2wordfast for examples and 
usage instructions
"""

from translate.storage import po
from translate.storage import wordfast
from translate.convert import convert
from translate.misc import wStringIO
import os

class po2wordfast:
    def convertfiles(self, inputfile, wffile, sourcelanguage='en', targetlanguage=None):
        """converts a .po file (possibly many) to a Wordfast TM file"""
        inputstore = po.pofile(inputfile)
        for inunit in inputstore.units:
            if inunit.isheader() or inunit.isblank() or not inunit.istranslated():
                continue
            source = inunit.source
            target = inunit.target
            newunit = wffile.addsourceunit(source)
            newunit.target = target
            newunit.targetlang = targetlanguage

def convertpo(inputfile, outputfile, templatefile, sourcelanguage='en', targetlanguage=None):
    """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
    convertor = po2wordfast()
    outputfile.wffile.header.targetlang = targetlanguage
    convertor.convertfiles(inputfile, outputfile.wffile, sourcelanguage, targetlanguage)
    return 1

class wfmultifile:
    def __init__(self, filename, mode=None):
        """initialises wfmultifile from a seekable inputfile or writable outputfile"""
        self.filename = filename
        if mode is None:
            if os.path.exists(filename):
                mode = 'r'
            else:
                mode = 'w'
        self.mode = mode
        self.multifilename = os.path.splitext(filename)[0]
        self.wffile = wordfast.WordfastTMFile()

    def openoutputfile(self, subfile):
        """returns a pseudo-file object for the given subfile"""
        def onclose(contents):
            pass
        outputfile = wStringIO.CatchStringOutput(onclose)
        outputfile.filename = subfile
        outputfile.wffile = self.wffile
        return outputfile


class WfOptionParser(convert.ArchiveConvertOptionParser):
    def recursiveprocess(self, options):
        if not options.targetlanguage:
            raise ValueError("You must specify the target language")
        super(WfOptionParser, self).recursiveprocess(options)
        self.output = open(options.output, 'w')
        #options.outputarchive.wffile.setsourcelanguage(options.sourcelanguage)
        self.output.write(str(options.outputarchive.wffile))

def main(argv=None):
    formats = {"po": ("txt", convertpo), ("po", "txt"): ("txt", convertpo)}
    archiveformats = {(None, "output"): wfmultifile, (None, "template"): wfmultifile}
    parser = WfOptionParser(formats, usepots=False, usetemplates=False, description=__doc__, archiveformats=archiveformats)
    parser.add_option("-l", "--language", dest="targetlanguage", default=None, 
                      help="set target language code (e.g. af-ZA) [required]", metavar="LANG")
    parser.add_option("", "--source-language", dest="sourcelanguage", default='en', 
                      help="set source language code (default: en)", metavar="LANG")
    parser.passthrough.append("sourcelanguage")
    parser.passthrough.append("targetlanguage")
    parser.run(argv)


if __name__ == '__main__':
    main()
