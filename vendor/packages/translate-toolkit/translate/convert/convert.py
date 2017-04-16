#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

"""Handles converting of files between formats (used by translate.convert tools)"""

import os.path
from translate.misc import optrecurse
# don't import optparse ourselves, get the version from optrecurse
optparse = optrecurse.optparse
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class ConvertOptionParser(optrecurse.RecursiveOptionParser, object):
    """a specialized Option Parser for convertor tools..."""
    def __init__(self, formats, usetemplates=False, usepots=False, allowmissingtemplate=False, description=None):
        """construct the specialized Option Parser"""
        optrecurse.RecursiveOptionParser.__init__(self, formats, usetemplates, 
                allowmissingtemplate=allowmissingtemplate, description=description)
        self.usepots = usepots
        self.setpotoption()
        self.set_usage()

    def add_fuzzy_option(self, default=False):
        """adds an option to include / exclude fuzzy translations"""
        fuzzyhelp = "use translations marked fuzzy"
        nofuzzyhelp = "don't use translations marked fuzzy"
        if default:
            fuzzyhelp += " (default)"
        else:
            nofuzzyhelp += " (default)"
        self.add_option("", "--fuzzy", dest="includefuzzy", action="store_true", default=default, help=fuzzyhelp)
        self.add_option("", "--nofuzzy", dest="includefuzzy", action="store_false", default=default, help=nofuzzyhelp)
        self.passthrough.append("includefuzzy")

    def add_duplicates_option(self, default="msgctxt"):
        """adds an option to say what to do with duplicate strings"""
        self.add_option("", "--duplicates", dest="duplicatestyle", default=default,
            type="choice", choices=["msgctxt", "merge"],
            help="what to do with duplicate strings (identical source text): merge, msgctxt (default: '%s')" % default, metavar="DUPLICATESTYLE")
        self.passthrough.append("duplicatestyle")

    def add_multifile_option(self, default="single"):
        """adds an option to say how to split the po/pot files"""
        self.add_option("", "--multifile", dest="multifilestyle", default=default,
            type="choice", choices=["single", "toplevel", "onefile"],
            help="how to split po/pot files (single, toplevel or onefile)", metavar="MULTIFILESTYLE")
        self.passthrough.append("multifilestyle")

    def potifyformat(self, fileformat):
        """converts a .po to a .pot where required"""
        if fileformat is None:
            return fileformat
        elif fileformat == "po":
            return "pot"
        elif fileformat.endswith(os.extsep + "po"):
            return fileformat + "t"
        else:
            return fileformat

    def getformathelp(self, formats):
        """make a nice help string for describing formats..."""
        # include implicit pot options...
        helpformats = []
        for fileformat in formats:
            helpformats.append(fileformat)
            potformat = self.potifyformat(fileformat)
            if potformat != fileformat:
                helpformats.append(potformat)
        return super(ConvertOptionParser, self).getformathelp(helpformats)

    def filterinputformats(self, options):
        """filters input formats, processing relevant switches in options"""
        if self.usepots and options.pot:
            return [self.potifyformat(inputformat) for inputformat in self.inputformats]
        else:
            return self.inputformats

    def filteroutputoptions(self, options):
        """filters output options, processing relevant switches in options"""
        if self.usepots and options.pot:
            outputoptions = {}
            for (inputformat, templateformat), (outputformat, convertor) in self.outputoptions.iteritems():
                inputformat = self.potifyformat(inputformat)
                templateformat = self.potifyformat(templateformat)
                outputformat = self.potifyformat(outputformat)
                outputoptions[(inputformat, templateformat)] = (outputformat, convertor)
            return outputoptions
        else:
            return self.outputoptions

    def setpotoption(self):
        """sets the -P/--pot option depending on input/output formats etc"""
        if self.usepots:
            potoption = optparse.Option("-P", "--pot", \
                    action="store_true", dest="pot", default=False, \
                    help="output PO Templates (.pot) rather than PO files (.po)")
            self.define_option(potoption)

    def verifyoptions(self, options):
        """verifies that the options are valid (required options are present, etc)"""
        pass

    def run(self, argv=None):
        """parses the command line options and runs the conversion"""
        (options, args) = self.parse_args(argv)
        options.inputformats = self.filterinputformats(options)
        options.outputoptions = self.filteroutputoptions(options)
        self.usepsyco(options)
        self.verifyoptions(options)
        self.recursiveprocess(options)

def copyinput(inputfile, outputfile, templatefile, **kwargs):
    """copies the input file to the output file"""
    outputfile.write(inputfile.read())
    return True

def copytemplate(inputfile, outputfile, templatefile, **kwargs):
    """copies the template file to the output file"""
    outputfile.write(templatefile.read())
    return True

