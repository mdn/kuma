#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2014 Zuza Software Foundation
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

"""Convert Java/Mozilla .properties files to Gettext PO localization files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/prop2po.html
for examples and usage instructions.
"""

import logging

from translate.convert.accesskey import UnitMixer
from translate.storage import po, properties


logger = logging.getLogger(__name__)


class prop2po:
    """convert a .properties file to a .po file for handling the
    translation."""

    def __init__(self, personality="java", blankmsgstr=False,
                 duplicatestyle="msgctxt"):
        self.personality = personality
        self.blankmsgstr = blankmsgstr
        self.duplicatestyle = duplicatestyle
        self.mixedkeys = {}
        self.mixer = UnitMixer(properties.labelsuffixes,
                               properties.accesskeysuffixes)

    def convertstore(self, thepropfile):
        """converts a .properties file to a .po file..."""
        thetargetfile = po.pofile()
        if self.personality in ("mozilla", "skype"):
            targetheader = thetargetfile.init_headers(
                    x_accelerator_marker="&",
                    x_merge_on="location",
            )
        else:
            targetheader = thetargetfile.header()
        targetheader.addnote("extracted from %s" % thepropfile.filename,
                             "developer")

        thepropfile.makeindex()
        self.mixedkeys = self.mixer.match_entities(thepropfile.id_index)
        # we try and merge the header po with any comments at the start of the
        # properties file
        appendedheader = False
        waitingcomments = []
        for propunit in thepropfile.units:
            pounit = self.convertpropunit(thepropfile, propunit, "developer")
            if pounit is None:
                waitingcomments.extend(propunit.comments)
            # FIXME the storage class should not be creating blank units
            if pounit is "discard":
                continue
            if not appendedheader:
                if propunit.isblank():
                    targetheader.addnote("\n".join(waitingcomments).rstrip(),
                                         "developer", position="prepend")
                    waitingcomments = []
                    pounit = None
                appendedheader = True
            if pounit is not None:
                pounit.addnote("\n".join(waitingcomments).rstrip(),
                               "developer", position="prepend")
                waitingcomments = []
                thetargetfile.addunit(pounit)
        if self.personality == "gaia":
            thetargetfile = self.fold_gaia_plurals(thetargetfile)
        thetargetfile.removeduplicates(self.duplicatestyle)
        return thetargetfile

    def mergestore(self, origpropfile, translatedpropfile):
        """converts two .properties files to a .po file..."""
        thetargetfile = po.pofile()
        if self.personality in ("mozilla", "skype"):
            targetheader = thetargetfile.init_headers(
                    x_accelerator_marker="&",
                    x_merge_on="location",
            )
        else:
            targetheader = thetargetfile.header()
        targetheader.addnote("extracted from %s, %s" % (origpropfile.filename, translatedpropfile.filename),
                             "developer")
        origpropfile.makeindex()
        #TODO: self.mixedkeys is overwritten below, so this is useless:
        self.mixedkeys = self.mixer.match_entities(origpropfile.id_index)
        translatedpropfile.makeindex()
        self.mixedkeys = self.mixer.match_entities(translatedpropfile.id_index)
        # we try and merge the header po with any comments at the start of
        # the properties file
        appendedheader = False
        waitingcomments = []
        # loop through the original file, looking at units one by one
        for origprop in origpropfile.units:
            origpo = self.convertpropunit(origpropfile, origprop, "developer")
            if origpo is None:
                waitingcomments.extend(origprop.comments)
            # FIXME the storage class should not be creating blank units
            if origpo is "discard":
                continue
            # handle the header case specially...
            if not appendedheader:
                if origprop.isblank():
                    targetheader.addnote(u"".join(waitingcomments).rstrip(),
                                         "developer", position="prepend")
                    waitingcomments = []
                    origpo = None
                appendedheader = True
            # try and find a translation of the same name...
            if origprop.name in translatedpropfile.locationindex:
                translatedprop = translatedpropfile.locationindex[origprop.name]
                # Need to check that this comment is not a copy of the
                # developer comments
                translatedpo = self.convertpropunit(translatedpropfile,
                                                    translatedprop,
                                                    "translator")
                if translatedpo is "discard":
                    continue
            else:
                translatedpo = None
            # if we have a valid po unit, get the translation and add it...
            if origpo is not None:
                if translatedpo is not None and not self.blankmsgstr:
                    origpo.target = translatedpo.source
                origpo.addnote(u"".join(waitingcomments).rstrip(),
                               "developer", position="prepend")
                waitingcomments = []
                thetargetfile.addunit(origpo)
            elif translatedpo is not None:
                logger.error("didn't convert original property definition '%s'",
                             origprop.name)
        if self.personality == "gaia":
            thetargetfile = self.fold_gaia_plurals(thetargetfile)
        thetargetfile.removeduplicates(self.duplicatestyle)
        return thetargetfile

    def fold_gaia_plurals(self, postore):
        """Fold the multiple plural units of a gaia file into a gettext plural."""

        def _append_plural_unit(store, plurals, plural):
            units = plurals[plural]
            sources = [u.source for u in units]
            targets = [u.target for u in units]
            # TODO: only consider the right ones for sources and targets
            plural_unit = store.addsourceunit(sources)
            plural_unit.target = targets
            plural_unit.addlocation(plural)
            del plurals[plural]

        new_store = type(postore)()
        plurals = {}
        current_plural = u""
        for unit in postore.units:
            if not unit.istranslatable():
                #TODO: reconsider: we could lose header comments here
                continue
            if u"plural(n)" in unit.source:
                if current_plural:
                    # End of a set of plural units
                    _append_plural_unit(new_store, plurals, current_plural)
                    current_plural = u""
                # start of a set of plural units
                location = unit.getlocations()[0]
                current_plural = location
                plurals[location] = []
                # We ignore the first one, since it doesn't contain translatable
                # text, only a marker.
            else:
                location = unit.getlocations()[0]
                if current_plural and location.startswith(current_plural):
                    plurals[current_plural].append(unit)
                    if not '[zero]' in location:
                        # We want to keep [zero] cases separately translatable
                        continue
                elif current_plural:
                    # End of a set of plural units
                    _append_plural_unit(new_store, plurals, current_plural)
                    current_plural = u""

                new_store.addunit(unit)

        if current_plural:
            # The file ended with a set of plural units
            _append_plural_unit(new_store, plurals, current_plural)
            current_plural = u""

        # if everything went well, there should be nothing left in plurals
        if len(plurals) != 0:
            logger.warning("Not all plural units converted correctly:" +
                           "\n".join(plurals.keys()))
        return new_store

    def convertunit(self, propunit, commenttype):
        """Converts a .properties unit to a .po unit. Returns None if empty
        or not for translation."""
        if propunit is None:
            return None
        # escape unicode
        pounit = po.pounit(encoding="UTF-8")
        if hasattr(propunit, "comments"):
            for comment in propunit.comments:
                if "DONT_TRANSLATE" in comment:
                    return "discard"
            pounit.addnote(u"".join(propunit.getnotes()).rstrip(), commenttype)
        # TODO: handle multiline msgid
        if propunit.isblank():
            return None
        pounit.addlocation(propunit.name)
        pounit.source = propunit.source
        pounit.target = u""
        return pounit

    def convertmixedunit(self, labelprop, accesskeyprop, commenttype):
        label_unit = self.convertunit(labelprop, commenttype)
        accesskey_unit = self.convertunit(accesskeyprop, commenttype)
        if label_unit is None:
            return accesskey_unit
        if accesskey_unit is None:
            return label_unit
        target_unit = po.pounit(encoding="UTF-8")
        return self.mixer.mix_units(label_unit, accesskey_unit, target_unit)

    def convertpropunit(self, store, unit, commenttype, mixbucket="dtd"):
        """Converts a unit from store to a po unit, keeping track of mixed
        names along the way.

        ``mixbucket`` can be specified to indicate if the given unit is part of
        the template or the translated file.
        """
        if self.personality != "mozilla":
            # XXX should we enable unit mixing for other personalities?
            return self.convertunit(unit, commenttype)

        # keep track of whether accesskey and label were combined
        key = unit.getid()
        if key not in self.mixedkeys:
            return self.convertunit(unit, commenttype)

        # use special convertmixed unit which produces one pounit with
        # both combined for the label and None for the accesskey
        alreadymixed = self.mixedkeys[key].get(mixbucket, None)
        if alreadymixed:
            # we are successfully throwing this away...
            return None
        elif alreadymixed is False:
            # The mix failed before
            return self.convertunit(unit, commenttype)

        #assert alreadymixed is None
        labelkey, accesskeykey = self.mixer.find_mixed_pair(self.mixedkeys, store, unit)
        labelprop = store.id_index.get(labelkey, None)
        accesskeyprop = store.id_index.get(accesskeykey, None)
        po_unit = self.convertmixedunit(labelprop, accesskeyprop, commenttype)
        if po_unit is not None:
            if accesskeykey is not None:
                self.mixedkeys[accesskeykey][mixbucket] = True
            if labelkey is not None:
                self.mixedkeys[labelkey][mixbucket] = True
            return po_unit
        else:
            # otherwise the mix failed. add each one separately and
            # remember they weren't mixed
            if accesskeykey is not None:
                self.mixedkeys[accesskeykey][mixbucket] = False
            if labelkey is not None:
                self.mixedkeys[labelkey][mixbucket] = False

        return self.convertunit(unit, commenttype)


