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

"""diff tool like GNU diff, but lets you have special options
that are useful in dealing with PO files"""

import difflib
import fnmatch
import os
import sys
import time
from argparse import ArgumentParser


lineterm = "\n"


def main():
    """main program for pydiff"""
    parser = ArgumentParser()
    # GNU diff like options
    parser.add_argument("-i", "--ignore-case", default=False, action="store_true",
                        help='Ignore case differences in file contents.')
    parser.add_argument("-U", "--unified", type=int, metavar="NUM", default=3,
                        dest="unified_lines",
                        help='Output NUM (default 3) lines of unified context')
    parser.add_argument("-r", "--recursive", default=False, action="store_true",
                        help='Recursively compare any subdirectories found.')
    parser.add_argument("-N", "--new-file", default=False, action="store_true",
                        help='Treat absent files as empty.')
    parser.add_argument("--unidirectional-new-file", default=False,
                        action="store_true",
                        help='Treat absent first files as empty.')
    parser.add_argument("-s", "--report-identical-files", default=False,
                        action="store_true",
                        help='Report when two files are the same.')
    parser.add_argument("-x", "--exclude", default=["CVS", "*.po~"],
                        action="append", metavar="PAT",
                        help='Exclude files that match PAT.')
    # our own options
    parser.add_argument("--fromcontains", type=str, default=None,
                        metavar="TEXT",
                        help='Only show changes where fromfile contains TEXT')
    parser.add_argument("--tocontains", type=str, default=None,
                        metavar="TEXT",
                        help='Only show changes where tofile contains TEXT')
    parser.add_argument("--contains", type=str, default=None,
                        metavar="TEXT",
                        help='Only show changes where fromfile or tofile contains TEXT')
    parser.add_argument("-I", "--ignore-case-contains", default=False, action="store_true",
                        help='Ignore case differences when matching any of the changes')
    parser.add_argument("--accelerator", dest="accelchars", default="",
                        metavar="ACCELERATORS",
                        help="ignores the given accelerator characters when matching")
    parser.add_argument("fromfile", nargs=1)
    parser.add_argument("tofile", nargs=1)
    args = parser.parse_args()

    fromfile, tofile = args.fromfile[0], args.tofile[0]
    if fromfile == "-" and tofile == "-":
        parser.error("Only one of fromfile and tofile can be read from stdin")

    if os.path.isdir(fromfile):
        if os.path.isdir(tofile):
            differ = DirDiffer(fromfile, tofile, args)
        else:
            parser.error("File %s is a directory while file %s is a regular file" %
                         (fromfile, tofile))
    else:
        if os.path.isdir(tofile):
            parser.error("File %s is a regular file while file %s is a directory" %
                         (fromfile, tofile))
        else:
            differ = FileDiffer(fromfile, tofile, args)
    differ.writediff(sys.stdout)


class DirDiffer:
    """generates diffs between directories"""

    def __init__(self, fromdir, todir, options):
        """Constructs a comparison between the two dirs using the
        given options"""
        self.fromdir = fromdir
        self.todir = todir
        self.options = options

    def isexcluded(self, difffile):
        """checks if the given filename has been excluded from the diff"""
        for exclude_pat in self.options.exclude:
            if fnmatch.fnmatch(difffile, exclude_pat):
                return True
        return False

    def writediff(self, outfile):
        """writes the actual diff to the given file"""
        fromfiles = os.listdir(self.fromdir)
        tofiles = os.listdir(self.todir)
        difffiles = dict.fromkeys(fromfiles + tofiles).keys()
        difffiles.sort()
        for difffile in difffiles:
            if self.isexcluded(difffile):
                continue
            from_ok = (difffile in fromfiles or self.options.new_file or
                       self.options.unidirectional_new_file)
            to_ok = (difffile in tofiles or self.options.new_file)
            if from_ok and to_ok:
                fromfile = os.path.join(self.fromdir, difffile)
                tofile = os.path.join(self.todir, difffile)
                if os.path.isdir(fromfile):
                    if os.path.isdir(tofile):
                        if self.options.recursive:
                            differ = DirDiffer(fromfile, tofile, self.options)
                            differ.writediff(outfile)
                        else:
                            outfile.write("Common subdirectories: %s and %s\n" %
                                          (fromfile, tofile))
                    else:
                        outfile.write("File %s is a directory while file %s is a regular file\n" %
                                      (fromfile, tofile))
                else:
                    if os.path.isdir(tofile):
                        parser.error("File %s is a regular file while file %s is a directory\n" %
                                     (fromfile, tofile))
                    else:
                        filediffer = FileDiffer(fromfile, tofile, self.options)
                        filediffer.writediff(outfile)
            elif from_ok:
                outfile.write("Only in %s: %s\n" % (self.fromdir, difffile))
            elif to_ok:
                outfile.write("Only in %s: %s\n" % (self.todir, difffile))


