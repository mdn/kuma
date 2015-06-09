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
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Convert Gettext PO localization files to a TMX (Translation Memory eXchange) file.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/po2tmx.html
for examples and usage instructions.
"""

import os

from translate.convert import convert
from translate.misc import wStringIO
from translate.storage import po, tmx


class po2tmx:

    def cleancomments(self, comments, comment_type=None):
        """Removes the comment marks from the PO strings."""
        # FIXME this is a bit hacky, needs some fixes in the PO classes
        for index, comment in enumerate(comments):
            if comment.startswith("#"):
                if comment_type is None:
                    comments[index] = comment[1:].rstrip()
                else:
                    comments[index] = comment[2:].strip()

        return ''.join(comments)

    def convertfiles(self, inputfile, tmxfile, sourcelanguage='en',
                     targetlanguage=None, comment=None):
        """converts a .po file (possibly many) to TMX file"""
        inputstore = po.pofile(inputfile)
        for inunit in inputstore.units:
            if inunit.isheader() or inunit.isblank() or not inunit.istranslated() or inunit.isfuzzy():
                continue
            source = inunit.source
            translation = inunit.target

            commenttext = {
                'source': self.cleancomments(inunit.sourcecomments, "source"),
                'type': self.cleancomments(inunit.typecomments, "type"),
                'others': self.cleancomments(inunit.othercomments),
            }.get(comment, None)

            tmxfile.addtranslation(source, sourcelanguage, translation,
                                   targetlanguage, commenttext)


def convertpo(inputfile, outputfile, templatefile, sourcelanguage='en',
              targetlanguage=None, comment=None):
    """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
    convertor = po2tmx()
    convertor.convertfiles(inputfile, outputfile.tmxfile, sourcelanguage,
                           targetlanguage, comment)
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
        self.output.close()


def main(argv=None):
    formats = {"po": ("tmx", convertpo), ("po", "tmx"): ("tmx", convertpo)}
    archiveformats = {(None, "output"): tmxmultifile, (None, "template"): tmxmultifile}
    parser = TmxOptionParser(formats, usepots=False, usetemplates=False, description=__doc__, archiveformats=archiveformats)
    parser.add_option("-l", "--language", dest="targetlanguage", default=None,
            help="set target language code (e.g. af-ZA) [required]", metavar="LANG")
    parser.add_option("", "--source-language", dest="sourcelanguage", default='en',
            help="set source language code (default: en)", metavar="LANG")
    comments = ['source', 'type', 'others', 'none']
    comments_help = ("set default comment import: none, source, type or "
                     "others (default: none)")
    parser.add_option("", "--comments", dest="comment", default="none",
                      type="choice", choices=comments, help=comments_help)
    parser.passthrough.append("sourcelanguage")
    parser.passthrough.append("targetlanguage")
    parser.passthrough.append("comment")
    parser.run(argv)


if __name__ == '__main__':
    main()