def convertstrings(inputfile, outputfile, templatefile, personality="strings",
                   pot=False, duplicatestyle="msgctxt", encoding=None):
    """.strings specific convertor function"""
    return convertprop(inputfile, outputfile, templatefile,
                       personality="strings", pot=pot,
                       duplicatestyle=duplicatestyle, encoding=encoding)


def convertmozillaprop(inputfile, outputfile, templatefile, pot=False,
                       duplicatestyle="msgctxt"):
    """Mozilla specific convertor function"""
    return convertprop(inputfile, outputfile, templatefile,
                       personality="mozilla", pot=pot,
                       duplicatestyle=duplicatestyle)


def convertprop(inputfile, outputfile, templatefile, personality="java",
                pot=False, duplicatestyle="msgctxt", encoding=None):
    """reads in inputfile using properties, converts using prop2po, writes
    to outputfile"""
    inputstore = properties.propfile(inputfile, personality, encoding)
    convertor = prop2po(personality=personality, blankmsgstr=pot,
                        duplicatestyle=duplicatestyle)
    if templatefile is None:
        outputstore = convertor.convertstore(inputstore)
    else:
        templatestore = properties.propfile(templatefile, personality, encoding)
        outputstore = convertor.mergestore(templatestore, inputstore)
    if outputstore.isempty():
        return 0
    outputfile.write(str(outputstore))
    return 1


formats = {
    "properties": ("po", convertprop),
    ("properties", "properties"): ("po", convertprop),
    "lang": ("po", convertprop),
    ("lang", "lang"): ("po", convertprop),
    "strings": ("po", convertstrings),
    ("strings", "strings"): ("po", convertstrings),
}


def main(argv=None):
    from translate.convert import convert
    parser = convert.ConvertOptionParser(formats, usetemplates=True,
                                         usepots=True,
                                         description=__doc__)
    parser.add_option("", "--personality", dest="personality",
            default=properties.default_dialect,
            type="choice",
            choices=properties.dialects.keys(),
            help="override the input file format: %s (for .properties files, default: %s)" %
                 (", ".join(properties.dialects.iterkeys()),
                  properties.default_dialect),
            metavar="TYPE")
    parser.add_option("", "--encoding", dest="encoding", default=None,
            help="override the encoding set by the personality",
            metavar="ENCODING")
    parser.add_duplicates_option()
    parser.passthrough.append("pot")
    parser.passthrough.append("personality")
    parser.passthrough.append("encoding")
    parser.run(argv)


if __name__ == '__main__':
    main()