class FileDiffer:
    """generates diffs between files"""

    def __init__(self, fromfile, tofile, options):
        """Constructs a comparison between the two files using the given
        options"""
        self.fromfile = fromfile
        self.tofile = tofile
        self.options = options

    def writediff(self, outfile):
        """writes the actual diff to the given file"""
        validfiles = True
        if os.path.exists(self.fromfile):
            self.from_lines = open(self.fromfile, 'U').readlines()
            fromfiledate = os.stat(self.fromfile).st_mtime
        elif self.fromfile == "-":
            self.from_lines = sys.stdin.readlines()
            fromfiledate = time.time()
        elif self.options.new_file or self.options.unidirectional_new_file:
            self.from_lines = []
            fromfiledate = 0
        else:
            outfile.write("%s: No such file or directory\n" % self.fromfile)
            validfiles = False
        if os.path.exists(self.tofile):
            self.to_lines = open(self.tofile, 'U').readlines()
            tofiledate = os.stat(self.tofile).st_mtime
        elif self.tofile == "-":
            self.to_lines = sys.stdin.readlines()
            tofiledate = time.time()
        elif self.options.new_file:
            self.to_lines = []
            tofiledate = 0
        else:
            outfile.write("%s: No such file or directory\n" % self.tofile)
            validfiles = False
        if not validfiles:
            return
        fromfiledate = time.ctime(fromfiledate)
        tofiledate = time.ctime(tofiledate)
        compare_from_lines = self.from_lines
        compare_to_lines = self.to_lines
        if self.options.ignore_case:
            compare_from_lines = [line.lower() for line in compare_from_lines]
            compare_to_lines = [line.lower() for line in compare_to_lines]
        matcher = difflib.SequenceMatcher(None, compare_from_lines, compare_to_lines)
        groups = matcher.get_grouped_opcodes(self.options.unified_lines)
        started = False
        fromstring = '--- %s\t%s%s' % (self.fromfile, fromfiledate, lineterm)
        tostring = '+++ %s\t%s%s' % (self.tofile, tofiledate, lineterm)

        for group in groups:
            hunk = "".join([line for line in self.unified_diff(group)])
            if self.options.fromcontains:
                if self.options.ignore_case_contains:
                    hunk_from_lines = "".join([line.lower() for line in self.get_from_lines(group)])
                else:
                    hunk_from_lines = "".join(self.get_from_lines(group))
                for accelerator in self.options.accelchars:
                    hunk_from_lines = hunk_from_lines.replace(accelerator, "")
                if self.options.fromcontains not in hunk_from_lines:
                    continue
            if self.options.tocontains:
                if self.options.ignore_case_contains:
                    hunk_to_lines = "".join([line.lower() for line in self.get_to_lines(group)])
                else:
                    hunk_to_lines = "".join(self.get_to_lines(group))
                for accelerator in self.options.accelchars:
                    hunk_to_lines = hunk_to_lines.replace(accelerator, "")
                if self.options.tocontains not in hunk_to_lines:
                    continue
            if self.options.contains:
                if self.options.ignore_case_contains:
                    hunk_lines = "".join([line.lower() for line in self.get_from_lines(group) + self.get_to_lines(group)])
                else:
                    hunk_lines = "".join(self.get_from_lines(group) + self.get_to_lines(group))
                for accelerator in self.options.accelchars:
                    hunk_lines = hunk_lines.replace(accelerator, "")
                if self.options.contains not in hunk_lines:
                    continue
            if not started:
                outfile.write(fromstring)
                outfile.write(tostring)
                started = True
            outfile.write(hunk)
        if not started and self.options.report_identical_files:
            outfile.write("Files %s and %s are identical\n" %
                          (self.fromfile, self.tofile))

    def get_from_lines(self, group):
        """returns the lines referred to by group, from the fromfile"""
        from_lines = []
        for tag, i1, i2, j1, j2 in group:
            from_lines.extend(self.from_lines[i1:i2])
        return from_lines

    def get_to_lines(self, group):
        """returns the lines referred to by group, from the tofile"""
        to_lines = []
        for tag, i1, i2, j1, j2 in group:
            to_lines.extend(self.to_lines[j1:j2])
        return to_lines

    def unified_diff(self, group):
        """takes the group of opcodes and generates a unified diff line
        by line"""
        i1, i2, j1, j2 = group[0][1], group[-1][2], group[0][3], group[-1][4]
        yield "@@ -%d,%d +%d,%d @@%s" % (i1 + 1, i2 - i1, j1 + 1, j2 - j1, lineterm)
        for tag, i1, i2, j1, j2 in group:
            if tag == 'equal':
                for line in self.from_lines[i1:i2]:
                    yield ' ' + line
                continue
            if tag == 'replace' or tag == 'delete':
                for line in self.from_lines[i1:i2]:
                    yield '-' + line
            if tag == 'replace' or tag == 'insert':
                for line in self.to_lines[j1:j2]:
                    yield '+' + line


if __name__ == "__main__":
    main()
