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
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#

"""module for parsing html files for translation"""

import re

from six.moves import html_parser
from six.moves.html_entities import name2codepoint

from translate.storage import base
from translate.storage.base import ParseError


# Override the piclose tag from simple > to ?> otherwise we consume HTML
# within the processing instructions
html_parser.piclose = re.compile('\?>')


strip_html_re = re.compile(r'''
(?s)^       # We allow newlines, and match start of line
<(?P<tag>[^\s?>]+)  # Match start of tag and the first character (not ? or >)
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

</(?P=tag)>   # Match ending tag; can't end with ?> and must be >=1 char
$           # Match end of line
''', re.VERBOSE)


def strip_html(text):
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

    result = strip_html_re.findall(text)
    if len(result) == 1:
        text = strip_html(result[0][1])
    return text


normalize_re = re.compile("\s\s+")


def normalize_html(text):
    """Remove double spaces from HTML snippets"""
    return normalize_re.sub(" ", text)


def safe_escape(html):
    """Escape &, < and >"""
    # FIXME we need to relook at these.  Escaping to cleanup htmlentity codes
    # is important but we can't mix "<code>&lt;".  In these cases we should
    # then abort the escaping
    return re.sub("&(?![a-zA-Z0-9]+;)", "&amp;", html)


class htmlunit(base.TranslationUnit):
    """A unit of translatable/localisable HTML content"""

    def __init__(self, source=None):
        self.locations = []
        self.setsource(source)

    def getsource(self):
        #TODO: Rethink how clever we should try to be with html entities.
        text = self._text.replace("&amp;", "&")
        text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
        return text

    def setsource(self, source):
        self._rich_source = None
        self._text = safe_escape(source)
    source = property(getsource, setsource)

    def addlocation(self, location):
        self.locations.append(location)

    def getlocations(self):
        return self.locations


