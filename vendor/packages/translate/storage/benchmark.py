#!/usr/bin/env python
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

import argparse
import cProfile
import os
import pstats
import random
import sys

from translate.storage import factory, placeables


class TranslateBenchmarker:
    """class to aid in benchmarking Translate Toolkit stores"""

    def __init__(self, test_dir, storeclass):
        """sets up benchmarking on the test directory"""
        self.test_dir = os.path.abspath(test_dir)
        self.StoreClass = storeclass
        self.extension = self.StoreClass.Extensions[0]
        self.project_dir = os.path.join(self.test_dir, "benchmark")
        self.file_dir = os.path.join(self.project_dir, "zxx")
        self.parsedfiles = []

    def clear_test_dir(self):
        """removes the given directory"""
        if os.path.exists(self.test_dir):
            for dirpath, subdirs, filenames in os.walk(self.test_dir, topdown=False):
                for name in filenames:
                    os.remove(os.path.join(dirpath, name))
                for name in subdirs:
                    os.rmdir(os.path.join(dirpath, name))
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)
        assert not os.path.exists(self.test_dir)

    def create_sample_files(self, num_dirs, files_per_dir, strings_per_file, source_words_per_string, target_words_per_string):
        """creates sample files for benchmarking"""
        if not os.path.exists(self.test_dir):
            os.mkdir(self.test_dir)
        if not os.path.exists(self.project_dir):
            os.mkdir(self.project_dir)
        if not os.path.exists(self.file_dir):
            os.mkdir(self.file_dir)
        for dirnum in range(num_dirs):
            if num_dirs > 1:
                dirname = os.path.join(self.file_dir, "sample_%d" % dirnum)
                if not os.path.exists(dirname):
                    os.mkdir(dirname)
            else:
                dirname = self.file_dir
            for filenum in range(files_per_dir):
                sample_file = self.StoreClass()
                for stringnum in range(strings_per_file):
                    source_string = " ".join(["word%d" % (random.randint(0, strings_per_file) * i) for i in range(source_words_per_string)])
                    sample_unit = sample_file.addsourceunit(source_string)
                    sample_unit.target = " ".join(["drow%d" % (random.randint(0, strings_per_file) * i) for i in range(target_words_per_string)])
                sample_file.savefile(os.path.join(dirname, "file_%d.%s" % (filenum, self.extension)))

    def parse_files(self, file_dir=None):
        """parses all the files in the test directory into memory"""
        count = 0
        self.parsedfiles = []
        if file_dir is None:
            file_dir = self.file_dir
        for dirpath, subdirs, filenames in os.walk(file_dir, topdown=False):
            for name in filenames:
                pofilename = os.path.join(dirpath, name)
                parsedfile = self.StoreClass(open(pofilename, 'r'))
                count += len(parsedfile.units)
                self.parsedfiles.append(parsedfile)
        print("counted %d units" % count)

    def parse_placeables(self):
        """parses placeables"""
        count = 0
        for parsedfile in self.parsedfiles:
            for unit in parsedfile.units:
                placeables.parse(unit.source, placeables.general.parsers)
                placeables.parse(unit.target, placeables.general.parsers)
            count += len(parsedfile.units)
        print("counted %d units" % count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('podir', metavar='DIR', type=str, nargs='?',
                        help='PO dir to use (default: create sample files)')
    parser.add_argument('--store-type', dest='storetype',
                        action='store_const', const='po', default="po",
                        help='type of the store to benchmark (default: po)')
    parser.add_argument('--check-parsing', dest='check_parsing',
                        action='store_true',
                        help='benchmark parsing files')
    parser.add_argument('--check-placeables', dest='check_placeables',
                        action='store_true',
                        help='benchmark placeables')
    args = parser.parse_args()

    storetype = args.storetype

    if storetype in factory.classes_str:
        _module, _class = factory.classes_str[storetype]
        module = __import__("translate.storage.%s" % _module,
                            globals(), fromlist=_module)
        storeclass = getattr(module, _class)
    else:
        print("StoreClass: '%s' is not a base class that the class factory can load" % storetype)
        sys.exit()

    sample_files = [
      # num_dirs, files_per_dir, strings_per_file, source_words_per_string, target_words_per_string
      # (1, 1, 2, 2, 2),
      (1, 1, 10000, 5, 10),   # Creat 1 very large file with German like ratios or source to target
      # (100, 10, 10, 5, 10),   # Create lots of directories and files with smaller then avarage size
      # (1, 5, 10, 10, 10),
      # (1, 10, 10, 10, 10),
      # (5, 10, 10, 10, 10),
      # (5, 10, 100, 20, 20),
      # (10, 20, 100, 10, 10),
      # (10, 20, 100, 10, 10),
      # (100, 2, 140, 3, 3),  # OpenOffice.org approximate ratios
    ]

    for sample_file_sizes in sample_files:
        benchmarker = TranslateBenchmarker("BenchmarkDir", storeclass)
        benchmarker.clear_test_dir()
        if args.podir is None:
            benchmarker.create_sample_files(*sample_file_sizes)
        benchmarker.parse_files(file_dir=args.podir)
        methods = []  # [("create_sample_files", "*sample_file_sizes")]

        if args.check_parsing:
            methods.append(("parse_files", ""))

        if args.check_placeables:
            methods.append(("parse_placeables", ""))

        for methodname, methodparam in methods:
            #print methodname, "%d dirs, %d files, %d strings, %d/%d words" % sample_file_sizes
            print("_______________________________________________________")
            statsfile = "%s_%s" % (methodname, storetype) + '_%d_%d_%d_%d_%d.stats' % sample_file_sizes
            cProfile.run('benchmarker.%s(%s)' % (methodname, methodparam), statsfile)
            stats = pstats.Stats(statsfile)
            stats.sort_stats('time').print_stats(20)
            print("_______________________________________________________")
        benchmarker.clear_test_dir()
