#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2003-2006 Zuza Software Foundation
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

"""Convert Comma-Separated Value (.csv) files to Gettext PO localization files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/csv2po.html
for examples and usage instructions.
"""

import logging

from translate.storage import csvl10n, po


logger = logging.getLogger(__name__)


def replacestrings(source, *pairs):
    """Use ``pairs`` of ``(original, replacement)`` to replace text found in
    ``source``.

    :param source: String to on which ``pairs`` of strings are to be replaced
    :type source: String
    :param \*pairs: Strings to be matched and replaced
    :type \*pairs: One or more tuples of (original, replacement)
    :return: String with ``*pairs`` of strings replaced
    """
    for orig, new in pairs:
        source = source.replace(orig, new)
    return source


def quotecsvstr(source):
    return '"' + \
           replacestrings(source,
                          ('\\"', '"'), ('"', '\\"'),
                          ("\\\\'", "\\'"), ('\\\\n', '\\n')) + \
           '"'


def simplify(string):
    return filter(type(string).isalnum, string)


class csv2po:
    """a class that takes translations from a .csv file and puts them in a
    .po file"""

    def __init__(self, templatepo=None, charset=None, duplicatestyle="keep"):
        """construct the converter..."""
        self.pofile = templatepo
        self.charset = charset
        self.duplicatestyle = duplicatestyle
        self.commentindex = {}
        self.sourceindex = {}
        self.simpleindex = {}
        self.csvfile = None
        self.duplicatecomments = []
        if self.pofile is not None:
            self.unmatched = 0
            self.makeindex()

    def makeindex(self):
        """makes indexes required for searching..."""
        for pounit in self.pofile.units:
            joinedcomment = " ".join(pounit.getlocations())
            source = pounit.source
            # the definitive way to match is by source comment (joinedcomment)
            if joinedcomment in self.commentindex:
                # unless more than one thing matches...
                self.duplicatecomments.append(joinedcomment)
            else:
                self.commentindex[joinedcomment] = pounit
            # do simpler matching in case things have been mangled...
            simpleid = simplify(source)
            # but check for duplicates
            if (simpleid in self.simpleindex and
                not (source in self.sourceindex)):
                # keep a list of them...
                self.simpleindex[simpleid].append(pounit)
            else:
                self.simpleindex[simpleid] = [pounit]
            # also match by standard msgid
            self.sourceindex[source] = pounit
        for comment in self.duplicatecomments:
            if comment in self.commentindex:
                del self.commentindex[comment]

    def convertunit(self, csvunit):
        """converts csv unit to po unit"""
        pounit = po.pounit(encoding="UTF-8")
        if csvunit.location:
            pounit.addlocation(csvunit.location)
        pounit.source = csvunit.source
        pounit.target = csvunit.target
        return pounit

    def handlecsvunit(self, csvunit):
        """handles reintegrating a csv unit into the .po file"""
        if (len(csvunit.location.strip()) > 0 and
            csvunit.location in self.commentindex):
            pounit = self.commentindex[csvunit.location]
        elif csvunit.source in self.sourceindex:
            pounit = self.sourceindex[csvunit.source]
        elif simplify(csvunit.source) in self.simpleindex:
            thepolist = self.simpleindex[simplify(csvunit.source)]
            if len(thepolist) > 1:
                csvfilename = getattr(self.csvfile, "filename", "(unknown)")
                matches = "\n  ".join(["possible match: " +
                                       pounit.source for pounit in thepolist])
                logger.warning("%s - csv entry not unique in pofile, "
                               "multiple matches found:\n"
                               "  location\t%s\n"
                               "  original\t%s\n"
                               "  translation\t%s\n"
                               "  %s",
                               csvfilename, csvunit.location,
                               csvunit.source, csvunit.target, matches)
                self.unmatched += 1
                return
            pounit = thepolist[0]
        else:
            csvfilename = getattr(self.csvfile, "filename", "(unknown)")
            logger.warning("%s - csv entry not found in pofile:\n"
                           "  location\t%s\n"
                           "  original\t%s\n"
                           "  translation\t%s",
                           csvfilename, csvunit.location,
                           csvunit.source, csvunit.target)
            self.unmatched += 1
            return
        if pounit.hasplural():
            # we need to work out whether we matched the singular or the plural
            singularid = pounit.source.strings[0]
            pluralid = pounit.source.strings[1]
            if csvunit.source == singularid:
                pounit.msgstr[0] = csvunit.target
            elif csvunit.source == pluralid:
                pounit.msgstr[1] = csvunit.target
            elif simplify(csvunit.source) == simplify(singularid):
                pounit.msgstr[0] = csvunit.target
            elif simplify(csvunit.source) == simplify(pluralid):
                pounit.msgstr[1] = csvunit.target
            else:
                logger.warning("couldn't work out singular/plural: %r, %r, %r",
                               csvunit.source, singularid, pluralid)
                self.unmatched += 1
                return
        else:
            pounit.target = csvunit.target

    def convertstore(self, thecsvfile):
        """converts a csvfile to a pofile, and returns it. uses templatepo if
        given at construction"""
        self.csvfile = thecsvfile
        if self.pofile is None:
            self.pofile = po.pofile()
            mergemode = False
        else:
            mergemode = True
        if self.pofile.units and self.pofile.units[0].isheader():
            targetheader = self.pofile.units[0]
            self.pofile.updateheader(content_type="text/plain; charset=UTF-8",
                                     content_transfer_encoding="8bit")
        else:
            targetheader = self.pofile.makeheader(charset="UTF-8",
                                                  encoding="8bit")
        targetheader.addnote("extracted from %s" % self.csvfile.filename,
                             "developer")
        mightbeheader = True
        for csvunit in self.csvfile.units:
            #if self.charset is not None:
            #    csvunit.source = csvunit.source.decode(self.charset)
            #    csvunit.target = csvunit.target.decode(self.charset)
            if mightbeheader:
                # ignore typical header strings...
                mightbeheader = False
                if csvunit.match_header():
                    continue
                if (len(csvunit.location.strip()) == 0 and
                    csvunit.source.find("Content-Type:") != -1):
                    continue
            if mergemode:
                self.handlecsvunit(csvunit)
            else:
                pounit = self.convertunit(csvunit)
                self.pofile.addunit(pounit)
        self.pofile.removeduplicates(self.duplicatestyle)
        return self.pofile


