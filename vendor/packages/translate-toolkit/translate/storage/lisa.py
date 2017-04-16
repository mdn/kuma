#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006-2009 Zuza Software Foundation
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

"""Parent class for LISA standards (TMX, TBX, XLIFF)"""

import re

from translate.storage import base
from translate.lang import data
try:
    from lxml import etree
    from translate.misc.xml_helpers import *
except ImportError, e:
    raise ImportError("lxml is not installed. It might be possible to continue without support for XML formats.")


def _findAllMatches(text, re_obj):
    """generate match objects for all L{re_obj} matches in L{text}."""
    start = 0
    max = len(text)
    while start < max:
        m = re_obj.search(text, start)
        if not m:
            break
        yield m
        start = m.end()

#TODO: we can now do better with our proper placeables support
placeholders = ['(%[diouxXeEfFgGcrs])', r'(\\+.?)', '(%[0-9]$lx)', '(%[0-9]\$[a-z])', '(<.+?>)']
re_placeholders = [re.compile(ph) for ph in placeholders]
def _getPhMatches(text):
    'return list of regexp matchobjects for with all place holders in the L{text}'
    matches = []
    for re_ph in re_placeholders:
        matches.extend(list(_findAllMatches(text, re_ph)))

    # sort them so they come sequentially
    matches.sort(lambda a, b: cmp(a.start(), b.start()))
    return matches


class LISAunit(base.TranslationUnit):
    """
    A single unit in the file.  Provisional work is done to make several
    languages possible.
    """

    #The name of the root element of this unit type:(termEntry, tu, trans-unit)
    rootNode = ""
    #The name of the per language element of this unit type:(termEntry, tu, trans-unit)
    languageNode = ""
    #The name of the innermost element of this unit type:(term, seg)
    textNode = ""

    namespace = None
    _default_xml_space = "preserve"
    """The default handling of spacing in the absense of an xml:space attribute.

    This is mostly for correcting XLIFF behaviour."""

    def __init__(self, source, empty=False, **kwargs):
        """Constructs a unit containing the given source string"""
        if empty:
            self._rich_source = None
            self._rich_target = None
            return
        self.xmlelement = etree.Element(self.namespaced(self.rootNode))
        #add descrip, note, etc.
        super(LISAunit, self).__init__(source)

    def __eq__(self, other):
        """Compares two units"""
        if not isinstance(other, LISAunit):
            return super(LISAunit, self).__eq__(other)
        languageNodes = self.getlanguageNodes()
        otherlanguageNodes = other.getlanguageNodes()
        if len(languageNodes) != len(otherlanguageNodes):
            return False
        for i in range(len(languageNodes)):
            mytext = self.getNodeText(languageNodes[i], getXMLspace(self.xmlelement, self._default_xml_space))
            othertext = other.getNodeText(otherlanguageNodes[i], getXMLspace(self.xmlelement, self._default_xml_space))
            if mytext != othertext:
                #TODO:^ maybe we want to take children and notes into account
                return False
        return True

    def namespaced(self, name):
        """Returns name in Clark notation.

           For example namespaced("source") in an XLIFF document might return::
               {urn:oasis:names:tc:xliff:document:1.1}source
           This is needed throughout lxml.
        """
        return namespaced(self.namespace, name)

    def set_source_dom(self, dom_node):
        languageNodes = self.getlanguageNodes()
        if len(languageNodes) > 0:
            self.xmlelement[0] = dom_node
        else:
            self.xmlelement.append(dom_node)

    def get_source_dom(self):
        return self.getlanguageNode(lang=None, index=0)
    source_dom = property(get_source_dom, set_source_dom)

    def setsource(self, text, sourcelang='en'):
        text = data.forceunicode(text)
        self.source_dom = self.createlanguageNode(sourcelang, text, "source")

    def getsource(self):
        return self.getNodeText(self.source_dom, getXMLspace(self.xmlelement, self._default_xml_space))
    source = property(getsource, setsource)

    def set_target_dom(self, dom_node, append=False):
        languageNodes = self.getlanguageNodes()
        assert len(languageNodes) > 0
        if dom_node is not None:
            if append or len(languageNodes) == 0:
                self.xmlelement.append(dom_node)
            else:
                self.xmlelement.insert(1, dom_node)
        if not append and len(languageNodes) > 1:
            self.xmlelement.remove(languageNodes[1])

    def get_target_dom(self, lang=None):
        if lang:
            return self.getlanguageNode(lang=lang)
        else:
            return self.getlanguageNode(lang=None, index=1)
    target_dom = property(get_target_dom)

    def settarget(self, text, lang='xx', append=False):
        #XXX: we really need the language - can't really be optional, and we
        # need to propagate it
        """Sets the "target" string (second language), or alternatively appends to the list"""
        text = data.forceunicode(text)
        #Firstly deal with reinitialising to None or setting to identical string
        if self.gettarget() == text:
            return
        languageNode = self.get_target_dom(None)
        if not text is None:
            if languageNode is None:
                languageNode = self.createlanguageNode(lang, text, "target")
                self.set_target_dom(languageNode, append)
            else:
                if self.textNode:
                    terms = languageNode.iter(self.namespaced(self.textNode))
                    try:
                        languageNode = terms.next()
                    except StopIteration, e:
                        pass
                languageNode.text = text
        else:
            self.set_target_dom(None, False)

    def gettarget(self, lang=None):
        """retrieves the "target" text (second entry), or the entry in the
        specified language, if it exists"""
        return self.getNodeText(self.get_target_dom(lang), getXMLspace(self.xmlelement, self._default_xml_space))
    target = property(gettarget, settarget)

    def createlanguageNode(self, lang, text, purpose=None):
        """Returns a xml Element setup with given parameters to represent a
        single language entry. Has to be overridden."""
        return None

    def createPHnodes(self, parent, text):
        """Create the text node in parent containing all the ph tags"""
        matches = _getPhMatches(text)
        if not matches:
            parent.text = text
            return

        # Now we know there will definitely be some ph tags
        start = matches[0].start()
        pretext = text[:start]
        if pretext:
            parent.text = pretext
        lasttag = parent
        for i, m in enumerate(matches):
            #pretext
            pretext = text[start:m.start()]
            # this will never happen with the first ph tag
            if pretext:
                lasttag.tail = pretext
            #ph node
            phnode = etree.SubElement(parent, self.namespaced("ph"))
            phnode.set("id", str(i+1))
            phnode.text = m.group()
            lasttag = phnode
            start = m.end()
        #post text
        if text[start:]:
            lasttag.tail = text[start:]

    def getlanguageNodes(self):
        """Returns a list of all nodes that contain per language information."""
        return list(self.xmlelement.iterchildren(self.namespaced(self.languageNode)))

    def getlanguageNode(self, lang=None, index=None):
        """Retrieves a languageNode either by language or by index"""
        if lang is None and index is None:
            raise KeyError("No criterea for languageNode given")
        languageNodes = self.getlanguageNodes()
        if lang:
            for set in languageNodes:
                if getXMLlang(set) == lang:
                    return set
        else:#have to use index
            if index >= len(languageNodes):
                return None
            else:
                return languageNodes[index]
        return None

    def getNodeText(self, languageNode, xml_space="preserve"):
        """Retrieves the term from the given languageNode"""
        if languageNode is None:
            return None
        if self.textNode:
            terms = languageNode.iterdescendants(self.namespaced(self.textNode))
            if terms is None:
                return None
            else:
                return getText(terms.next(), xml_space)
        else:
            return getText(languageNode, xml_space)

    def __str__(self):
        return etree.tostring(self.xmlelement, pretty_print=True, encoding='utf-8')

    def _set_property(self, name, value):
        self.xmlelement.attrib[name] = value

    xid = property(lambda self:        self.xmlelement.attrib[self.namespaced('xid')],
                   lambda self, value: self._set_property(self.namespaced('xid'), value))

    rid = property(lambda self:        self.xmlelement.attrib[self.namespaced('rid')],
                   lambda self, value: self._set_property(self.namespaced('rid'), value))

    def createfromxmlElement(cls, element):
        term = cls(None, empty=True)
        term.xmlelement = element
        return term
    createfromxmlElement = classmethod(createfromxmlElement)

