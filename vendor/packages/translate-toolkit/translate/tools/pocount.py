#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2003-2009 Zuza Software Foundation
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

"""Create string and word counts for supported localization files including:
XLIFF, TMX, Gettex PO and MO, Qt .ts and .qm, Wordfast TM, etc

See: http://translate.sourceforge.net/wiki/toolkit/pocount for examples and
usage instructions
"""

from translate.storage import factory
from translate.storage import statsdb
from optparse import OptionParser
import sys
import os

# define style constants
style_full, style_csv, style_short_strings, style_short_words = range(4)

# default output style
default_style = style_full


def calcstats_old(filename):
    """This is the previous implementation of calcstats() and is left for
    comparison and debuging purposes."""
    # ignore totally blank or header units
    try:
        store = factory.getobject(filename)
    except ValueError, e:
        print str(e)
        return {}
    units = filter(lambda unit: not unit.isheader(), store.units)
    translated = translatedmessages(units)
    fuzzy = fuzzymessages(units)
    review = filter(lambda unit: unit.isreview(), units)
    untranslated = untranslatedmessages(units)
    wordcounts = dict(map(lambda unit: (unit, statsdb.wordsinunit(unit)), units))
    sourcewords = lambda elementlist: sum(map(lambda unit: wordcounts[unit][0], elementlist))
    targetwords = lambda elementlist: sum(map(lambda unit: wordcounts[unit][1], elementlist))
    stats = {}

    #units
    stats["translated"] = len(translated)
    stats["fuzzy"] = len(fuzzy)
    stats["untranslated"] = len(untranslated)
    stats["review"] = len(review)
    stats["total"] = stats["translated"] + stats["fuzzy"] + stats["untranslated"]

    #words
    stats["translatedsourcewords"] = sourcewords(translated)
    stats["translatedtargetwords"] = targetwords(translated)
    stats["fuzzysourcewords"] = sourcewords(fuzzy)
    stats["untranslatedsourcewords"] = sourcewords(untranslated)
    stats["reviewsourcewords"] = sourcewords(review)
    stats["totalsourcewords"] = stats["translatedsourcewords"] + \
                                stats["fuzzysourcewords"] + \
                                stats["untranslatedsourcewords"]
    return stats

def calcstats(filename):
    statscache = statsdb.StatsCache()
    return statscache.filetotals(filename)

def summarize(title, stats, style=style_full, indent=8, incomplete_only=False):
    """
    Print summary for a .po file in specified format.

    @param title: name of .po file
    @param stats: array with translation statistics for the file specified
    @param indent: indentation of the 2nd column (length of longest filename)
    @param incomplete_only: omit fully translated files
    @type incomplete_only: Boolean
    @rtype: Boolean
    @return: 1 if counting incomplete files (incomplete_only=True) and the 
    file is completely translated, 0 otherwise
    """
    def percent(denominator, devisor):
        if devisor == 0:
            return 0
        else:
            return denominator*100/devisor

    if incomplete_only and (stats["total"] == stats["translated"]):
        return 1

    if (style == style_csv):
        print "%s, " % title,
        print "%d, %d, %d," % (stats["translated"], stats["translatedsourcewords"], stats["translatedtargetwords"]),
        print "%d, %d," % (stats["fuzzy"], stats["fuzzysourcewords"]),
        print "%d, %d," % (stats["untranslated"], stats["untranslatedsourcewords"]),
        print "%d, %d" % (stats["total"], stats["totalsourcewords"]),
        if stats["review"] > 0:
            print ", %d, %d" % (stats["review"], stats["reviewsourdcewords"]),
        print
    elif (style == style_short_strings):
        spaces = " "*(indent - len(title))
        print "%s%s strings: total: %d\t| %dt\t%df\t%du\t| %d%%t\t%d%%f\t%d%%u" % (title, spaces,\
              stats["total"], stats["translated"], stats["fuzzy"], stats["untranslated"], \
              percent(stats["translated"], stats["total"]), \
              percent(stats["fuzzy"], stats["total"]), \
              percent(stats["untranslated"], stats["total"]))
    elif (style == style_short_words):
        spaces = " "*(indent - len(title))
        print "%s%s source words: total: %d\t| %dt\t%df\t%du\t| %d%%t\t%d%%f\t%d%%u" % (title, spaces,\
              stats["totalsourcewords"], stats["translatedsourcewords"], stats["fuzzysourcewords"], stats["untranslatedsourcewords"], \
              percent(stats["translatedsourcewords"], stats["totalsourcewords"]), \
              percent(stats["fuzzysourcewords"], stats["totalsourcewords"]), \
              percent(stats["untranslatedsourcewords"], stats["totalsourcewords"]))
    else: # style == style_full
        print title
        print "type              strings      words (source)    words (translation)"
        print "translated:   %5d (%3d%%) %10d (%3d%%) %15d" % \
                (stats["translated"], \
                percent(stats["translated"], stats["total"]), \
                stats["translatedsourcewords"], \
                percent(stats["translatedsourcewords"], stats["totalsourcewords"]), \
                stats["translatedtargetwords"])
        print "fuzzy:        %5d (%3d%%) %10d (%3d%%)             n/a" % \
                (stats["fuzzy"], \
                percent(stats["fuzzy"], stats["total"]), \
                stats["fuzzysourcewords"], \
                percent(stats["fuzzysourcewords"], stats["totalsourcewords"]))
        print "untranslated: %5d (%3d%%) %10d (%3d%%)             n/a" % \
                (stats["untranslated"], \
                percent(stats["untranslated"], stats["total"]), \
                stats["untranslatedsourcewords"], \
                percent(stats["untranslatedsourcewords"], stats["totalsourcewords"]))
        print "Total:        %5d %17d %22d" % \
                (stats["total"], \
                stats["totalsourcewords"], \
                stats["translatedtargetwords"])
        if stats["review"] > 0:
            print "review:       %5d %17d                    n/a" % \
                    (stats["review"], stats["reviewsourcewords"])
        print
    return 0

