#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2006 Zuza Software Foundation
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

"""Convert a Mozilla .dtd UTF-8 localization format to a
Gettext PO localization file.

Uses the po and dtd modules, and the
dtd2po convertor class which is in this module
You can convert back to .dtd using po2dtd.py.
"""

from translate.convert.accesskey import UnitMixer
from translate.misc import quote
from translate.storage import dtd, po


def is_css_entity(entity):
    """Says if the given entity is likely to contain CSS that should not be
    translated."""
    if '.' in entity:
        prefix, suffix = entity.rsplit('.', 1)
        if (suffix in ["height", "width", "unixWidth", "macWidth", "size"] or
            suffix.startswith("style")):
            return True
    return False


class dtd2po:

    def __init__(self, blankmsgstr=False, duplicatestyle="msgctxt"):
        self.currentgroup = None
        self.blankmsgstr = blankmsgstr
        self.duplicatestyle = duplicatestyle
        self.mixedentities = {}
        self.mixer = UnitMixer(dtd.labelsuffixes, dtd.accesskeysuffixes)

    def convertcomments(self, dtd_unit, po_unit):
        entity = dtd_unit.getid()
        if len(entity) > 0:
            po_unit.addlocation(entity)
        for commenttype, comment in dtd_unit.comments:
            # handle groups
            if (commenttype == "locgroupstart"):
                groupcomment = comment.replace('BEGIN', 'GROUP')
                self.currentgroup = groupcomment
            elif (commenttype == "locgroupend"):
                groupcomment = comment.replace('END', 'GROUP')
                self.currentgroup = None
            # handle automatic comment
            if commenttype == "automaticcomment":
                po_unit.addnote(comment, origin="developer")
            # handle normal comments
            else:
                po_unit.addnote(quote.stripcomment(comment), origin="developer")
        # handle group stuff
        if self.currentgroup is not None:
            po_unit.addnote(quote.stripcomment(self.currentgroup),
                          origin="translator")
        if is_css_entity(entity):
            po_unit.addnote("Do not translate this.  Only change the numeric values if you need this dialogue box to appear bigger",
                          origin="developer")

    def convertstrings(self, dtd_unit, po_unit):
        # extract the string, get rid of quoting
        unquoted = dtd_unit.source.replace("\r", "")
        # escape backslashes... but not if they're for a newline
        # unquoted = unquoted.replace("\\", "\\\\").replace("\\\\n", "\\n")
        # now split the string into lines and quote them
        lines = unquoted.split('\n')
        while lines and not lines[0].strip():
            del lines[0]
        while lines and not lines[-1].strip():
            del lines[-1]
        # quotes have been escaped already by escapeforpo, so just add the
        # start and end quotes
        if len(lines) > 1:
            po_unit.source = "\n".join([lines[0].rstrip() + ' '] +
                    [line.strip() + ' ' for line in lines[1:-1]] +
                    [lines[-1].lstrip()])
        elif lines:
            po_unit.source = lines[0]
        else:
            po_unit.source = ""
        po_unit.target = ""

    def convertunit(self, dtd_unit):
        """Converts a simple (non-mixed) dtd unit into a po unit.

        Returns None if empty or not for translation.
        """
        if dtd_unit is None:
            return None
        po_unit = po.pounit(encoding="UTF-8")
        # remove unwanted stuff
        for commentnum in range(len(dtd_unit.comments)):
            commenttype, locnote = dtd_unit.comments[commentnum]
            # if this is a localization note
            if commenttype == 'locnote':
                # parse the locnote into the entity and the actual note
                typeend = quote.findend(locnote, 'LOCALIZATION NOTE')
                # parse the id
                idstart = locnote.find('(', typeend)
                if idstart == -1:
                    continue
                idend = locnote.find(')', (idstart + 1))
                entity = locnote[idstart+1:idend].strip()
                # parse the actual note
                actualnotestart = locnote.find(':', (idend + 1))
                actualnoteend = locnote.find('-->', idend)
                actualnote = locnote[actualnotestart+1:actualnoteend].strip()
                # if it's for this entity, process it
                if dtd_unit.getid() == entity:
                    # if it says don't translate (and nothing more),
                    if actualnote.startswith("DONT_TRANSLATE"):
                        # take out the entity,definition and the
                        # DONT_TRANSLATE comment
                        dtd_unit.setid("")
                        dtd_unit.source = ""
                        del dtd_unit.comments[commentnum]
                        # finished this for loop
                        break
                    else:
                        # convert it into an automatic comment, to be
                        # processed by convertcomments
                        dtd_unit.comments[commentnum] = ("automaticcomment",
                                                       actualnote)
        # do a standard translation
        self.convertcomments(dtd_unit, po_unit)
        self.convertstrings(dtd_unit, po_unit)
        if po_unit.isblank() and not po_unit.getlocations():
            return None
        else:
            return po_unit

    def convertmixedunit(self, labeldtd, accesskeydtd):
        label_unit = self.convertunit(labeldtd)
        accesskey_unit = self.convertunit(accesskeydtd)
        if label_unit is None:
            return accesskey_unit
        if accesskey_unit is None:
            return label_unit
        target_unit = po.pounit(encoding="UTF-8")
        return self.mixer.mix_units(label_unit, accesskey_unit, target_unit)

    def convertdtdunit(self, store, unit, mixbucket="dtd"):
        """Converts a unit from store to a po unit, keeping track of mixed
        entities along the way.

        ``mixbucket`` can be specified to indicate if the given unit is part of
        the template or the translated file.
        """
        # keep track of whether accesskey and label were combined
        entity = unit.getid()
        if entity not in self.mixedentities:
            return self.convertunit(unit)

        # use special convertmixed unit which produces one pounit with
        # both combined for the label and None for the accesskey
        alreadymixed = self.mixedentities[entity].get(mixbucket, None)
        if alreadymixed:
            # we are successfully throwing this away...
            return None
        elif alreadymixed is False:
            # The mix failed before
            return self.convertunit(unit)

        #assert alreadymixed is None
        labelentity, accesskeyentity = self.mixer.find_mixed_pair(self.mixedentities, store, unit)
        labeldtd = store.id_index.get(labelentity, None)
        accesskeydtd = store.id_index.get(accesskeyentity, None)
        po_unit = self.convertmixedunit(labeldtd, accesskeydtd)
        if po_unit is not None:
            if accesskeyentity is not None:
                self.mixedentities[accesskeyentity][mixbucket] = True
            if labelentity is not None:
                self.mixedentities[labelentity][mixbucket] = True
            return po_unit
        else:
            # otherwise the mix failed. add each one separately and
            # remember they weren't mixed
            if accesskeyentity is not None:
                self.mixedentities[accesskeyentity][mixbucket] = False
            if labelentity is not None:
                self.mixedentities[labelentity][mixbucket] = False

        return self.convertunit(unit)

    def convertstore(self, dtd_store):
        target_store = po.pofile()
        targetheader = target_store.init_headers(
                x_accelerator_marker="&",
                x_merge_on="location",
        )
        targetheader.addnote("extracted from %s" % dtd_store.filename,
                             "developer")

        dtd_store.makeindex()
        self.mixedentities = self.mixer.match_entities(dtd_store.id_index)
        # go through the dtd and convert each unit
        for dtd_unit in dtd_store.units:
            if not dtd_unit.istranslatable():
                continue
            po_unit = self.convertdtdunit(dtd_store, dtd_unit)
            if po_unit is not None:
                target_store.addunit(po_unit)
        target_store.removeduplicates(self.duplicatestyle)
        return target_store

    def mergestore(self, origdtdfile, translateddtdfile):
        target_store = po.pofile()
        targetheader = target_store.init_headers(
                x_accelerator_marker="&",
                x_merge_on="location",
        )
        targetheader.addnote("extracted from %s, %s" %
                             (origdtdfile.filename,
                              translateddtdfile.filename),
                             "developer")

        origdtdfile.makeindex()
        #TODO: self.mixedentities is overwritten below, so this is useless:
        self.mixedentities = self.mixer.match_entities(origdtdfile.id_index)
        translateddtdfile.makeindex()
        self.mixedentities = self.mixer.match_entities(translateddtdfile.id_index)
        # go through the dtd files and convert each unit
        for origdtd in origdtdfile.units:
            if not origdtd.istranslatable():
                continue
            origpo = self.convertdtdunit(origdtdfile, origdtd,
                                         mixbucket="orig")
            orig_entity = origdtd.getid()
            if orig_entity in self.mixedentities:
                mixedentitydict = self.mixedentities[orig_entity]
                if "orig" not in mixedentitydict:
                    # this means that the entity is mixed in the translation,
                    # but not the original - treat as unmixed
                    mixbucket = "orig"
                    del self.mixedentities[orig_entity]
                elif mixedentitydict["orig"]:
                    # the original entity is already mixed successfully
                    mixbucket = "translate"
                else:
                    # ??
                    mixbucket = "orig"
            else:
                mixbucket = "translate"
            if origpo is None:
                # this means its a mixed entity (with accesskey) that's
                # already been dealt with)
                continue
            if orig_entity in translateddtdfile.id_index:
                translateddtd = translateddtdfile.id_index[orig_entity]
                translatedpo = self.convertdtdunit(translateddtdfile,
                                                   translateddtd,
                                                   mixbucket=mixbucket)
            else:
                translatedpo = None
            if origpo is not None:
                if translatedpo is not None and not self.blankmsgstr:
                    origpo.target = translatedpo.source
                target_store.addunit(origpo)
        target_store.removeduplicates(self.duplicatestyle)
        return target_store


