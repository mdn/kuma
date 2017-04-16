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
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""script to convert a mozilla .dtd UTF-8 localization format to a
gettext .po localization file using the po and dtd modules, and the
dtd2po convertor class which is in this module
You can convert back to .dtd using po2dtd.py"""

from translate.storage import po
from translate.storage import dtd
from translate.misc import quote
from translate.convert import accesskey as accesskeyfn

def is_css_entity(entity):
    """Says if the given entity is likely to contain CSS that should not be
    translated."""
    if '.' in entity:
        prefix, suffix = entity.rsplit('.', 1)
        if suffix in ["height", "width", "unixWidth", "macWidth", "size"] or suffix.startswith("style"):
            return True
    return False

class dtd2po:
    def __init__(self, blankmsgstr=False, duplicatestyle="msgctxt"):
        self.currentgroup = None
        self.blankmsgstr = blankmsgstr
        self.duplicatestyle = duplicatestyle

    def convertcomments(self, thedtd, thepo):
        entity = quote.rstripeol(thedtd.entity)
        if len(entity) > 0:
            thepo.addlocation(thedtd.entity)
        for commenttype, comment in thedtd.comments:
            # handle groups
            if (commenttype == "locgroupstart"):
                groupcomment = comment.replace('BEGIN','GROUP')
                self.currentgroup = groupcomment
            elif (commenttype == "locgroupend"):
                groupcomment = comment.replace('END','GROUP')
                self.currentgroup = None
            # handle automatic comment
            if commenttype == "automaticcomment":
                thepo.addnote(comment, origin="developer")
            # handle normal comments
            else:
                thepo.addnote(quote.stripcomment(comment), origin="developer")
        # handle group stuff
        if self.currentgroup is not None:
            thepo.addnote(quote.stripcomment(self.currentgroup), origin="translator")
        if is_css_entity(entity):
            thepo.addnote("Do not translate this.  Only change the numeric values if you need this dialogue box to appear bigger", origin="developer")

    def convertstrings(self, thedtd, thepo):
        # extract the string, get rid of quoting
        unquoted = dtd.unquotefromdtd(thedtd.definition).replace("\r", "")
        # escape backslashes... but not if they're for a newline
        # unquoted = unquoted.replace("\\", "\\\\").replace("\\\\n", "\\n")
        # now split the string into lines and quote them
        lines = unquoted.split('\n')
        while lines and not lines[0].strip():
            del lines[0]
        while lines and not lines[-1].strip():
            del lines[-1]
        # quotes have been escaped already by escapeforpo, so just add the start and end quotes
        if len(lines) > 1:
            thepo.source = "\n".join([lines[0].rstrip() + ' '] + \
                    [line.strip() + ' ' for line in lines[1:-1]] + \
                    [lines[-1].lstrip()])
        elif lines:
            thepo.source = lines[0]
        else:
            thepo.source = ""
        thepo.target = ""

    def convertunit(self, thedtd):
        """converts a dtd unit to a po unit, returns None if empty or not for translation"""
        if thedtd is None:
            return None
        if getattr(thedtd, "entityparameter", None) == "SYSTEM":
            return None
        thepo = po.pounit(encoding="UTF-8")
        # remove unwanted stuff
        for commentnum in range(len(thedtd.comments)):
            commenttype, locnote = thedtd.comments[commentnum]
            # if this is a localization note
            if commenttype == 'locnote':
                # parse the locnote into the entity and the actual note
                typeend = quote.findend(locnote,'LOCALIZATION NOTE')
                # parse the id
                idstart = locnote.find('(', typeend)
                if idstart == -1: continue
                idend = locnote.find(')', idstart+1)
                entity = locnote[idstart+1:idend].strip()
                # parse the actual note
                actualnotestart = locnote.find(':', idend+1)
                actualnoteend = locnote.find('-->', idend)
                actualnote = locnote[actualnotestart+1:actualnoteend].strip()
                # if it's for this entity, process it
                if thedtd.entity == entity:
                    # if it says don't translate (and nothing more),
                    if actualnote.startswith("DONT_TRANSLATE"):
                        # take out the entity,definition and the DONT_TRANSLATE comment
                        thedtd.entity = ""
                        thedtd.definition = ""
                        del thedtd.comments[commentnum]
                        # finished this for loop
                        break
                    else:
                        # convert it into an automatic comment, to be processed by convertcomments
                        thedtd.comments[commentnum] = ("automaticcomment", actualnote)
        # do a standard translation
        self.convertcomments(thedtd, thepo)
        self.convertstrings(thedtd, thepo)
        if thepo.isblank() and not thepo.getlocations():
            return None
        else:
            return thepo

    def convertmixedunit(self, labeldtd, accesskeydtd):
        labelpo = self.convertunit(labeldtd)
        accesskeypo = self.convertunit(accesskeydtd)
        if labelpo is None:
            return accesskeypo
        if accesskeypo is None:
            return labelpo
        thepo = po.pounit(encoding="UTF-8")
        thepo.addlocations(labelpo.getlocations())
        thepo.addlocations(accesskeypo.getlocations())
        thepo.msgidcomment = thepo._extract_msgidcomments() + labelpo._extract_msgidcomments()
        thepo.msgidcomment = thepo._extract_msgidcomments() + accesskeypo._extract_msgidcomments()
        thepo.addnote(labelpo.getnotes("developer"), "developer")
        thepo.addnote(accesskeypo.getnotes("developer"), "developer")
        thepo.addnote(labelpo.getnotes("translator"), "translator")
        thepo.addnote(accesskeypo.getnotes("translator"), "translator")
        # redo the strings from original dtd...
        label = dtd.unquotefromdtd(labeldtd.definition).decode('UTF-8')
        accesskey = dtd.unquotefromdtd(accesskeydtd.definition).decode('UTF-8')
        label = accesskeyfn.combine(label, accesskey)
        if label is None:
            return None
        thepo.source = label
        thepo.target = ""
        return thepo

    def findmixedentities(self, thedtdfile):
        """creates self.mixedentities from the dtd file..."""
        self.mixedentities = {} # those entities which have a .label/.title and .accesskey combined
        for entity in thedtdfile.index.keys():
            for labelsuffix in dtd.labelsuffixes:
                if entity.endswith(labelsuffix):
                    entitybase = entity[:entity.rfind(labelsuffix)]
                    # see if there is a matching accesskey in this line, making this a
                    # mixed entity
                    for akeytype in dtd.accesskeysuffixes:
                        if thedtdfile.index.has_key(entitybase + akeytype):
                            # add both versions to the list of mixed entities
                            self.mixedentities[entity] = {}
                            self.mixedentities[entitybase+akeytype] = {}
                    # check if this could be a mixed entity (labelsuffix and ".accesskey")

    def convertdtdunit(self, thedtdfile, thedtd, mixbucket="dtd"):
        """converts a dtd unit from thedtdfile to a po unit, handling mixed entities along the way..."""
        # keep track of whether accesskey and label were combined
        if thedtd.entity in self.mixedentities:
            # use special convertmixed unit which produces one pounit with
            # both combined for the label and None for the accesskey
            alreadymixed = self.mixedentities[thedtd.entity].get(mixbucket, None)
            if alreadymixed:
                # we are successfully throwing this away...
                return None
            elif alreadymixed is None:
                # depending on what we come across first, work out the label and the accesskey
                labeldtd, accesskeydtd = None, None
                labelentity, accesskeyentity = None, None
                for labelsuffix in dtd.labelsuffixes:
                    if thedtd.entity.endswith(labelsuffix):
                        entitybase = thedtd.entity[:thedtd.entity.rfind(labelsuffix)]
                        for akeytype in dtd.accesskeysuffixes:
                            if thedtdfile.index.has_key(entitybase + akeytype):
                                labelentity, labeldtd = thedtd.entity, thedtd
                                accesskeyentity = labelentity[:labelentity.rfind(labelsuffix)]+akeytype
                                accesskeydtd = thedtdfile.index[accesskeyentity]
                                break
                else:
                    for akeytype in dtd.accesskeysuffixes:
                        if thedtd.entity.endswith(akeytype):
                            accesskeyentity, accesskeydtd = thedtd.entity, thedtd
                            for labelsuffix in dtd.labelsuffixes:
                                labelentity = accesskeyentity[:accesskeyentity.rfind(akeytype)]+labelsuffix
                                if thedtdfile.index.has_key(labelentity):
                                    labeldtd = thedtdfile.index[labelentity]
                                    break
                            else:
                                labelentity = None
                                accesskeyentity = None
                thepo = self.convertmixedunit(labeldtd, accesskeydtd)
                if thepo is not None:
                    if accesskeyentity is not None:
                        self.mixedentities[accesskeyentity][mixbucket] = True
                    if labelentity is not None:
                        self.mixedentities[labelentity][mixbucket] = True
                    return thepo
                else:
                    # otherwise the mix failed. add each one separately and remember they weren't mixed
                    if accesskeyentity is not None:
                        self.mixedentities[accesskeyentity][mixbucket] = False
                    if labelentity is not None:
                        self.mixedentities[labelentity][mixbucket] = False
        return self.convertunit(thedtd)

    def convertstore(self, thedtdfile):
        thetargetfile = po.pofile()
        targetheader = thetargetfile.init_headers(charset="UTF-8", encoding="8bit", x_accelerator_marker="&")
        targetheader.addnote("extracted from %s" % thedtdfile.filename, "developer")

        thedtdfile.makeindex()
        self.findmixedentities(thedtdfile)
        # go through the dtd and convert each unit
        for thedtd in thedtdfile.units:
            if thedtd.isnull():
                continue
            thepo = self.convertdtdunit(thedtdfile, thedtd)
            if thepo is not None:
                thetargetfile.addunit(thepo)
        thetargetfile.removeduplicates(self.duplicatestyle)
        return thetargetfile

    def mergestore(self, origdtdfile, translateddtdfile):
        thetargetfile = po.pofile()
        targetheader = thetargetfile.init_headers(charset="UTF-8", encoding="8bit")
        targetheader.addnote("extracted from %s, %s" % (origdtdfile.filename, translateddtdfile.filename), "developer")

        origdtdfile.makeindex()
        self.findmixedentities(origdtdfile)
        translateddtdfile.makeindex()
        self.findmixedentities(translateddtdfile)
        # go through the dtd files and convert each unit
        for origdtd in origdtdfile.units:
            if origdtd.isnull():
                continue
            origpo = self.convertdtdunit(origdtdfile, origdtd, mixbucket="orig")
            if origdtd.entity in self.mixedentities:
                mixedentitydict = self.mixedentities[origdtd.entity]
                if "orig" not in mixedentitydict:
                    # this means that the entity is mixed in the translation, but not the original - treat as unmixed
                    mixbucket = "orig"
                    del self.mixedentities[origdtd.entity]
                elif mixedentitydict["orig"]:
                    # the original entity is already mixed successfully
                    mixbucket = "translate"
                else:
                    # ??
                    mixbucket = "orig"
            else:
                mixbucket = "translate"
            if origpo is None:
                # this means its a mixed entity (with accesskey) that's already been dealt with)
                continue
            if origdtd.entity in translateddtdfile.index:
                translateddtd = translateddtdfile.index[origdtd.entity]
                translatedpo = self.convertdtdunit(translateddtdfile, translateddtd, mixbucket=mixbucket)
            else:
                translatedpo = None
            if origpo is not None:
                if translatedpo is not None and not self.blankmsgstr:
                    origpo.target = translatedpo.source
                thetargetfile.addunit(origpo)
        thetargetfile.removeduplicates(self.duplicatestyle)
        return thetargetfile

def convertdtd(inputfile, outputfile, templatefile, pot=False, duplicatestyle="msgctxt"):
    """reads in inputfile and templatefile using dtd, converts using dtd2po, writes to outputfile"""
    inputstore = dtd.dtdfile(inputfile)
    convertor = dtd2po(blankmsgstr=pot, duplicatestyle=duplicatestyle)
    if templatefile is None:
        outputstore = convertor.convertstore(inputstore)
    else:
        templatestore = dtd.dtdfile(templatefile)
        outputstore = convertor.mergestore(templatestore, inputstore)
    if outputstore.isempty():
        return 0
    outputfile.write(str(outputstore))
    return 1

def main(argv=None):
    from translate.convert import convert
    formats = {"dtd": ("po", convertdtd), ("dtd", "dtd"): ("po", convertdtd)}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, usepots=True, description=__doc__)
    parser.add_duplicates_option()
    parser.passthrough.append("pot")
    parser.run(argv)

if __name__ == '__main__':
    main()