def fuzzymessages(units):
    return filter(lambda unit: unit.isfuzzy() and unit.target, units)

def translatedmessages(units):
    return filter(lambda unit: unit.istranslated(), units)

def untranslatedmessages(units):
    return filter(lambda unit: not (unit.istranslated() or unit.isfuzzy()) and unit.source, units)

class summarizer:
    def __init__(self, filenames, style=default_style, incomplete_only=False):
        self.totals = {}
        self.filecount = 0
        self.longestfilename = 0
        self.style = style
        self.incomplete_only = incomplete_only
        self.complete_count = 0

        if (self.style == style_csv):
            print "Filename, Translated Messages, Translated Source Words, Translated \
Target Words, Fuzzy Messages, Fuzzy Source Words, Untranslated Messages, \
Untranslated Source Words, Total Message, Total Source Words, \
Review Messages, Review Source Words"
        if (self.style == style_short_strings or self.style == style_short_words):
            for filename in filenames:  # find longest filename
                if (len(filename) > self.longestfilename):
                    self.longestfilename = len(filename)
        for filename in filenames:
            if not os.path.exists(filename):
                print >> sys.stderr, "cannot process %s: does not exist" % filename
                continue
            elif os.path.isdir(filename):
                self.handledir(filename)
            else:
                self.handlefile(filename)
        if self.filecount > 1 and (self.style == style_full):
            if self.incomplete_only:
                summarize("TOTAL (incomplete only):", self.totals, incomplete_only=True)
                print "File count (incomplete):   %5d" % (self.filecount - self.complete_count)
            else:
                summarize("TOTAL:", self.totals, incomplete_only=False)
            print "File count:   %5d" % (self.filecount)
            print

    def updatetotals(self, stats):
        """Update self.totals with the statistics in stats."""
        for key in stats.keys():
            if not self.totals.has_key(key):
                self.totals[key] = 0
            self.totals[key] += stats[key]

    def handlefile(self, filename):
        try:
            stats = calcstats(filename)
            self.updatetotals(stats)
            self.complete_count += summarize(filename, stats, self.style, self.longestfilename, self.incomplete_only)
            self.filecount += 1
        except: # This happens if we have a broken file.
            print >> sys.stderr, sys.exc_info()[1]

    def handlefiles(self, dirname, filenames):
        for filename in filenames:
            pathname = os.path.join(dirname, filename)
            if os.path.isdir(pathname):
                self.handledir(pathname)
            else:
                self.handlefile(pathname)

    def handledir(self, dirname):
        path, name = os.path.split(dirname)
        if name in ["CVS", ".svn", "_darcs", ".git", ".hg", ".bzr"]:
            return
        entries = os.listdir(dirname)
        self.handlefiles(dirname, entries)

def main():
    parser = OptionParser(usage="usage: %prog [options] po-files")
    parser.add_option("--incomplete", action="store_const", const = True, dest = "incomplete_only",
                      help="skip 100% translated files.")
    # options controlling output format:
    parser.add_option("--full", action="store_const", const = style_csv, dest = "style_full",
                      help="(default) statistics in full, verbose format")
    parser.add_option("--csv", action="store_const", const = style_csv, dest = "style_csv",
                      help="statistics in CSV format")
    parser.add_option("--short", action="store_const", const = style_csv, dest = "style_short_strings",
                      help="same as --short-strings")
    parser.add_option("--short-strings", action="store_const", const = style_csv, dest = "style_short_strings",
                      help="statistics of strings in short format - one line per file")
    parser.add_option("--short-words", action="store_const", const = style_csv, dest = "style_short_words",
                      help="statistics of words in short format - one line per file")

    (options, args) = parser.parse_args()

    if (options.incomplete_only == None):
        options.incomplete_only = False

    if (options.style_full and options.style_csv) or \
       (options.style_full and options.style_short_strings) or \
       (options.style_full and options.style_short_words) or \
       (options.style_csv and options.style_short_strings) or \
       (options.style_csv and options.style_short_words) or \
       (options.style_short_strings and options.style_short_words):
        parser.error("options --full, --csv, --short-strings and --short-words are mutually exclusive")
        sys.exit(2)

    style = default_style   # default output style
    if options.style_csv:
        style = style_csv
    if options.style_full:
        style = style_full
    if options.style_short_strings:
        style = style_short_strings
    if options.style_short_words:
        style = style_short_words

    try:
        import psyco
        psyco.full()
    except Exception:
        pass

    summarizer(args, style, options.incomplete_only)

if __name__ == '__main__':
    main()
