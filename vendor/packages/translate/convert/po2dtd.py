#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2009,2012 Zuza Software Foundation
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

"""Converts a Gettext PO file to a UTF-8 encoded Mozilla .dtd file.

.. note: Conversion is either done using a template plus PO file or just
   using the .po file.
"""

import warnings

from translate.convert import accesskey, convert
from translate.misc import quote
from translate.storage import dtd, po


def dtdwarning(message, category, filename, lineno, line=None):
    return "Warning: %s\n" % message
warnings.formatwarning = dtdwarning


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
                        # Use the source language accesskey
                        label, unquotedstr = accesskey.extract(inputunit.source)
                    else:
                        original = dtdunit.source
                        # For the sake of diffs we keep the case of the
                        # accesskey the same if we know the translation didn't
                        # change. Casing matters in XUL.
                        if unquotedstr == dtdunit.source and original.lower() == unquotedstr.lower():
                            if original.isupper():
                                unquotedstr = unquotedstr.upper()
                            elif original.islower():
                                unquotedstr = unquotedstr.lower()
    dtdunit.source = unquotedstr


class redtd:
    """this is a convertor class that creates a new dtd based on a template using translations in a po"""

    def __init__(self, dtdfile, android=False, remove_untranslated=False):
        self.dtdfile = dtdfile
        self.mixer = accesskey.UnitMixer(dtd.labelsuffixes, dtd.accesskeysuffixes)
        self.android = False
        self.remove_untranslated = remove_untranslated

    def convertstore(self, inputstore, includefuzzy=False):
        for inunit in inputstore.units:
            self.handleinunit(inunit, includefuzzy)
        return self.dtdfile

    def handleinunit(self, inunit, includefuzzy):
        entities = inunit.getlocations()
        mixedentities = self.mixer.match_entities(entities)
        for entity in entities:
            if entity in self.dtdfile.id_index:
                # now we need to replace the definition of entity with msgstr
                dtdunit = self.dtdfile.id_index[entity]  # find the dtd
                if inunit.istranslated() or not bool(inunit.source):
                    applytranslation(entity, dtdunit, inunit, mixedentities)
                elif self.remove_untranslated and not (includefuzzy and inunit.isfuzzy()):
                    dtdunit.entity = None
                else:
                    applytranslation(entity, dtdunit, inunit, mixedentities)


class po2dtd:
    """this is a convertor class that creates a new dtd file based on a po file without a template"""

    def __init__(self, android=False, remove_untranslated=False):
        self.android = android
        self.remove_untranslated = remove_untranslated

    def convertcomments(self, inputunit, dtdunit):
        entities = inputunit.getlocations()
        if len(entities) > 1:
            # don't yet handle multiple entities
            dtdunit.comments.append(("conversionnote", '<!-- CONVERSION NOTE - multiple entities -->\n'))
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
            locnote = quote.unstripcomment("LOCALIZATION NOTE (" + dtdunit.entity + "): " + msgidcomment)
            dtdunit.comments.append(("locnote", locnote))

    def convertstrings(self, inputunit, dtdunit):
        if inputunit.istranslated() or not bool(inputunit.source):
            unquoted = inputunit.target
        elif self.remove_untranslated:
            unquoted = None
        else:
            unquoted = inputunit.source
        dtdunit.source = dtd.removeinvalidamps(dtdunit.entity, unquoted)

    def convertunit(self, inputunit):
        dtdunit = dtd.dtdunit()
        self.convertcomments(inputunit, dtdunit)
        self.convertstrings(inputunit, dtdunit)
        return dtdunit

    def convertstore(self, inputstore, includefuzzy=False):
        outputstore = dtd.dtdfile(android=self.android)
        self.currentgroups = []
        for inputunit in inputstore.units:
            if ((includefuzzy or not inputunit.isfuzzy()) and
                (inputunit.istranslated() or not self.remove_untranslated)):
                dtdunit = self.convertunit(inputunit)
                if dtdunit is not None:
                    outputstore.addunit(dtdunit)
        return outputstore


def convertdtd(inputfile, outputfile, templatefile, includefuzzy=False,
               remove_untranslated=False, outputthreshold=None):
    inputstore = po.pofile(inputfile)

    if not convert.should_output_store(inputstore, outputthreshold):
        return False

    # Some of the DTD files used for Firefox Mobile are actually completely
    # different with different escaping and quoting rules. The best way to
    # identify them seems to be on their file path in the tree (based on code
    # in compare-locales).
    android_dtd = False
    header_comment = u""
    input_header = inputstore.header()
    if input_header:
        header_comment = input_header.getnotes("developer")
        if "embedding/android" in header_comment or "mobile/android/base" in header_comment:
            android_dtd = True

    if templatefile is None:
        convertor = po2dtd(android=android_dtd,
                           remove_untranslated=remove_untranslated)
    else:
        templatestore = dtd.dtdfile(templatefile, android=android_dtd)
        convertor = redtd(templatestore, android=android_dtd,
                          remove_untranslated=remove_untranslated)
    outputstore = convertor.convertstore(inputstore, includefuzzy)
    outputfile.write(str(outputstore))
    return 1


def main(argv=None):
    # handle command line options
    formats = {"po": ("dtd", convertdtd), ("po", "dtd"): ("dtd", convertdtd)}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, description=__doc__)
    parser.add_option("", "--removeuntranslated", dest="remove_untranslated",
            default=False, action="store_true",
            help="remove untranslated strings from output")
    parser.add_threshold_option()
    parser.add_fuzzy_option()
    parser.passthrough.append("remove_untranslated")
    parser.run(argv)


if __name__ == '__main__':
    main()
