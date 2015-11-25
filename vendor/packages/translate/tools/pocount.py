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

"""Count strings and words for supported localization files.

These include: XLIFF, TMX, Gettex PO and MO, Qt .ts and .qm, Wordfast TM, etc

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/pocount.html
for examples and usage instructions.
"""

from __future__ import print_function

import logging
import os
import sys
from argparse import ArgumentParser

from translate.storage import factory, statsdb


logger = logging.getLogger(__name__)

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
    except ValueError as e:
        logger.warning(e)
        return {}
    units = filter(lambda unit: unit.istranslatable(), store.units)
    translated = translatedmessages(units)
    fuzzy = fuzzymessages(units)
    review = filter(lambda unit: unit.isreview(), units)
    untranslated = untranslatedmessages(units)
    wordcounts = dict(map(lambda unit: (unit, statsdb.wordsinunit(unit)), units))
    sourcewords = lambda elementlist: sum(map(lambda unit: wordcounts[unit][0], elementlist))
    targetwords = lambda elementlist: sum(map(lambda unit: wordcounts[unit][1], elementlist))
    stats = {}

    # units
    stats["translated"] = len(translated)
    stats["fuzzy"] = len(fuzzy)
    stats["untranslated"] = len(untranslated)
    stats["review"] = len(review)
    stats["total"] = stats["translated"] + \
                     stats["fuzzy"] + \
                     stats["untranslated"]

    # words
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
    return statscache.filetotals(filename, extended=True)


