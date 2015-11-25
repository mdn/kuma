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

"""Base classes for storage interfaces."""

import logging
try:
    import cPickle as pickle
except ImportError:
    import pickle

from translate.misc.multistring import multistring
from translate.storage.placeables import (StringElem, general,
                                          parse as rich_parse)
from translate.storage.workflow import StateEnum as states


def force_override(method, baseclass):
    """Forces derived classes to override method."""

    if type(method.im_self) == type(baseclass):
        # then this is a classmethod and im_self is the actual class
        actualclass = method.im_self
    else:
        actualclass = method.im_class
    if actualclass != baseclass:
        raise NotImplementedError(
            "%s does not reimplement %s as required by %s" %
            (actualclass.__name__, method.__name__, baseclass.__name__))


class ParseError(Exception):

    def __init__(self, inner_exc):
        self.inner_exc = inner_exc

    def __str__(self):
        return repr(self.inner_exc)


class TranslationUnit(object):
    """Base class for translation units.

    Our concept of a *translation unit* is influenced heavily by `XLIFF
    <http://docs.oasis-open.org/xliff/xliff-core/xliff-core.html>`_.

    As such most of the method- and variable names borrows from XLIFF
    terminology.

    A translation unit consists of the following:

    - A *source* string. This is the original translatable text.
    - A *target* string. This is the translation of the *source*.
    - Zero or more *notes* on the unit. Notes would typically be some comments
      from a translator on the unit, or some comments originating from the
      source code.
    - Zero or more *locations*. Locations indicate where in the original source
      code this unit came from.
    - Zero or more *errors*. Some tools (eg.
      :mod:`~translate.filters.pofilter`) can run checks on translations and
      produce error messages.

    """

    rich_parsers = []
    """A list of functions to use for parsing a string into a rich string
    tree."""

    # State constants
    S_OBSOLETE = states.OBSOLETE
    S_EMPTY = states.EMPTY
    S_NEEDS_WORK = states.NEEDS_WORK
    S_REJECTED = states.REJECTED
    S_NEEDS_REVIEW = states.NEEDS_REVIEW
    S_UNREVIEWED = states.UNREVIEWED
    S_FINAL = states.FINAL

    # Elaborate state support could look something like this:
    # STATE = {
    #     S_OBSOLETE: (states.OBSOLETE, states.EMPTY),
    #     S_EMPTY: (states.EMPTY, states.NEEDS_WORK),
    #     S_NEEDS_WORK: (states.NEEDS_WORK, states.REJECTED),
    #     S_REJECTED: (states.REJECTED, states.NEEDS_REVIEW),
    #     S_NEEDS_REVIEW: (states.NEEDS_REVIEW, states.UNREVIEWED),
    #     S_UNREVIEWED: (states.UNREVIEWED, states.FINAL),
    #     S_FINAL: (states.FINAL, states.MAX),
    # }
    # """
    # Default supported states:
    #     * obsolete: The unit is not to be used.
    #     * empty: The unit has not been translated before.
    #     * needs work: Some translation has been done, but is not complete.
    #     * rejected: The unit has been reviewed, but was rejected.
    #     * needs review: The unit has been translated, but review was requested.
    #     * unreviewed: The unit has been translated, but not reviewed.
    #     * final: The unit is translated, reviewed and accepted.
    # """
    #
    # ... but by default a format will not support state:
    STATE = {}

    _store = None
    _source = None
    _target = None
    _rich_source = None
    _rich_target = None
    _state_n = 0
    notes = ""

    def __init__(self, source=None):
        """Constructs a TranslationUnit containing the given source string."""
        if source is not None:
            self.source = source

    def __eq__(self, other):
        """Compares two TranslationUnits.

        :type other: :class:`TranslationUnit`
        :param other: Another :class:`TranslationUnit`
        :rtype: Boolean
        :return: Returns *True* if the supplied :class:`TranslationUnit`
                 equals this unit.
        """
        return self.source == other.source and self.target == other.target

    def __str__(self):
        """Converts to a string representation that can be parsed back using
        :meth:`~.TranslationStore.parsestring`."""
        # no point in pickling store object, so let's hide it for a while.
        store = getattr(self, "_store", None)
        self._store = None
        dump = pickle.dumps(self)
        self._store = store
        return dump

    @classmethod
    def rich_to_multistring(cls, elem_list):
        """Convert a "rich" string tree to a ``multistring``:

           >>> from translate.storage.placeables.interfaces import X
           >>> rich = [StringElem(['foo', X(id='xxx', sub=[' ']), 'bar'])]
           >>> TranslationUnit.rich_to_multistring(rich)
           multistring(u'foo bar')
        """
        return multistring([unicode(elem) for elem in elem_list])

    def multistring_to_rich(self, mulstring):
        """Convert a multistring to a list of "rich" string trees:

           >>> target = multistring([u'foo', u'bar', u'baz'])
           >>> TranslationUnit.multistring_to_rich(target)
           [<StringElem([<StringElem([u'foo'])>])>,
            <StringElem([<StringElem([u'bar'])>])>,
            <StringElem([<StringElem([u'baz'])>])>]
        """
        if isinstance(mulstring, multistring):
            return [rich_parse(s, self.rich_parsers) for s in mulstring.strings]
        return [rich_parse(mulstring, self.rich_parsers)]

    def setsource(self, source):
        """Set the source string to the given value."""
        self._rich_source = None
        self._source = source
    source = property(lambda self: self._source, setsource)

    def settarget(self, target):
        """Set the target string to the given value."""
        self._rich_target = None
        self._target = target
    target = property(lambda self: self._target, settarget)

    def _get_rich_source(self):
        if self._rich_source is None:
            self._rich_source = self.multistring_to_rich(self.source)
        return self._rich_source

    def _set_rich_source(self, value):
        if not hasattr(value, '__iter__'):
            raise ValueError('value must be iterable')
        if len(value) < 1:
            raise ValueError('value must have at least one element.')
        if not isinstance(value[0], StringElem):
            raise ValueError('value[0] must be of type StringElem.')
        self._rich_source = list(value)
        multi = self.rich_to_multistring(value)
        if self.source != multi:
            self.source = multi
    rich_source = property(_get_rich_source, _set_rich_source)
    """
    .. seealso:: :meth:`.rich_to_multistring`, :meth:`multistring_to_rich`
    """

    def _get_rich_target(self):
        if self._rich_target is None:
            self._rich_target = self.multistring_to_rich(self.target)
        return self._rich_target

    def _set_rich_target(self, value):
        if not hasattr(value, '__iter__'):
            raise ValueError('value must be iterable')
        if len(value) < 1:
            raise ValueError('value must have at least one element.')
        if not isinstance(value[0], StringElem):
            raise ValueError('value[0] must be of type StringElem.')
        self._rich_target = list(value)
        self.target = self.rich_to_multistring(value)
    rich_target = property(_get_rich_target, _set_rich_target)
    """
    .. seealso:: :meth:`.rich_to_multistring`, :meth:`.multistring_to_rich`
    """

    def gettargetlen(self):
        """Returns the length of the target string.

        :rtype: Integer

        .. note::

           Plural forms might be combined.
        """
        length = len(self.target or "")
        strings = getattr(self.target, "strings", [])
        if strings:
            length += sum([len(pluralform) for pluralform in strings[1:]])
        return length

    def getid(self):
        """A unique identifier for this unit.

        :rtype: string
        :return: an identifier for this unit that is unique in the store

        Derived classes should override this in a way that guarantees a unique
        identifier for each unit in the store.
        """
        return self.source

    def setid(self, value):
        """Sets the unique identified for this unit.

        only implemented if format allows ids independant from other
        unit properties like source or context"""
        pass

    def getlocations(self):
        """A list of source code locations.

        :rtype: List

        .. note::

           Shouldn't be implemented if the format doesn't support it.
        """
        return []

    def addlocation(self, location):
        """Add one location to the list of locations.

        .. note::

           Shouldn't be implemented if the format doesn't support it.
        """
        pass

    def addlocations(self, location):
        """Add a location or a list of locations.

        .. note::

           Most classes shouldn't need to implement this, but should rather
           implement :meth:`TranslationUnit.addlocation`.

        .. warning::

           This method might be removed in future.
        """
        if isinstance(location, list):
            for item in location:
                self.addlocation(item)
        else:
            self.addlocation(location)

    def getcontext(self):
        """Get the message context."""
        return ""

    def setcontext(self, context):
        """Set the message context"""
        pass

    def getnotes(self, origin=None):
        """Returns all notes about this unit.

        It will probably be freeform text or something reasonable that can be
        synthesised by the format.
        It should not include location comments (see
        :meth:`~.TranslationUnit.getlocations`).
        """
        return getattr(self, "notes", "")

    def addnote(self, text, origin=None, position="append"):
        """Adds a note (comment).

        :type text: string
        :param text: Usually just a sentence or two.
        :type origin: string
        :param origin: Specifies who/where the comment comes from.
                       Origin can be one of the following text strings:
                       - 'translator'
                       - 'developer', 'programmer', 'source code' (synonyms)
        """
        if position == "append" and getattr(self, "notes", None):
            self.notes += '\n' + text
        else:
            self.notes = text

    def removenotes(self):
        """Remove all the translator's notes."""
        self.notes = u''

    def adderror(self, errorname, errortext):
        """Adds an error message to this unit.

        :type errorname: string
        :param errorname: A single word to id the error.
        :type errortext: string
        :param errortext: The text describing the error.
        """
        pass

    def geterrors(self):
        """Get all error messages.

        :rtype: Dictionary
        """
        return {}

    def markreviewneeded(self, needsreview=True, explanation=None):
        """Marks the unit to indicate whether it needs review.

        :keyword needsreview: Defaults to True.
        :keyword explanation: Adds an optional explanation as a note.
        """
        pass

    def istranslated(self):
        """Indicates whether this unit is translated.

        This should be used rather than deducing it from .target,
        to ensure that other classes can implement more functionality
        (as XLIFF does).
        """
        return bool(self.target) and not self.isfuzzy()

    def istranslatable(self):
        """Indicates whether this unit can be translated.

        This should be used to distinguish real units for translation from
        header, obsolete, binary or other blank units.
        """
        return bool(self.source)

    def isfuzzy(self):
        """Indicates whether this unit is fuzzy."""
        return False

    def markfuzzy(self, value=True):
        """Marks the unit as fuzzy or not."""
        pass

    def isobsolete(self):
        """indicate whether a unit is obsolete"""
        return False

    def makeobsolete(self):
        """Make a unit obsolete"""
        pass

    def isheader(self):
        """Indicates whether this unit is a header."""
        return False

    def isreview(self):
        """Indicates whether this unit needs review."""
        return False

    def isblank(self):
        """Used to see if this unit has no source or target string.

        .. note::

           This is probably used more to find translatable units,
           and we might want to move in that direction rather and
           get rid of this.
        """
        return not (self.source or self.target)

    def hasplural(self):
        """Tells whether or not this specific unit has plural strings."""
        #TODO: Reconsider
        return False

    def getsourcelanguage(self):
        return self._store.getsourcelanguage()

    def gettargetlanguage(self):
        return self._store.gettargetlanguage()

    def merge(self, otherunit, overwrite=False, comments=True,
              authoritative=False):
        """Do basic format agnostic merging."""
        if not self.target or overwrite:
            self.rich_target = otherunit.rich_target

    def unit_iter(self):
        """Iterator that only returns this unit."""
        yield self

    def getunits(self):
        """This unit in a list."""
        return [self]

    @classmethod
    def buildfromunit(cls, unit):
        """Build a native unit from a foreign unit, preserving as much
        information as possible."""
        if type(unit) == cls and hasattr(unit, "copy") and callable(unit.copy):
            return unit.copy()
        newunit = cls(unit.source)
        newunit.target = unit.target
        newunit.markfuzzy(unit.isfuzzy())
        locations = unit.getlocations()
        if locations:
            newunit.addlocations(locations)
        notes = unit.getnotes()
        if notes:
            newunit.addnote(notes)
        return newunit

    xid = property(lambda self: None, lambda self, value: None)
    rid = property(lambda self: None, lambda self, value: None)

    def get_state_id(self, n=None):
        if n is None:
            n = self.get_state_n()
        for state_id, state_range in self.STATE.iteritems():
            if state_range[0] <= n < state_range[1]:
                return state_id
        if self.STATE:
            raise ValueError('No state containing value %s' % (n))
        else:
            return n

    def get_state_n(self):
        if self.STATE:
            return self._state_n
        else:
            return self.istranslated() and self.S_UNREVIEWED or self.S_EMPTY

    def set_state_n(self, value):
        self._state_n = value

    def infer_state(self):
        """Empty method that should be overridden in sub-classes to infer the
            current state(_n) of the unit from its current state."""
        pass


