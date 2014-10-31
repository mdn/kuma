#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2006 Zuza Software Foundation
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

"""classes that hold units of .properties files (propunit) or entire files
   (propfile) these files are used in translating Mozilla and other software

   The following U{.properties file
   description<http://java.sun.com/j2se/1.4.2/docs/api/java/util/Properties.html#load(java.io.InputStream)>}
   and U{example <http://www.exampledepot.com/egs/java.util/Props.html>} give some
   good references to the .properties specification.

   Properties file may also hold Java
   U{MessageFormat<http://java.sun.com/j2se/1.4.2/docs/api/java/text/MessageFormat.html>} 
   messages.  No special handling is provided in this storage class for MessageFormat,
   but this may be implemented in future.

   Implementation
   ==============
   A simple summary of what is permissible follows.

   Comments::
     # a comment
     ! a comment

   Name and Value pairs::
     # Note that the b and c are escaped for epydoc rendering
     a = a string
     d.e.f = another string
     b = a string with escape sequences \\t \\n \\r \\\\ \\" \\' \\ (space) \u0123
     c = a string with a continuation line \\
         continuation line
"""

from translate.storage import base
from translate.misc import quote
from translate.lang import data
import re

# the rstripeols convert dos <-> unix nicely as well
# output will be appropriate for the platform

eol = "\n"

def find_delimeter(line):
    """Find the type and position of the delimeter in a property line.

    Property files can be delimeted by "=", ":" or whitespace (space for now).
    We find the position of each delimeter, then find the one that appears 
    first.

    @param line: A properties line
    @type line: str
    @return: Delimeter character and offset within L{line}
    @rtype: Tuple (Delimeter char, Offset Integer)
    """
    delimeters = {"=": -1, ":": -1, " ": -1}
    # Find the position of each delimeter type
    for delimeter, pos in delimeters.iteritems():
        prewhitespace = len(line) - len(line.lstrip())
        pos = line.find(delimeter, prewhitespace)
        while pos != -1:
            if delimeters[delimeter] == -1 and line[pos-1] != "\\":
                delimeters[delimeter] = pos
                break
            pos = line.find(delimeter, pos+1)
    # Find the first "=" or ":" delimeter
    mindelimeter = None
    minpos = -1
    for delimeter, pos in delimeters.iteritems():
        if pos == -1 or delimeter == " ":
            continue
        if minpos == -1 or pos < minpos:
            minpos = pos
            mindelimeter = delimeter
    if mindelimeter is None and delimeters[" "] != -1:
        # Use space delimeter if we found nothing else
        return (" ", delimeters[" "])
    if mindelimeter is not None and delimeters[" "] < delimeters[mindelimeter]:
        # If space delimeter occurs earlier then ":" or "=" then it is the 
        # delimeter only if there are non-whitespace characters between it and
        # the other detected delimeter.
        if len(line[delimeters[" "]:delimeters[mindelimeter]].strip()) > 0:
            return (" ", delimeters[" "])
    return (mindelimeter, minpos)

def is_line_continuation(line):
    """Determine whether L{line} has a line continuation marker.

    .properties files can be terminated with a backslash (\\) indicating
    that the 'value' continues on the next line.  Continuation is only 
    valid if there are an odd number of backslashses (an even number
    would result in a set of N/2 slashes not an escape)

    @param line: A properties line
    @type line: str
    @return: Does L{line} end with a line continuation
    @rtype: Boolean
    """
    pos = -1
    count = 0
    if len(line) == 0:
        return False
    # Count the slashes from the end of the line. Ensure we don't
    # go into infinite loop.
    while len(line) >= -pos and line[pos:][0] == "\\":
        pos -= 1
        count += 1
    return (count % 2) == 1  # Odd is a line continuation, even is not

def key_strip(key):
    """Cleanup whitespace found around a key

    @param key: A properties key
    @type key: str
    @return: Key without any uneeded whitespace
    @rtype: str
    """
    newkey = key.rstrip()
    # If line now end in \ we put back the whitespace that was escaped
    if newkey[-1:] == "\\":
        newkey += key[len(newkey):len(newkey)+1]
    return newkey.lstrip()

default_encoding = {"java": "latin1", "mozilla": "utf-8", "skype": "utf-16"}

