#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2013 Zuza Software Foundation
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

"""Classes that hold units of .dtd files (:class:`dtdunit`) or entire files
(:class:`dtdfile`).

These are specific .dtd files for localisation used by mozilla.

Specifications
    The following information is provided by Mozilla:

    `Specification <http://www.w3.org/TR/REC-xml/#sec-entexpand>`_

    There is a grammar for entity definitions, which isn't really precise,
    as the spec says.  There's no formal specification for DTD files, it's
    just "whatever makes this work" basically. The whole piece is clearly not
    the strongest point of the xml spec

    XML elements are allowed in entity values. A number of things that are
    allowed will just break the resulting document, Mozilla forbids these
    in their DTD parser.

Dialects
    There are two dialects:

    - Regular DTD
    - Android DTD

    Both dialects are similar, but the Android DTD uses some particular escapes
    that regular DTDs don't have.

Escaping in regular DTD
    In DTD usually there are characters escaped in the entities. In order to
    ease the translation some of those escaped characters are unescaped when
    reading from, or converting, the DTD, and that are escaped again when
    saving, or converting to a DTD.

    In regular DTD the following characters are usually or sometimes escaped:

    - The % character is escaped using &#037; or &#37; or &#x25;
    - The " character is escaped using &quot;
    - The ' character is escaped using &apos; (partial roundtrip)
    - The & character is escaped using &amp;
    - The < character is escaped using &lt; (not yet implemented)
    - The > character is escaped using &gt; (not yet implemented)

    Besides the previous ones there are a lot of escapes for a huge number of
    characters. This escapes usually have the form of &#NUMBER; where NUMBER
    represents the numerical code for the character.

    There are a few particularities in DTD escaping. Some of the escapes are
    not yet implemented since they are not really necessary, or because its
    implementation is too hard.

    A special case is the ' escaping using &apos; which doesn't provide a full
    roundtrip conversion in order to support some special Mozilla DTD files.

    Also the " character is never escaped in the case that the previous
    character is = (the sequence =" is present on the string) in order to avoid
    escaping the " character indicating an attribute assignment, for example in
    a href attribute for an a tag in HTML (anchor tag).

Escaping in Android DTD
    It has the sames escapes as in regular DTD, plus this ones:

    - The ' character is escaped using \&apos; or \' or \u0027
    - The " character is escaped using \&quot;
"""

import re
import warnings
from cStringIO import StringIO
try:
    from lxml import etree
except ImportError:
    etree = None

from translate.misc import quote
from translate.storage import base


labelsuffixes = (".label", ".title")
"""Label suffixes: entries with this suffix are able to be comibed with accesskeys
found in in entries ending with :attr:`.accesskeysuffixes`"""
accesskeysuffixes = (".accesskey", ".accessKey", ".akey")
"""Accesskey Suffixes: entries with this suffix may be combined with labels
ending in :attr:`.labelsuffixes` into accelerator notation"""


def quoteforandroid(source):
    """Escapes a line for Android DTD files. """
    # Replace "'" character with the \u0027 escape. Other possible replaces are
    # "\\&apos;" or "\\'".
    source = source.replace(u"'", u"\\u0027")
    source = source.replace(u"\"", u"\\&quot;")
    value = quotefordtd(source)  # value is an UTF-8 encoded string.
    return value


def unquotefromandroid(source):
    """Unquotes a quoted Android DTD definition."""
    value = unquotefromdtd(source)  # value is an UTF-8 encoded string.
    value = value.replace(u"\\&apos;", u"'")
    value = value.replace(u"\\'", u"'")
    value = value.replace(u"\\u0027", u"'")
    value = value.replace("\\\"", "\"")  # This converts \&quot; to ".
    return value


_DTD_CODEPOINT2NAME = {
    ord("%"): "#037",  # Always escape % sign as &#037;.
    ord("&"): "amp",
   #ord("<"): "lt",  # Not really so useful.
   #ord(">"): "gt",  # Not really so useful.
}

