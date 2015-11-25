#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2014 Zuza Software Foundation
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

"""Classes that hold units of .properties, and similar, files that are used in
translating Java, Mozilla, MacOS and other software.

The :class:`propfile` class is a monolingual class with :class:`propunit`
providing unit level access.

The .properties store has become a general key value pair class with
:class:`Dialect` providing the ability to change the behaviour of the
parsing and handling of the various dialects.

Currently we support:

- Java .properties
- Mozilla .properties
- Adobe Flex files
- MacOS X .strings files
- Skype .lang files

The following provides references and descriptions of the various
dialects supported:

Java
    Java .properties are supported completely except for the ability to drop
    pairs that are not translated.

    The following `.properties file description
    <http://docs.oracle.com/javase/1.4.2/docs/api/java/util/Properties.html#load(java.io.InputStream)>`_
    gives a good references to the .properties specification.

    Properties file may also hold Java `MessageFormat
    <http://docs.oracle.com/javase/1.4.2/docs/api/java/text/MessageFormat.html>`_
    messages.  No special handling is provided in this storage class for
    MessageFormat, but this may be implemented in future.

    All delimiter types, comments, line continuations and spaces handling in
    delimeters are supported.

Mozilla
    Mozilla files use '=' as a delimiter, are UTF-8 encoded and thus don't
    need \\u escaping.  Any \\U values will be converted to correct Unicode
    characters.

Strings
    Mac OS X strings files are implemented using
    `these <https://developer.apple.com/library/mac/#documentation/MacOSX/Conceptual/BPInternational/Articles/StringsFiles.html>`_
    `two <https://developer.apple.com/library/mac/#documentation/Cocoa/Conceptual/LoadingResources/Strings/Strings.html>`_
    articles as references.

Flex
    Adobe Flex files seem to be normal .properties files but in UTF-8 just like
    Mozilla files. This
    `page <http://livedocs.adobe.com/flex/3/html/help.html?content=l10n_3.html>`_
    provides the information used to implement the dialect.

Skype
    Skype .lang files seem to be UTF-16 encoded .properties files.

A simple summary of what is permissible follows.

Comments supported:

.. code-block:: properties

   # a comment
   ! a comment
   // a comment (only at the beginning of a line)
   /* a comment (not across multiple lines) */

Name and Value pairs:

.. code-block:: properties

   # Delimiters
   key = value
   key : value
   key value

   # Space in key and around value
   \ key\ = \ value

   # Note that the b and c are escaped for reST rendering
   b = a string with escape sequences \\t \\n \\r \\\\ \\" \\' \\ (space) \u0123
   c = a string with a continuation line \\
       continuation line

   # Special cases
   # key with no value
   key
   # value no key (extractable in prop2po but not mergeable in po2prop)
   =value

   # .strings specific
   "key" = "value";

"""

import re

from translate.lang import data
from translate.misc import quote
from translate.misc.deprecation import deprecated
from translate.storage import base


labelsuffixes = (".label", ".title")
"""Label suffixes: entries with this suffix are able to be comibed with accesskeys
found in in entries ending with :attr:`.accesskeysuffixes`"""
accesskeysuffixes = (".accesskey", ".accessKey", ".akey")
"""Accesskey Suffixes: entries with this suffix may be combined with labels
ending in :attr:`.labelsuffixes` into accelerator notation"""


# the rstripeols convert dos <-> unix nicely as well
# output will be appropriate for the platform

eol = "\n"


def _find_delimiter(line, delimiters):
    """Find the type and position of the delimiter in a property line.

    Property files can be delimited by "=", ":" or whitespace (space for now).
    We find the position of each delimiter, then find the one that appears
    first.

    :param line: A properties line
    :type line: str
    :param delimiters: valid delimiters
    :type delimiters: list
    :return: delimiter character and offset within *line*
    :rtype: Tuple (delimiter char, Offset Integer)
    """
    delimiter_dict = {}
    for delimiter in delimiters:
        delimiter_dict[delimiter] = -1
    delimiters = delimiter_dict
    # Find the position of each delimiter type
    for delimiter, pos in delimiters.iteritems():
        prewhitespace = len(line) - len(line.lstrip())
        pos = line.find(delimiter, prewhitespace)
        while pos != -1:
            if delimiters[delimiter] == -1 and line[pos-1] != u"\\":
                delimiters[delimiter] = pos
                break
            pos = line.find(delimiter, pos + 1)
    # Find the first delimiter
    mindelimiter = None
    minpos = -1
    for delimiter, pos in delimiters.iteritems():
        if pos == -1 or delimiter == u" ":
            continue
        if minpos == -1 or pos < minpos:
            minpos = pos
            mindelimiter = delimiter
    if mindelimiter is None and delimiters.get(u" ", -1) != -1:
        # Use space delimiter if we found nothing else
        return (u" ", delimiters[" "])
    if (mindelimiter is not None and
        u" " in delimiters and
        delimiters[u" "] < delimiters[mindelimiter]):
        # If space delimiter occurs earlier than ":" or "=" then it is the
        # delimiter only if there are non-whitespace characters between it and
        # the other detected delimiter.
        if len(line[delimiters[u" "]:delimiters[mindelimiter]].strip()) > 0:
            return (u" ", delimiters[u" "])
    return (mindelimiter, minpos)


