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

"""Classes that hold units of .po files (pounit) or entire files (pofile).

Gettext-style .po (or .pot) files are used in translations for KDE, GNOME and
many other projects.

This uses libgettextpo from the gettext package. Any version before 0.17 will
at least cause some subtle bugs or may not work at all. Developers might want
to have a look at gettext-tools/libgettextpo/gettext-po.h from the gettext
package for the public API of the library.
"""

from translate.misc.multistring import multistring
from translate.storage import pocommon
from translate.storage.pocommon import encodingToUse
from translate.misc import quote
from translate.lang import data
from ctypes import *
import ctypes.util
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import os
import pypo
import re
import sys
import tempfile

lsep = " "
"""Seperator for #: entries"""

STRING = c_char_p

# Structures
class po_message(Structure):
    _fields_ = []

# Function prototypes
xerror_prototype = CFUNCTYPE(None, c_int, POINTER(po_message), STRING, c_uint, c_uint, c_int, STRING)
xerror2_prototype = CFUNCTYPE(None, c_int, POINTER(po_message), STRING, c_uint, c_uint, c_int, STRING, POINTER(po_message), STRING, c_uint, c_uint, c_int, STRING)


# Structures (error handler)
class po_xerror_handler(Structure):
    _fields_ = [('xerror', xerror_prototype),
                ('xerror2', xerror2_prototype)]

class po_error_handler(Structure):
    _fields_ = [
    ('error', CFUNCTYPE(None, c_int, c_int, STRING)),
    ('error_at_line', CFUNCTYPE(None, c_int, c_int, STRING, c_uint, STRING)),
    ('multiline_warning', CFUNCTYPE(None, STRING, STRING)),
    ('multiline_error', CFUNCTYPE(None, STRING, STRING)),
]

# Callback functions for po_xerror_handler
def xerror_cb(severity, message, filename, lineno, column, multilint_p, message_text):
    print >> sys.stderr, "xerror_cb", severity, message, filename, lineno, column, multilint_p, message_text
    if severity >= 1:
        raise ValueError(message_text)

def xerror2_cb(severity, message1, filename1, lineno1, column1, multiline_p1, message_text1, message2, filename2, lineno2, column2, multiline_p2, message_text2):
    print >> sys.stderr, "xerror2_cb", severity, message1, filename1, lineno1, column1, multiline_p1, message_text1, message2, filename2, lineno2, column2, multiline_p2, message_text2
    if severity >= 1:
        raise ValueError(message_text1)



# Load libgettextpo
gpo = None
# 'gettextpo' is recognised on Unix, while only 'libgettextpo' is recognised on
# windows. Therefore we test both.
names = ['gettextpo', 'libgettextpo']
for name in names:
    lib_location = ctypes.util.find_library(name)
    if lib_location:
        gpo = cdll.LoadLibrary(lib_location)
        if gpo:
            break
else:
    # Now we are getting desperate, so let's guess a unix type DLL that might 
    # be in LD_LIBRARY_PATH or loaded with LD_PRELOAD
    try:
        gpo = cdll.LoadLibrary('libgettextpo.so')
    except OSError, e:
        raise ImportError("gettext PO library not found")

# Setup return and paramater types
# File access
gpo.po_file_read_v3.argtypes = [STRING, POINTER(po_xerror_handler)]
gpo.po_file_write_v2.argtypes = [c_int, STRING, POINTER(po_xerror_handler)]
gpo.po_file_write_v2.retype = c_int

# Header
gpo.po_file_domain_header.restype = STRING
gpo.po_header_field.restype = STRING
gpo.po_header_field.argtypes = [STRING, STRING]

# Locations (filepos)
gpo.po_filepos_file.restype = STRING
gpo.po_message_filepos.restype = c_int
gpo.po_message_filepos.argtypes = [c_int, c_int]
gpo.po_message_add_filepos.argtypes = [c_int, STRING, c_int]