def quotefordtd(source):
    """Quotes and escapes a line for regular DTD files."""
    source = quote.entityencode(source, _DTD_CODEPOINT2NAME)
    if '"' in source:
        source = source.replace("'", "&apos;")  # This seems not to runned.
        if '="' not in source:  # Avoid escaping " chars in href attributes.
            source = source.replace("\"", "&quot;")
            value = "\"" + source + "\""  # Quote using double quotes.
        else:
            value = "'" + source + "'"  # Quote using single quotes.
    else:
        value = "\"" + source + "\""  # Quote using double quotes.
    return value.encode('utf-8')


_DTD_NAME2CODEPOINT = {
    "quot":   ord('"'),
    "amp":    ord("&"),
   #"lt":     ord("<"),  # Not really so useful.
   #"gt":     ord(">"),  # Not really so useful.
   # FIXME these should probably be handled in a more general way
    "#x0022": ord('"'),
    "#187":   ord(u"»"),
    "#037":   ord("%"),
    "#37":    ord("%"),
    "#x25":   ord("%"),
}

def unquotefromdtd(source):
    """unquotes a quoted dtd definition"""
    # extract the string, get rid of quoting
    if len(source) == 0:
        source = '""'
    # The quote characters should be the first and last characters in the
    # string. Of course there could also be quote characters within the string.
    quotechar = source[0]
    extracted, quotefinished = quote.extractwithoutquotes(source, quotechar, quotechar, allowreentry=False)
    extracted = extracted.decode('utf-8')
    if quotechar == "'":
        extracted = extracted.replace("&apos;", "'")
    extracted = quote.entitydecode(extracted, _DTD_NAME2CODEPOINT)
    return extracted


def removeinvalidamps(name, value):
    """Find and remove ampersands that are not part of an entity definition.

    A stray & in a DTD file can break an application's ability to parse the
    file. In Mozilla localisation this is very important and these can break the
    parsing of files used in XUL and thus break interface rendering. Tracking
    down the problem is very difficult, thus by removing potential broken
    ampersand and warning the users we can ensure that the output DTD will
    always be parsable.

    :type name: String
    :param name: Entity name
    :type value: String
    :param value: Entity text value
    :rtype: String
    :return: Entity value without bad ampersands
    """

    def is_valid_entity_name(name):
        """Check that supplied *name* is a valid entity name."""
        if name.replace('.', '').replace('_', '').isalnum():
            return True
        elif name[0] == '#' and name[1:].isalnum():
            return True
        return False

    amppos = 0
    invalid_amps = []
    while amppos >= 0:
        amppos = value.find("&", amppos)
        if amppos != -1:
            amppos += 1
            semipos = value.find(";", amppos)
            if semipos != -1:
                if is_valid_entity_name(value[amppos:semipos]):
                    continue
            invalid_amps.append(amppos - 1)
    if len(invalid_amps) > 0:
        warnings.warn("invalid ampersands in dtd entity %s" % (name))
        adjustment = 0
        for amppos in invalid_amps:
            value = value[:amppos-adjustment] + value[amppos-adjustment+1:]
            adjustment += 1
    return value


