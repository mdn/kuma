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
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Grep XLIFF, Gettext PO and TMX localization files

Matches are output to snippet files of the same type which can then be reviewed 
and later merged using pomerge

See: http://translate.sourceforge.net/wiki/toolkit/pogrep for examples and
usage instructions
"""

from translate.storage import factory
from translate.storage.poheader import poheader
from translate.misc import optrecurse
from translate.misc.multistring import multistring
from translate.lang import data
import re
import locale


class GrepMatch(object):
    """Just a small data structure that represents a search match."""

    # INITIALIZERS #
    def __init__(self, unit, part='target', part_n=0, start=0, end=0):
        self.unit   = unit
        self.part   = part
        self.part_n = part_n
        self.start  = start
        self.end    = end

    # ACCESSORS #
    def get_getter(self):
        if self.part == 'target':
            if self.unit.hasplural():
                getter = lambda: self.unit.target.strings[self.part_n]
            else:
                getter = lambda: self.unit.target
            return getter
        elif self.part == 'source':
            if self.unit.hasplural():
                getter = lambda: self.unit.source.strings[self.part_n]
            else:
                getter = lambda: self.unit.source
            return getter
        elif self.part == 'notes':
            def getter():
                return self.unit.getnotes()[self.part_n]
            return getter
        elif self.part == 'locations':
            def getter():
                return self.unit.getlocations()[self.part_n]
            return getter

    def get_setter(self):
        if self.part == 'target':
            if self.unit.hasplural():
                def setter(value):
                    strings = self.unit.target.strings
                    strings[self.part_n] = value
                    self.unit.target = strings
            else:
                def setter(value):
                    self.unit.target = value
            return setter

    # SPECIAL METHODS #
    def __str__(self):
        start, end = self.start, self.end
        if start < 3:
            start = 3
        if end > len(self.get_getter()()) - 3:
            end = len(self.get_getter()()) - 3
        matchpart = self.get_getter()()[start-2:end+2]
        return '<GrepMatch "%s" part=%s[%d] start=%d end=%d>' % (matchpart, self.part, self.part_n, self.start, self.end)

    def __repr__(self):
        return str(self)

def real_index(string, nfc_index):
    """Calculate the real index in the unnormalized string that corresponds to
    the index nfc_index in the normalized string."""
    length = nfc_index
    max_length = len(string)
    while len(data.normalize(string[:length])) <= nfc_index:
        if length == max_length:
            return length
        length += 1
    return length - 1


def find_matches(unit, part, strings, re_search):
    """Return the GrepFilter objects where re_search matches in strings."""
    matches = []
    for n, string in enumerate(strings):
        if not string:
            continue
        normalized = data.normalize(string)
        for matchobj in re_search.finditer(normalized):
            start = real_index(string, matchobj.start())
            end = real_index(string, matchobj.end())
            matches.append(GrepMatch(unit, part=part, part_n=n, start=start, end=end))
    return matches

class GrepFilter:
    def __init__(self, searchstring, searchparts, ignorecase=False, useregexp=False,
            invertmatch=False, accelchar=None, encoding='utf-8',
            max_matches=0):
        """builds a checkfilter using the given checker"""
        if isinstance(searchstring, unicode):
            self.searchstring = searchstring
        else:
            self.searchstring = searchstring.decode(encoding)
        self.searchstring = data.normalize(self.searchstring)
        if searchparts:
            # For now we still support the old terminology, except for the old 'source'
            # which has a new meaning now.
            self.search_source = ('source' in searchparts) or ('msgid' in searchparts)
            self.search_target = ('target' in searchparts) or ('msgstr' in searchparts)
            self.search_notes =  ('notes' in searchparts) or ('comment' in searchparts)
            self.search_locations = 'locations' in searchparts
        else:
            self.search_source = True
            self.search_target = True
            self.search_notes = False
            self.search_locations = False
        self.ignorecase = ignorecase
        if self.ignorecase:
            self.searchstring = self.searchstring.lower()
        self.useregexp = useregexp
        if self.useregexp:
            self.searchpattern = re.compile(self.searchstring)
        self.invertmatch = invertmatch
        self.accelchar = accelchar
        self.max_matches = max_matches

    def matches(self, teststr):
        if teststr is None:
            return False
        teststr = data.normalize(teststr)
        if self.ignorecase:
            teststr = teststr.lower()
        if self.accelchar:
            teststr = re.sub(self.accelchar + self.accelchar, "#", teststr)
            teststr = re.sub(self.accelchar, "", teststr)
        if self.useregexp:
            found = self.searchpattern.search(teststr)
        else:
            found = teststr.find(self.searchstring) != -1
        if self.invertmatch:
            found = not found
        return found

    def filterunit(self, unit):
        """runs filters on an element"""
        if unit.isheader(): return []

        if self.search_source:
            if isinstance(unit.source, multistring):
                strings = unit.source.strings
            else:
                strings = [unit.source]
            for string in strings:
                if self.matches(string):
                    return True

        if self.search_target:
            if isinstance(unit.target, multistring):
                strings = unit.target.strings
            else:
                strings = [unit.target]
            for string in strings:
                if self.matches(string):
                    return True

        if self.search_notes:
            if self.matches(unit.getnotes()):
                return True
        if self.search_locations:
            if self.matches(u" ".join(unit.getlocations())):
                return True
        return False

    def filterfile(self, thefile):
        """runs filters on a translation file object"""
        thenewfile = type(thefile)()
        thenewfile.setsourcelanguage(thefile.sourcelanguage)
        thenewfile.settargetlanguage(thefile.targetlanguage)
        for unit in thefile.units:
            if self.filterunit(unit):
                thenewfile.addunit(unit)

        if isinstance(thenewfile, poheader):
            thenewfile.updateheader(add=True, **thefile.parseheader())
        return thenewfile

    def getmatches(self, units):
        if not self.searchstring:
            return [], []

        searchstring = self.searchstring
        flags = re.LOCALE | re.MULTILINE | re.UNICODE

        if self.ignorecase:
            flags |= re.IGNORECASE
        if not self.useregexp:
            searchstring = re.escape(searchstring)
        self.re_search = re.compile(u'(%s)' % (searchstring), flags)

        matches = []
        indexes = []

        for index, unit in enumerate(units):
            old_length = len(matches)

            if self.search_target:
                if unit.hasplural():
                    targets = unit.target.strings
                else:
                    targets = [unit.target]
                matches.extend(find_matches(unit, 'target', targets, self.re_search))
            if self.search_source:
                if unit.hasplural():
                    sources = unit.source.strings
                else:
                    sources = [unit.source]
                matches.extend(find_matches(unit, 'source', sources, self.re_search))
            if self.search_notes:
                matches.extend(find_matches(unit, 'notes', unit.getnotes(), self.re_search))

            if self.search_locations:
                matches.extend(find_matches(unit, 'locations', unit.getlocations(), self.re_search))

            # A search for a single letter or an all-inclusive regular
            # expression could give enough results to cause performance
            # problems. The answer is probably not very useful at this scale.
            if self.max_matches and len(matches) > self.max_matches:
                raise Exception("Too many matches found")

            if len(matches) > old_length:
                old_length = len(matches)
                indexes.append(index)

        return matches, indexes

class GrepOptionParser(optrecurse.RecursiveOptionParser):
    """a specialized Option Parser for the grep tool..."""
    def parse_args(self, args=None, values=None):
        """parses the command line options, handling implicit input/output args"""
        (options, args) = optrecurse.optparse.OptionParser.parse_args(self, args, values)
        # some intelligence as to what reasonable people might give on the command line
        if args:
            options.searchstring = args[0]
            args = args[1:]
        else:
            self.error("At least one argument must be given for the search string")
        if args and not options.input:
            if not options.output:
                options.input = args[:-1]
                args = args[-1:]
            else:
                options.input = args
                args = []
        if args and not options.output:
            options.output = args[-1]
            args = args[:-1]
        if args:
            self.error("You have used an invalid combination of --input, --output and freestanding args")
        if isinstance(options.input, list) and len(options.input) == 1:
            options.input = options.input[0]
        return (options, args)

    def set_usage(self, usage=None):
        """sets the usage string - if usage not given, uses getusagestring for each option"""
        if usage is None:
            self.usage = "%prog searchstring " + " ".join([self.getusagestring(option) for option in self.option_list])
        else:
            super(GrepOptionParser, self).set_usage(usage)

    def run(self):
        """parses the arguments, and runs recursiveprocess with the resulting options"""
        (options, args) = self.parse_args()
        options.inputformats = self.inputformats
        options.outputoptions = self.outputoptions
        options.checkfilter = GrepFilter(options.searchstring, options.searchparts, options.ignorecase, options.useregexp, options.invertmatch, options.accelchar, locale.getpreferredencoding())
        self.usepsyco(options)
        self.recursiveprocess(options)

def rungrep(inputfile, outputfile, templatefile, checkfilter):
    """reads in inputfile, filters using checkfilter, writes to outputfile"""
    fromfile = factory.getobject(inputfile)
    tofile = checkfilter.filterfile(fromfile)
    if tofile.isempty():
        return False
    outputfile.write(str(tofile))
    return True

def cmdlineparser():
    formats = {"po":("po", rungrep), "pot":("pot", rungrep), 
            "mo":("mo", rungrep), "gmo":("gmo", rungrep), 
            "tmx":("tmx", rungrep),
            "xliff":("xliff", rungrep), "xlf":("xlf", rungrep), "xlff":("xlff", rungrep), 
            None:("po", rungrep)}
    parser = GrepOptionParser(formats)
    parser.add_option("", "--search", dest="searchparts",
        action="append", type="choice", choices=["source", "target", "notes", "locations", "msgid", "msgstr", "comment" ],
        metavar="SEARCHPARTS", help="searches the given parts (source, target, notes and locations)")
    parser.add_option("-I", "--ignore-case", dest="ignorecase",
        action="store_true", default=False, help="ignore case distinctions")
    parser.add_option("-e", "--regexp", dest="useregexp",
        action="store_true", default=False, help="use regular expression matching")
    parser.add_option("-v", "--invert-match", dest="invertmatch",
        action="store_true", default=False, help="select non-matching lines")
    parser.add_option("", "--accelerator", dest="accelchar",
        action="store", type="choice", choices=["&", "_", "~"],
        metavar="ACCELERATOR", help="ignores the given accelerator when matching")
    parser.set_usage()
    parser.passthrough.append('checkfilter')
    parser.description = __doc__
    return parser

def main():
    parser = cmdlineparser()
    parser.run()

if __name__ == '__main__':
    main()