# Message (get methods)
gpo.po_message_comments.restype = STRING
gpo.po_message_extracted_comments.restype = STRING
gpo.po_message_prev_msgctxt.restype = STRING
gpo.po_message_prev_msgid.restype = STRING
gpo.po_message_prev_msgid_plural.restype = STRING
gpo.po_message_is_format.restype = c_int
gpo.po_message_is_format.argtypes = [c_int, STRING]
gpo.po_message_set_format.argtypes = [c_int, STRING, c_int]
gpo.po_message_msgctxt.restype = STRING
gpo.po_message_msgid.restype = STRING
gpo.po_message_msgid_plural.restype = STRING
gpo.po_message_msgstr.restype = STRING
gpo.po_message_msgstr_plural.restype = STRING

# Message (set methods)
gpo.po_message_set_comments.argtypes = [c_int, STRING]
gpo.po_message_set_extracted_comments.argtypes = [c_int, STRING]
gpo.po_message_set_fuzzy.argtypes = [c_int, c_int]
gpo.po_message_set_msgctxt.argtypes = [c_int, STRING]

# Setup the po_xerror_handler
xerror_handler = po_xerror_handler()
xerror_handler.xerror = xerror_prototype(xerror_cb)
xerror_handler.xerror2 = xerror2_prototype(xerror2_cb)

def escapeforpo(text):
    return pypo.escapeforpo(text)

def quoteforpo(text):
    return pypo.quoteforpo(text)

def unquotefrompo(postr):
    return pypo.unquotefrompo(postr)

def get_libgettextpo_version():
    """Returns the libgettextpo version

       @rtype: three-value tuple
       @return: libgettextpo version in the following format::
           (major version, minor version, subminor version)
    """
    libversion = c_long.in_dll(gpo, 'libgettextpo_version')
    major = libversion.value >> 16
    minor = libversion.value >> 8
    subminor = libversion.value - (major << 16) - (minor << 8)
    return major, minor, subminor


