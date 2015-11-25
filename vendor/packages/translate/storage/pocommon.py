#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2011 Zuza Software Foundation
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

import re
import urllib

from translate.storage import base, poheader
from translate.storage.workflow import StateEnum as state


msgid_comment_re = re.compile("_: (.*?)\n")


def extract_msgid_comment(text):
    """The one definitive way to extract a msgid comment out of an unescaped
    unicode string that might contain it.

    :rtype: unicode"""
    msgidcomment = msgid_comment_re.match(text)
    if msgidcomment:
        return msgidcomment.group(1)
    return u""


def quote_plus(text):
    """Quote the query fragment of a URL; replacing ' ' with '+'"""
    return urllib.quote_plus(text.encode("utf-8"))


def unquote_plus(text):
    """unquote('%7e/abc+def') -> '~/abc def'"""
    try:
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        return urllib.unquote_plus(text).decode('utf-8')
    except UnicodeEncodeError as e:
        # for some reason there is a non-ascii character here. Let's assume it
        # is already unicode (because of originally decoding the file)
        return text


class pounit(base.TranslationUnit):
    S_FUZZY_OBSOLETE = state.OBSOLETE - 1
    S_OBSOLETE = state.OBSOLETE
    S_UNTRANSLATED = state.EMPTY
    S_FUZZY = state.NEEDS_WORK
    S_TRANSLATED = state.UNREVIEWED

    STATE = {
        S_FUZZY_OBSOLETE: (S_FUZZY_OBSOLETE, state.OBSOLETE),
        S_OBSOLETE: (state.OBSOLETE, state.EMPTY),
        S_UNTRANSLATED: (state.EMPTY, state.NEEDS_WORK),
        S_FUZZY: (state.NEEDS_WORK, state.UNREVIEWED),
        S_TRANSLATED: (state.UNREVIEWED, state.MAX),
    }

    def adderror(self, errorname, errortext):
        """Adds an error message to this unit."""
        text = u'(pofilter) %s: %s' % (errorname, errortext)
        # Don't add the same error twice:
        if text not in self.getnotes(origin='translator'):
            self.addnote(text, origin="translator")

    def geterrors(self):
        """Get all error messages."""
        notes = self.getnotes(origin="translator").split('\n')
        errordict = {}
        for note in notes:
            if '(pofilter) ' in note:
                error = note.replace('(pofilter) ', '')
                errorname, errortext = error.split(': ', 1)
                errordict[errorname] = errortext
        return errordict

    def markreviewneeded(self, needsreview=True, explanation=None):
        """Marks the unit to indicate whether it needs review. Adds an optional explanation as a note."""
        if needsreview:
            reviewnote = "(review)"
            if explanation:
                reviewnote += " " + explanation
            self.addnote(reviewnote, origin="translator")
        else:
            # Strip (review) notes.
            notestring = self.getnotes(origin="translator")
            notes = notestring.split('\n')
            newnotes = []
            for note in notes:
                if not '(review)' in note:
                    newnotes.append(note)
            newnotes = '\n'.join(newnotes)
            self.removenotes()
            self.addnote(newnotes, origin="translator")

    def istranslated(self):
        return super(pounit, self).istranslated() and not self.isobsolete() and not self.isheader()

    def istranslatable(self):
        return not (self.isheader() or self.isblank() or self.isobsolete())

    def hasmarkedcomment(self, commentmarker):
        raise NotImplementedError

    def isreview(self):
        return self.hasmarkedcomment("review") or self.hasmarkedcomment("pofilter")

    def isobsolete(self):
        return self.STATE[self.S_FUZZY_OBSOLETE][0] <= self.get_state_n() < self.STATE[self.S_OBSOLETE][1]

    def isfuzzy(self):
        # implementation specific fuzzy detection, must not use get_state_n()
        raise NotImplementedError()

    def markfuzzy(self, present=True):
        if present:
            self.set_state_n(self.STATE[self.S_FUZZY][0])
        else:
            self.set_state_n(self.STATE[self.S_TRANSLATED][0])
        # set_state_n will check if target exists

    def makeobsolete(self):
        if self.isfuzzy():
            self.set_state_n(self.STATE[self.S_FUZZY_OBSOLETE][0])
        else:
            self.set_state_n(self.STATE[self.S_OBSOLETE][0])

    def resurrect(self):
        self.set_state_n(self.STATE[self.S_TRANSLATED][0])
        if not self.gettarget():
            self.set_state_n(self.STATE[self.S_UNTRANSLATED][0])

    def _domarkfuzzy(self, present=True):
        raise NotImplementedError()

    def get_state_n(self):
        value = super(pounit, self).get_state_n()
        if value <= self.S_OBSOLETE:
            return value
        if self.target:
            if self.isfuzzy():
                return self.S_FUZZY
            else:
                return self.S_TRANSLATED
        else:
            return self.S_UNTRANSLATED

    def set_state_n(self, value):
        super(pounit, self).set_state_n(value)
        has_target = False
        if self.hasplural():
            for string in self.target.strings:
                if string:
                    has_target = True
                    break
        else:
            has_target = bool(self.target)
        if has_target:
            isfuzzy = self.STATE[self.S_FUZZY][0] <= value < self.STATE[self.S_FUZZY][1] or \
                    self.STATE[self.S_FUZZY_OBSOLETE][0] <= value < self.STATE[self.S_FUZZY_OBSOLETE][1]
            self._domarkfuzzy(isfuzzy)  # Implementation specific fuzzy-marking
        else:
            super(pounit, self).set_state_n(self.S_UNTRANSLATED)
            self._domarkfuzzy(False)


def encodingToUse(encoding):
    """Tests whether the given encoding is known in the python runtime, or returns utf-8.
    This function is used to ensure that a valid encoding is always used."""
    if encoding == "CHARSET" or encoding is None:
        return 'utf-8'
    return encoding
#    if encoding is None: return False
#    return True
#    try:
#        tuple = codecs.lookup(encoding)
#    except LookupError:
#        return False
#    return True


class pofile(poheader.poheader, base.TranslationStore):
    Name = "Gettext PO file"  # pylint: disable=E0602
    Mimetypes = ["text/x-gettext-catalog", "text/x-gettext-translation", "text/x-po", "text/x-pot"]
    Extensions = ["po", "pot"]
    # We don't want windows line endings on Windows:
    _binary = True

    def __init__(self, inputfile=None, encoding=None):
        super(pofile, self).__init__(unitclass=self.UnitClass)
        self.units = []
        self.filename = ''
        self._encoding = encodingToUse(encoding)
        if inputfile is not None:
            self.parse(inputfile)
        else:
            self.init_headers()

    @property
    def merge_on(self):
        """The matching criterion to use when merging on."""
        return self.parseheader().get('X-Merge-On', 'id')