@deprecated("Use Dialect.find_delimiter instead")
def find_delimeter(line):
    """Misspelled function that is kept around in case someone relies on it.

    .. deprecated:: 1.7.0
       Use :func:`find_delimiter` instead
    """
    return _find_delimiter(line, DialectJava.delimiters)


def is_line_continuation(line):
    """Determine whether *line* has a line continuation marker.

    .properties files can be terminated with a backslash (\\) indicating
    that the 'value' continues on the next line.  Continuation is only
    valid if there are an odd number of backslashses (an even number
    would result in a set of N/2 slashes not an escape)

    :param line: A properties line
    :type line: str
    :return: Does *line* end with a line continuation
    :rtype: Boolean
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


def is_comment_one_line(line):
    """Determine whether a *line* is a one-line comment.

    :param line: A properties line
    :type line: unicode
    :return: True if line is a one-line comment
    :rtype: bool
    """
    stripped = line.strip()
    line_starters = (u'#', u'!', u'//', )
    for starter in line_starters:
        if stripped.startswith(starter):
            return True
    if stripped.startswith(u'/*') and stripped.endswith(u'*/'):
        return True
    return False


def is_comment_start(line):
    """Determine whether a *line* starts a new multi-line comment.

    :param line: A properties line
    :type line: unicode
    :return: True if line starts a new multi-line comment
    :rtype: bool
    """
    stripped = line.strip()
    return stripped.startswith('/*') and not stripped.endswith('*/')


def is_comment_end(line):
    """Determine whether a *line* ends a new multi-line comment.

    :param line: A properties line
    :type line: unicode
    :return: True if line ends a new multi-line comment
    :rtype: bool
    """
    stripped = line.strip()
    return not stripped.startswith('/*') and stripped.endswith('*/')


def _key_strip(key):
    """Cleanup whitespace found around a key

    :param key: A properties key
    :type key: str
    :return: Key without any unneeded whitespace
    :rtype: str
    """
    newkey = key.rstrip()
    # If string now ends in \ we put back the whitespace that was escaped
    if newkey[-1:] == "\\":
        newkey += key[len(newkey):len(newkey)+1]
    return newkey.lstrip()

dialects = {}
default_dialect = "java"


def register_dialect(dialect):
    """Decorator that registers the dialect."""
    dialects[dialect.name] = dialect
    return dialect


def get_dialect(dialect=default_dialect):
    return dialects.get(dialect)


class Dialect(object):
    """Settings for the various behaviours in key=value files."""
    name = None
    default_encoding = 'iso-8859-1'
    delimiters = None
    pair_terminator = u""
    key_wrap_char = u""
    value_wrap_char = u""
    drop_comments = []

    @classmethod
    def encode(cls, string, encoding=None):
        """Encode the string"""
        # FIXME: dialects are a bad idea, not possible for subclasses
        # to override key methods
        if encoding != "utf-8":
            return quote.javapropertiesencode(string or u"")
        return string or u""

    @classmethod
    def find_delimiter(cls, line):
        """Find the delimiter"""
        return _find_delimiter(line, cls.delimiters)

    @classmethod
    def key_strip(cls, key):
        """Strip unneeded characters from the key"""
        return _key_strip(key)

    @classmethod
    def value_strip(cls, value):
        """Strip unneeded characters from the value"""
        return value.lstrip()


@register_dialect
class DialectJava(Dialect):
    name = "java"
    default_encoding = "iso-8859-1"
    delimiters = [u"=", u":", u" "]


@register_dialect
class DialectJavaUtf8(DialectJava):
    name = "java-utf8"
    default_encoding = "utf-8"
    delimiters = [u"=", u":", u" "]

    @classmethod
    def encode(cls, string, encoding=None):
        return quote.mozillapropertiesencode(string or u"")


@register_dialect
class DialectFlex(DialectJava):
    name = "flex"
    default_encoding = "utf-8"


@register_dialect
class DialectMozilla(DialectJavaUtf8):
    name = "mozilla"
    delimiters = [u"="]

    @classmethod
    def encode(cls, string, encoding=None):
        """Encode the string"""
        string = quote.mozillapropertiesencode(string or u"")
        string = quote.mozillaescapemarginspaces(string or u"")
        return string


@register_dialect
class DialectGaia(DialectMozilla):
    name = "gaia"
    delimiters = [u"="]


@register_dialect
class DialectSkype(Dialect):
    name = "skype"
    default_encoding = "utf-16"
    delimiters = [u"="]

    @classmethod
    def encode(cls, string, encoding=None):
        return quote.mozillapropertiesencode(string or u"")


@register_dialect
class DialectStrings(Dialect):
    name = "strings"
    default_encoding = "utf-16"
    delimiters = [u"="]
    pair_terminator = u";"
    key_wrap_char = u'"'
    value_wrap_char = u'"'
    out_ending = u';'
    out_delimiter_wrappers = u' '
    drop_comments = ["/* No comment provided by engineer. */"]

    @classmethod
    def key_strip(cls, key):
        """Strip unneeded characters from the key"""
        newkey = key.rstrip().rstrip('"')
        # If string now ends in \ we put back the char that was escaped
        if newkey[-1:] == "\\":
            newkey += key[len(newkey):len(newkey)+1]
        ret = newkey.lstrip().lstrip('"')
        return ret.replace('\\"', '"')

    @classmethod
    def value_strip(cls, value):
        """Strip unneeded characters from the value"""
        newvalue = value.rstrip().rstrip(';').rstrip('"')
        # If string now ends in \ we put back the char that was escaped
        if newvalue[-1:] == "\\":
            newvalue += value[len(newvalue):len(newvalue)+1]
        ret = newvalue.lstrip().lstrip('"')
        return ret.replace('\\"', '"')

    @classmethod
    def encode(cls, string, encoding=None):
        return string.replace("\n", r"\n").replace("\t", r"\t")


@register_dialect
class DialectStringsUtf8(DialectStrings):
    name = "strings-utf8"
    default_encoding = "utf-8"


class propunit(base.TranslationUnit):
    """An element of a properties file i.e. a name and value, and any
    comments associated."""

    def __init__(self, source="", personality="java"):
        """Construct a blank propunit."""
        self.personality = get_dialect(personality)
        super(propunit, self).__init__(source)
        self.name = u""
        self.value = u""
        self.translation = u""
        self.delimiter = u"="
        self.comments = []
        self.source = source
        # a pair of symbols to enclose delimiter on the output
        # (a " " can be used for the sake of convenience)
        self.out_delimiter_wrappers = getattr(self.personality,
                                              'out_delimiter_wrappers', u'')
        # symbol that should end every property sentence
        # (e.g. ";" is required for Mac OS X strings)
        self.out_ending = getattr(self.personality, 'out_ending', u'')

    def getsource(self):
        value = quote.propertiesdecode(self.value)
        return value

    def setsource(self, source):
        self._rich_source = None
        source = data.forceunicode(source)
        self.value = self.personality.encode(source or u"", self.encoding)

    source = property(getsource, setsource)

    def gettarget(self):
        translation = quote.propertiesdecode(self.translation)
        translation = re.sub(u"\\\\ ", u" ", translation)
        return translation

    def settarget(self, target):
        self._rich_target = None
        target = data.forceunicode(target)
        self.translation = self.personality.encode(target or u"",
                                                   self.encoding)

    target = property(gettarget, settarget)

    @property
    def encoding(self):
        if self._store:
            return self._store.encoding
        else:
            return self.personality.default_encoding

    def __str__(self):
        """Convert to a string. Double check that unicode is handled
        somehow here."""
        source = self.getoutput()
        assert isinstance(source, unicode)
        return source.encode(self.encoding)

    def getoutput(self):
        """Convert the element back into formatted lines for a
        .properties file"""
        notes = self.getnotes()
        if notes:
            notes += u"\n"
        if self.isblank():
            return notes + u"\n"
        else:
            self.value = self.personality.encode(self.source, self.encoding)
            self.translation = self.personality.encode(self.target,
                                                       self.encoding)
            # encode key, if needed
            key = self.name
            kwc = self.personality.key_wrap_char
            if kwc:
                key = key.replace(kwc, '\\%s' % kwc)
                key = '%s%s%s' % (kwc, key, kwc)
            # encode value, if needed
            value = self.translation or self.value
            vwc = self.personality.value_wrap_char
            if vwc:
                value = value.replace(vwc, '\\%s' % vwc)
                value = '%s%s%s' % (vwc, value, vwc)
            wrappers = self.out_delimiter_wrappers
            delimiter = '%s%s%s' % (wrappers, self.delimiter, wrappers)
            ending = self.out_ending
            out_dict = {
                "notes": notes,
                "key": key,
                "del": delimiter,
                "value": value,
                "ending": ending,
            }
            return u"%(notes)s%(key)s%(del)s%(value)s%(ending)s\n" % out_dict

    def getlocations(self):
        return [self.name]

    def addnote(self, text, origin=None, position="append"):
        if origin in ['programmer', 'developer', 'source code', None]:
            text = data.forceunicode(text)
            self.comments.append(text)
        else:
            return super(propunit, self).addnote(text, origin=origin,
                                                 position=position)

    def getnotes(self, origin=None):
        if origin in ['programmer', 'developer', 'source code', None]:
            return u'\n'.join(self.comments)
        else:
            return super(propunit, self).getnotes(origin)

    def removenotes(self):
        self.comments = []

    def isblank(self):
        """returns whether this is a blank element, containing only
        comments."""
        return not (self.name or self.value)

    def istranslatable(self):
        return bool(self.name)

    def getid(self):
        return self.name

    def setid(self, value):
        self.name = value


class propfile(base.TranslationStore):
    """this class represents a .properties file, made up of propunits"""
    UnitClass = propunit

    def __init__(self, inputfile=None, personality="java", encoding=None):
        """construct a propfile, optionally reading in from inputfile"""
        super(propfile, self).__init__(unitclass=self.UnitClass)
        self.personality = get_dialect(personality)
        self.encoding = encoding or self.personality.default_encoding
        self.filename = getattr(inputfile, 'name', '')
        if inputfile is not None:
            propsrc = inputfile.read()
            inputfile.close()
            self.parse(propsrc)
            self.makeindex()

    def parse(self, propsrc):
        """Read the source of a properties file in and include them
        as units."""
        text, encoding = self.detect_encoding(propsrc,
            default_encodings=[self.personality.default_encoding, 'utf-8',
                               'utf-16'])
        if not text:
            raise IOError("Cannot detect encoding for %s." % (self.filename or
                                                              "given string"))
        self.encoding = encoding
        propsrc = text

        newunit = propunit("", self.personality.name)
        inmultilinevalue = False
        inmultilinecomment = False

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
                    newunit = propunit("", self.personality.name)
            # otherwise, this could be a comment
            # FIXME handle // inline comments
            elif (inmultilinecomment or is_comment_one_line(line) or
                  is_comment_start(line) or is_comment_end(line)):
                # add a comment
                if line not in self.personality.drop_comments:
                    newunit.comments.append(line)
                if is_comment_start(line):
                    inmultilinecomment = True
                elif is_comment_end(line):
                    inmultilinecomment = False
            elif not line.strip():
                # this is a blank line...
                if str(newunit).strip():
                    self.addunit(newunit)
                    newunit = propunit("", self.personality.name)
            else:
                newunit.delimiter, delimiter_pos = self.personality.find_delimiter(line)
                if delimiter_pos == -1:
                    newunit.name = self.personality.key_strip(line)
                    newunit.value = u""
                    self.addunit(newunit)
                    newunit = propunit("", self.personality.name)
                else:
                    newunit.name = self.personality.key_strip(line[:delimiter_pos])
                    if is_line_continuation(line[delimiter_pos+1:].lstrip()):
                        inmultilinevalue = True
                        newunit.value = line[delimiter_pos+1:].lstrip()[:-1]
                    else:
                        newunit.value = self.personality.value_strip(line[delimiter_pos+1:])
                        self.addunit(newunit)
                        newunit = propunit("", self.personality.name)
        # see if there is a leftover one...
        if inmultilinevalue or len(newunit.comments) > 0:
            self.addunit(newunit)

    def __str__(self):
        """Convert the units back to lines."""
        lines = []
        for unit in self.units:
            lines.append(unit.getoutput())
        uret = u"".join(lines)
        return uret.encode(self.encoding)

class javafile(propfile):
    Name = "Java Properties"
    Extensions = ['properties']

    def __init__(self, *args, **kwargs):
        kwargs['personality'] = "java"
        kwargs['encoding'] = "auto"
        super(javafile, self).__init__(*args, **kwargs)


class javautf8file(propfile):
    Name = "Java Properties (UTF-8)"
    Extensions = ['properties']

    def __init__(self, *args, **kwargs):
        kwargs['personality'] = "java-utf8"
        kwargs['encoding'] = "utf-8"
        super(javautf8file, self).__init__(*args, **kwargs)


class stringsfile(propfile):
    Name = "OS X Strings"
    Extensions = ['strings']

    def __init__(self, *args, **kwargs):
        kwargs['personality'] = "strings"
        super(stringsfile, self).__init__(*args, **kwargs)


class stringsutf8file(propfile):
    Name = "OS X Strings (UTF-8)"
    Extensions = ['strings']

    def __init__(self, *args, **kwargs):
        kwargs['personality'] = "strings-utf8"
        kwargs['encoding'] = "utf-8"
        super(stringsutf8file, self).__init__(*args, **kwargs)