def convertcsv(inputfile, outputfile, templatefile, charset=None,
               columnorder=None, duplicatestyle="msgctxt"):
    """reads in inputfile using csvl10n, converts using csv2po, writes to
    outputfile"""
    inputstore = csvl10n.csvfile(inputfile, fieldnames=columnorder)
    if templatefile is None:
        convertor = csv2po(charset=charset, duplicatestyle=duplicatestyle)
    else:
        templatestore = po.pofile(templatefile)
        convertor = csv2po(templatestore, charset=charset,
                           duplicatestyle=duplicatestyle)
    outputstore = convertor.convertstore(inputstore)
    if outputstore.isempty():
        return 0
    outputfile.write(str(outputstore))
    return 1


def main(argv=None):
    from translate.convert import convert
    formats = {
        ("csv", "po"): ("po", convertcsv),
        ("csv", "pot"): ("po", convertcsv),
        ("csv", None): ("po", convertcsv),
    }
    parser = convert.ConvertOptionParser(formats, usetemplates=True,
                                         usepots=True,
                                         description=__doc__)
    parser.add_option("", "--charset", dest="charset", default=None,
        help="set charset to decode from csv files", metavar="CHARSET")
    parser.add_option("", "--columnorder", dest="columnorder", default=None,
        help="specify the order and position of columns (location,source,target)")
    parser.add_duplicates_option()
    parser.passthrough.append("charset")
    parser.passthrough.append("columnorder")
    parser.run(argv)


if __name__ == '__main__':
    main()