class htmlfile(html_parser.HTMLParser, base.TranslationStore):
    UnitClass = htmlunit

    MARKINGTAGS = [
        "address",
        "caption",
        "div",
        "dt", "dd",
        "figcaption",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "li",
        "p",
        "pre",
        "title",
        "th", "td",
    ]
    """Text in these tags that will be extracted from the HTML document"""

    MARKINGATTRS = []
    """Text from tags with these attributes will be extracted from the HTML
    document"""

    INCLUDEATTRS = [
        "alt",
        "abbr",
        "content",
        "standby",
        "summary",
        "title"
    ]
    """Text from these attributes are extracted"""

    SELF_CLOSING_TAGS = [
        u"area",
        u"base",
        u"basefont",
        u"br",
        u"col",
        u"frame",
        u"hr",
        u"img",
        u"input",
        u"link",
        u"meta",
        u"param",
    ]
    """HTML self-closing tags.  Tags that should be specified as <img /> but
    might be <img>.
    `Reference <http://learnwebsitemaking.com/htmlselfclosingtags.html>`_"""

    def __init__(self, includeuntaggeddata=None, inputfile=None,
                 callback=None):
        self.units = []
        self.filename = getattr(inputfile, 'name', None)
        self.currentblock = u""
        self.currentcomment = u""
        self.currenttag = None
        self.currentpos = -1
        self.tag_path = []
        self.filesrc = u""
        self.currentsrc = u""
        self.pidict = {}
        if callback is None:
            self.callback = self._simple_callback
        else:
            self.callback = callback
        self.includeuntaggeddata = includeuntaggeddata
        html_parser.HTMLParser.__init__(self)

        if inputfile is not None:
            htmlsrc = inputfile.read()
            inputfile.close()
            self.parse(htmlsrc)

    def _simple_callback(self, string):
        return string

    ENCODING_RE = re.compile('''<meta.*
                                content.*=.*?charset.*?=\s*?
                                ([^\s]*)
                                \s*?["']\s*?>
                             ''', re.VERBOSE | re.IGNORECASE)

    def guess_encoding(self, htmlsrc):
        """Returns the encoding of the html text.

        We look for 'charset=' within a meta tag to do this.
        """

        result = self.ENCODING_RE.findall(htmlsrc)
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
            return htmlsrc.decode('utf-8')

    def pi_escape(self, text):
        """Replaces all instances of process instruction with placeholders,
        and returns the new text and a dictionary of tags.  The current
        implementation replaces <?foo?> with <?md5(foo)?>.  The hash => code
        conversions are stored in self.pidict for later use in restoring the
        real PHP.

        The purpose of this is to remove all potential "tag-like" code from
        inside PHP.  The hash looks nothing like an HTML tag, but the following
        PHP::
          $a < $b ? $c : ($d > $e ? $f : $g)
        looks like it contains an HTML tag::
          < $b ? $c : ($d >
        to nearly any regex.  Hence, we replace all contents of PHP with simple
        strings to help our regexes out.

        """
        result = re.findall('(?s)<\?(.*?)\?>', text)
        for pi in result:
            pi_escaped = pi.replace("<", "%lt;").replace(">", "%gt;")
            self.pidict[pi_escaped] = pi
            text = text.replace(pi, pi_escaped)
        return text

    def pi_unescape(self, text):
        """Replaces the PHP placeholders in text with the real code"""
        for pi_escaped, pi in self.pidict.items():
            text = text.replace(pi_escaped, pi)
        return text

    def parse(self, htmlsrc):
        htmlsrc = self.do_encoding(htmlsrc)
        htmlsrc = self.pi_escape(htmlsrc)  # Clear out the PHP before parsing
        self.feed(htmlsrc)

    def addhtmlblock(self, text):
        text = strip_html(text)
        text = self.pi_unescape(text)  # Before adding anything, restore PHP
        text = normalize_html(text)
        if self.has_translatable_content(text):
            unit = self.addsourceunit(text)
            unit.addlocation("%s+%s:%d" %
                              (self.filename, ".".join(self.tag_path),
                               self.currentpos))
            unit.addnote(self.currentcomment)

    def has_translatable_content(self, text):
        """Check if the supplied HTML snippet has any content that needs to be
        translated."""

        text = text.strip()
        result = re.findall('(?i).*(charset.*=.*)', text)
        if len(result) == 1:
            return False

        # TODO: Get a better way to find untranslatable entities.
        if text == '&nbsp;':
            return False

        pattern = '<\?.*?\?>'  # Lazily strip all PHP
        result = re.sub(pattern, '', text).strip()
        pattern = '<[^>]*>'  # Strip all HTML tags
        result = re.sub(pattern, '', result).strip()
        if result:
            return True
        else:
            return False

    def buildtag(self, tag, attrs=None, startend=False):
        """Create an HTML tag"""
        selfclosing = u""
        if startend:
            selfclosing = u" /"
        if attrs != [] and attrs is not None:
            return u"<%(tag)s %(attrs)s%(selfclosing)s>" % \
                    {"tag": tag,
                     "attrs": " ".join(['%s="%s"' % pair for pair in attrs]),
                     "selfclosing": selfclosing}
        else:
            return u"<%(tag)s%(selfclosing)s>" % {"tag": tag,
                                                  "selfclosing": selfclosing}