class dtdunit(base.TranslationUnit):
    """An entity definition from a DTD file (and any associated comments)."""

    def __init__(self, source="", android=False):
        """construct the dtdunit, prepare it for parsing"""
        self.android = android

        super(dtdunit, self).__init__(source)
        self.comments = []
        self.unparsedlines = []
        self.incomment = False
        self.inentity = False
        self.entity = "FakeEntityOnlyForInitialisationAndTesting"
        self.source = source
        self.space_pre_entity = ' '
        self.space_pre_definition = ' '
        self.closing = ">"

    # Note that source and target are equivalent for monolingual units
    def setsource(self, source):
        """Sets the definition to the quoted value of source"""
        if self.android:
            self.definition = quoteforandroid(source)
        else:
            self.definition = quotefordtd(source)
        self._rich_source = None

    def getsource(self):
        """gets the unquoted source string"""
        if self.android:
            return unquotefromandroid(self.definition)
        else:
            return unquotefromdtd(self.definition)
    source = property(getsource, setsource)

    def settarget(self, target):
        """Sets the definition to the quoted value of target"""
        if target is None:
            target = ""
        if self.android:
            self.definition = quoteforandroid(target)
        else:
            self.definition = quotefordtd(target)
        self._rich_target = None

    def gettarget(self):
        """gets the unquoted target string"""
        if self.android:
            return unquotefromandroid(self.definition)
        else:
            return unquotefromdtd(self.definition)
    target = property(gettarget, settarget)

    def getid(self):
        return self.entity

    def setid(self, new_id):
        self.entity = new_id

    def getlocations(self):
        """Return the entity as location (identifier)."""
        assert quote.rstripeol(self.entity) == self.entity
        return [self.entity]

    def addlocation(self, location):
        """Set the entity to the given "location"."""
        self.entity = location

    def isnull(self):
        """returns whether this dtdunit doesn't actually have an entity definition"""
        # for dtds, we currently return a blank string if there is no .entity (==location in other files)
        # TODO: this needs to work better with base class expectations
        return self.entity is None

    def istranslatable(self):
        if getattr(self, "entityparameter", None) == "SYSTEM" or self.isnull():
            return False
        return True

    def parse(self, dtdsrc):
        """read the first dtd element from the source code into this object, return linesprocessed"""
        self.comments = []
        # make all the lists the same
        self._locfilenotes = self.comments
        self._locgroupstarts = self.comments
        self._locgroupends = self.comments
        self._locnotes = self.comments
        # self._locfilenotes = []
        # self._locgroupstarts = []
        # self._locgroupends = []
        # self._locnotes = []
        # self.comments = []
        self.entity = None
        self.definition = ''
        if not dtdsrc:
            return 0
        lines = dtdsrc.split("\n")
        linesprocessed = 0
        comment = ""
        for line in lines:
            line += "\n"
            linesprocessed += 1
            # print "line(%d,%d): " % (self.incomment,self.inentity),line[:-1]
            if not self.incomment:
                if (line.find('<!--') != -1):
                    self.incomment = True
                    self.continuecomment = False
                    # now work out the type of comment, and save it (remember we're not in the comment yet)
                    (comment, dummy) = quote.extract(line, "<!--", "-->", None, 0)
                    if comment.find('LOCALIZATION NOTE') != -1:
                        l = quote.findend(comment, 'LOCALIZATION NOTE')
                        while (comment[l] == ' '):
                            l += 1
                        if comment.find('FILE', l) == l:
                            self.commenttype = "locfile"
                        elif comment.find('BEGIN', l) == l:
                            self.commenttype = "locgroupstart"
                        elif comment.find('END', l) == l:
                            self.commenttype = "locgroupend"
                        else:
                            self.commenttype = "locnote"
                    else:
                        # plain comment
                        self.commenttype = "comment"
                #FIXME: bloody entity might share a line with something important
                elif not self.inentity and re.search("%.*;", line):
                    # now work out the type of comment, and save it (remember we're not in the comment yet)
                    self.comments.append(("comment", line))
                    line = ""
                    continue

            if self.incomment:
                # some kind of comment
                (comment, self.incomment) = quote.extract(line, "<!--", "-->", None, self.continuecomment)
                # print "comment(%d,%d): " % (self.incomment,self.continuecomment),comment
                self.continuecomment = self.incomment
                # strip the comment out of what will be parsed
                line = line.replace(comment, "", 1)
                # add a end of line of this is the end of the comment
                if not self.incomment:
                    if line.isspace():
                        comment += line
                        line = ''
                    else:
                        comment += '\n'
                # check if there's actually an entity definition that's commented out
                # TODO: parse these, store as obsolete messages
                # if comment.find('<!ENTITY') != -1:
                #     # remove the entity from the comment
                #     comment, dummy = quote.extractwithoutquotes(comment, ">", "<!ENTITY", None, 1)
                # depending on the type of comment (worked out at the start), put it in the right place
                # make it record the comment and type as a tuple
                commentpair = (self.commenttype, comment)
                if self.commenttype == "locfile":
                    self._locfilenotes.append(commentpair)
                elif self.commenttype == "locgroupstart":
                    self._locgroupstarts.append(commentpair)
                elif self.commenttype == "locgroupend":
                    self._locgroupends.append(commentpair)
                elif self.commenttype == "locnote":
                    self._locnotes.append(commentpair)
                elif self.commenttype == "comment":
                    self.comments.append(commentpair)

            if not self.inentity and not self.incomment:
                entitypos = line.find('<!ENTITY')
                if entitypos != -1:
                    self.inentity = True
                    beforeentity = line[:entitypos].strip()
                    if beforeentity.startswith("#"):
                        self.hashprefix = beforeentity
                    self.entitypart = "start"
                else:
                    self.unparsedlines.append(line)

            if self.inentity:
                if self.entitypart == "start":
                    # the entity definition
                    e = quote.findend(line, '<!ENTITY')
                    line = line[e:]
                    self.entitypart = "name"
                    self.entitytype = "internal"
                if self.entitypart == "name":
                    s = 0
                    e = 0
                    while (e < len(line) and line[e].isspace()):
                        e += 1
                    self.space_pre_entity = ' ' * (e - s)
                    s = e
                    self.entity = ''
                    if (e < len(line) and line[e] == '%'):
                        self.entitytype = "external"
                        self.entityparameter = ""
                        e += 1
                        while (e < len(line) and line[e].isspace()):
                            e += 1
                    while (e < len(line) and not line[e].isspace()):
                        self.entity += line[e]
                        e += 1
                    s = e

                    assert quote.rstripeol(self.entity) == self.entity
                    while (e < len(line) and line[e].isspace()):
                        e += 1
                    self.space_pre_definition = ' ' * (e - s)
                    if self.entity:
                        if self.entitytype == "external":
                            self.entitypart = "parameter"
                        else:
                            self.entitypart = "definition"
                        # remember the start position and the quote character
                        if e == len(line):
                            self.entityhelp = None
                            e = 0
                            continue
                        elif self.entitypart == "definition":
                            self.entityhelp = (e, line[e])
                            self.instring = False
                if self.entitypart == "parameter":
                    while (e < len(line) and line[e].isspace()):
                        e += 1
                    paramstart = e
                    while (e < len(line) and line[e].isalnum()):
                        e += 1
                    self.entityparameter += line[paramstart:e]
                    while (e < len(line) and line[e].isspace()):
                        e += 1
                    line = line[e:]
                    e = 0
                    if not line:
                        continue
                    if line[0] in ('"', "'"):
                        self.entitypart = "definition"
                        self.entityhelp = (e, line[e])
                        self.instring = False
                if self.entitypart == "definition":
                    if self.entityhelp is None:
                        e = 0
                        while (e < len(line) and line[e].isspace()):
                            e += 1
                        if e == len(line):
                            continue
                        self.entityhelp = (e, line[e])
                        self.instring = False
                    # actually the lines below should remember instring, rather than using it as dummy
                    e = self.entityhelp[0]
                    if (self.entityhelp[1] == "'"):
                        (defpart, self.instring) = quote.extract(line[e:], "'", "'", startinstring=self.instring, allowreentry=False)
                    elif (self.entityhelp[1] == '"'):
                        (defpart, self.instring) = quote.extract(line[e:], '"', '"', startinstring=self.instring, allowreentry=False)
                    else:
                        raise ValueError("Unexpected quote character... %r" % (self.entityhelp[1]))
                    # for any following lines, start at the beginning of the line. remember the quote character
                    self.entityhelp = (0, self.entityhelp[1])
                    self.definition += defpart
                    if not self.instring:
                        self.closing = line[e+len(defpart):].rstrip("\n\r")
                        self.inentity = False
                        break

        # uncomment this line to debug processing
        if 0:
            for attr in dir(self):
                r = repr(getattr(self, attr))
                if len(r) > 60:
                    r = r[:57] + "..."
                self.comments.append(("comment", "self.%s = %s" % (attr, r)))
        return linesprocessed

    def __str__(self):
        """convert to a string. double check that unicode is handled somehow here"""
        source = self.getoutput()
        if isinstance(source, unicode):
            return source.encode(getattr(self, "encoding", "UTF-8"))
        return source

    def getoutput(self):
        """convert the dtd entity back to string form"""
        lines = []
        lines.extend([comment for commenttype, comment in self.comments])
        lines.extend(self.unparsedlines)
        if self.isnull():
            result = "".join(lines)
            return result.rstrip() + "\n"
        # for f in self._locfilenotes: yield f
        # for ge in self._locgroupends: yield ge
        # for gs in self._locgroupstarts: yield gs
        # for n in self._locnotes: yield n
        if len(self.entity) > 0:
            if getattr(self, 'entitytype', None) == 'external':
                entityline = '<!ENTITY % ' + self.entity + ' ' + self.entityparameter + ' ' + self.definition + self.closing
            else:
                entityline = '<!ENTITY' + self.space_pre_entity + self.entity + self.space_pre_definition + self.definition + self.closing
            if getattr(self, 'hashprefix', None):
                entityline = self.hashprefix + " " + entityline
            if isinstance(entityline, unicode):
                entityline = entityline.encode('UTF-8')
            lines.append(entityline + '\n')
        return "".join(lines)


