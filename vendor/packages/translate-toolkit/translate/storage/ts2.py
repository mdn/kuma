#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

"""Module for handling Qt linguist (.ts) files.

This will eventually replace the older ts.py which only supports the older 
format. While converters haven't been updated to use this module, we retain 
both.

U{TS file format 4.3<http://doc.trolltech.com/4.3/linguist-ts-file-format.html>}, 
U{4.5<http://doc.trolltech.com/4.5/linguist-ts-file-format.html>},
U{Example<http://svn.ez.no/svn/ezcomponents/trunk/Translation/docs/linguist-format.txt>}, 
U{Plurals forms<http://www.koders.com/cpp/fidE7B7E83C54B9036EB7FA0F27BC56BCCFC4B9DF34.aspx#L200>}

U{Specification of the valid variable entries <http://doc.trolltech.com/4.3/qstring.html#arg>}, 
U{2 <http://doc.trolltech.com/4.3/qstring.html#arg-2>}
"""

from translate.storage import base, lisa
from translate.storage.placeables import general
from translate.misc.multistring import multistring
from translate.lang import data
from lxml import etree

# TODO: handle translation types

NPLURALS = {
'jp': 1,
'en': 2,
'fr': 2,
'lv': 3,
'ga': 3,
'cs': 3,
'sk': 3,
'mk': 3,
'lt': 3,
'ru': 3,
'pl': 3,
'ro': 3,
'sl': 4,
'mt': 4,
'cy': 5,
'ar': 6,
}

class tsunit(lisa.LISAunit):
    """A single term in the xliff file."""

    rootNode = "message"
    languageNode = "source"
    textNode = ""
    namespace = ''
    rich_parsers = general.parsers

    def createlanguageNode(self, lang, text, purpose):
        """Returns an xml Element setup with given parameters."""

        assert purpose
        if purpose == "target":
            purpose = "translation"
        langset = etree.Element(self.namespaced(purpose))
        #TODO: check language
