#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2006,2008 Zuza Software Foundation
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

"""module for parsing html files for translation"""

import re
from translate.storage import base
from HTMLParser import HTMLParser

class htmlunit(base.TranslationUnit):
    """A unit of translatable/localisable HTML content"""
    def __init__(self, source=None):
        self.locations = []
        self.setsource(source)

    def getsource(self):
        #TODO: Rethink how clever we should try to be with html entities.
        return self.text.replace("&amp;", "&").replace("&lt;", "<").replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    
    def setsource(self, source):
        self.text = source.replace("&", "&amp;").replace("<", "&lt;")
    source = property(getsource, setsource)

    def addlocation(self, location):
        self.locations.append(location)

    def getlocations(self):
        return self.locations


class htmlfile(HTMLParser, base.TranslationStore):
    UnitClass = htmlunit
    markingtags = ["p", "title", "h1", "h2", "h3", "h4", "h5", "h6", "th", "td", "div", "li", "dt", "dd", "address", "caption"]
    markingattrs = []
    includeattrs = ["alt", "summary", "standby", "abbr", "content"]

    def __init__(self, includeuntaggeddata=None, inputfile=None):
        self.units = []
        self.filename = getattr(inputfile, 'name', None) 
        self.currentblock = ""
        self.currentblocknum = 0
        self.currentcomment = ""
        self.currenttag = None
        self.includeuntaggeddata = includeuntaggeddata
        HTMLParser.__init__(self)

        if inputfile is not None:
            htmlsrc = inputfile.read()
            inputfile.close()
            self.parse(htmlsrc)

    def guess_encoding(self, htmlsrc):
        """Returns the encoding of the html text.

        We look for 'charset=' within a meta tag to do this.
        """

        pattern = '''(?i)<meta.*content.*=.*charset.*=\\s*([^\\s]*)\\s*["']'''
        result = re.findall(pattern, htmlsrc)
        encoding = None
        if result:
            encoding = result[0]
        return encoding

    def do_encoding(self, htmlsrc):
        """Return the html text properly encoded based on a charset."""
        charset = self.guess_encoding(htmlsrc)
        if charset:
            return htmlsrc.decode(charset)
        else:
            return htmlsrc

    def phprep(self, text):
        """Replaces all instances of PHP with placeholder tags, and returns
        the new text and a dictionary of tags.  The current implementation
        replaces <?foo?> with <?md5(foo)?>.  The hash => code conversions
        are stored in self.phpdict for later use in restoring the real PHP.

        The purpose of this is to remove all potential "tag-like" code from
        inside PHP.  The hash looks nothing like an HTML tag, but the following
        PHP::
          $a < $b ? $c : ($d > $e ? $f : $g)
        looks like it contains an HTML tag::
          < $b ? $c : ($d >
        to nearly any regex.  Hence, we replace all contents of PHP with simple
        strings to help our regexes out.

        """

        from translate.misc import hash

        self.phpdict = {}
        result = re.findall('(?s)<\?(.*?)\?>', text)
        for cmd in result:
            h = hash.md5_f(cmd).hexdigest()
            self.phpdict[h] = cmd
            text = text.replace(cmd, h)
        return text

    def reintrophp(self, text):
        """Replaces the PHP placeholders in text with the real code"""
        for hash, code in self.phpdict.items():
            text = text.replace(hash, code) 
        return text

    def parse(self, htmlsrc):
        htmlsrc = self.do_encoding(htmlsrc)
        htmlsrc = self.phprep(htmlsrc) #Clear out the PHP before parsing
        self.feed(htmlsrc)

    def addhtmlblock(self, text):
        text = self.strip_html(text)
        text = self.reintrophp(text) #Before adding anything, restore PHP
        if self.has_translatable_content(text):
            self.currentblocknum += 1
            unit = self.addsourceunit(text)
            unit.addlocation("%s:%d" % (self.filename, self.currentblocknum))
            unit.addnote(self.currentcomment)

    def strip_html(self, text):
        """Strip unnecessary html from the text.

        HTML tags are deemed unnecessary if it fully encloses the translatable
        text, eg. '<a href="index.html">Home Page</a>'.

        HTML tags that occurs within the normal flow of text will not be removed,
        eg. 'This is a link to the <a href="index.html">Home Page</a>.'
        """
        text = text.strip()

        # If all that is left is PHP, return ""
        result = re.findall('(?s)^<\?.*?\?>$', text)
        if len(result) == 1:
            return "" 

        # These two patterns are the same; the first one is more concise...
        #pattern = '(?s)^<[^?>](?:(?:[^>]|(?:<\?.*?\?>))*[^?>])?>(.*)</.*[^?]>$'
        pattern = re.compile(r'''
        (?s)^       # We allow newlines, and match start of line
        <[^?>]      # Match start of tag and the first character (not ? or >)
        (?:
          (?:
            [^>]    # Anything that's not a > is valid tag material
              |     
            (?:<\?.*?\?>) # Matches <? foo ?> lazily; PHP is valid
          )*        # Repeat over valid tag material 
          [^?>]     # If we have > 1 char, the last char can't be ? or >
        )?          # The repeated chars are optional, so that <a>, <p> work 
        >           # Match ending > of opening tag

        (.*)        # Match actual contents of tag

        </.*[^?]>   # Match ending tag; can't end with ?> and must be >=1 char 
        $           # Match end of line
        ''', re.VERBOSE)
        result = re.findall(pattern, text)
        if len(result) == 1:
            text = self.strip_html(result[0])
        return text

    def has_translatable_content(self, text):
        """Check if the supplied HTML snippet has any content that needs to be translated."""

        text = text.strip()
        result = re.findall('(?i).*(charset.*=.*)', text)
        if len(result) == 1:
            return False

        # TODO: Get a better way to find untranslatable entities.
        if text == '&nbsp;':
            return False

        pattern = '<\?.*?\?>' # Lazily strip all PHP
        result = re.sub(pattern, '', text).strip()
        pattern = '<[^>]*>' #Strip all HTML tags
        result = re.sub(pattern, '', result).strip()
        if result:
            return True
        else:
            return False

