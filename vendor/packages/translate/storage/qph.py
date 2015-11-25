#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008, 2010 Zuza Software Foundation
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
#

"""Module for handling Qt Linguist Phrase Book (.qph) files.

Extract from the `Qt Linguist Manual: Translators
<http://doc.trolltech.com/4.3/linguist-translators.html>`_:
.qph Qt Phrase Book Files are human-readable XML files containing standard
phrases and their translations. These files are created and updated by Qt
Linguist and may be used by any number of projects and applications.

A DTD to define the format does not seem to exist, but the following `code
<http://qt.gitorious.org/qt/qt/blobs/4.7/tools/linguist/shared/qph.cpp>`_
provides the reference implementation for the Qt Linguist product.
"""

from lxml import etree

from translate.lang import data
from translate.storage import lisa


class QphUnit(lisa.LISAunit):
    """A single term in the qph file."""

    rootNode = "phrase"
    languageNode = "source"
    textNode = ""
    namespace = ''

    def createlanguageNode(self, lang, text, purpose):
        """Returns an xml Element setup with given parameters."""
        assert purpose
        langset = etree.Element(self.namespaced(purpose))
        langset.text = text
        return langset

    def _getsourcenode(self):
        return self.xmlelement.find(self.namespaced(self.languageNode))

    def _gettargetnode(self):
        return self.xmlelement.find(self.namespaced("target"))

    def getlanguageNodes(self):
        """We override this to get source and target nodes."""

        def not_none(node):
            return not node is None

        return filter(not_none, [self._getsourcenode(), self._gettargetnode()])

    def addnote(self, text, origin=None, position="append"):
        """Add a note specifically in a "definition" tag"""
        current_notes = self.getnotes(origin)
        self.removenotes()
        note = etree.SubElement(self.xmlelement, self.namespaced("definition"))
        note.text = "\n".join(filter(None, [current_notes, text.strip()]))

    def getnotes(self, origin=None):
        #TODO: consider only responding when origin has certain values
        notenode = self.xmlelement.find(self.namespaced("definition"))
        comment = ''
        if not notenode is None:
            comment = notenode.text
        return comment

    def removenotes(self):
        """Remove all the translator notes."""
        note = self.xmlelement.find(self.namespaced("definition"))
        if not note is None:
            self.xmlelement.remove(note)


class QphFile(lisa.LISAfile):
    """Class representing a QPH file store."""
    UnitClass = QphUnit
    Name = "Qt Phrase Book"
    Mimetypes = ["application/x-qph"]
    Extensions = ["qph"]
    rootNode = "QPH"
    bodyNode = "QPH"
    XMLskeleton = '''<!DOCTYPE QPH>
<QPH>
</QPH>
'''
    namespace = ''

    def initbody(self):
        """Initialises self.body so it never needs to be retrieved from the
        XML again."""
        self.namespace = self.document.getroot().nsmap.get(None, None)
        self.header = self.document.getroot()
        self.body = self.document.getroot()  # The root node contains the units

    def getsourcelanguage(self):
        """Get the source language for this .qph file.

        We don't implement setsourcelanguage as users really shouldn't be
        altering the source language in .qph files, it should be set correctly
        by the extraction tools.

        :return: ISO code e.g. af, fr, pt_BR
        :rtype: String
        """
        lang = data.normalize_code(self.header.get('sourcelanguage', "en"))
        if lang == 'en-us':
            return 'en'
        return lang

    def gettargetlanguage(self):
        """Get the target language for this .qph file.

        :return: ISO code e.g. af, fr, pt_BR
        :rtype: String
        """
        return data.normalize_code(self.header.get('language'))

    def settargetlanguage(self, targetlanguage):
        """Set the target language for this .qph file to *targetlanguage*.

        :param targetlanguage: ISO code e.g. af, fr, pt_BR
        :type targetlanguage: String
        """
        if targetlanguage:
            self.header.set('language', targetlanguage)

    def __str__(self):
        """Converts to a string containing the file's XML.

        We have to override this to ensure mimic the Qt convention:
            - no XML decleration
        """
        return etree.tostring(self.document, pretty_print=True,
                              xml_declaration=False, encoding='utf-8')
