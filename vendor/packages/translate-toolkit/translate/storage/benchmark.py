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
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from translate.storage import factory
import os
import cProfile
import pstats
import random
import sys

class TranslateBenchmarker:
    """class to aid in benchmarking Translate Toolkit stores"""
    def __init__(self, test_dir, storeclass):
        """sets up benchmarking on the test directory"""
        self.test_dir = os.path.abspath(test_dir)
        self.StoreClass = storeclass
        self.extension = self.StoreClass.Extensions[0]
        self.project_dir = os.path.join(self.test_dir, "benchmark")
        self.file_dir = os.path.join(self.project_dir, "zxx")

    def clear_test_dir(self):
        """removes the given directory"""
        if os.path.exists(self.test_dir):
            for dirpath, subdirs, filenames in os.walk(self.test_dir, topdown=False):
                for name in filenames:
                    os.remove(os.path.join(dirpath, name))
                for name in subdirs:
                    os.rmdir(os.path.join(dirpath, name))
        if os.path.exists(self.test_dir): os.rmdir(self.test_dir)
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

    def parse_file(self):
        """parses all the files in the test directory into memory"""
        count = 0
        for dirpath, subdirs, filenames in os.walk(self.file_dir, topdown=False):
            for name in filenames:
                pofilename = os.path.join(dirpath, name)
                parsedfile = self.StoreClass(open(pofilename, 'r'))
                count += len(parsedfile.units)
        print "counted %d units" % count

if __name__ == "__main__":
    storetype = "po"
    if len(sys.argv) > 1:
        storetype = sys.argv[1]
    if storetype in factory.classes:
        storeclass = factory.classes[storetype]
    else:
        print "StoreClass: '%s' is not a base class that the class factory can load" % storetype
        sys.exit()
    for sample_file_sizes in [
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
      ]:
        benchmarker = TranslateBenchmarker("BenchmarkDir", storeclass)
        benchmarker.clear_test_dir()
        benchmarker.create_sample_files(*sample_file_sizes)
        methods = [("create_sample_files", "*sample_file_sizes"), ("parse_file", ""), ]
        for methodname, methodparam in methods:
            print methodname, "%d dirs, %d files, %d strings, %d/%d words" % sample_file_sizes
            print "_______________________________________________________"
            statsfile = "%s_%s" % (methodname, storetype) + '_%d_%d_%d_%d_%d.stats' % sample_file_sizes
            cProfile.run('benchmarker.%s(%s)' % (methodname, methodparam), statsfile)
            stats = pstats.Stats(statsfile)
            stats.sort_stats('cumulative').print_stats(20)
            print "_______________________________________________________"
        #benchmarker.clear_test_dir()