class pounit(pocommon.pounit):
    def __init__(self, source=None, encoding='utf-8', gpo_message=None):
        self._rich_source = None
        self._rich_target = None
        self._encoding = encoding
        if not gpo_message:
            self._gpo_message = gpo.po_message_create()
        if source or source == "":
            self.source = source
            self.target = ""
        elif gpo_message:
            self._gpo_message = gpo_message

    def setmsgid_plural(self, msgid_plural): 
        if isinstance(msgid_plural, list):
            msgid_plural = "".join(msgid_plural)
        gpo.po_message_set_msgid_plural(self._gpo_message, msgid_plural)
    msgid_plural = property(None, setmsgid_plural)

    def getsource(self):
        def remove_msgid_comments(text):
            if not text:
                return text
            if text.startswith("_:"):
                remainder = re.search(r"_: .*\n(.*)", text)
                if remainder:
                    return remainder.group(1)
                else:
                    return u""
            else:
                return text
        singular = remove_msgid_comments(gpo.po_message_msgid(self._gpo_message).decode(self._encoding))
        if singular:
            if self.hasplural():
                multi = multistring(singular, self._encoding)
                pluralform = gpo.po_message_msgid_plural(self._gpo_message).decode(self._encoding)
                multi.strings.append(pluralform)
                return multi
            else:
                return singular
        else:
            return u""

    def setsource(self, source):
        if isinstance(source, multistring):
            source = source.strings
        if isinstance(source, unicode):
            source = source.encode(self._encoding)
        if isinstance(source, list):
            gpo.po_message_set_msgid(self._gpo_message, source[0].encode(self._encoding))
            if len(source) > 1:
                gpo.po_message_set_msgid_plural(self._gpo_message, source[1].encode(self._encoding))
        else:
            gpo.po_message_set_msgid(self._gpo_message, source)
            gpo.po_message_set_msgid_plural(self._gpo_message, None)
            
    source = property(getsource, setsource)

    def gettarget(self):
        if self.hasplural():
            plurals = []
            nplural = 0
            plural = gpo.po_message_msgstr_plural(self._gpo_message, nplural)
            while plural:
                plurals.append(plural.decode(self._encoding))
                nplural += 1
                plural = gpo.po_message_msgstr_plural(self._gpo_message, nplural)
            if plurals:
                multi = multistring(plurals, encoding=self._encoding)
            else:
                multi = multistring(u"")
        else:
            multi = (gpo.po_message_msgstr(self._gpo_message) or "").decode(self._encoding)
        return multi

    def settarget(self, target):
        # for plural strings: convert 'target' into a list
        if self.hasplural():
            if isinstance(target, multistring):
                target = target.strings
            elif isinstance(target, basestring):
                target = [target]
        # for non-plurals: check number of items in 'target'
        elif isinstance(target, (dict, list)):
            if len(target) == 1:
                target = target[0]
            else:
                raise ValueError("po msgid element has no plural but msgstr has %d elements (%s)" % (len(target), target))
        # empty the previous list of messages
        # TODO: the "pypo" implementation does not remove the previous items of
        #   the target, if self.target == target (essentially: comparing only
        #   the first item of a plural string with the single new string)
        #   Maybe this behaviour should be unified.
        if isinstance(target, (dict, list)):
            i = 0
            message = gpo.po_message_msgstr_plural(self._gpo_message, i)
            while message is not None:
                gpo.po_message_set_msgstr_plural(self._gpo_message, i, None)
                i += 1
                message = gpo.po_message_msgstr_plural(self._gpo_message, i)
        # add the items of a list
        if isinstance(target, list):
            for i in range(len(target)):
                targetstring = target[i]
                if isinstance(targetstring, unicode):
                    targetstring = targetstring.encode(self._encoding)
                gpo.po_message_set_msgstr_plural(self._gpo_message, i, targetstring)
        # add the values of a dict
        elif isinstance(target, dict):
            for i, targetstring in enumerate(target.itervalues()):
                gpo.po_message_set_msgstr_plural(self._gpo_message, i, targetstring)
        # add a single string
        else:
            if isinstance(target, unicode):
                target = target.encode(self._encoding)
            if target is None:
                gpo.po_message_set_msgstr(self._gpo_message, "")
            else:
                gpo.po_message_set_msgstr(self._gpo_message, target)
    target = property(gettarget, settarget)

    def getid(self):
        """The unique identifier for this unit according to the convensions in
        .mo files."""
        id = (gpo.po_message_msgid(self._gpo_message) or "").decode(self._encoding)
        # Gettext does not consider the plural to determine duplicates, only 
        # the msgid. For generation of .mo files, we might want to use this
        # code to generate the entry for the hash table, but for now, it is 
        # commented out for conformance to gettext.