class dtdfile(base.TranslationStore):
    """A .dtd file made up of dtdunits."""
    UnitClass = dtdunit

    def __init__(self, inputfile=None, android=False):
        """construct a dtdfile, optionally reading in from inputfile"""
        base.TranslationStore.__init__(self, unitclass=self.UnitClass)
        self.filename = getattr(inputfile, 'name', '')
        self.android = android
        if inputfile is not None:
            dtdsrc = inputfile.read()
            self.parse(dtdsrc)
            self.makeindex()

    def parse(self, dtdsrc):
        """read the source code of a dtd file in and include them as dtdunits in self.units"""
        start = 0
        end = 0
        lines = dtdsrc.split("\n")
        while end < len(lines):
            if (start == end):
                end += 1
            foundentity = False
            while end < len(lines):
                if end >= len(lines):
                    break
                if lines[end].find('<!ENTITY') > -1:
                    foundentity = True
                if foundentity and re.match("[\"']\s*>", lines[end]):
                    end += 1
                    break
                end += 1
            # print "processing from %d to %d" % (start,end)

            linesprocessed = 1  # to initialise loop
            while linesprocessed >= 1:
                newdtd = dtdunit(android=self.android)
                try:
                    linesprocessed = newdtd.parse("\n".join(lines[start:end]))
                    if linesprocessed >= 1 and (not newdtd.isnull() or newdtd.unparsedlines):
                        self.units.append(newdtd)
                except Exception as e:
                    warnings.warn("%s\nError occured between lines %d and %d:\n%s" % (e, start + 1, end, "\n".join(lines[start:end])))
                start += linesprocessed

    def __str__(self):
        """convert to a string. double check that unicode is handled somehow here"""
        source = self.getoutput()
        if not self._valid_store():
            warnings.warn("DTD file '%s' does not validate" % self.filename)
            return None
        if isinstance(source, unicode):
            return source.encode(getattr(self, "encoding", "UTF-8"))
        return source

    def getoutput(self):
        """convert the units back to source"""
        sources = [str(dtd) for dtd in self.units]
        return "".join(sources)

    def makeindex(self):
        """makes self.id_index dictionary keyed on entities"""
        self.id_index = {}
        for dtd in self.units:
            if not dtd.isnull():
                self.id_index[dtd.entity] = dtd

    def _valid_store(self):
        """Validate the store to determine if it is valid

        This uses ElementTree to parse the DTD

        :return: If the store passes validation
        :rtype: Boolean
        """
        # Android files are invalid DTDs
        if etree is not None and not self.android:
            try:
                # #expand is a Mozilla hack and are removed as they are not valid in DTDs
                dtd = etree.DTD(StringIO(re.sub("#expand", "", self.getoutput())))
            except etree.DTDParseError as e:
                warnings.warn("DTD parse error: %s" % e.error_log)
                return False
        return True
