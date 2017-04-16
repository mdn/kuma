#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2002-2007 Zuza Software Foundation
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

from translate.storage import base
from translate.storage import poheader

import re

msgid_comment_re = re.compile("_: (.*?)\n")

def extract_msgid_comment(text):
    """The one definitive way to extract a msgid comment out of an unescaped
    unicode string that might contain it.

    @rtype: unicode"""
    msgidcomment = msgid_comment_re.match(text)
    if msgidcomment:
        return msgidcomment.group(1)
    return u""


class pounit(base.TranslationUnit):

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
                errorname, errortext = error.split(': ')
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
        return super(pounit, self).istranslated() and not self.isobsolete()

    def istranslatable(self):
        return not (self.isheader() or self.isblank() or self.isobsolete())

    def isreview(self):
        return self.hasmarkedcomment("review") or self.hasmarkedcomment("pofilter")


def encodingToUse(encoding):
    """Tests whether the given encoding is known in the python runtime, or returns utf-8.
    This function is used to ensure that a valid encoding is always used."""
    if encoding == "CHARSET" or encoding == None:
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
    Name = _("Gettext PO file")
    Mimetypes  = ["text/x-gettext-catalog", "text/x-gettext-translation", "text/x-po", "text/x-pot"]
    Extensions = ["po", "pot"]

    def __init__(self, inputfile=None, encoding=None):
        super(pofile, self).__init__(unitclass=self.UnitClass)
        self.units = []
        self.filename = ''
        self._encoding = encodingToUse(encoding)
        if inputfile is not None:
            self.parse(inputfile)
        else:
            self.init_headers()