#        plural = gpo.po_message_msgid_plural(self._gpo_message)
#        if not plural is None:
#            id = '%s\0%s' % (id, plural)
        context = gpo.po_message_msgctxt(self._gpo_message)
        if context:
            id = u"%s\04%s" % (context.decode(self._encoding), id)
        return id

    def getnotes(self, origin=None):
        if origin == None:
            comments = gpo.po_message_comments(self._gpo_message) + \
                       gpo.po_message_extracted_comments(self._gpo_message)
        elif origin == "translator":
            comments = gpo.po_message_comments(self._gpo_message)
        elif origin in ["programmer", "developer", "source code"]:
            comments = gpo.po_message_extracted_comments(self._gpo_message)
        else:
            raise ValueError("Comment type not valid")

        if comments and get_libgettextpo_version() < (0, 17, 0):
            comments = "\n".join([line.strip() for line in comments.split("\n")])
        # Let's drop the last newline
        return comments[:-1].decode(self._encoding)

    def addnote(self, text, origin=None, position="append"):
        # ignore empty strings and strings without non-space characters
        if not (text and text.strip()):
            return
        text = data.forceunicode(text)
        oldnotes = self.getnotes(origin)
        newnotes = None
        if oldnotes:
            if position == "append":
                newnotes = oldnotes + "\n" + text
            elif position == "merge":
                if oldnotes != text:
                    oldnoteslist = oldnotes.split("\n")
                    for newline in text.split("\n"):
                        newline = newline.rstrip()
                        # avoid duplicate comment lines (this might cause some problems)
                        if newline not in oldnotes or len(newline) < 5:
                            oldnoteslist.append(newline)
                    newnotes = "\n".join(oldnoteslist)
            else:
                newnotes = text + '\n' + oldnotes
        else:
            newnotes = "\n".join([line.rstrip() for line in text.split("\n")])

        if newnotes:
            newlines = []
            needs_space = get_libgettextpo_version() < (0, 17, 0)
            for line in newnotes.split("\n"):
                if line and needs_space:
                    newlines.append(" " + line)
                else:
                    newlines.append(line)
            newnotes = "\n".join(newlines).encode(self._encoding)
            if origin in ["programmer", "developer", "source code"]:
                gpo.po_message_set_extracted_comments(self._gpo_message, newnotes)
            else:
                gpo.po_message_set_comments(self._gpo_message, newnotes)

    def removenotes(self):
        gpo.po_message_set_comments(self._gpo_message, "")

    def copy(self):
        newpo = self.__class__()
        newpo._gpo_message = self._gpo_message
        return newpo

    def merge(self, otherpo, overwrite=False, comments=True, authoritative=False):
        """Merges the otherpo (with the same msgid) into this one.

        Overwrite non-blank self.msgstr only if overwrite is True
        merge comments only if comments is True
        """

        if not isinstance(otherpo, pounit):
            super(pounit, self).merge(otherpo, overwrite, comments)
            return
        if comments:
            self.addnote(otherpo.getnotes("translator"), origin="translator", position="merge")
            # FIXME mergelists(self.typecomments, otherpo.typecomments)
            if not authoritative:
                # We don't bring across otherpo.automaticcomments as we consider ourself
                # to be the the authority.  Same applies to otherpo.msgidcomments
                self.addnote(otherpo.getnotes("developer"), origin="developer", position="merge")
                self.msgidcomment = otherpo._extract_msgidcomments() or None
                self.addlocations(otherpo.getlocations())
        if not self.istranslated() or overwrite:
            # Remove kde-style comments from the translation (if any).
            if self._extract_msgidcomments(otherpo.target):
                otherpo.target = otherpo.target.replace('_: ' + otherpo._extract_msgidcomments()+ '\n', '')
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
        #return self.source == u"" and self.target != u""
        # we really want to make sure that there is no msgidcomment or msgctxt
        return self.getid() == "" and len(self.target) > 0

    def isblank(self):
        return len(self.source) == len(self.target) == len(self.getcontext()) == 0

    def hastypecomment(self, typecomment):
        return gpo.po_message_is_format(self._gpo_message, typecomment)

    def settypecomment(self, typecomment, present=True):
        gpo.po_message_set_format(self._gpo_message, typecomment, present)

    def hasmarkedcomment(self, commentmarker):
        commentmarker = "(%s)" % commentmarker
        for comment in self.getnotes("translator").split("\n"):
            if comment.startswith(commentmarker):
                return True
        return False

    def isfuzzy(self):
        return gpo.po_message_is_fuzzy(self._gpo_message)

    def markfuzzy(self, present=True):
        gpo.po_message_set_fuzzy(self._gpo_message, present)

    def isobsolete(self):
        return gpo.po_message_is_obsolete(self._gpo_message)

    def makeobsolete(self):
        # FIXME: libgettexpo currently does not reset other data, we probably want to do that
        # but a better solution would be for libgettextpo to output correct data on serialisation
        gpo.po_message_set_obsolete(self._gpo_message, True)

    def resurrect(self):
        gpo.po_message_set_obsolete(self._gpo_message, False)

    def hasplural(self):
        return gpo.po_message_msgid_plural(self._gpo_message) is not None

    def _extract_msgidcomments(self, text=None):
        """Extract KDE style msgid comments from the unit.

        @rtype: String
        @return: Returns the extracted msgidcomments found in this unit's msgid.
        """
        if not text:
            text = gpo.po_message_msgid(self._gpo_message).decode(self._encoding)
        if text:
            return pocommon.extract_msgid_comment(text)
        return u""

    def setmsgidcomment(self, msgidcomment):
        if msgidcomment:
            self.source = u"_: %s\n%s" % (msgidcomment, self.source)
    msgidcomment = property(_extract_msgidcomments, setmsgidcomment)

    def __str__(self):
        pf = pofile()
        pf.addunit(self)
        return str(pf)

    def getlocations(self):
        locations = []
        i = 0
        location = gpo.po_message_filepos(self._gpo_message, i)
        while location:
            locname = gpo.po_filepos_file(location)
            locline = gpo.po_filepos_start_line(location)
            if locline == -1:
                locstring = locname
            else:
                locstring = locname + ":" + str(locline)
            locations.append(locstring)
            i += 1
            location = gpo.po_message_filepos(self._gpo_message, i)
        return locations

    def addlocation(self, location):
        for loc in location.split():
            parts = loc.split(":")
            file = parts[0]
            if len(parts) == 2:
                line = int(parts[1] or "0")
            else:
                line = -1
            gpo.po_message_add_filepos(self._gpo_message, file, line)

    def getcontext(self):
        msgctxt = gpo.po_message_msgctxt(self._gpo_message)
        if msgctxt:
            return msgctxt.decode(self._encoding)
        else:
            msgidcomment = self._extract_msgidcomments()
            return msgidcomment

    def buildfromunit(cls, unit):
        """Build a native unit from a foreign unit, preserving as much
        information as possible."""
        if type(unit) == cls and hasattr(unit, "copy") and callable(unit.copy):
            return unit.copy()
        elif isinstance(unit, pocommon.pounit):
            newunit = cls(unit.source)
            newunit.target = unit.target
            #context
            newunit.msgidcomment = unit._extract_msgidcomments()
            context = unit.getcontext()
            if not newunit.msgidcomment and context:
                gpo.po_message_set_msgctxt(newunit._gpo_message, context)

            locations = unit.getlocations()
            if locations:
                newunit.addlocations(locations)
            notes = unit.getnotes("developer")
            if notes:
                newunit.addnote(notes, "developer")
            notes = unit.getnotes("translator")
            if notes:
                newunit.addnote(notes, "translator")
            if unit.isobsolete():
                newunit.makeobsolete()
            newunit.markfuzzy(unit.isfuzzy())
            for tc in ['python-format', 'c-format', 'php-format']:
                if unit.hastypecomment(tc):
                    newunit.settypecomment(tc)
                    # We assume/guess/hope that there will only be one
                    break
            return newunit
        else:
            return base.TranslationUnit.buildfromunit(unit)
    buildfromunit = classmethod(buildfromunit)