#        lisa.setXMLlang(langset, lang)

        langset.text = text
        return langset

    def _getsourcenode(self):
        return self.xmlelement.find(self.namespaced(self.languageNode))

    def _gettargetnode(self):
        return self.xmlelement.find(self.namespaced("translation"))

    def getlanguageNodes(self):
        """We override this to get source and target nodes."""
        def not_none(node):
            return not node is None
        return filter(not_none, [self._getsourcenode(), self._gettargetnode()])

    def getsource(self):
        # TODO: support <byte>. See bug 528.
        sourcenode = self._getsourcenode()
        if self.hasplural():
            return multistring([sourcenode.text])
        else:
            return data.forceunicode(sourcenode.text)
    source = property(getsource, lisa.LISAunit.setsource)
    rich_source = property(base.TranslationUnit._get_rich_source, base.TranslationUnit._set_rich_source)

    def settarget(self, text):
        # This is a fairly destructive implementation. Don't assume that this
        # is necessarily correct in all regards, but it does deal with a lot of
        # cases. It is hard to deal with plurals, since 
        #Firstly deal with reinitialising to None or setting to identical string
        if self.gettarget() == text:
            return
        strings = []
        if isinstance(text, multistring):
            strings = text.strings
        elif isinstance(text, list):
            strings = text
        else:
            strings = [text]
        targetnode = self._gettargetnode()
        type = targetnode.get("type")
        targetnode.clear()
        if type:
            targetnode.set("type", type)
        if self.hasplural() or len(strings) > 1:
            self.xmlelement.set("numerus", "yes")
            for string in strings:
                numerus = etree.SubElement(targetnode, self.namespaced("numerusform"))
                numerus.text = data.forceunicode(string) or u""
        else:
            targetnode.text = data.forceunicode(text) or u""

    def gettarget(self):
        targetnode = self._gettargetnode()
        if targetnode is None:
            etree.SubElement(self.xmlelement, self.namespaced("translation"))
            return None
        if self.hasplural():
            numerus_nodes = targetnode.findall(self.namespaced("numerusform"))
            return multistring([node.text or u"" for node in numerus_nodes])
        else:
            return data.forceunicode(targetnode.text) or u""
    target = property(gettarget, settarget)
    rich_target = property(base.TranslationUnit._get_rich_target, base.TranslationUnit._set_rich_target)

    def hasplural(self):
        return self.xmlelement.get("numerus") == "yes"

    def addnote(self, text, origin=None, position="append"):
        """Add a note specifically in a "comment" tag"""
        if isinstance(text, str):
            text = text.decode("utf-8")
        current_notes = self.getnotes(origin)
        self.removenotes(origin)
        if origin in ["programmer", "developer", "source code"]:
            note = etree.SubElement(self.xmlelement, self.namespaced("extracomment"))
        else:
            note = etree.SubElement(self.xmlelement, self.namespaced("translatorcomment"))
        if position == "append":
            note.text = "\n".join(filter(None, [current_notes, text.strip()]))
        else:
            note.text = text.strip()

    def getnotes(self, origin=None):
        #TODO: consider only responding when origin has certain values
        comments = []
        if origin in ["programmer", "developer", "source code", None]:
            notenode = self.xmlelement.find(self.namespaced("comment"))
            if notenode is not None:
                comments.append(notenode.text)
            notenode = self.xmlelement.find(self.namespaced("extracomment"))
            if notenode is not None:
                comments.append(notenode.text)
        if origin in ["translator", None]:
            notenode = self.xmlelement.find(self.namespaced("translatorcomment"))
            if notenode is not None:
                comments.append(notenode.text)
        return '\n'.join(comments)

    def removenotes(self, origin=None):
        """Remove all the translator notes."""
        if origin in ["programmer", "developer", "source code", None]:
            note = self.xmlelement.find(self.namespaced("comment"))
            if not note is None:
                self.xmlelement.remove(note)
            note = self.xmlelement.find(self.namespaced("extracomment"))
            if not note is None:
                self.xmlelement.remove(note)
        if origin in ["translator", None]:
            note = self.xmlelement.find(self.namespaced("translatorcomment"))
            if not note is None:
                self.xmlelement.remove(note)


    def _gettype(self):
        """Returns the type of this translation."""
        targetnode = self._gettargetnode()
        if targetnode is not None:
            return targetnode.get("type")
        return None

    def _settype(self, value=None):
        """Set the type of this translation."""
        if value is None and self._gettype:
            # lxml recommends against using .attrib, but there seems to be no
            # other way
            self._gettargetnode().attrib.pop("type")
        else:
            self._gettargetnode().set("type", value)

    def isreview(self):
        """States whether this unit needs to be reviewed"""
        return self._gettype() == "unfinished"

    def isfuzzy(self):
        return self._gettype() == "unfinished"

    def markfuzzy(self, value=True):
        if value:
            self._settype("unfinished")
        else:
            self._settype(None)

    def getid(self):
        context_name = self.getcontext()
        #XXX: context_name is not supposed to be able to be None (the <name> 
        # tag is compulsary in the <context> tag)
        if context_name is not None:
            return context_name + self.source
        else:
            return self.source

    def istranslatable(self):
        # Found a file in the wild with no context and an empty source. This
        # served as a header, so let's classify this as not translatable.
        # http://bibletime.svn.sourceforge.net/viewvc/bibletime/trunk/bibletime/i18n/messages/bibletime_ui.ts
        # Furthermore, let's decide to handle obsolete units as untranslatable
        # like we do with PO.
        return bool(self.getid()) and not self.isobsolete()

    def getcontext(self):
        parent =  self.xmlelement.getparent()
        if parent is None:
            return None
        context = parent.find("name")
        if context is None:
            return None
        return context.text

    def addlocation(self, location):
        if isinstance(location, str):
            location = location.decode("utf-8")
        location = etree.SubElement(self.xmlelement, self.namespaced("location"))
        filename, line = location.split(':', 1)
        location.set("filename", filename)
        location.set("line", line or "")

    def getlocations(self):
        location = self.xmlelement.find(self.namespaced("location"))
        if location is None:
            return []
        else:
            return [':'.join([location.get("filename"), location.get("line")])]

    def merge(self, otherunit, overwrite=False, comments=True, authoritative=False):
        super(tsunit, self).merge(otherunit, overwrite, comments)
        #TODO: check if this is necessary:
        if otherunit.isfuzzy():
            self.markfuzzy()

    def isobsolete(self):
        return self._gettype() == "obsolete"