class Replacer:
    """an object that knows how to replace strings in files"""
    def __init__(self, searchstring, replacestring):
        self.searchstring = searchstring
        self.replacestring = replacestring

    def doreplace(self, text):
        """actually replace the text"""
        if self.searchstring is not None and self.replacestring is not None:
            return text.replace(self.searchstring, self.replacestring)
        else:
            return text

    def searchreplaceinput(self, inputfile, outputfile, templatefile, **kwargs):
        """copies the input file to the output file, searching and replacing"""
        outputfile.write(self.doreplace(inputfile.read()))
        return True

    def searchreplacetemplate(self, inputfile, outputfile, templatefile, **kwargs):
        """copies the template file to the output file, searching and replacing"""
        outputfile.write(self.doreplace(templatefile.read()))
        return True

# archive files need to know how to:
# - openarchive: creates an archive object for the archivefilename
#   * requires a constructor that takes the filename
# - iterarchivefile: iterate through the names in the archivefile
#   * requires the default iterator to do this
# - archivefileexists: check if a given pathname exists inside the archivefile
#   * uses the in operator - requires __contains__ (or will use __iter__ by default)
# - openarchiveinputfile: returns an open input file from the archive, given the path
#   * requires an archivefile.openinputfile method that takes the pathname
# - openarchiveoutputfile: returns an open output file from the archive, given the path
#   * requires an archivefile.openoutputfile method that takes the pathname