#From here on below, follows the methods of the HTMLParser

    def startblock(self, tag):
        self.addhtmlblock(self.currentblock)
        self.currentblock = ""
        self.currentcomment = ""
        self.currenttag = tag

    def endblock(self):
        self.addhtmlblock(self.currentblock)
        self.currentblock = ""
        self.currentcomment = ""
        self.currenttag = None

    def handle_starttag(self, tag, attrs):
        newblock = 0
        if tag in self.markingtags:
            newblock = 1
        for attrname, attrvalue in attrs:
            if attrname in self.markingattrs:
                newblock = 1
            if attrname in self.includeattrs:
                self.addhtmlblock(attrvalue)

        if newblock:
            self.startblock(tag)
        elif self.currenttag is not None:
            self.currentblock += self.get_starttag_text()

    def handle_startendtag(self, tag, attrs):
        for attrname, attrvalue in attrs:
            if attrname in self.includeattrs:
                self.addhtmlblock(attrvalue)
        if self.currenttag is not None:
            self.currentblock += self.get_starttag_text()

    def handle_endtag(self, tag):
        if tag == self.currenttag:
            self.endblock()
        elif self.currenttag is not None: 
            self.currentblock += '</%s>' % tag

    def handle_data(self, data):
        if self.currenttag is not None:
            self.currentblock += data
        elif self.includeuntaggeddata:
            self.startblock(None)
            self.currentblock += data

    def handle_charref(self, name):
        self.handle_data("&#%s;" % name)

    def handle_entityref(self, name):
        self.handle_data("&%s;" % name)

    def handle_comment(self, data):
        # we can place comments above the msgid as translator comments!
        if self.currentcomment == "":
            self.currentcomment = data
        else:
            self.currentcomment += '\n' + data

    def handle_pi(self, data):
        self.handle_data("<?%s>" % data)

class POHTMLParser(htmlfile):
    pass

