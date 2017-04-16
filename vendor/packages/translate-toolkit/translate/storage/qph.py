#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

"""Module for handling Qt Phrase Book (.qph) files.

Extract from the U{Qt Linguist Manual:
Translators<http://doc.trolltech.com/4.3/linguist-translators.html>}:
.qph Qt Phrase Book Files are human-readable XML files containing standard
phrases and their translations. These files are created and updated by Qt
Linguist and may be used by any number of projects and applications.

A DTD to define the format does not seem to exist, but the following U{code
<http://www.google.com/codesearch?hl=en&q=show:gtsFsbhpVeE:KeGnQG0wDCQ:xOXsNYqccyE&sa=N&ct=rd&cs_p=ftp://ftp.trolltech.com/qt/source/qt-x11-opensource-4.0.0-b1.tar.gz&cs_f=qt-x11-opensource-4.0.0-b1/tools/linguist/linguist/phrase.cpp>} 
provides the reference implementation for the Qt Linguist product.
"""

from translate.storage import lisa
from lxml import etree

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
        assert isinstance(text, unicode)
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
    Name = _("Qt Phrase Book")
    Mimetypes  = ["application/x-qph"]
    Extensions = ["qph"]
    rootNode = "QPH"
    bodyNode = "QPH"
    XMLskeleton = '''<!DOCTYPE QPH>
<QPH>
</QPH>
'''
    namespace = ''

    def initbody(self):
        """Initialises self.body so it never needs to be retrieved from the XML again."""
        self.namespace = self.document.getroot().nsmap.get(None, None)
        self.body = self.document.getroot() # The root node contains the units

    def __str__(self):
        """Converts to a string containing the file's XML.
        
        We have to override this to ensure mimic the Qt convention:
            - no XML decleration
            - plain DOCTYPE that lxml seems to ignore
        """
        # A bug in lxml means we have to output the doctype ourselves. For 
        # more information, see:
        # http://codespeak.net/pipermail/lxml-dev/2008-October/004112.html
        # The problem was fixed in lxml 2.1.3
        output = etree.tostring(self.document, pretty_print=True, 
                xml_declaration=False, encoding='utf-8')
        if not "<!DOCTYPE QPH>" in output[:30]:
            output = "<!DOCTYPE QPH>" + output
        return output
