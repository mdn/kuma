#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2005-2007 Zuza Software Foundation
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

"""Conflict finder for Gettext PO localization files

See: http://translate.sourceforge.net/wiki/toolkit/poconflicts for examples and
usage instructions
"""

from translate.storage import factory
from translate.storage import po
from translate.misc import optrecurse
import sys
import os

class ConflictOptionParser(optrecurse.RecursiveOptionParser):
    """a specialized Option Parser for the conflict tool..."""
    def parse_args(self, args=None, values=None):
        """parses the command line options, handling implicit input/output args"""
        (options, args) = optrecurse.optparse.OptionParser.parse_args(self, args, values)
        # some intelligence as to what reasonable people might give on the command line
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
        if not options.output:
            self.error("output file is required")
        if args:
            self.error("You have used an invalid combination of --input, --output and freestanding args")
        if isinstance(options.input, list) and len(options.input) == 1:
            options.input = options.input[0]
        return (options, args)

    def set_usage(self, usage=None):
        """sets the usage string - if usage not given, uses getusagestring for each option"""
        if usage is None:
            self.usage = "%prog " + " ".join([self.getusagestring(option) for option in self.option_list]) + \
                    "\n  input directory is searched for PO files, PO files with name of conflicting string are output in output directory"
        else:
            super(ConflictOptionParser, self).set_usage(usage)

    def run(self):
        """parses the arguments, and runs recursiveprocess with the resulting options"""
        (options, args) = self.parse_args()
        options.inputformats = self.inputformats
        options.outputoptions = self.outputoptions
        self.usepsyco(options)
        self.recursiveprocess(options)

    def recursiveprocess(self, options):
        """recurse through directories and process files"""
        if self.isrecursive(options.input, 'input') and getattr(options, "allowrecursiveinput", True):
            if not self.isrecursive(options.output, 'output'):
                try:
                    self.warning("Output directory does not exist. Attempting to create")
                    os.mkdir(options.output)
                except:
                    self.error(optrecurse.optparse.OptionValueError("Output directory does not exist, attempt to create failed"))
            if isinstance(options.input, list):
                inputfiles = self.recurseinputfilelist(options)
            else:
                inputfiles = self.recurseinputfiles(options)
        else:
            if options.input:
                inputfiles = [os.path.basename(options.input)]
                options.input = os.path.dirname(options.input)
            else:
                inputfiles = [options.input]
        self.textmap = {}
        self.initprogressbar(inputfiles, options)
        for inputpath in inputfiles:
            fullinputpath = self.getfullinputpath(options, inputpath)
            try:
                success = self.processfile(None, options, fullinputpath)
            except Exception, error:
                if isinstance(error, KeyboardInterrupt):
                    raise
                self.warning("Error processing: input %s" % (fullinputpath), options, sys.exc_info())
                success = False
            self.reportprogress(inputpath, success)
        del self.progressbar
        self.buildconflictmap()
        self.outputconflicts(options)

    def clean(self, string, options):
        """returns the cleaned string that contains the text to be matched"""
        if options.ignorecase:
            string = string.lower()
        for accelerator in options.accelchars:
            string = string.replace(accelerator, "")
        string = string.strip()
        return string

    def processfile(self, fileprocessor, options, fullinputpath):
        """process an individual file"""
        inputfile = self.openinputfile(options, fullinputpath)
        inputfile = factory.getobject(inputfile)
        for unit in inputfile.units:
            if unit.isheader() or not unit.istranslated():
                continue
            if unit.hasplural():
                continue
            if not options.invert:
                source = self.clean(unit.source, options)
                target = self.clean(unit.target, options)
            else:
                target = self.clean(unit.source, options)
                source = self.clean(unit.target, options)
            self.textmap.setdefault(source, []).append((target, unit, fullinputpath))

    def flatten(self, text, joinchar):
        """flattens text to just be words"""
        flattext = ""
        for c in text:
            if c.isalnum():
                flattext += c
            elif flattext[-1:].isalnum():
                flattext += joinchar
        return flattext.rstrip(joinchar)

    def buildconflictmap(self):
        """work out which strings are conflicting"""
        self.conflictmap = {}
        for source, translations in self.textmap.iteritems():
            source = self.flatten(source, " ")
            if len(source) <= 1:
                continue
            if len(translations) > 1:
                uniquetranslations = dict.fromkeys([target for target, unit, filename in translations])
                if len(uniquetranslations) > 1:
                    self.conflictmap[source] = translations

    def outputconflicts(self, options):
        """saves the result of the conflict match"""
        print "%d/%d different strings have conflicts" % (len(self.conflictmap), len(self.textmap))
        reducedmap = {}
        for source, translations in self.conflictmap.iteritems():
            words = source.split()
            words.sort(lambda x, y: cmp(len(x), len(y)))
            source = words[-1]
            reducedmap.setdefault(source, []).extend(translations)
        # reduce plurals
        plurals = {}
        for word in reducedmap:
            if word + "s" in reducedmap:
                plurals[word] = word + "s"
        for word, pluralword in plurals.iteritems():
            reducedmap[word].extend(reducedmap.pop(pluralword))
        for source, translations in reducedmap.iteritems():
            flatsource = self.flatten(source, "-")
            fulloutputpath = os.path.join(options.output, flatsource + os.extsep + "po")
            conflictfile = po.pofile()
            for target, unit, filename in translations:
                unit.othercomments.append("# (poconflicts) %s\n" % filename)
                conflictfile.units.append(unit)
            open(fulloutputpath, "w").write(str(conflictfile))

def main():
    formats = {"po":("po", None), None:("po", None)}
    parser = ConflictOptionParser(formats)
    parser.add_option("-I", "--ignore-case", dest="ignorecase",
        action="store_true", default=False, help="ignore case distinctions")
    parser.add_option("-v", "--invert", dest="invert",
        action="store_true", default=False, help="invert the conflicts thus extracting conflicting destination words")
    parser.add_option("", "--accelerator", dest="accelchars", default="",
        metavar="ACCELERATORS", help="ignores the given accelerator characters when matching")
    parser.set_usage()
    parser.description = __doc__
    parser.run()


if __name__ == '__main__':
    main()