class tsfile(lisa.LISAfile):
    """Class representing a XLIFF file store."""
    UnitClass = tsunit
    Name = _("Qt Linguist Translation File")
    Mimetypes  = ["application/x-linguist"]
    Extensions = ["ts"]
    rootNode = "TS"
    # We will switch out .body to fit with the context we are working on
    bodyNode = "context"
    XMLskeleton = '''<!DOCTYPE TS>
<TS>
</TS>
'''
    namespace = ''

    def __init__(self, *args, **kwargs):
        self._contextname = None
        lisa.LISAfile.__init__(self, *args, **kwargs)

    def initbody(self):
        """Initialises self.body."""
        self.namespace = self.document.getroot().nsmap.get(None, None)
        if self._contextname:
            self.body = self.getcontextnode(self._contextname)
        else:
            self.body = self.document.getroot()

    def gettargetlanguage(self):
        """Get the target language for this .ts file.

        @return: ISO code e.g. af, fr, pt_BR
        @rtype: String
        """
        return self.body.get('language')

    def settargetlanguage(self, targetlanguage):
        """Set the target language for this .ts file to L{targetlanguage}.

        @param targetlanguage: ISO code e.g. af, fr, pt_BR
        @type targetlanguage: String
        """
        if targetlanguage:
            self.body.set('language', targetlanguage)

    def _createcontext(self, contextname, comment=None):
        """Creates a context node with an optional comment"""
        context = etree.SubElement(self.document.getroot(), self.namespaced(self.bodyNode))
        name = etree.SubElement(context, self.namespaced("name"))
        name.text = contextname
        if comment:
            comment_node = context.SubElement(context, "comment")
            comment_node.text = comment
        return context

    def _getcontextname(self, contextnode):
        """Returns the name of the given context node."""
        return contextnode.find(self.namespaced("name")).text

    def _getcontextnames(self):
        """Returns all contextnames in this TS file."""
        contextnodes = self.document.findall(self.namespaced("context"))
        contextnames = [self.getcontextname(contextnode) for contextnode in contextnodes]
        return contextnames

    def _getcontextnode(self, contextname):
        """Returns the context node with the given name."""
        contextnodes = self.document.findall(self.namespaced("context"))
        for contextnode in contextnodes:
            if self._getcontextname(contextnode) == contextname:
                return contextnode
        return None

    def addunit(self, unit, new=True, contextname=None, createifmissing=True):
        """Adds the given unit to the last used body node (current context).

        If the contextname is specified, switch to that context (creating it
        if allowed by createifmissing)."""
        if contextname is None:
            contextname = unit.getcontext()

        if self._contextname != contextname:
            if not self._switchcontext(contextname, createifmissing):
                return None
        super(tsfile, self).addunit(unit, new)
#        lisa.setXMLspace(unit.xmlelement, "preserve")
        return unit

    def _switchcontext(self, contextname, createifmissing=False):
        """Switch the current context to the one named contextname, optionally
        creating it if it doesn't exist."""
        self._contextname = contextname
        contextnode = self._getcontextnode(contextname)
        if contextnode is None:
            if not createifmissing:
                return False
            contextnode = self._createcontext(contextname)

        self.body = contextnode
        if self.body is None:
            return False
        return True

    def nplural(self):
        lang = self.body.get("language")
        if NPLURALS.has_key(lang):
            return NPLURALS[lang]
        else:
            return 1

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
        if not "<!DOCTYPE TS>" in output[:30]:
            output = "<!DOCTYPE TS>" + output
        return output


