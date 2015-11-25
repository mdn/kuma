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

import logging
import os
from argparse import ArgumentParser

from translate.storage import factory, tmdb


logger = logging.getLogger(__name__)


class Builder:

    def __init__(self, tmdbfile, source_lang, target_lang, filenames):
        self.tmdb = tmdb.TMDB(tmdbfile)
        self.source_lang = source_lang
        self.target_lang = target_lang

        for filename in filenames:
            if not os.path.exists(filename):
                logger.error("cannot process %s: does not exist", filename)
                continue
            elif os.path.isdir(filename):
                self.handledir(filename)
            else:
                self.handlefile(filename)
        self.tmdb.connection.commit()

    def handlefile(self, filename):
        try:
            store = factory.getobject(filename)
        except Exception as e:
            logger.error(str(e))
            return
        # do something useful with the store and db
        try:
            self.tmdb.add_store(store, self.source_lang, self.target_lang, commit=False)
        except Exception as e:
            print(e)
        print("File added:", filename)

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
    parser.add_argument(
        "-d", "--tmdb", dest="tmdb_file", default="tm.db",
        help="translation memory database file (default: tm.db)")
    parser.add_argument(
        "-s", "--import-source-lang", dest="source_lang", default="en",
        help="source language of translation files (default: en)")
    parser.add_argument(
        "-t", "--import-target-lang", dest="target_lang",
        help="target language of translation files", required=True)
    parser.add_argument(
        "files", metavar="input files", nargs="+"
    )
    args = parser.parse_args()

    logging.basicConfig(format="%(name)s: %(levelname)s: %(message)s")

    Builder(args.tmdb_file, args.source_lang, args.target_lang, args.files)

if __name__ == '__main__':
    main()