def convertdtd(inputfile, outputfile, templatefile, pot=False,
               duplicatestyle="msgctxt"):
    """reads in inputfile and templatefile using dtd, converts using dtd2po,
    writes to outputfile"""
    android_dtd = False
    if hasattr(inputfile, "name"):
        # Check if it is an Android DTD file.
        if ("embedding/android" in inputfile.name or
            "mobile/android/base" in inputfile.name):
            android_dtd = True
    inputstore = dtd.dtdfile(inputfile, android=android_dtd)
    convertor = dtd2po(blankmsgstr=pot, duplicatestyle=duplicatestyle)
    if templatefile is None:
        outputstore = convertor.convertstore(inputstore)
    else:
        templatestore = dtd.dtdfile(templatefile, android=android_dtd)
        outputstore = convertor.mergestore(templatestore, inputstore)
    if outputstore.isempty():
        return 0
    outputfile.write(str(outputstore))
    return 1


def main(argv=None):
    from translate.convert import convert
    formats = {
        "dtd": ("po", convertdtd),
        ("dtd", "dtd"): ("po", convertdtd),
    }
    parser = convert.ConvertOptionParser(formats, usetemplates=True,
                                         usepots=True, description=__doc__)
    parser.add_duplicates_option()
    parser.passthrough.append("pot")
    parser.run(argv)


if __name__ == '__main__':
    main()
