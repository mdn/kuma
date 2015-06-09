#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2009 Zuza Software Foundation
# Copyright 2013 F Wolff
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

"""Classes that hold units of Gettext .po files (pounit) or entire
files (pofile).
"""

import copy
import re
import textwrap
from cStringIO import StringIO

from translate.lang import data
from translate.misc import quote
from translate.misc.deprecation import deprecated
from translate.misc.multistring import multistring
from translate.storage import base, pocommon, poparser
from translate.storage.pocommon import encodingToUse


lsep = "\n#: "
"""Separator for #: entries"""

# general functions for quoting / unquoting po strings

po_unescape_map = {"\\r": "\r", "\\t": "\t", '\\"': '"', '\\n': '\n', '\\\\': '\\'}
po_escape_map = dict([(value, key) for (key, value) in po_unescape_map.items()])


def escapeforpo(line):
    """Escapes a line for po format. assumes no \n occurs in the line.

    :param line: unescaped text
    """
    special_locations = []
    for special_key in po_escape_map:
        special_locations.extend(quote.find_all(line, special_key))
    special_locations = dict.fromkeys(special_locations).keys()
    special_locations.sort()
    escaped_line = ""
    last_location = 0
    for location in special_locations:
        escaped_line += line[last_location:location]
        escaped_line += po_escape_map[line[location:location+1]]
        last_location = location + 1
    escaped_line += line[last_location:]
    return escaped_line


def unescapehandler(escape):
    return po_unescape_map.get(escape, escape)


wrapper = textwrap.TextWrapper(
        width=77,
        replace_whitespace=False,
        expand_tabs=False,
        drop_whitespace=False
)
wrapper.wordsep_re = re.compile(
    r'(\s+|'                                  # any whitespace
    r'\w*\\.|'                                # any escape should not be split
    r'[\w\!\'\&\.\,\?]+\s+|'                  # space should go with a word
    r'[^\s\w]*\w+[a-zA-Z]-(?=\w+[a-zA-Z])|'   # hyphenated words
    r'(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w))')   # em-dash
wrapper.wordsep_re_uni = re.compile(wrapper.wordsep_re.pattern, re.UNICODE)


def quoteforpo(text):
    """Quotes the given text for a PO file, returning quoted and
    escaped lines"""
    if text is None:
        return []
    text = escapeforpo(text)
    lines = text.split(u"\\n")
    for i, l in enumerate(lines[:-1]):
        lines[i] = l + u"\\n"

    polines = []
    len_lines = len(lines)
    if len_lines > 2 or (len_lines == 2 and lines[1]) or len(lines[0]) > 71:
        polines.append(u'""')
    for line in lines:
        lns = wrapper.wrap(line)
        for ln in lns:
            polines.append(u'"%s"' % ln)
    return polines


@deprecated("Use pypo.unescape() instead")
def extractpoline(line):
    """Remove quote and unescape line from po file.

    :param line: a quoted line from a po file (msgid or msgstr)

    .. deprecated:: 1.10
       Replaced by :func:`unescape`. :func:`extractpoline` is kept to allow
       tests of correctness, and in case of external users.
    """
    extracted = quote.extractwithoutquotes(line, '"', '"', '\\', includeescapes=unescapehandler)[0]
    return extracted


def unescape(line):
    """Unescape the given line.

    Quotes on either side should already have been removed.
    """
    escape_places = quote.find_all(line, u"\\")
    if not escape_places:
        return line

    # filter escaped escapes
    true_escape = False
    true_escape_places = []
    for escape_pos in escape_places:
        if escape_pos - 1 in escape_places:
            true_escape = not true_escape
        else:
            true_escape = True
        if true_escape:
            true_escape_places.append(escape_pos)

    extracted = u""
    lastpos = 0
    for pos in true_escape_places:
        # everything leading up to the escape
        extracted += line[lastpos:pos]
        # the escaped sequence (consuming 2 characters)
        extracted += unescapehandler(line[pos:pos+2])
        lastpos = pos+2

    extracted += line[lastpos:]
    return extracted


def unquotefrompo(postr):
    return u"".join([unescape(line[1:-1]) for line in postr])


