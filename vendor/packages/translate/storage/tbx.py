#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006-2010 Zuza Software Foundation
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

"""module for handling TBX glossary files"""

from lxml import etree

from translate.storage import lisa


class tbxunit(lisa.LISAunit):
    """A single term in the TBX file.
Provisional work is done to make several languages possible."""
    rootNode = "termEntry"
    languageNode = "langSet"
    textNode = "term"

    def createlanguageNode(self, lang, text, purpose):
        """returns a langset xml Element setup with given parameters"""
        if isinstance(text, str):
            text = text.decode("utf-8")
        langset = etree.Element(self.languageNode)
        lisa.setXMLlang(langset, lang)
        tig = etree.SubElement(langset, "tig")  # or ntig with termGrp inside
        term = etree.SubElement(tig, self.textNode)
        # probably not what we want:
        # lisa.setXMLspace(term, "preserve")
        term.text = text
        return langset

    def getid(self):
        # The id attribute is optional
        return self.xmlelement.get("id") or self.source


class tbxfile(lisa.LISAfile):
    """Class representing a TBX file store."""
    UnitClass = tbxunit
    Name = "TBX Glossary"
    Mimetypes = ["application/x-tbx"]
    Extensions = ["tbx"]
    rootNode = "martif"
    bodyNode = "body"
    XMLskeleton = '''<?xml version="1.0"?>
<!DOCTYPE martif PUBLIC "ISO 12200:1999A//DTD MARTIF core (DXFcdV04)//EN" "TBXcdv04.dtd">
<martif type="TBX">
<martifHeader>
<fileDesc>
<sourceDesc><p>Translate Toolkit</p></sourceDesc>
</fileDesc>
</martifHeader>
<text><body></body></text>
</martif>'''

    def addheader(self):
        """Initialise headers with TBX specific things."""
        lisa.setXMLlang(self.document.getroot(), self.sourcelanguage)