class TranslationStore(object):
    """Base class for stores for multiple translation units of type
    UnitClass."""

    UnitClass = TranslationUnit
    """The class of units that will be instantiated and used by this class"""
    Name = "Base translation store"
    """The human usable name of this store type"""
    Mimetypes = None
    """A list of MIME types associated with this store type"""
    Extensions = None
    """A list of file extentions associated with this store type"""
    _binary = False
    """Indicates whether a file should be accessed as a binary file."""
    suggestions_in_format = False
    """Indicates if format can store suggestions and alternative translation
    for a unit"""

    sourcelanguage = None
    targetlanguage = None

    def __init__(self, unitclass=None):
        """Construct a blank TranslationStore."""
        self.units = []
        if unitclass:
            self.UnitClass = unitclass

    def getsourcelanguage(self):
        """Get the source language for this store."""
        return self.sourcelanguage

    def setsourcelanguage(self, sourcelanguage):
        """Set the source language for this store."""
        self.sourcelanguage = sourcelanguage

    def gettargetlanguage(self):
        """Get the target language for this store."""
        return self.targetlanguage

    def settargetlanguage(self, targetlanguage):
        """Set the target language for this store."""
        self.targetlanguage = targetlanguage

    def getprojectstyle(self):
        """Get the project type for this store."""
        return getattr(self, '_project_style', None)

    def setprojectstyle(self, project_style):
        """Set the project type for this store."""
        self._project_style = project_style

    def unit_iter(self):
        """Iterator over all the units in this store."""
        for unit in self.units:
            yield unit

    def getunits(self):
        """Return a list of all units in this store."""
        return [unit for unit in self.unit_iter()]

    def addunit(self, unit):
        """Append the given unit to the object's list of units.

        This method should always be used rather than trying to modify the
        list manually.

        :type unit: :class:`TranslationUnit`
        :param unit: The unit that will be added.
        """
        unit._store = self
        self.units.append(unit)

    def addsourceunit(self, source):
        """Add and returns a new unit with the given source string.

        :rtype: :class:`TranslationUnit`
        """
        unit = self.UnitClass(source)
        self.addunit(unit)
        return unit

    def findid(self, id):
        """find unit with matching id by checking id_index"""
        self.require_index()
        return self.id_index.get(id, None)

    def findunit(self, source):
        """Find the unit with the given source string.

        :rtype: :class:`TranslationUnit` or None
        """
        if len(getattr(self, "sourceindex", [])):
            if source in self.sourceindex:
                return self.sourceindex[source][0]
        else:
            for unit in self.units:
                if unit.source == source:
                    return unit
        return None

    def findunits(self, source):
        """Find the units with the given source string.

        :rtype: :class:`TranslationUnit` or None
        """
        if len(getattr(self, "sourceindex", [])):
            if source in self.sourceindex:
                return self.sourceindex[source]
        else:
            #FIXME: maybe we should generate index here instead since
            #we'll scan all units anyway
            result = []
            for unit in self.units:
                if unit.source == source:
                    result.append(unit)
            return result
        return None

    def translate(self, source):
        """Return the translated string for a given source string.

        :rtype: String or None
        """
        unit = self.findunit(source)
        if unit and unit.target:
            return unit.target
        else:
            return None

    def remove_unit_from_index(self, unit):
        """Remove a unit from source and locaton indexes"""

        def remove_unit(source):
            if source in self.sourceindex:
                try:
                    self.sourceindex[source].remove(unit)
                    if len(self.sourceindex[source]) == 0:
                        del(self.sourceindex[source])
                except ValueError:
                    pass

        if unit.hasplural():
            for source in unit.source.strings:
                remove_unit(source)
        else:
            remove_unit(unit.source)

        for location in unit.getlocations():
            if location in self.locationindex \
                   and self.locationindex[location] is not None \
                   and self.locationindex[location] == unit:
                del(self.locationindex[location])

    def add_unit_to_index(self, unit):
        """Add a unit to source and location idexes"""
        self.id_index[unit.getid()] = unit

        def insert_unit(source):
            if not source in self.sourceindex:
                self.sourceindex[source] = [unit]
            else:
                self.sourceindex[source].append(unit)

        if unit.hasplural():
            for source in unit.source.strings:
                insert_unit(source)
        else:
            insert_unit(unit.source)

        for location in unit.getlocations():
            if location in self.locationindex:
                # if sources aren't unique, don't use them
                #FIXME: maybe better store a list of units like sourceindex
                self.locationindex[location] = None
            else:
                self.locationindex[location] = unit

    def makeindex(self):
        """Indexes the items in this store. At least .sourceindex should be
        useful."""
        self.locationindex = {}
        self.sourceindex = {}
        self.id_index = {}
        for index, unit in enumerate(self.units):
            unit.index = index
            if not (unit.isheader() or unit.isblank()):
                self.add_unit_to_index(unit)

    def require_index(self):
        """make sure source index exists"""
        if not hasattr(self, "id_index"):
            self.makeindex()

    def getids(self, filename=None):
        """return a list of unit ids"""
        self.require_index()
        return self.id_index.keys()

    def __getstate__(self):
        odict = self.__dict__.copy()
        odict['fileobj'] = None
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)
        if getattr(self, "filename", False):
            self.fileobj = open(self.filename)

    def __str__(self):
        """Converts to a string representation that can be parsed back using
        :meth:`~.TranslationStore.parsestring`."""
        # We can't pickle fileobj if it is there, so let's hide it for a while.
        fileobj = getattr(self, "fileobj", None)
        self.fileobj = None
        dump = pickle.dumps(self)
        self.fileobj = fileobj
        return dump

    def isempty(self):
        """Return True if the object doesn't contain any translation units."""
        if len(self.units) == 0:
            return True
        for unit in self.units:
            if unit.istranslatable():
                return False
        return True

    def _assignname(self):
        """Tries to work out what the name of the filesystem file is and
        assigns it to .filename."""
        fileobj = getattr(self, "fileobj", None)
        if fileobj:
            filename = getattr(fileobj, "name",
                               getattr(fileobj, "filename", None))
            if filename:
                self.filename = filename

    @classmethod
    def parsestring(cls, storestring):
        """Convert the string representation back to an object."""
        newstore = cls()
        if storestring:
            newstore.parse(storestring)
        return newstore

    def detect_encoding(self, text, default_encodings=None):
        if not default_encodings:
            default_encodings = ['utf-8']
        try:
            import chardet
            # many false complaints with ellipse (see bug 1825)
            detected_encoding = chardet.detect(text.replace("…", ""))
            if detected_encoding['confidence'] < 0.48:
                detected_encoding = None
            elif detected_encoding['encoding'] == 'ascii':
                detected_encoding['encoding'] = 'utf-8'
        except ImportError:
            detected_encoding = None

        encodings = []
        if self.encoding == 'auto':
            if detected_encoding and detected_encoding['encoding'] not in encodings:
                encodings.append(detected_encoding['encoding'])
            for encoding in default_encodings:
                if encoding not in encodings:
                    encodings.append(encoding)
        else:
            encodings.append(self.encoding)
            if (detected_encoding and
                    detected_encoding['encoding'] != self.encoding and
                    detected_encoding['confidence'] != 1.0):
                logging.warn("trying to parse %s with encoding: %s but "
                             "detected encoding is %s (confidence: %s)",
                             self.filename, self.encoding,
                             detected_encoding['encoding'],
                             detected_encoding['confidence'])
            encodings.append(self.encoding)

        for encoding in encodings:
            try:
                r_text = unicode(text, encoding)
                r_encoding = encoding
                break
            except UnicodeDecodeError:
                r_text = None
                r_encoding = None
        if r_encoding == 'ascii':
            r_encoding = 'utf-8'
        return r_text, r_encoding

    def parse(self, data):
        """parser to process the given source string"""
        self.units = pickle.loads(data).units

    def savefile(self, storefile):
        """Write the string representation to the given file (or filename)."""
        storestring = str(self)
        if isinstance(storefile, basestring):
            mode = 'w'
            if self._binary:
                mode = 'wb'
            storefile = open(storefile, mode)
        self.fileobj = storefile
        self._assignname()
        storefile.write(storestring)
        storefile.close()

    def save(self):
        """Save to the file that data was originally read from, if
        available."""
        fileobj = getattr(self, "fileobj", None)
        mode = 'w'
        if self._binary:
            mode = 'wb'
        if not fileobj:
            filename = getattr(self, "filename", None)
            if filename:
                fileobj = file(filename, mode)
        else:
            fileobj.close()
            filename = getattr(fileobj, "name",
                               getattr(fileobj, "filename", None))
            if not filename:
                raise ValueError("No file or filename to save to")
            fileobj = fileobj.__class__(filename, mode)
        self.savefile(fileobj)

    @classmethod
    def parsefile(cls, storefile):
        """Reads the given file (or opens the given filename) and parses back
        to an object."""
        mode = 'r'
        if cls._binary:
            mode = 'rb'
        if isinstance(storefile, basestring):
            storefile = open(storefile, mode)
        mode = getattr(storefile, "mode", mode)
        #For some reason GzipFile returns 1, so we have to test for that here
        if mode == 1 or "r" in mode:
            storestring = storefile.read()
            storefile.close()
        else:
            storestring = ""
        newstore = cls.parsestring(storestring)
        newstore.fileobj = storefile
        newstore._assignname()
        return newstore

    @property
    def merge_on(self):
        """The matching criterion to use when merging on.

        :return: The default matching criterion for all the subclasses.
        :rtype: string
        """
        return "id"
