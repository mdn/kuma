#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2005-2009 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""module for parsing TMX translation memeory files"""

from translate.storage import lisa
from lxml import etree

from translate import __version__

class tmxunit(lisa.LISAunit):
    """A single unit in the TMX file."""
    rootNode = "tu"
    languageNode = "tuv"
    textNode = "seg"

    def createlanguageNode(self, lang, text, purpose):
        """returns a langset xml Element setup with given parameters"""
        if isinstance(text, str):
            text = text.decode("utf-8")
        langset = etree.Element(self.languageNode)
        lisa.setXMLlang(langset, lang)
        seg = etree.SubElement(langset, self.textNode)
        # implied by the standard:
        # lisa.setXMLspace(seg, "preserve")
        seg.text = text
        return langset

    def getid(self):
        """Returns the identifier for this unit. The optional tuid property is
        used if available, otherwise we inherit .getid(). Note that the tuid
        property is only mandated to be unique from TMX 2.0."""
        id = self.xmlelement.get("tuid", "")
        return id or super(tmxunit, self).getid()

    def istranslatable(self):
        return bool(self.source)

    def addnote(self, text, origin=None, position="append"):
        """Add a note specifically in a "note" tag.

        The origin parameter is ignored"""
        if isinstance(text, str):
            text = text.decode("utf-8")
        note = etree.SubElement(self.xmlelement, self.namespaced("note"))
        note.text = text.strip()

    def getnotelist(self, origin=None):
        """Private method that returns the text from notes.

        The origin parameter is ignored.."""
        note_nodes = self.xmlelement.iterdescendants(self.namespaced("note"))
        note_list = [lisa.getText(note) for note in note_nodes]

        return note_list

    def getnotes(self, origin=None):
        return '\n'.join(self.getnotelist(origin=origin))

    def removenotes(self):
        """Remove all the translator notes."""
        notes = self.xmlelement.iterdescendants(self.namespaced("note"))
        for note in notes:
            self.xmlelement.remove(note)

    def adderror(self, errorname, errortext):
        """Adds an error message to this unit."""
        #TODO: consider factoring out: some duplication between XLIFF and TMX
        text = errorname + ': ' + errortext
        self.addnote(text, origin="pofilter")

    def geterrors(self):
        """Get all error messages."""
        #TODO: consider factoring out: some duplication between XLIFF and TMX
        notelist = self.getnotelist(origin="pofilter")
        errordict = {}
        for note in notelist:
            errorname, errortext = note.split(': ')
            errordict[errorname] = errortext
        return errordict

    def copy(self):
        """Make a copy of the translation unit.

        We don't want to make a deep copy - this could duplicate the whole XML
        tree. For now we just serialise and reparse the unit's XML."""
        #TODO: check performance
        new_unit = self.__class__(None, empty=True)
        new_unit.xmlelement = etree.fromstring(etree.tostring(self.xmlelement))
        return new_unit


class tmxfile(lisa.LISAfile):
    """Class representing a TMX file store."""
    UnitClass = tmxunit
    Name = _("TMX Translation Memory")
    Mimetypes  = ["application/x-tmx"]
    Extensions = ["tmx"]
    rootNode = "tmx"
    bodyNode = "body"
    XMLskeleton = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE tmx SYSTEM "tmx14.dtd">
<tmx version="1.4">
<header></header>
<body></body>
</tmx>'''

    def addheader(self):
        headernode = self.document.getroot().iterchildren(self.namespaced("header")).next()
        headernode.set("creationtool", "Translate Toolkit - po2tmx")
        headernode.set("creationtoolversion", __version__.sver)
        headernode.set("segtype", "sentence")
        headernode.set("o-tmf", "UTF-8")
        headernode.set("adminlang", "en")
        #TODO: consider adminlang. Used for notes, etc. Possibly same as targetlanguage
        headernode.set("srclang", self.sourcelanguage)
        headernode.set("datatype", "PlainText")
        #headernode.set("creationdate", "YYYYMMDDTHHMMSSZ"
        #headernode.set("creationid", "CodeSyntax"

    def addtranslation(self, source, srclang, translation, translang):
        """addtranslation method for testing old unit tests"""
        unit = self.addsourceunit(source)
        unit.target = translation
        tuvs = unit.xmlelement.iterdescendants(self.namespaced('tuv'))
        lisa.setXMLlang(tuvs.next(), srclang)
        lisa.setXMLlang(tuvs.next(), translang)

    def translate(self, sourcetext, sourcelang=None, targetlang=None):
        """method to test old unit tests"""
        return getattr(self.findunit(sourcetext), "target", None)