class LISAfile(base.TranslationStore):
    """A class representing a file store for one of the LISA file formats."""
    UnitClass = LISAunit
    #The root node of the XML document:
    rootNode = ""
    #The root node of the content section:
    bodyNode = ""
    #The XML skeleton to use for empty construction:
    XMLskeleton = ""

    namespace = None

    def __init__(self, inputfile=None, sourcelanguage='en', targetlanguage=None, unitclass=None):
        super(LISAfile, self).__init__(unitclass=unitclass)
        if inputfile is not None:
            self.parse(inputfile)
            assert self.document.getroot().tag == self.namespaced(self.rootNode)
        else:
            # We strip out newlines to ensure that spaces in the skeleton doesn't
            # interfere with the the pretty printing of lxml
            self.parse(self.XMLskeleton.replace("\n", ""))
            self.setsourcelanguage(sourcelanguage)
            self.settargetlanguage(targetlanguage)
            self.addheader()
        self._encoding = "UTF-8"

    def addheader(self):
        """Method to be overridden to initialise headers, etc."""
        pass

    def namespaced(self, name):
        """Returns name in Clark notation.

           For example namespaced("source") in an XLIFF document might return::
               {urn:oasis:names:tc:xliff:document:1.1}source
           This is needed throughout lxml.
        """
        return namespaced(self.namespace, name)

    def initbody(self):
        """Initialises self.body so it never needs to be retrieved from the XML again."""
        self.namespace = self.document.getroot().nsmap.get(None, None)
        self.body = self.document.find('//%s' % self.namespaced(self.bodyNode))

    def addsourceunit(self, source):
        #TODO: miskien moet hierdie eerder addsourcestring of iets genoem word?
        """Adds and returns a new unit with the given string as first entry."""
        newunit = self.UnitClass(source)
        self.addunit(newunit)
        return newunit

    def addunit(self, unit, new=True):
        unit.namespace = self.namespace
        super(LISAfile, self).addunit(unit)
        if new:
            self.body.append(unit.xmlelement)

    def __str__(self):
        """Converts to a string containing the file's XML"""
        return etree.tostring(self.document, pretty_print=True, xml_declaration=True, encoding='utf-8')

    def parse(self, xml):
        """Populates this object from the given xml string"""
        if not hasattr(self, 'filename'):
            self.filename = getattr(xml, 'name', '')
        if hasattr(xml, "read"):
            xml.seek(0)
            posrc = xml.read()
            xml = posrc
        if etree.LXML_VERSION >= (2, 1, 0):
            #Since version 2.1.0 we can pass the strip_cdata parameter to
            #indicate that we don't want cdata to be converted to raw XML
            parser = etree.XMLParser(strip_cdata=False)
        else:
            parser = etree.XMLParser()
        self.document = etree.fromstring(xml, parser).getroottree()
        self._encoding = self.document.docinfo.encoding
        self.initbody()
        assert self.document.getroot().tag == self.namespaced(self.rootNode)
        for entry in self.document.getroot().iterdescendants(self.namespaced(self.UnitClass.rootNode)):
            term = self.UnitClass.createfromxmlElement(entry)
            self.addunit(term, new=False)