class propunit(base.TranslationUnit):
    """an element of a properties file i.e. a name and value, and any comments
    associated"""
    def __init__(self, source="", personality="java"):
        """construct a blank propunit"""
        self.personality = personality
        super(propunit, self).__init__(source)
        self.name = ""
        self.value = u""
        self.translation = u""
        self.delimeter = u"="
        self.comments = []
        self.source = source

    def setsource(self, source):
        source = data.forceunicode(source)
        if self.personality == "mozilla" or self.personality == "skype":
            self.value = quote.mozillapropertiesencode(source or u"")
        else:
            self.value = quote.javapropertiesencode(source or u"")

    def getsource(self):
        value = quote.propertiesdecode(self.value)
        value = re.sub(u"\\\\ ", u" ", value)
        return value

    source = property(getsource, setsource)

    def settarget(self, target):
        target = data.forceunicode(target)
        if self.personality == "mozilla" or self.personality == "skype":
            self.translation = quote.mozillapropertiesencode(target or u"")
        else:
            self.translation = quote.javapropertiesencode(target or u"")

    def gettarget(self):
        translation = quote.propertiesdecode(self.translation)
        translation = re.sub(u"\\\\ ", u" ", translation)
        return translation

    target = property(gettarget, settarget)

    def __str__(self):
        """convert to a string. double check that unicode is handled somehow here"""
        source = self.getoutput()
        if isinstance(source, unicode):
            return source.encode(default_encoding[self.personality])
        return source

    def getoutput(self):
        """convert the element back into formatted lines for a .properties file"""
        notes = self.getnotes()
        if notes:
            notes += u"\n"
        if self.isblank():
            return notes
        else:
            if "\\u" in self.value and self.personality == "mozilla":
                self.value = quote.mozillapropertiesencode(self.source)
            if "\\u" in self.translation and self.personality == "mozilla":
                self.translation = quote.mozillapropertiesencode(self.target)
            value = self.translation or self.value
            return u"%s%s%s%s\n" % (notes, self.name, self.delimeter, value)

    def getlocations(self):
        return [self.name]

    def addnote(self, text, origin=None, position="append"):
        if origin in ['programmer', 'developer', 'source code', None]:
            text = data.forceunicode(text)
            self.comments.append(text)
        else:
            return super(propunit, self).addnote(text, origin=origin, position=position)

    def getnotes(self, origin=None):
        if origin in ['programmer', 'developer', 'source code', None]:
            return u'\n'.join(self.comments)
        else:
            return super(propunit, self).getnotes(origin)

    def removenotes(self):
        self.comments = []

    def isblank(self):
        """returns whether this is a blank element, containing only comments..."""
        return not (self.name or self.value)

    def istranslatable(self):
        return bool(self.name)

    def getid(self):
        return self.name

class propfile(base.TranslationStore):
    """this class represents a .properties file, made up of propunits"""
    UnitClass = propunit
    def __init__(self, inputfile=None, personality="java"):
        """construct a propfile, optionally reading in from inputfile"""
        super(propfile, self).__init__(unitclass = self.UnitClass)
        self.filename = getattr(inputfile, 'name', '')
        if inputfile is not None:
            propsrc = inputfile.read()
            inputfile.close()
            self.parse(propsrc, personality)

    def parse(self, propsrc, personality="java"):
        """read the source of a properties file in and include them as units"""
        newunit = propunit("", personality)
        inmultilinevalue = False
        propsrc = unicode(propsrc, default_encoding[personality])
        for line in propsrc.split(u"\n"):
            # handle multiline value if we're in one
            line = quote.rstripeol(line)
            if inmultilinevalue:
                newunit.value += line.lstrip()
                # see if there's more
                inmultilinevalue = is_line_continuation(newunit.value)
                # if we're still waiting for more...
                if inmultilinevalue:
                    # strip the backslash
                    newunit.value = newunit.value[:-1]
                if not inmultilinevalue:
                    # we're finished, add it to the list...
                    self.addunit(newunit)
                    newunit = propunit("", personality)
            # otherwise, this could be a comment
            elif line.strip()[:1] in (u'#', u'!'):
                # add a comment
                newunit.comments.append(line)
            elif not line.strip():
                # this is a blank line...
                if str(newunit).strip():
                    self.addunit(newunit)
                    newunit = propunit("", personality)
            else:
                delimeter_char, delimeter_pos = find_delimeter(line)
                if delimeter_pos == -1:
                    continue
                # otherwise, this is a definition
                else:
                    newunit.delimeter = delimeter_char
                    newunit.name = key_strip(line[:delimeter_pos])
                    newunit.value = line[delimeter_pos+1:].lstrip()
                    # backslash at end means carry string on to next line
                    if is_line_continuation(newunit.value):
                        inmultilinevalue = True
                        newunit.value = newunit.value[:-1]
                    else:
                        self.addunit(newunit)
                        newunit = propunit("", personality)
        # see if there is a leftover one...
        if inmultilinevalue or len(newunit.comments) > 0:
            self.addunit(newunit)

    def __str__(self):
        """convert the units back to lines"""
        lines = []
        for unit in self.units:
            lines.append(str(unit))
        return "".join(lines)

