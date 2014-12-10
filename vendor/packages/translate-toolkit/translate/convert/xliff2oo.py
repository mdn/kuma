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
#

"""convert XLIFF localization files to an OpenOffice.org (SDF) localization file"""

import sys
import os
from translate.storage import oo
from translate.storage import factory
from translate.filters import pofilter
from translate.filters import checks
from translate.filters import autocorrect 
import time

class reoo:
    def __init__(self, templatefile, languages=None, timestamp=None, includefuzzy=False, long_keys=False, filteraction="exclude"):
        """construct a reoo converter for the specified languages (timestamp=0 means leave unchanged)"""
        # languages is a pair of language ids
        self.long_keys = long_keys
        self.readoo(templatefile)
        self.languages = languages
        self.filteraction = filteraction
        if timestamp is None:
            self.timestamp = time.strptime("2002-02-02 02:02:02", "%Y-%m-%d %H:%M:%S")
        else:
            self.timestamp = timestamp
        if self.timestamp:
            self.timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", self.timestamp)
        else:
            self.timestamp_str = None
        self.includefuzzy = includefuzzy

    def makeindex(self):
        """makes an index of the oo keys that are used in the source file"""
        self.index = {}
        for ookey, theoo in self.o.ookeys.iteritems():
            sourcekey = oo.makekey(ookey, self.long_keys)
            self.index[sourcekey] = theoo

    def readoo(self, of):
        """read in the oo from the file"""
        oosrc = of.read()
        self.o = oo.oofile()
        self.o.parse(oosrc)
        self.makeindex()

    def handleunit(self, unit):
        # TODO: make this work for multiple columns in oo...
        locations = unit.getlocations()
        # technically our formats should just have one location for each entry...
        # but we handle multiple ones just to be safe...
        for location in locations:
            subkeypos = location.rfind('.')
            subkey = location[subkeypos+1:]
            key = location[:subkeypos]
            # this is just to handle our old system of using %s/%s:%s instead of %s/%s#%s
            key = key.replace(':', '#')
            # this is to handle using / instead of \ in the sourcefile...
            key = key.replace('\\', '/')
            key = oo.normalizefilename(key)
            if self.index.has_key(key):
                # now we need to replace the definition of entity with msgstr
                theoo = self.index[key] # find the oo
                self.applytranslation(key, subkey, theoo, unit)
            else:
                print >> sys.stderr, "couldn't find key %s from po in %d keys" % (key, len(self.index))
                try:
                    sourceunitlines = str(unit)
                    if isinstance(sourceunitlines, unicode):
                        sourceunitlines = sourceunitlines.encode("utf-8")
                    print >> sys.stderr, sourceunitlines
                except:
                    print >> sys.stderr, "error outputting source unit %r" % (str(unit),)

    def applytranslation(self, key, subkey, theoo, unit):
        """applies the translation from the source unit to the oo unit"""
        if not self.includefuzzy and unit.isfuzzy():
            return
        makecopy = False
        if self.languages is None:
            part1 = theoo.lines[0]
            if len(theoo.lines) > 1:
                part2 = theoo.lines[1]
            else:
                makecopy = True
        else:
            part1 = theoo.languages[self.languages[0]]
            if self.languages[1] in theoo.languages:
                part2 = theoo.languages[self.languages[1]]
            else:
                makecopy = True
        if makecopy:
            part2 = oo.ooline(part1.getparts())
        unquotedid = unit.source
        unquotedstr = unit.target
        # If there is no translation, we don't want to add a line
        if len(unquotedstr.strip()) == 0:
            return
        if isinstance(unquotedstr, unicode):
            unquotedstr = unquotedstr.encode("UTF-8")
        # finally set the new definition in the oo, but not if its empty
        if len(unquotedstr) > 0:
            subkey = subkey.strip()
            setattr(part2, subkey, unquotedstr)
        # set the modified time
        if self.timestamp_str:
            part2.timestamp = self.timestamp_str
        if self.languages:
            part2.languageid = self.languages[1]
        if makecopy:
            theoo.addline(part2)

    def convertstore(self, sourcestore):
        self.p = sourcestore
        # translate the strings
        for unit in self.p.units:
            # there may be more than one element due to msguniq merge
            if filter.validelement(unit, self.p.filename, self.filteraction):
                self.handleunit(unit)
        # return the modified oo file object
        return self.o