def is_null(lst):
    return lst == [] or len(lst) == 1 and lst[0] == '""'


def extractstr(string):
    left = string.find('"')
    right = string.rfind('"')
    if right > -1:
        return string[left:right+1]
    else:
        return string[left:] + '"'


class pounit(pocommon.pounit):
    # othercomments = []      #   # this is another comment
    # automaticcomments = []  #   #. comment extracted from the source code
    # sourcecomments = []     #   #: sourcefile.xxx:35
    # prev_msgctxt = []       #   #| The previous values that msgctxt and msgid held
    # prev_msgid = []         #
    # prev_msgid_plural = []  #
    # typecomments = []       #   #, fuzzy
    # msgidcomments = []      #   _: within msgid
    # msgctxt
    # msgid = []
    # msgstr = []

    # Our homegrown way to indicate what must be copied in a shallow
    # fashion
    __shallow__ = ['_store']

    def __init__(self, source=None, encoding="UTF-8"):
        self._encoding = encodingToUse(encoding)
        self.obsolete = False
        self._initallcomments(blankall=True)
        self.prev_msgctxt = []
        self.prev_msgid = []
        self.prev_msgid_plural = []
        self.msgctxt = []
        self.msgid = []
        self.msgid_pluralcomments = []
        self.msgid_plural = []
        self.msgstr = []
        pocommon.pounit.__init__(self, source)

    def _initallcomments(self, blankall=False):
        """Initialises allcomments"""
        if blankall:
            self.othercomments = []
            self.automaticcomments = []
            self.sourcecomments = []
            self.typecomments = []
            self.msgidcomments = []

    def _get_all_comments(self):
        return [self.othercomments,
                self.automaticcomments,
                self.sourcecomments,
                self.typecomments,
                self.msgidcomments,
                ]

    allcomments = property(_get_all_comments)

    def _get_source_vars(self, msgid, msgid_plural):
        singular = unquotefrompo(msgid)
        if self.hasplural():
            pluralform = unquotefrompo(msgid_plural)
            return multistring([singular, pluralform], self._encoding)
        return singular

    def _set_source_vars(self, source):
        msgid = None
        msgid_plural = None
        if isinstance(source, str):
            source = source.decode(self._encoding)
        if isinstance(source, multistring):
            source = source.strings
        if isinstance(source, list):
            msgid = quoteforpo(source[0])
            if len(source) > 1:
                msgid_plural = quoteforpo(source[1])
            else:
                msgid_plural = []
        else:
            msgid = quoteforpo(source)
            msgid_plural = []
        return msgid, msgid_plural

    def getsource(self):
        """Returns the unescaped msgid"""
        return self._get_source_vars(self.msgid, self.msgid_plural)

    def setsource(self, source):
        """Sets the msgid to the given (unescaped) value.

        :param source: an unescaped source string.
        """
        self._rich_source = None
        self.msgid, self.msgid_plural = self._set_source_vars(source)
    source = property(getsource, setsource)

    def _get_prev_source(self):
        """Returns the unescaped msgid"""
        return self._get_source_vars(self.prev_msgid, self.prev_msgid_plural)

    def _set_prev_source(self, source):
        """Sets the msgid to the given (unescaped) value.

        :param source: an unescaped source string.
        """
        self.prev_msgid, self.prev_msgid_plural = self._set_source_vars(source)
    prev_source = property(_get_prev_source, _set_prev_source)

    def gettarget(self):
        """Returns the unescaped msgstr"""
        if isinstance(self.msgstr, dict):
            return multistring(map(unquotefrompo, self.msgstr.values()), self._encoding)
        else:
            return unquotefrompo(self.msgstr)

    def settarget(self, target):
        """Sets the msgstr to the given (unescaped) value"""
        self._rich_target = None
        if isinstance(target, str):
            target = target.decode(self._encoding)
        if self.hasplural():
            if isinstance(target, multistring):
                target = target.strings
            elif isinstance(target, basestring):
                target = [target]
        elif isinstance(target, (dict, list)):
            if len(target) == 1:
                target = target[0]
            else:
                raise ValueError("po msgid element has no plural but msgstr has %d elements (%s)" % (len(target), target))
        templates = self.msgstr
        if isinstance(templates, list):
            templates = {0: templates}
        if isinstance(target, list):
            self.msgstr = dict([(i, quoteforpo(target[i])) for i in range(len(target))])
        elif isinstance(target, dict):
            self.msgstr = dict([(i, quoteforpo(targetstring)) for i, targetstring in target.iteritems()])
        else:
            self.msgstr = quoteforpo(target)
    target = property(gettarget, settarget)

    def getalttrans(self):
        """Return a list of alternate units.

        Previous msgid and current msgstr is combined to form a single
        alternative unit."""
        prev_source = self.prev_source
        if prev_source and self.isfuzzy():
            unit = type(self)(prev_source)
            unit.target = self.target
            # Already released versions of Virtaal (0.6.x) only supported XLIFF
            # alternatives, and expect .xmlelement.get().
            # This can be removed soon:
            unit.xmlelement = dict()
            return [unit]
        return []

    def getnotes(self, origin=None):
        """Return comments based on origin value.

        :param origin: programmer, developer, source code, translator or None
        """
        if origin is None:
            comments = u"".join([comment[2:] for comment in self.othercomments])
            comments += u"".join([comment[3:] for comment in self.automaticcomments])
        elif origin == "translator":
            comments = u"".join([comment[2:] for comment in self.othercomments])
        elif origin in ["programmer", "developer", "source code"]:
            comments = u"".join([comment[3:] for comment in self.automaticcomments])
        else:
            raise ValueError("Comment type not valid")
        # Let's drop the last newline
        return comments[:-1]

    def addnote(self, text, origin=None, position="append"):
        """This is modeled on the XLIFF method.

        See :meth:`translate.storage.xliff.xliffunit.addnote`
        """
        # ignore empty strings and strings without non-space characters
        if not (text and text.strip()):
            return
        text = data.forceunicode(text)
        commentlist = self.othercomments
        linestart = "# "
        autocomments = False
        if origin in ["programmer", "developer", "source code"]:
            autocomments = True
            commentlist = self.automaticcomments
            linestart = "#. "
        text = text.split("\n")
        newcomments = [linestart + line + "\n" for line in text]
        if position == "append":
            newcomments = commentlist + newcomments
        elif position == "prepend":
            newcomments = newcomments + commentlist

        if autocomments:
            self.automaticcomments = newcomments
        else:
            self.othercomments = newcomments

    def removenotes(self):
        """Remove all the translator's notes (other comments)"""
        self.othercomments = []

    def __deepcopy__(self, memo={}):
        # Make an instance to serve as the copy
        new_unit = self.__class__()
        # We'll be testing membership frequently, so make a set from
        # self.__shallow__
        shallow = set(self.__shallow__)
        # Make deep copies of all members which are not in shallow
        for key, value in self.__dict__.iteritems():
            if key not in shallow:
                setattr(new_unit, key, copy.deepcopy(value))
        # Make shallow copies of all members which are in shallow
        for key in set(shallow):
            setattr(new_unit, key, getattr(self, key))
        # Mark memo with ourself, so that we won't get deep copied
        # again
        memo[id(self)] = self
        # Return our copied unit
        return new_unit

    def copy(self):
        return copy.deepcopy(self)

    def _msgidlen(self):
        if self.hasplural():
            return len(unquotefrompo(self.msgid)) + len(unquotefrompo(self.msgid_plural))
        else:
            return len(unquotefrompo(self.msgid))

    def _msgstrlen(self):
        if isinstance(self.msgstr, dict):
            combinedstr = "\n".join(filter(None, [unquotefrompo(msgstr) for msgstr in self.msgstr.itervalues()]))
            return len(combinedstr)
        else:
            return len(unquotefrompo(self.msgstr))

    def merge(self, otherpo, overwrite=False, comments=True, authoritative=False):
        """Merges the otherpo (with the same msgid) into this one.

        Overwrite non-blank self.msgstr only if overwrite is True
        merge comments only if comments is True
        """

        def mergelists(list1, list2, split=False):
            #decode where necessary
            if unicode in [type(item) for item in list2] + [type(item) for item in list1]:
                for position, item in enumerate(list1):
                    if isinstance(item, str):
                        list1[position] = item.decode("utf-8")
                for position, item in enumerate(list2):
                    if isinstance(item, str):
                        list2[position] = item.decode("utf-8")

            #Determine the newline style of list1
            lineend = ""
            if list1 and list1[0]:
                for candidate in ["\n", "\r", "\n\r"]:
                    if list1[0].endswith(candidate):
                        lineend = candidate
                if not lineend:
                    lineend = ""
            else:
                lineend = "\n"

            #Split if directed to do so:
            if split:
                splitlist1 = []
                splitlist2 = []
                prefix = "#"
                for item in list1:
                    splitlist1.extend(item.split()[1:])
                    prefix = item.split()[0]
                for item in list2:
                    splitlist2.extend(item.split()[1:])
                    prefix = item.split()[0]
                list1.extend(["%s %s%s" % (prefix, item, lineend) for item in splitlist2 if not item in splitlist1])
            else:
                #Normal merge, but conform to list1 newline style
                if list1 != list2:
                    for item in list2:
                        if lineend:
                            item = item.rstrip() + lineend
                        # avoid duplicate comment lines (this might cause some problems)
                        if item not in list1 or len(item) < 5:
                            list1.append(item)
        if not isinstance(otherpo, pounit):
            super(pounit, self).merge(otherpo, overwrite, comments)
            return
        if comments:
            mergelists(self.othercomments, otherpo.othercomments)
            mergelists(self.typecomments, otherpo.typecomments)
            if not authoritative:
                # We don't bring across otherpo.automaticcomments as we
                # consider ourself to be the the authority.  Same applies
                # to otherpo.msgidcomments
                mergelists(self.automaticcomments, otherpo.automaticcomments)
                mergelists(self.msgidcomments, otherpo.msgidcomments)
                mergelists(self.sourcecomments, otherpo.sourcecomments, split=True)
        if not self.istranslated() or overwrite:
            # Remove kde-style comments from the translation (if any).
            if self._extract_msgidcomments(otherpo.target):
                otherpo.target = otherpo.target.replace('_: ' + otherpo._extract_msgidcomments() + '\n', '')
            self.target = otherpo.target
            if self.source != otherpo.source or self.getcontext() != otherpo.getcontext():
                self.markfuzzy()
            else:
                self.markfuzzy(otherpo.isfuzzy())
        elif not otherpo.istranslated():
            if self.source != otherpo.source:
                self.markfuzzy()
        else:
            if self.target != otherpo.target:
                self.markfuzzy()

    def isheader(self):
        #return (self._msgidlen() == 0) and (self._msgstrlen() > 0) and (len(self.msgidcomments) == 0)
        #rewritten here for performance:
        return (is_null(self.msgid)
                        and not is_null(self.msgstr)
                        and self.msgidcomments == []
                        and is_null(self.msgctxt))

    def isblank(self):
        if self.isheader() or len(self.msgidcomments):
            return False
        if (self._msgidlen() == 0) and (self._msgstrlen() == 0) and (is_null(self.msgctxt)):
            return True
        return False
        # TODO: remove:
        # Before, the equivalent of the following was the final return statement:
        # return len(self.source.strip()) == 0

    def hastypecomment(self, typecomment):
        """Check whether the given type comment is present"""
        if not self.typecomments:
            return False
        for tc in self.typecomments:
            # check for word boundaries properly by using a regular expression
            if re.search("\\b%s\\b" % typecomment, tc):
                return True
        return False

    def hasmarkedcomment(self, commentmarker):
        """Check whether the given comment marker is present.

        These should appear as::

                # (commentmarker) ...
        """
        commentmarker = "(%s)" % commentmarker
        for comment in self.othercomments:
            if comment.replace("#", "", 1).strip().startswith(commentmarker):
                return True
        return False

    def settypecomment(self, typecomment, present=True):
        """Alters whether a given typecomment is present"""
        if self.hastypecomment(typecomment) != present:
            typecomments = re.findall(r"\b[-\w]+\b", "\n".join(self.typecomments))
            if present:
                typecomments.append(typecomment)
            else:
                typecomments.remove(typecomment)
            if typecomments:
                typecomments.sort()
                self.typecomments = ["#, %s\n" % ", ".join(typecomments)]
            else:
                self.typecomments = []

    def isfuzzy(self):
        return self.hastypecomment('fuzzy')

    def markfuzzy(self, present=True):
        if present:
            self.set_state_n(self.STATE[self.S_FUZZY][0])
        elif self.hasplural() and not self._msgstrlen() or is_null(self.msgstr):
            self.set_state_n(self.STATE[self.S_UNTRANSLATED][0])
        else:
            self.set_state_n(self.STATE[self.S_TRANSLATED][0])
        self._domarkfuzzy(present)

    def _domarkfuzzy(self, present=True):
        self.settypecomment("fuzzy", present)

    def infer_state(self):
        if self.obsolete:
            self.makeobsolete()
        else:
            self.markfuzzy(self.hastypecomment('fuzzy'))

    def isobsolete(self):
        return self.obsolete

    def makeobsolete(self):
        """Makes this unit obsolete"""
        super(pounit, self).makeobsolete()
        self.obsolete = True
        self.sourcecomments = []
        self.automaticcomments = []

    def resurrect(self):
        """Makes an obsolete unit normal"""
        super(pounit, self).resurrect()
        self.obsolete = False

    def hasplural(self):
        """returns whether this pounit contains plural strings..."""
        return len(self.msgid_plural) > 0

    def parse(self, src):
        return poparser.parse_unit(poparser.ParseState(StringIO(src), pounit), self)

    def _getmsgpartstr(self, partname, partlines, partcomments=""):
        if isinstance(partlines, dict):
            partkeys = partlines.keys()
            partkeys.sort()
            return "".join([self._getmsgpartstr("%s[%d]" % (partname, partkey), partlines[partkey], partcomments) for partkey in partkeys])
        partstr = partname + " "
        partstartline = 0
        if len(partlines) > 0 and len(partcomments) == 0:
            partstr += partlines[0]
            partstartline = 1
        elif len(partcomments) > 0:
            if len(partlines) > 0 and len(unquotefrompo(partlines[:1])) == 0:
                # if there is a blank leader line, it must come before the comment
                partstr += partlines[0] + '\n'
                # but if the whole string is blank, leave it in
                if len(partlines) > 1:
                    partstartline += 1
            else:
                # All partcomments should start on a newline
                partstr += '""\n'
            # combine comments into one if more than one
            if len(partcomments) > 1:
                combinedcomment = []
                for comment in partcomments:
                    comment = unquotefrompo([comment])
                    if comment.startswith("_:"):
                        comment = comment[len("_:"):]
                    if comment.endswith("\\n"):
                        comment = comment[:-len("\\n")]
                    #Before we used to strip. Necessary in some cases?
                    combinedcomment.append(comment)
                partcomments = quoteforpo("_:%s" % "".join(combinedcomment))
            # comments first, no blank leader line needed
            partstr += "\n".join(partcomments)
            partstr = quote.rstripeol(partstr)
        else:
            partstr += '""'
        partstr += '\n'
        # add the rest
        for partline in partlines[partstartline:]:
            partstr += partline + '\n'
        return partstr

    def _encodeifneccessary(self, output):
        """Encodes unicode strings and returns other strings unchanged"""
        if isinstance(output, unicode):
            encoding = encodingToUse(getattr(self, "_encoding", "UTF-8"))
            return output.encode(encoding)
        return output

    def __str__(self):
        """Convert to a string. Double check that unicode is handled
        somehow here"""
        output = self._getoutput()
        return self._encodeifneccessary(output)

    def _getoutput(self):
        """return this po element as a string"""

        def add_prev_msgid_lines(lines, prefix, header, var):
            if len(var) > 0:
                lines.append("%s %s %s\n" % (prefix, header, var[0]))
                lines.extend("%s %s\n" % (prefix, line) for line in var[1:])

        def add_prev_msgid_info(lines, prefix):
            add_prev_msgid_lines(lines, prefix, 'msgctxt', self.prev_msgctxt)
            add_prev_msgid_lines(lines, prefix, 'msgid', self.prev_msgid)
            add_prev_msgid_lines(lines, prefix, 'msgid_plural', self.prev_msgid_plural)

        lines = []
        lines.extend(self.othercomments)
        if self.isobsolete():
            lines.extend(self.typecomments)
            obsoletelines = []
            add_prev_msgid_info(obsoletelines, prefix="#~|")
            if self.msgctxt:
                obsoletelines.append(self._getmsgpartstr("#~ msgctxt", self.msgctxt))
            obsoletelines.append(self._getmsgpartstr("#~ msgid", self.msgid, self.msgidcomments))
            if self.msgid_plural or self.msgid_pluralcomments:
                obsoletelines.append(self._getmsgpartstr("#~ msgid_plural", self.msgid_plural, self.msgid_pluralcomments))
            obsoletelines.append(self._getmsgpartstr("#~ msgstr", self.msgstr))
            for index, obsoleteline in enumerate(obsoletelines):
                # We need to account for a multiline msgid or msgstr here
                obsoletelines[index] = obsoleteline.replace('\n"', '\n#~ "')
            lines.extend(obsoletelines)
            return u"".join(lines)
        # if there's no msgid don't do msgid and string, unless we're the
        # header this will also discard any comments other than plain
        # othercomments...
        if is_null(self.msgid):
            if not (self.isheader() or self.getcontext() or self.sourcecomments):
                return u"".join(lines)
        lines.extend(self.automaticcomments)
        lines.extend(self.sourcecomments)
        lines.extend(self.typecomments)
        add_prev_msgid_info(lines, prefix="#|")
        if self.msgctxt:
            lines.append(self._getmsgpartstr(u"msgctxt", self.msgctxt))
        lines.append(self._getmsgpartstr(u"msgid", self.msgid, self.msgidcomments))
        if self.msgid_plural or self.msgid_pluralcomments:
            lines.append(self._getmsgpartstr(u"msgid_plural", self.msgid_plural, self.msgid_pluralcomments))
        lines.append(self._getmsgpartstr(u"msgstr", self.msgstr))
        postr = u"".join(lines)
        return postr

    def getlocations(self):
        """Get a list of locations from sourcecomments in the PO unit

        rtype: List
        return: A list of the locations with '#: ' stripped

        """
        locations = []
        for sourcecomment in self.sourcecomments:
            locations += quote.rstripeol(sourcecomment)[3:].split()
        for i, loc in enumerate(locations):
            locations[i] = pocommon.unquote_plus(loc)
        return locations

    def addlocation(self, location):
        """Add a location to sourcecomments in the PO unit

        :param location: Text location e.g. 'file.c:23' does not include #:
        :type location: String

        """
        location = data.forceunicode(location)
        if location.find(" ") != -1:
            location = pocommon.quote_plus(location)
        self.sourcecomments.append("#: %s\n" % location)

    def _extract_msgidcomments(self, text=None):
        """Extract KDE style msgid comments from the unit.

        :rtype: String
        :return: Returns the extracted msgidcomments found in this
                 unit's msgid.
        """

        if not text:
            text = unquotefrompo(self.msgidcomments)
        return text.split('\n')[0].replace('_: ', '', 1)

    def setmsgidcomment(self, msgidcomment):
        if msgidcomment:
            self.msgidcomments = ['"_: %s\\n"' % msgidcomment]
        else:
            self.msgidcomments = []

    msgidcomment = property(_extract_msgidcomments, setmsgidcomment)

    def getcontext(self):
        """Get the message context."""
        return unquotefrompo(self.msgctxt) + self._extract_msgidcomments()

    def setcontext(self, context):
        context = data.forceunicode(context)
        self.msgctxt = quoteforpo(context)

    def getid(self):
        """Returns a unique identifier for this unit."""
        context = self.getcontext()
        # Gettext does not consider the plural to determine duplicates, only
        # the msgid. For generation of .mo files, we might want to use this
        # code to generate the entry for the hash table, but for now, it is
        # commented out for conformance to gettext.
