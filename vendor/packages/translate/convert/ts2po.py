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

"""Convert Qt Linguist (.ts) files to Gettext PO localization files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/ts2po.html
for examples and usage instructions.
"""


from translate.storage import po, ts


class ts2po:

    def __init__(self, duplicatestyle="msgctxt", pot=False):
        self.duplicatestyle = duplicatestyle
        self.pot = pot

    def convertmessage(self, contextname, messagenum, source, target, msgcomments, transtype):
        """makes a pounit from the given message"""
        thepo = po.pounit(encoding="UTF-8")
        thepo.addlocation("%s#%d" % (contextname, messagenum))
        thepo.source = source
        if not self.pot:
            thepo.target = target
        if len(msgcomments) > 0:
            thepo.addnote(msgcomments)
        if transtype == "unfinished" and thepo.istranslated():
            thepo.markfuzzy()
        if transtype == "obsolete":
            # This should use the Gettext obsolete method but it would require quite a bit of work
            thepo.addnote("(obsolete)", origin="developer")
            # using the fact that -- quote -- "(this is nonsense)"
        return thepo

    def convertfile(self, inputfile):
        """converts a .ts file to .po format"""
        tsfile = ts.QtTsParser(inputfile)
        thetargetfile = po.pofile()

        for contextname, messages in tsfile.iteritems():
            messagenum = 0
            for message in messages:
                messagenum += 1
                source = tsfile.getmessagesource(message)
                translation = tsfile.getmessagetranslation(message)
                comment = tsfile.getmessagecomment(message)
                transtype = tsfile.getmessagetype(message)
                thepo = self.convertmessage(contextname, messagenum, source, translation, comment, transtype)
                thetargetfile.addunit(thepo)
        thetargetfile.removeduplicates(self.duplicatestyle)
        return thetargetfile


def convertts(inputfile, outputfile, templates, pot=False, duplicatestyle="msgctxt"):
    """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
    convertor = ts2po(duplicatestyle=duplicatestyle, pot=pot)
    outputstore = convertor.convertfile(inputfile)
    if outputstore.isempty():
        return 0
    outputfile.write(str(outputstore))
    return 1


def main(argv=None):
    from translate.convert import convert
    formats = {"ts": ("po", convertts)}
    parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
    parser.add_duplicates_option()
    parser.passthrough.append("pot")
    parser.run(argv)