#From here on below, follows the methods of the HTMLParser

    def startblock(self, tag, attrs=None):
        self.addhtmlblock(self.currentblock)
        if self.callback(normalize_html(strip_html(self.currentsrc))):
            self.filesrc += self.currentsrc.replace(strip_html(self.currentsrc),
                                                    self.callback(normalize_html(strip_html(self.currentsrc)).replace("\n", " ")))
        else:
            self.filesrc += self.currentsrc
        self.currentblock = ""
        self.currentcomment = ""
        self.currenttag = tag
        self.currentpos = self.getpos()[0]
        self.currentsrc = self.buildtag(tag, attrs)

    def endblock(self):
        self.addhtmlblock(self.currentblock)
        if self.callback(normalize_html(strip_html(self.currentsrc))) is not None:
            self.filesrc += self.currentsrc.replace(strip_html(self.currentsrc),
                                                    self.callback(normalize_html(strip_html(self.currentsrc).replace("\n", " "))))
        else:
            self.filesrc += self.currentsrc
        self.currentblock = ""
        self.currentcomment = ""
        self.currenttag = None
        self.currentpos = -1
        self.currentsrc = ""

    def handle_starttag(self, tag, attrs):
        newblock = False
        if self.tag_path != [] \
           and self.tag_path[-1:][0] in self.SELF_CLOSING_TAGS:
            self.tag_path.pop()
        self.tag_path.append(tag)
        if tag in self.MARKINGTAGS:
            newblock = True
        for i, attr in enumerate(attrs):
            attrname, attrvalue = attr
            if attrname in self.MARKINGATTRS:
                newblock = True
            if attrname in self.INCLUDEATTRS and self.currentblock == "":
                self.addhtmlblock(attrvalue)
                attrs[i] = (attrname,
                            self.callback(normalize_html(attrvalue).replace("\n", " ")))

        if newblock:
            self.startblock(tag, attrs)
        elif self.currenttag is not None:
            self.currentblock += self.get_starttag_text()
            self.currentsrc += self.get_starttag_text()
        else:
            self.filesrc += self.buildtag(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        for i, attr in enumerate(attrs):
            attrname, attrvalue = attr
            if attrname in self.INCLUDEATTRS and self.currentblock == "":
                self.addhtmlblock(attrvalue)
                attrs[i] = (attrname,
                            self.callback(normalize_html(attrvalue).replace("\n", " ")))
        if self.currenttag is not None:
            self.currentblock += self.get_starttag_text()
            self.currentsrc += self.get_starttag_text()
        else:
            self.filesrc += self.buildtag(tag, attrs, startend=True)

    def handle_endtag(self, tag):
        if tag == self.currenttag:
            self.currentsrc += "</%(tag)s>" % {"tag": tag}
            self.endblock()
        elif self.currenttag is not None:
            self.currentblock += '</%s>' % tag
            self.currentsrc += '</%s>' % tag
        else:
            self.filesrc += '</%s>' % tag
        try:
            popped = self.tag_path.pop()
        except IndexError:
            raise ParseError("Mismatched tags: no more tags: line %s" %
                             self.getpos()[0])
        while popped in self.SELF_CLOSING_TAGS:
            popped = self.tag_path.pop()
        if popped != tag:
            raise ParseError("Mismatched closing tag: "
                             "expected '%s' got '%s' at line %s" %
                             (popped, tag, self.getpos()[0]))

    def handle_data(self, data):
        if self.currenttag is not None:
            self.currentblock += data
            self.currentsrc += self.callback(data)
        elif self.includeuntaggeddata:
            self.startblock(None)
            self.currentblock += data
            self.currentsrc += data
        else:
            self.filesrc += self.callback(data)

    def handle_charref(self, name):
        """Handle entries in the form &#NNNN; e.g. &#8417;"""
        self.handle_data(unichr(int(name)))

    def handle_entityref(self, name):
        """Handle named entities of the form &aaaa; e.g. &rsquo;"""
        if name in ['gt', 'lt', 'amp']:
            self.handle_data("&%s;" % name)
        else:
            self.handle_data(unichr(name2codepoint.get(name, u"&%s;" % name)))

    def handle_comment(self, data):
        # we can place comments above the msgid as translator comments!
        if self.currentcomment == "":
            self.currentcomment = data
        else:
            self.currentcomment += u'\n' + data
        self.filesrc += "<!--%s-->" % data

    def handle_pi(self, data):
        self.handle_data("<?%s?>" % self.pi_unescape(data))


class POHTMLParser(htmlfile):
    pass
