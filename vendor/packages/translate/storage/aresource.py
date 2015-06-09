#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Michal Čihař
# Copyright 2014 Luca De Petrillo
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

"""Module for handling Android String and Plurals resource files."""

import re
import os

from lxml import etree

from translate.lang import data
from translate.storage import base, lisa
from translate.misc.multistring import multistring

from babel.core import Locale

EOF = None
WHITESPACE = ' \n\t'  # Whitespace that we collapse.
MULTIWHITESPACE = re.compile('[ \n\t]{2}')


class AndroidResourceUnit(base.TranslationUnit):
    """A single entry in the Android String resource file."""

    @classmethod
    def createfromxmlElement(cls, element):
        term = None
        # Actually this class supports only plurals and string tags
        if ((element.tag == "plurals") or (element.tag == "string")):
            term = cls(None, xmlelement=element)
        return term

    def __init__(self, source, empty=False, xmlelement=None, **kwargs):
        if xmlelement is not None:
            self.xmlelement = xmlelement
        else:
            if self.hasplurals(source):
                self.xmlelement = etree.Element("plurals")
            else:
                self.xmlelement = etree.Element("string")
            self.xmlelement.tail = '\n'
        if source is not None:
            self.setid(source)
        super(AndroidResourceUnit, self).__init__(source)

    def istranslatable(self):
        return (
            bool(self.getid())
            and self.xmlelement.get('translatable') != 'false'
        )

    def isblank(self):
        return not bool(self.getid())

    def getid(self):
        return self.xmlelement.get("name")

    def setid(self, newid):
        return self.xmlelement.set("name", newid)

    def getcontext(self):
        return self.xmlelement.get("name")

    def unescape(self, text):
        '''
        Remove escaping from Android resource.

        Code stolen from android2po
        <https://github.com/miracle2k/android2po>
        '''
        # Return text for empty elements
        if text is None:
            return ''

        # We need to collapse multiple whitespace while paying
        # attention to Android's quoting and escaping.
        space_count = 0
        active_quote = False
        active_percent = False
        active_escape = False
        formatted = False
        i = 0
        text = list(text) + [EOF]
        while i < len(text):
            c = text[i]

            # Handle whitespace collapsing
            if c is not EOF and c in WHITESPACE:
                space_count += 1
            elif space_count > 1:
                # Remove duplicate whitespace; Pay attention: We
                # don't do this if we are currently inside a quote,
                # except for one special case: If we have unbalanced
                # quotes, e.g. we reach eof while a quote is still
                # open, we *do* collapse that trailing part; this is
                # how Android does it, for some reason.
                if not active_quote or c is EOF:
                    # Replace by a single space, will get rid of
                    # non-significant newlines/tabs etc.
                    text[i-space_count : i] = ' '
                    i -= space_count - 1
                space_count = 0
            elif space_count == 1:
                # At this point we have a single whitespace character,
                # but it might be a newline or tab. If we write this
                # kind of insignificant whitespace into the .po file,
                # it will be considered significant on import. So,
                # make sure that this kind of whitespace is always a
                # standard space.
                text[i-1] = ' '
                space_count = 0
            else:
                space_count = 0

            # Handle quotes
            if c == '"' and not active_escape:
                active_quote = not active_quote
                del text[i]
                i -= 1

            # If the string is run through a formatter, it will have
            # percentage signs for String.format
            if c == '%' and not active_escape:
                active_percent = not active_percent
            elif not active_escape and active_percent:
                formatted = True
                active_percent = False

            # Handle escapes
            if c == '\\':
                if not active_escape:
                    active_escape = True
                else:
                    # A double-backslash represents a single;
                    # simply deleting the current char will do.
                    del text[i]
                    i -= 1
                    active_escape = False
            else:
                if active_escape:
                    # Handle the limited amount of escape codes
                    # that we support.
                    # TODO: What about \r, or \r\n?
                    if c is EOF:
                        # Basically like any other char, but put
                        # this first so we can use the ``in`` operator
                        # in the clauses below without issue.
                        pass
                    elif c == 'n' or c == 'N':
                        text[i-1 : i+1] = '\n'  # an actual newline
                        i -= 1
                    elif c == 't' or c == 'T':
                        text[i-1 : i+1] = '\t'  # an actual tab
                        i -= 1
                    elif c == ' ':
                        text[i-1 : i+1] = ' '  # an actual space
                        i -= 1
                    elif c in '"\'@':
                        text[i-1 : i] = ''  # remove the backslash
                        i -= 1
                    elif c == 'u':
                        # Unicode sequence. Android is nice enough to deal
                        # with those in a way which let's us just capture
                        # the next 4 characters and raise an error if they
                        # are not valid (rather than having to use a new
                        # state to parse the unicode sequence).
                        # Exception: In case we are at the end of the
                        # string, we support incomplete sequences by
                        # prefixing the missing digits with zeros.
                        # Note: max(len()) is needed in the slice due to
                        # trailing ``None`` element.
                        max_slice = min(i+5, len(text)-1)
                        codepoint_str = "".join(text[i+1 : max_slice])
                        if len(codepoint_str) < 4:
                            codepoint_str = u"0" * (4-len(codepoint_str)) + codepoint_str
                        try:
                            # We can't trust int() to raise a ValueError,
                            # it will ignore leading/trailing whitespace.
                            if not codepoint_str.isalnum():
                                raise ValueError(codepoint_str)
                            codepoint = unichr(int(codepoint_str, 16))
                        except ValueError:
                            raise ValueError('bad unicode escape sequence')

                        text[i-1 : max_slice] = codepoint
                        i -= 1
                    else:
                        # All others, remove, like Android does as well.
                        text[i-1 : i+1] = ''
                        i -= 1
                    active_escape = False

            i += 1

        # Join the string together again, but w/o EOF marker
        return "".join(text[:-1])

    def escape(self, text, add_quote=True):
        '''
        Escape all the characters which need to be escaped in an Android XML file.
        '''
        if text is None:
            return
        if len(text) == 0:
            return ''
        text = text.replace('\\', '\\\\')
        text = text.replace('\n', '\\n')
        # This will add non intrusive real newlines to
        # ones in translation improving readability of result
        text = text.replace(' \\n', '\n\\n')
        text = text.replace('\t', '\\t')
        text = text.replace('\'', '\\\'')
        text = text.replace('"', '\\"')

        # @ needs to be escaped at start
        if text.startswith('@'):
            text = '\\@' + text[1:]
        # Quote strings with more whitespace
        if add_quote and (text[0] in WHITESPACE or text[-1] in WHITESPACE or len(MULTIWHITESPACE.findall(text)) > 0):
            return '"%s"' % text
        return text

    def setsource(self, source):
        super(AndroidResourceUnit, self).setsource(source)

    def getsource(self, lang=None):
        if (super(AndroidResourceUnit, self).source is None):
            return self.target
        else:
            return super(AndroidResourceUnit, self).source

    source = property(getsource, setsource)

    def set_xml_text_value(self, target, xmltarget):
        if '<' in target:
            # Handle text with possible markup
            target = target.replace('&', '&amp;')
            try:
                # Try as XML
                newstring = etree.fromstring('<string>%s</string>' % target)
            except:
                # Fallback to string with XML escaping
                target = target.replace('<', '&lt;')
                newstring = etree.fromstring('<string>%s</string>' % target)
            # Update text
            if newstring.text is None:
                xmltarget.text = ''
            else:
                xmltarget.text = newstring.text
            # Remove old elements
            for x in xmltarget.iterchildren():
                xmltarget.remove(x)
            # Escape all text parts
            for x in newstring.iter():
                x.text = self.escape(x.text, False)
                if x.prefix is not None:
                    x.prefix = self.escape(x.prefix, False)
                if x.tail is not None:
                    x.tail = self.escape(x.tail, False)
            # Add new elements
            for x in newstring.iterchildren():
                xmltarget.append(x)
        else:
            # Handle text only
            xmltarget.text = self.escape(target)

    def settarget(self, target):
        if (self.hasplurals(self.source) or self.hasplurals(target)):
            # Fix the root tag if mismatching
            if self.xmlelement.tag != "plurals":
                old_id = self.getid()
                self.xmlelement = etree.Element("plurals")
                self.setid(old_id)

            lang_tags = set(Locale(self.gettargetlanguage()).plural_form.tags)
            # Ensure that the implicit default "other" rule is present (usually omitted by Babel)
            lang_tags.add('other')

            # Get plural tags in the right order.
            plural_tags = [tag for tag in ['zero', 'one', 'two', 'few', 'many', 'other'] if tag in lang_tags]

            # Get string list to handle, wrapping non multistring/list targets into a list.
            if isinstance(target, multistring):
                plural_strings = target.strings
            elif isinstance(target, list):
                plural_strings = target
            else:
                plural_strings = [target]

            # Sync plural_strings elements to plural_tags count.
            if len(plural_strings) < len(plural_tags):
                plural_strings += [''] * (len(plural_tags) - len(plural_strings))
            plural_strings = plural_strings[:len(plural_tags)]

            # Rebuild plurals.
            for entry in self.xmlelement.iterchildren():
                self.xmlelement.remove(entry)

            self.xmlelement.text = "\n\t"

            for plural_tag, plural_string in zip(plural_tags, plural_strings):
                item = etree.Element("item")
                item.set("quantity", plural_tag)
                self.set_xml_text_value(plural_string, item)
                item.tail = "\n\t"
                self.xmlelement.append(item)
            # Remove the tab from last item
            item.tail = "\n"
        else:
            # Fix the root tag if mismatching
            if self.xmlelement.tag != "string":
                old_id = self.getid()
                self.xmlelement = etree.Element("string")
                self.setid(old_id)

            self.set_xml_text_value(target, self.xmlelement)

        super(AndroidResourceUnit, self).settarget(target)

    def get_xml_text_value(self, xmltarget):
        # Grab inner text
        target = self.unescape(xmltarget.text or u'')
        # Include markup as well
        target += u''.join([data.forceunicode(etree.tostring(child, encoding='utf-8')) for child in xmltarget.iterchildren()])
        return target

    def gettarget(self, lang=None):
        if (self.xmlelement.tag == "plurals"):
            target = []
            for entry in self.xmlelement.iterchildren():
                target.append(self.get_xml_text_value(entry))
            return multistring(target)
        else:
            return self.get_xml_text_value(self.xmlelement)

    target = property(gettarget, settarget)

    def getlanguageNode(self, lang=None, index=None):
        return self.xmlelement

    # Notes are handled as previous sibling comments.
    def addnote(self, text, origin=None, position="append"):
        if origin in ['programmer', 'developer', 'source code', None]:
            self.xmlelement.addprevious(etree.Comment(text))
        else:
            return super(AndroidResourceUnit, self).addnote(text, origin=origin,
                                                 position=position)

    def getnotes(self, origin=None):
        if origin in ['programmer', 'developer', 'source code', None]:
            comments = []
            if (self.xmlelement is not None):
                prevSibling = self.xmlelement.getprevious()
                while ((prevSibling is not None) and (prevSibling.tag is etree.Comment)):
                    comments.insert(0, prevSibling.text)
                    prevSibling = prevSibling.getprevious()

            return u'\n'.join(comments)
        else:
            return super(AndroidResourceUnit, self).getnotes(origin)

    def removenotes(self):
        if ((self.xmlelement is not None) and (self.xmlelement.getparent is not None)):
            prevSibling = self.xmlelement.getprevious()
            while ((prevSibling is not None) and (prevSibling.tag is etree.Comment)):
                prevSibling.getparent().remove(prevSibling)
                prevSibling = self.xmlelement.getprevious()

        super(AndroidResourceUnit, self).removenotes()

    def __str__(self):
        return etree.tostring(self.xmlelement, pretty_print=True,
                              encoding='utf-8')

    def __eq__(self, other):
        return (str(self) == str(other))

    def hasplurals(self, thing):
        if isinstance(thing, multistring):
            return True
        elif isinstance(thing, list):
            return True
        return False