def getmtime(filename):
    import stat
    return time.localtime(os.stat(filename)[stat.ST_MTIME])

class oocheckfilter(pofilter.pocheckfilter):
    def validelement(self, unit, filename, filteraction):
        """Returns whether or not to use unit in conversion. (filename is just for error reporting)"""
        if filteraction == "none": return True
        filterresult = self.filterunit(unit)
        if filterresult:
            if filterresult != autocorrect:
                for filtername, filtermessage in filterresult.iteritems():
                    location = unit.getlocations()[0]
                    if filtername in self.options.error:
                        print >> sys.stderr, "Error at %s::%s: %s" % (filename, location, filtermessage)
                        return not filteraction in ["exclude-all", "exclude-serious"]
                    if filtername in self.options.warning or self.options.alwayswarn:
                        print >> sys.stderr, "Warning at %s::%s: %s" % (filename, location, filtermessage)
                        return not filteraction in ["exclude-all"]
        return True

class oofilteroptions:
    error = ['variables', 'xmltags', 'escapes']
    warning = ['blank']
    #To only issue warnings for tests listed in warning, change the following to False:
    alwayswarn = True
    limitfilters = error + warning
    #To use all available tests, uncomment the following:
    #limitfilters = []
    #To exclude certain tests, list them in here:
    excludefilters = {}
    includefuzzy = False
    includereview = False
    autocorrect = False

options = oofilteroptions()
filter = oocheckfilter(options, [checks.OpenOfficeChecker, checks.StandardUnitChecker], checks.openofficeconfig)

def convertoo(inputfile, outputfile, templatefile, sourcelanguage=None, targetlanguage=None, timestamp=None, includefuzzy=False, multifilestyle="single", filteraction=None):
    inputstore = factory.getobject(inputfile)
    inputstore.filename = getattr(inputfile, 'name', '')
    if not targetlanguage:
        raise ValueError("You must specify the target language")
    if not sourcelanguage:
        if targetlanguage.isdigit():
            sourcelanguage = "01"
        else:
            sourcelanguage = "en-US"
    languages = (sourcelanguage, targetlanguage)
    if templatefile is None:
        raise ValueError("must have template file for oo files")
    else:
        convertor = reoo(templatefile, languages=languages, timestamp=timestamp, includefuzzy=includefuzzy, long_keys=multifilestyle != "single", filteraction=filteraction)
    outputstore = convertor.convertstore(inputstore)
    # TODO: check if we need to manually delete missing items
    outputfile.write(str(outputstore))
    return True

def main(argv=None):
    from translate.convert import convert
    formats = {("po", "oo"):("oo", convertoo), ("xlf", "oo"):("oo", convertoo), ("xlf", "sdf"):("sdf", convertoo)}
    # always treat the input as an archive unless it is a directory
    archiveformats = {(None, "output"): oo.oomultifile, (None, "template"): oo.oomultifile}
    parser = convert.ArchiveConvertOptionParser(formats, usetemplates=True, description=__doc__, archiveformats=archiveformats)
    parser.add_option("-l", "--language", dest="targetlanguage", default=None, 
            help="set target language code (e.g. af-ZA) [required]", metavar="LANG")
    parser.add_option("", "--source-language", dest="sourcelanguage", default=None, 
            help="set source language code (default en-US)", metavar="LANG")
    parser.add_option("-T", "--keeptimestamp", dest="timestamp", default=None, action="store_const", const=0,
            help="don't change the timestamps of the strings")
    parser.add_option("", "--nonrecursiveoutput", dest="allowrecursiveoutput", default=True, action="store_false", help="don't treat the output oo as a recursive store")
    parser.add_option("", "--nonrecursivetemplate", dest="allowrecursivetemplate", default=True, action="store_false", help="don't treat the template oo as a recursive store")
    parser.add_option("", "--filteraction", dest="filteraction", default="none", metavar="ACTION",
            help="action on pofilter failure: none (default), warn, exclude-serious, exclude-all")
    parser.add_fuzzy_option()
    parser.add_multifile_option()
    parser.passthrough.append("sourcelanguage")
    parser.passthrough.append("targetlanguage")
    parser.passthrough.append("timestamp")
    parser.passthrough.append("filteraction")
    parser.run(argv)

if __name__ == '__main__':
    main()
