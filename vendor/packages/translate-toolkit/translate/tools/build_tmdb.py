#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

"""Import units from translations files into tmdb."""

import sys
import os
from optparse import OptionParser
from translate.storage import factory
from translate.storage import tmdb


class Builder:
    def __init__(self, tmdbfile, source_lang, target_lang, filenames):
        self.tmdb = tmdb.TMDB(tmdbfile)
        self.source_lang = source_lang
        self.target_lang = target_lang

        for filename in filenames:
            if not os.path.exists(filename):
                print >> sys.stderr, "cannot process %s: does not exist" % filename
                continue
            elif os.path.isdir(filename):
                self.handledir(filename)
            else:
                self.handlefile(filename)
        self.tmdb.connection.commit()

    def handlefile(self, filename):
        try:
            store = factory.getobject(filename)
        except Exception, e:
            print >> sys.stderr, str(e)
            return
        # do something useful with the store and db
        try:
            self.tmdb.add_store(store, self.source_lang, self.target_lang, commit=False)
        except Exception, e:
            print e
        print "File added:", filename

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
    try:
        import psyco
        psyco.full()
    except Exception:
        pass
    parser = OptionParser(usage="%prog [options] <input files>")
    parser.add_option(
        "-d", "--tmdb", dest="tmdb_file", default="tm.db",
        help="translation memory database file (default: tm.db)"
    )
    parser.add_option(
        "-s", "--import-source-lang", dest="source_lang", default="en",
        help="source language of translation files (default: en)"
    )
    parser.add_option(
        "-t", "--import-target-lang", dest="target_lang",
        help="target language of translation files"
    )
    (options, args) = parser.parse_args()

    if not options.target_lang:
        parser.error('No target language specified.')

    if len(args) < 1:
        parser.error('No input file(s) specified.')

    Builder(options.tmdb_file, options.source_lang, options.target_lang, args)

if __name__ == '__main__':
    main()