class AndroidResourceFile(lisa.LISAfile):
    """Class representing an Android String resource file store."""
    UnitClass = AndroidResourceUnit
    Name = "Android String Resource"
    Mimetypes = ["application/xml"]
    Extensions = ["xml"]
    rootNode = "resources"
    bodyNode = "resources"
    XMLskeleton = '''<?xml version="1.0" encoding="utf-8"?>
<resources></resources>'''

    def initbody(self):
        """Initialises self.body so it never needs to be retrieved from the
        XML again."""
        self.namespace = self.document.getroot().nsmap.get(None, None)
        self.body = self.document.getroot()

    def parse(self, xml):
        """Populates this object from the given xml string"""
        if not hasattr(self, 'filename'):
            self.filename = getattr(xml, 'name', '')
        if hasattr(xml, "read"):
            xml.seek(0)
            posrc = xml.read()
            xml = posrc
        parser = etree.XMLParser(strip_cdata=False)
        self.document = etree.fromstring(xml, parser).getroottree()
        self._encoding = self.document.docinfo.encoding
        self.initbody()
        assert self.document.getroot().tag == self.namespaced(self.rootNode)

        for entry in self.document.getroot().iterchildren():
            term = self.UnitClass.createfromxmlElement(entry)
            if term is not None:
                self.addunit(term, new=False)

    def gettargetlanguage(self):
        target_lang = super(AndroidResourceFile, self).gettargetlanguage()

        # If targetlanguage isn't set, we try to extract it from the filename path (if any).
        if (target_lang is None) and hasattr(self, 'filename') and self.filename:
            # Android standards expect resource files to be in a directory named "values[-<lang>[-r<region>]]".
            parent_dir = os.path.split(os.path.dirname(self.filename))[1]
            match = re.search('^values-(\w*)', parent_dir)
            if (match is not None):
                target_lang = match.group(1)
            elif (parent_dir == 'values'):
                # If the resource file is inside the "values" directory, then it is the default/source language.
                target_lang = self.sourcelanguage

            # Cache it
            self.settargetlanguage(target_lang)

        return target_lang