class pofile(pocommon.pofile):
    UnitClass = pounit
    def __init__(self, inputfile=None, encoding=None, unitclass=pounit):
        self._gpo_memory_file = None
        self._gpo_message_iterator = None
        super(pofile, self).__init__(inputfile=inputfile, encoding=encoding)
        if inputfile is None:
            self._gpo_memory_file = gpo.po_file_create()
            self._gpo_message_iterator = gpo.po_message_iterator(self._gpo_memory_file, None)

    def addunit(self, unit, new=True):
        if new:
            gpo.po_message_insert(self._gpo_message_iterator, unit._gpo_message)
        super(pofile, self).addunit(unit)

    def removeduplicates(self, duplicatestyle="merge"):
        """make sure each msgid is unique ; merge comments etc from duplicates into original"""
        # TODO: can we handle consecutive calls to removeduplicates()? What
        # about files already containing msgctxt? - test
        id_dict = {}
        uniqueunits = []
        # TODO: this is using a list as the pos aren't hashable, but this is slow.
        # probably not used frequently enough to worry about it, though.
        markedpos = []
        def addcomment(thepo):
            thepo.msgidcomment = " ".join(thepo.getlocations())
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
                    if origpo not in markedpos:
                        gpo.po_message_set_msgctxt(origpo._gpo_message, " ".join(origpo.getlocations()))
                        markedpos.append(thepo)
                    gpo.po_message_set_msgctxt(thepo._gpo_message, " ".join(thepo.getlocations()))
                    uniqueunits.append(thepo)
            else:
                if not id:
                    if duplicatestyle == "merge":
                        addcomment(thepo)
                    else:
                        gpo.po_message_set_msgctxt(thepo._gpo_message, " ".join(thepo.getlocations()))
                id_dict[id] = thepo
                uniqueunits.append(thepo)
        new_gpo_memory_file = gpo.po_file_create()
        new_gpo_message_iterator = gpo.po_message_iterator(new_gpo_memory_file, None)
        for unit in uniqueunits:
            gpo.po_message_insert(new_gpo_message_iterator, unit._gpo_message)
        gpo.po_message_iterator_free(self._gpo_message_iterator)
        self._gpo_message_iterator = new_gpo_message_iterator
        self._gpo_memory_file = new_gpo_memory_file
        self.units = uniqueunits

    def __str__(self):
        def obsolete_workaround():
            # Remove all items that are not output by msgmerge when a unit is obsolete.  This is a work 
            # around for bug in libgettextpo
            # FIXME Do version test in case they fix this bug
            for unit in self.units:
                if unit.isobsolete():
                    gpo.po_message_set_extracted_comments(unit._gpo_message, "")
                    location = gpo.po_message_filepos(unit._gpo_message, 0)
                    while location:
                        gpo.po_message_remove_filepos(unit._gpo_message, 0)
                        location = gpo.po_message_filepos(unit._gpo_message, 0)
        outputstring = ""
        if self._gpo_memory_file:
            obsolete_workaround()
            f, fname = tempfile.mkstemp(prefix='translate', suffix='.po')
            os.close(f)
            self._gpo_memory_file = gpo.po_file_write_v2(self._gpo_memory_file, fname, xerror_handler)
            f = open(fname)
            outputstring = f.read()
            f.close()
            os.remove(fname)
        return outputstring

    def isempty(self):
        """Returns True if the object doesn't contain any translation units."""
        if len(self.units) == 0:
            return True
        # Skip the first unit if it is a header.
        if self.units[0].isheader():
            units = self.units[1:]
        else:
            units = self.units

        for unit in units:
            if not unit.isblank() and not unit.isobsolete():
                return False
        return True

    def parse(self, input):
        if hasattr(input, 'name'):
            self.filename = input.name
        elif not getattr(self, 'filename', ''):
            self.filename = ''

        if hasattr(input, "read"):
            posrc = input.read()
            input.close()
            input = posrc

        needtmpfile = not os.path.isfile(input)
        if needtmpfile:
            # This is not a file - we write the string to a temporary file
            fd, fname = tempfile.mkstemp(prefix='translate', suffix='.po')
            os.write(fd, input)
            input = fname
            os.close(fd)

        self._gpo_memory_file = gpo.po_file_read_v3(input, xerror_handler)
        if self._gpo_memory_file is None:
            print >> sys.stderr, "Error:"

        if needtmpfile:
            os.remove(input)

        # Handle xerrors here
        self._header = gpo.po_file_domain_header(self._gpo_memory_file, None)
        if self._header:
            charset = gpo.po_header_field(self._header, "Content-Type")
            if charset:
                charset = re.search("charset=([^\\s]+)", charset).group(1)
            self._encoding = encodingToUse(charset)
        self._gpo_message_iterator = gpo.po_message_iterator(self._gpo_memory_file, None)
        newmessage = gpo.po_next_message(self._gpo_message_iterator)
        while newmessage:
            newunit = pounit(gpo_message=newmessage, encoding=self._encoding)
            self.addunit(newunit, new=False)
            newmessage = gpo.po_next_message(self._gpo_message_iterator)
        self._free_iterator()

    def __del__(self):
        # We currently disable this while we still get segmentation faults.
        # Note that this is definitely leaking memory because of this.
        return
        self._free_iterator()
        if self._gpo_memory_file is not None:
            gpo.po_file_free(self._gpo_memory_file)
            self._gpo_memory_file = None

    def _free_iterator(self):
        # We currently disable this while we still get segmentation faults.
        # Note that this is definitely leaking memory because of this.
        return
        if self._gpo_message_iterator is not None:
            gpo.po_message_iterator_free(self._gpo_message_iterator)
            self._gpo_message_iterator = None