def summarize(title, stats, style=style_full, indent=8, incomplete_only=False):
    """Print summary for a .po file in specified format.

    :param title: name of .po file
    :param stats: array with translation statistics for the file specified
    :param indent: indentation of the 2nd column (length of longest filename)
    :param incomplete_only: omit fully translated files
    :type incomplete_only: Boolean
    :rtype: Boolean
    :return: 1 if counting incomplete files (incomplete_only=True) and the
             file is completely translated, 0 otherwise
    """

    def percent(denominator, devisor):
        if devisor == 0:
            return 0
        else:
            return denominator * 100 / devisor

    if incomplete_only and (stats["total"] == stats["translated"]):
        return 1

    if (style == style_csv):
        print("%s, " % title, end=' ')
        print("%d, %d, %d," % (stats["translated"],
                               stats["translatedsourcewords"],
                               stats["translatedtargetwords"]), end=' ')
        print("%d, %d," % (stats["fuzzy"], stats["fuzzysourcewords"]), end=' ')
        print("%d, %d," % (stats["untranslated"],
                           stats["untranslatedsourcewords"]), end=' ')
        print("%d, %d" % (stats["total"], stats["totalsourcewords"]), end=' ')
        if stats["review"] > 0:
            print(", %d, %d" % (stats["review"], stats["reviewsourdcewords"]), end=' ')
        print()
    elif (style == style_short_strings):
        spaces = " " * (indent - len(title))
        print("%s%s strings: total: %d\t| %dt\t%df\t%du\t| %d%%t\t%d%%f\t%d%%u" % (
              title, spaces,
              stats["total"], stats["translated"], stats["fuzzy"], stats["untranslated"],
              percent(stats["translated"], stats["total"]),
              percent(stats["fuzzy"], stats["total"]),
              percent(stats["untranslated"], stats["total"])))
    elif (style == style_short_words):
        spaces = " " * (indent - len(title))
        print("%s%s source words: total: %d\t| %dt\t%df\t%du\t| %d%%t\t%d%%f\t%d%%u" % (
              title, spaces,
              stats["totalsourcewords"], stats["translatedsourcewords"], stats["fuzzysourcewords"], stats["untranslatedsourcewords"],
              percent(stats["translatedsourcewords"], stats["totalsourcewords"]),
              percent(stats["fuzzysourcewords"], stats["totalsourcewords"]),
              percent(stats["untranslatedsourcewords"], stats["totalsourcewords"])))
    else:  # style == style_full
        print(title)
        print("type              strings      words (source)    words (translation)")
        print("translated:   %5d (%3d%%) %10d (%3d%%) %15d" % (
              stats["translated"],
              percent(stats["translated"], stats["total"]),
              stats["translatedsourcewords"],
              percent(stats["translatedsourcewords"], stats["totalsourcewords"]),
              stats["translatedtargetwords"]))
        print("fuzzy:        %5d (%3d%%) %10d (%3d%%)             n/a" % (
              stats["fuzzy"],
              percent(stats["fuzzy"], stats["total"]),
              stats["fuzzysourcewords"],
              percent(stats["fuzzysourcewords"], stats["totalsourcewords"])))
        print("untranslated: %5d (%3d%%) %10d (%3d%%)             n/a" % (
              stats["untranslated"],
              percent(stats["untranslated"], stats["total"]),
              stats["untranslatedsourcewords"],
              percent(stats["untranslatedsourcewords"], stats["totalsourcewords"])))
        print("Total:        %5d %17d %22d" % (
              stats["total"],
              stats["totalsourcewords"],
              stats["translatedtargetwords"]))
        if "extended" in stats:
            print("")
            for state, e_stats in stats["extended"].iteritems():
                print("%s:    %5d (%3d%%) %10d (%3d%%) %15d" % (
                      state, e_stats["units"], percent(e_stats["units"], stats["total"]),
                      e_stats["sourcewords"], percent(e_stats["sourcewords"], stats["totalsourcewords"]),
                      e_stats["targetwords"]))

        if stats["review"] > 0:
            print("review:       %5d %17d                    n/a" % (
                  stats["review"], stats["reviewsourcewords"]))
        print()
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
            print("""Filename, Translated Messages, Translated Source Words, Translated
Target Words, Fuzzy Messages, Fuzzy Source Words, Untranslated Messages,
Untranslated Source Words, Total Message, Total Source Words,
Review Messages, Review Source Words""")
        if (self.style == style_short_strings or self.style == style_short_words):
            for filename in filenames:  # find longest filename
                if (len(filename) > self.longestfilename):
                    self.longestfilename = len(filename)
        for filename in filenames:
            if not os.path.exists(filename):
                logger.error("cannot process %s: does not exist", filename)
                continue
            elif os.path.isdir(filename):
                self.handledir(filename)
            else:
                self.handlefile(filename)
        if self.filecount > 1 and (self.style == style_full):
            if self.incomplete_only:
                summarize("TOTAL (incomplete only):", self.totals,
                incomplete_only=True)
                print("File count (incomplete):   %5d" % (self.filecount - self.complete_count))
            else:
                summarize("TOTAL:", self.totals, incomplete_only=False)
            print("File count:   %5d" % (self.filecount))
            print()

    def updatetotals(self, stats):
        """Update self.totals with the statistics in stats."""
        for key in stats.keys():
            if key == "extended":
                # FIXME: calculate extended totals
                continue
            if not key in self.totals:
                self.totals[key] = 0
            self.totals[key] += stats[key]

    def handlefile(self, filename):
        try:
            stats = calcstats(filename)
            self.updatetotals(stats)
            self.complete_count += summarize(filename, stats, self.style,
                                             self.longestfilename,
                                             self.incomplete_only)
            self.filecount += 1
        except Exception:  # This happens if we have a broken file.
            logger.error(sys.exc_info()[1])

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
    parser = ArgumentParser()
    parser.add_argument("--incomplete", action="store_true", default=False,
                        dest="incomplete_only",
                        help="skip 100%% translated files.")
    if sys.version_info[:2] <= (2, 6):
        # Python 2.6 using argparse from PyPI cannot define a mutually
        # exclusive group as a child of a group, but it works if it is a child
        # of the parser.  We lose the group title but the functionality works.
        # See https://code.google.com/p/argparse/issues/detail?id=90
        megroup = parser.add_mutually_exclusive_group()
    else:
        output_group = parser.add_argument_group("Output format")
        megroup = output_group.add_mutually_exclusive_group()
    megroup.add_argument("--full", action="store_const", const=style_full,
                        dest="style", default=style_full,
                        help="(default) statistics in full, verbose format")
    megroup.add_argument("--csv", action="store_const", const=style_csv,
                        dest="style",
                        help="statistics in CSV format")
    megroup.add_argument("--short", action="store_const", const=style_short_strings,
                        dest="style",
                        help="same as --short-strings")
    megroup.add_argument("--short-strings", action="store_const",
                        const=style_short_strings, dest="style",
                        help="statistics of strings in short format - one line per file")
    megroup.add_argument("--short-words", action="store_const",
                        const=style_short_words, dest="style",
                        help="statistics of words in short format - one line per file")

    parser.add_argument("files", nargs="+")

    args = parser.parse_args()

    logging.basicConfig(format="%(name)s: %(levelname)s: %(message)s")

    summarizer(args.files, args.style, args.incomplete_only)

if __name__ == '__main__':
    main()