#        id = '\0'.join(self.source.strings)
        id = self.source
        if self.msgidcomments:
            id = u"_: %s\n%s" % (context, id)
        elif context:
            id = u"%s\04%s" % (context, id)
        return id


class pofile(pocommon.pofile):
    """A .po file containing various units"""
    UnitClass = pounit

    def parse(self, input):
        """Parses the given file or file source string."""
        if True:
            if hasattr(input, 'name'):
                self.filename = input.name
            elif not getattr(self, 'filename', ''):
                self.filename = ''
            if isinstance(input, str):
                input = StringIO(input)
            # clear units to get rid of automatically generated headers before parsing
            self.units = []
            poparser.parse_units(poparser.ParseState(input, pounit), self)

    def removeduplicates(self, duplicatestyle="merge"):
        """Make sure each msgid is unique ; merge comments etc from
        duplicates into original"""
        # TODO: can we handle consecutive calls to removeduplicates()? What
        # about files already containing msgctxt? - test
        id_dict = {}
        uniqueunits = []
        # TODO: this is using a list as the pos aren't hashable, but this is slow.
        # probably not used frequently enough to worry about it, though.
        markedpos = []

        def addcomment(thepo):
            thepo.msgidcomments.append('"_: %s\\n"' % " ".join(thepo.getlocations()))
            markedpos.append(thepo)
        for thepo in self.units:
            id = thepo.getid()
            if thepo.isheader() and not thepo.getlocations():
                # header msgids shouldn't be merged...
                uniqueunits.append(thepo)
            elif id in id_dict:
                if duplicatestyle == "merge":
                    if id:
                        id_dict[id].merge(thepo)
                    else:
                        addcomment(thepo)
                        uniqueunits.append(thepo)
                elif duplicatestyle == "msgctxt":
                    origpo = id_dict[id]
                    if origpo not in markedpos and id:
                        # if it doesn't have an id, we already added msgctxt
                        origpo.msgctxt.append('"%s"' % escapeforpo(" ".join(origpo.getlocations())))
                        markedpos.append(thepo)
                    thepo.msgctxt.append('"%s"' % escapeforpo(" ".join(thepo.getlocations())))
                    uniqueunits.append(thepo)
            else:
                if not id:
                    if duplicatestyle == "merge":
                        addcomment(thepo)
                    else:
                        thepo.msgctxt.append('"%s"' % escapeforpo(" ".join(thepo.getlocations())))
                id_dict[id] = thepo
                uniqueunits.append(thepo)
        self.units = uniqueunits

    def __str__(self):
        """Convert to a string. Double check that unicode is handled somehow
        here"""
        output = self._getoutput()
        if isinstance(output, unicode):
            try:
                return output.encode(getattr(self, "_encoding", "UTF-8"))
            except UnicodeEncodeError as e:
                self.updateheader(add=True, Content_Type="text/plain; charset=UTF-8")
                self._encoding = "UTF-8"
                for unit in self.units:
                    unit._encoding = "UTF-8"
                return self._getoutput().encode("UTF-8")

        return output

    def _getoutput(self):
        """convert the units back to lines"""
        lines = []
        for unit in self.units:
            unitsrc = unit._getoutput() + u"\n"
            lines.append(unitsrc)
        lines = u"".join(lines).rstrip()
        #After the last pounit we will have \n\n and we only want to end in \n:
        if lines:
            lines += u"\n"
        return lines

    def encode(self, lines):
        """encode any unicode strings in lines in self._encoding"""
        newlines = []
        encoding = self._encoding
        if encoding is None or encoding.lower() == "charset":
            encoding = 'UTF-8'
        for line in lines:
            if isinstance(line, unicode):
                line = line.encode(encoding)
            newlines.append(line)
        return newlines

    def decode(self, lines):
        """decode any non-unicode strings in lines with self._encoding"""
        newlines = []
        for line in lines:
            if (isinstance(line, str) and self._encoding is not None and
                self._encoding.lower() != "charset"):
                try:
                    line = line.decode(self._encoding)
                except UnicodeError as e:
                    raise UnicodeError("Error decoding line with encoding %r: %s. Line is %r" %
                                       (self._encoding, e, line))
            newlines.append(line)
        return newlines

    def unit_iter(self):
        for unit in self.units:
            if not (unit.isheader() or unit.isobsolete()):
                yield unit