class ArchiveConvertOptionParser(ConvertOptionParser):
    """ConvertOptionParser that can handle recursing into single archive files.
    archiveformats maps extension to class. if the extension doesn't matter, it can be None.
    if the extension is only valid for input/output/template, it can be given as (extension, filepurpose)"""
    def __init__(self, formats, usetemplates=False, usepots=False, description=None, archiveformats=None):
        if archiveformats is None:
            self.archiveformats = {}
        else:
            self.archiveformats = archiveformats
        self.archiveoptions = {}
        ConvertOptionParser.__init__(self, formats, usetemplates, usepots, description=description)

    def setarchiveoptions(self, **kwargs):
        """allows setting options that will always be passed to openarchive"""
        self.archiveoptions = kwargs

    def isrecursive(self, fileoption, filepurpose='input'):
        """checks if fileoption is a recursive file"""
        if self.isarchive(fileoption, filepurpose): return True
        return super(ArchiveConvertOptionParser, self).isrecursive(fileoption, filepurpose)

    def isarchive(self, fileoption, filepurpose='input'):
        """returns whether the file option is an archive file"""
        if not isinstance(fileoption, (str, unicode)):
            return False
        mustexist = (filepurpose != 'output')
        if mustexist and not os.path.isfile(fileoption):
            return False
        fileext = self.splitext(fileoption)[1]
        # if None is in the archive formats, then treat all non-directory inputs as archives
        return self.getarchiveclass(fileext, filepurpose, os.path.isdir(fileoption)) is not None

    def getarchiveclass(self, fileext, filepurpose, isdir=False):
        """returns the archiveclass for the given fileext and filepurpose"""
        archiveclass = self.archiveformats.get(fileext, None)
        if archiveclass is not None:
            return archiveclass
        archiveclass = self.archiveformats.get((fileext, filepurpose), None)
        if archiveclass is not None:
            return archiveclass
        if not isdir:
            archiveclass = self.archiveformats.get(None, None)
            if archiveclass is not None:
                return archiveclass
            archiveclass = self.archiveformats.get((None, filepurpose), None)
            if archiveclass is not None:
                return archiveclass
        return None

    def openarchive(self, archivefilename, filepurpose, **kwargs):
        """creates an archive object for the given file"""
        archiveext = self.splitext(archivefilename)[1]
        archiveclass = self.getarchiveclass(archiveext, filepurpose, os.path.isdir(archivefilename))
        archiveoptions = self.archiveoptions.copy()
        archiveoptions.update(kwargs)
        return archiveclass(archivefilename, **archiveoptions)

    def recurseinputfiles(self, options):
        """recurse through archive file / directories and return files to be converted"""
        if self.isarchive(options.input, 'input'):
            options.inputarchive = self.openarchive(options.input, 'input')
            return self.recursearchivefiles(options)
        else:
            return super(ArchiveConvertOptionParser, self).recurseinputfiles(options)

    def recursearchivefiles(self, options):
        """recurse through archive files and convert files"""
        inputfiles = []
        for inputpath in options.inputarchive:
            if self.isexcluded(options, inputpath):
                continue
            top, name = os.path.split(inputpath)
            if not self.isvalidinputname(options, name):
                continue
            inputfiles.append(inputpath)
        return inputfiles

    def openinputfile(self, options, fullinputpath):
        """opens the input file"""
        if self.isarchive(options.input, 'input'):
            return options.inputarchive.openinputfile(fullinputpath)
        else:
            return super(ArchiveConvertOptionParser, self).openinputfile(options, fullinputpath)

    def getfullinputpath(self, options, inputpath):
        """gets the absolute path to an input file"""
        if self.isarchive(options.input, 'input'):
            return inputpath
        else:
            return os.path.join(options.input, inputpath)

    def opentemplatefile(self, options, fulltemplatepath):
        """opens the template file (if required)"""
        if fulltemplatepath is not None:
            if options.recursivetemplate and self.isarchive(options.template, 'template'):
                # TODO: deal with different names in input/template archives
                if fulltemplatepath in options.templatearchive:
                    return options.templatearchive.openinputfile(fulltemplatepath)
                else:
                    self.warning("missing template file %s" % fulltemplatepath)
        return super(ArchiveConvertOptionParser, self).opentemplatefile(options, fulltemplatepath)

    def getfulltemplatepath(self, options, templatepath):
        """gets the absolute path to a template file"""
        if templatepath is not None and self.usetemplates and options.template:
            if self.isarchive(options.template, 'template'):
                return templatepath
            elif not options.recursivetemplate:
                return templatepath
            else:
                return os.path.join(options.template, templatepath)
        else:
            return None

    def templateexists(self, options, templatepath):
        """returns whether the given template exists..."""
        if templatepath is not None:
            if self.isarchive(options.template, 'template'):
                # TODO: deal with different names in input/template archives
                return templatepath in options.templatearchive
        return super(ArchiveConvertOptionParser, self).templateexists(options, templatepath)

    def getfulloutputpath(self, options, outputpath):
        """gets the absolute path to an output file"""
        if self.isarchive(options.output, 'output'):
            return outputpath
        elif options.recursiveoutput and options.output:
            return os.path.join(options.output, outputpath)
        else:
            return outputpath

    def checkoutputsubdir(self, options, subdir):
        """checks to see if subdir under options.output needs to be created, creates if neccessary"""
        if not self.isarchive(options.output, 'output'):
            super(ArchiveConvertOptionParser, self).checkoutputsubdir(options, subdir)

    def openoutputfile(self, options, fulloutputpath):
        """opens the output file"""
        if self.isarchive(options.output, 'output'):
            outputstream = options.outputarchive.openoutputfile(fulloutputpath)
            if outputstream is None:
                self.warning("Could not find where to put %s in output archive; writing to tmp" % fulloutputpath)
                return StringIO()
            return outputstream
        else:
            return super(ArchiveConvertOptionParser, self).openoutputfile(options, fulloutputpath)

    def inittemplatearchive(self, options):
        """opens the templatearchive if not already open"""
        if not self.usetemplates:
            return
        if options.template and self.isarchive(options.template, 'template') and not hasattr(options, "templatearchive"):
            options.templatearchive = self.openarchive(options.template, 'template')

    def initoutputarchive(self, options):
        """creates an outputarchive if required"""
        if options.output and self.isarchive(options.output, 'output'):
            options.outputarchive = self.openarchive(options.output, 'output', mode="w")

    def recursiveprocess(self, options):
        """recurse through directories and convert files"""
        if hasattr(options, "multifilestyle"):
            self.setarchiveoptions(multifilestyle=options.multifilestyle)
            for filetype in ("input", "output", "template"):
                allowoption = "allowrecursive%s" % filetype
                if options.multifilestyle == "onefile" and getattr(options, allowoption, True):
                    setattr(options, allowoption, False)
        self.inittemplatearchive(options)
        self.initoutputarchive(options)
        return super(ArchiveConvertOptionParser, self).recursiveprocess(options)

    def processfile(self, fileprocessor, options, fullinputpath, fulloutputpath, fulltemplatepath):
        """run an invidividual conversion"""
        if self.isarchive(options.output, 'output'):
            inputfile = self.openinputfile(options, fullinputpath)
            # TODO: handle writing back to same archive as input/template
            templatefile = self.opentemplatefile(options, fulltemplatepath)
            outputfile = self.openoutputfile(options, fulloutputpath)
            passthroughoptions = self.getpassthroughoptions(options)
            if fileprocessor(inputfile, outputfile, templatefile, **passthroughoptions):
                if not outputfile.isatty():
                    outputfile.close()
                return True
            else:
                if fulloutputpath and os.path.isfile(fulloutputpath):
                    outputfile.close()
                    os.unlink(fulloutputpath)
                return False
        else:
            return super(ArchiveConvertOptionParser, self).processfile(fileprocessor, options, fullinputpath, fulloutputpath, fulltemplatepath)

def main(argv=None):
    parser = ArchiveConvertOptionParser({}, description=__doc__)
    parser.run(argv)

