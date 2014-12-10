#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2002-2009 Zuza Software Foundation
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

"""script that converts a .po file to a UTF-8 encoded .dtd file as used by mozilla
either done using a template or just using the .po file"""

from translate.storage import dtd
from translate.storage import po
from translate.misc import quote
from translate.convert import accesskey
import warnings

def getmixedentities(entities):
    """returns a list of mixed .label and .accesskey entities from a list of entities"""
    mixedentities = []    # those entities which have a .label and .accesskey combined
    # search for mixed entities...
    for entity in entities:
        for labelsuffix in dtd.labelsuffixes:
            if entity.endswith(labelsuffix):
                entitybase = entity[:entity.rfind(labelsuffix)]
                # see if there is a matching accesskey, making this a mixed entity
                for akeytype in dtd.accesskeysuffixes:
                    if entitybase + akeytype in entities:
                        # add both versions to the list of mixed entities
                        mixedentities += [entity, entitybase+akeytype]
    return mixedentities

def applytranslation(entity, dtdunit, inputunit, mixedentities):
    """applies the translation for entity in the po unit to the dtd unit"""
    # this converts the po-style string to a dtd-style string
    unquotedstr = inputunit.target
    # check there aren't missing entities...
    if len(unquotedstr.strip()) == 0:
        return
    # handle mixed entities
    for labelsuffix in dtd.labelsuffixes:
        if entity.endswith(labelsuffix):
            if entity in mixedentities:
                unquotedstr, akey = accesskey.extract(unquotedstr)
                break
    else:
        for akeytype in dtd.accesskeysuffixes:
            if entity.endswith(akeytype):
                if entity in mixedentities:
                    label, unquotedstr = accesskey.extract(unquotedstr)
                    if not unquotedstr:
                        warnings.warn("Could not find accesskey for %s" % entity)
                    else:
                        original = dtd.unquotefromdtd(dtdunit.definition)
                        # For the sake of diffs we keep the case of the
                        # accesskey the same if we know the translation didn't
                        # change. Casing matters in XUL.
                        if unquotedstr == dtdunit.source and original.lower() == unquotedstr.lower():
                            if original.isupper():
                                unquotedstr = unquotedstr.upper()
                            elif original.islower():
                                unquotedstr = unquotedstr.lower()
    if len(unquotedstr) > 0:
        dtdunit.definition = dtd.quotefordtd(dtd.removeinvalidamps(entity, unquotedstr))

class redtd:
    """this is a convertor class that creates a new dtd based on a template using translations in a po"""
    def __init__(self, dtdfile):
        self.dtdfile = dtdfile

    def convertstore(self, inputstore, includefuzzy=False):
        # translate the strings
        for inunit in inputstore.units:
            # there may be more than one entity due to msguniq merge
            if includefuzzy or not inunit.isfuzzy():
                self.handleinunit(inunit)
        return self.dtdfile

    def handleinunit(self, inunit):
        entities = inunit.getlocations()
        mixedentities = getmixedentities(entities)
        for entity in entities:
            if self.dtdfile.index.has_key(entity):
                # now we need to replace the definition of entity with msgstr
                dtdunit = self.dtdfile.index[entity] # find the dtd
                applytranslation(entity, dtdunit, inunit, mixedentities)

class po2dtd:
    """this is a convertor class that creates a new dtd file based on a po file without a template"""
    def convertcomments(self, inputunit, dtdunit):
        entities = inputunit.getlocations()
        if len(entities) > 1:
            # don't yet handle multiple entities
            dtdunit.comments.append(("conversionnote",'<!-- CONVERSION NOTE - multiple entities -->\n'))
            dtdunit.entity = entities[0]
        elif len(entities) == 1:
            dtdunit.entity = entities[0]
        else:
            # this produces a blank entity, which doesn't write anything out
            dtdunit.entity = ""

        if inputunit.isfuzzy():
            dtdunit.comments.append(("potype", "fuzzy\n"))
        for note in inputunit.getnotes("translator").split("\n"):
            if not note:
                continue
            note = quote.unstripcomment(note)
            if (note.find('LOCALIZATION NOTE') == -1) or (note.find('GROUP') == -1):
                dtdunit.comments.append(("comment", note))
        # msgidcomments are special - they're actually localization notes
        msgidcomment = inputunit._extract_msgidcomments()
        if msgidcomment:
            locnote = quote.unstripcomment("LOCALIZATION NOTE ("+dtdunit.entity+"): "+msgidcomment)
            dtdunit.comments.append(("locnote", locnote))


    def convertstrings(self, inputunit, dtdunit):
        if inputunit.istranslated():
            unquoted = inputunit.target
        else:
            unquoted = inputunit.source
        dtdunit.definition = dtd.quotefordtd(dtd.removeinvalidamps(dtdunit.entity, unquoted))

    def convertunit(self, inputunit):
        dtdunit = dtd.dtdunit()
        self.convertcomments(inputunit, dtdunit)
        self.convertstrings(inputunit, dtdunit)
        return dtdunit

    def convertstore(self, inputstore, includefuzzy=False):
        outputstore = dtd.dtdfile()
        self.currentgroups = []
        for inputunit in inputstore.units:
            if includefuzzy or not inputunit.isfuzzy():
                dtdunit = self.convertunit(inputunit)
                if dtdunit is not None:
                    outputstore.addunit(dtdunit)
        return outputstore

def convertdtd(inputfile, outputfile, templatefile, includefuzzy=False):
    inputstore = po.pofile(inputfile)
    if templatefile is None:
        convertor = po2dtd()
    else:
        templatestore = dtd.dtdfile(templatefile)
        convertor = redtd(templatestore)
    outputstore = convertor.convertstore(inputstore, includefuzzy)
    outputfile.write(str(outputstore))
    return 1

def main(argv=None):
    # handle command line options
    from translate.convert import convert
    formats = {"po": ("dtd", convertdtd), ("po", "dtd"): ("dtd", convertdtd)}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, description=__doc__)
    parser.add_fuzzy_option()
    parser.run(argv)

if __name__ == '__main__':
    main()

