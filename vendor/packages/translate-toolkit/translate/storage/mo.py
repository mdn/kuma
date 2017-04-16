#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007 Zuza Software Foundation
#
# the function "__str__" was derived from Python v2.4
#       (Tools/i18n/msgfmt.py - function "generate"):
#   Written by Martin v. Löwis <loewis@informatik.hu-berlin.de>
#   Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006 Python Software Foundation.
#   All rights reserved.
#   original license: Python Software Foundation (version 2)
# 
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

"""Module for parsing Gettext .mo files for translation.

The coding of .mo files was produced from U{Gettext documentation
<http://www.gnu.org/software/gettext/manual/gettext.html#MO-Files>},
Pythons msgfmt.py and by observing and testing existing .mo files in the wild.

The hash algorithm is implemented for MO files, this should result in 
faster access of the MO file.  The hash is optional for Gettext
and is not needed for reading or writing MO files, in this implementation
it is always on and does produce sometimes different results to Gettext
in very small files.
"""

from translate.storage import base
from translate.storage import po
from translate.storage import poheader
from translate.misc.multistring import multistring
import struct
import array
import re

MO_MAGIC_NUMBER = 0x950412deL

def mounpack(filename='messages.mo'):
    """Helper to unpack Gettext MO files into a Python string"""
    f = open(filename)
    s = f.read()
    print "\\x%02x"*len(s) % tuple(map(ord, s))
    f.close()

def my_swap4(result):
    c0 = (result >> 0) & 0xff
    c1 = (result >> 8) & 0xff
    c2 = (result >> 16) & 0xff
    c3 = (result >> 24) & 0xff

    return (c0 << 24) | (c1 << 16) | (c2 << 8) | c3

def hashpjw(str_param):
    HASHWORDBITS = 32
    hval = 0
    g = None
    s = str_param
    for s in str_param:
        hval = hval << 4
        hval += ord(s)
        g = hval & 0xf << (HASHWORDBITS - 4)
        if (g != 0):
            hval = hval ^ g >> (HASHWORDBITS - 8)
            hval = hval ^ g
    return hval

def get_next_prime_number(start):
    # find the smallest prime number that is greater or equal "start"
    def is_prime(num):
        # special small numbers
        if (num < 2) or (num == 4):
            return False
        if (num == 2) or (num == 3):
            return True
        # check for numbers > 4
        for divider in range(2, num/2):
            if num % divider == 0:
                return False
        return True

    candidate = start
    while not is_prime(candidate):
        candidate += 1
    return candidate


class mounit(base.TranslationUnit):
    """A class representing a .mo translation message."""
    def __init__(self, source=None):
        self.msgctxt = []
        self.msgidcomments = []
        super(mounit, self).__init__(source)

    def getcontext(self):
        """Get the message context"""
        # Still need to handle KDE comments
        if self.msgctxt is None:
            return None
        return "".join(self.msgctxt)

    def isheader(self):
        """Is this a header entry?"""
        return self.source == u""

    def istranslatable(self):
        """Is this message translateable?"""
        return bool(self.source)

class mofile(base.TranslationStore, poheader.poheader):
    """A class representing a .mo file."""
    UnitClass = mounit
    Name = _("Gettext MO file")
    Mimetypes  = ["application/x-gettext-catalog", "application/x-mo"]
    Extensions = ["mo", "gmo"]
    _binary = True

    def __init__(self, inputfile=None, unitclass=mounit):
        self.UnitClass = unitclass
        base.TranslationStore.__init__(self, unitclass=unitclass)
        self.filename = ''
        if inputfile is not None:
            self.parsestring(inputfile)

    def __str__(self):
        """Output a string representation of the MO data file"""
        # check the header of this file for the copyright note of this function
        def add_to_hash_table(string, i):
            V = hashpjw(string)
            S = hash_size <= 2 and 3 or hash_size # Taken from gettext-0.17:gettext-tools/src/write-mo.c:408-409
            hash_cursor = V % S;
            orig_hash_cursor = hash_cursor;
            increment = 1 + (V % (S - 2));
            while True:
                index = hash_table[hash_cursor]
                if (index == 0):
                    hash_table[hash_cursor] = i + 1
                    break
                hash_cursor += increment
                hash_cursor = hash_cursor % S
                assert (hash_cursor != orig_hash_cursor)

        # hash_size should be the smallest prime number that is greater
        # or equal (4 / 3 * N) - where N is the number of keys/units.
        # see gettext-0.17:gettext-tools/src/write-mo.c:406
        hash_size = get_next_prime_number(int((len(self.units) * 4) / 3))
        if hash_size <= 2:
            hash_size = 3
        MESSAGES = {}
        for unit in self.units:
            if isinstance(unit.source, multistring):
                source = "".join(unit.msgidcomments) + "\0".join(unit.source.strings)
            else:
                source = "".join(unit.msgidcomments) + unit.source
            if unit.msgctxt:
                source = "".join(unit.msgctxt) + "\x04" + source
            if isinstance(unit.target, multistring):
                target = "\0".join(unit.target.strings)
            else:
                target = unit.target
            if unit.target:
                MESSAGES[source.encode("utf-8")] = target
        # using "I" works for 32- and 64-bit systems, but not for 16-bit!
        hash_table = array.array("I", [0] * hash_size)
        keys = MESSAGES.keys()
        # the keys are sorted in the .mo file
        keys.sort()
        offsets = []
        ids = strs = ''
        for i, id in enumerate(keys):
            # For each string, we need size and file offset.  Each string is NUL
            # terminated; the NUL does not count into the size.
            # TODO: We don't do any encoding detection from the PO Header
            add_to_hash_table(id, i)
            string = MESSAGES[id] # id is already encoded for use as a dictionary key
            if isinstance(string, unicode):
                string = string.encode('utf-8')
            offsets.append((len(ids), len(id), len(strs), len(string)))
            ids = ids + id + '\0'
            strs = strs + string + '\0'
        output = ''
        # The header is 7 32-bit unsigned integers
        keystart = 7*4+16*len(keys)+hash_size*4
        # and the values start after the keys
        valuestart = keystart + len(ids)
        koffsets = []
        voffsets = []
        # The string table first has the list of keys, then the list of values.
        # Each entry has first the size of the string, then the file offset.
        for o1, l1, o2, l2 in offsets:
            koffsets = koffsets + [l1, o1+keystart]
            voffsets = voffsets + [l2, o2+valuestart]
        offsets = koffsets + voffsets
        output = struct.pack("Iiiiiii",
                             MO_MAGIC_NUMBER,   # Magic
                             0,                 # Version
                             len(keys),         # # of entries
                             7*4,               # start of key index
                             7*4+len(keys)*8,   # start of value index
                             hash_size, 7*4+2*(len(keys)*8))              # size and offset of hash table
        # additional data is not necessary for empty mo files
        if (len(keys) > 0):
            output = output + array.array("i", offsets).tostring()
            output = output + hash_table.tostring()
            output = output + ids
            output = output + strs
        return output

    def parse(self, input):
        """parses the given file or file source string"""
        if hasattr(input, 'name'):
            self.filename = input.name
        elif not getattr(self, 'filename', ''):
            self.filename = ''
        if hasattr(input, "read"):
            mosrc = input.read()
            input.close()
            input = mosrc
        little, = struct.unpack("<L", input[:4])
        big, = struct.unpack(">L", input[:4])
        if little == MO_MAGIC_NUMBER:
            endian = "<"
        elif big == MO_MAGIC_NUMBER:
            endian = ">"
        else:
            raise ValueError("This is not an MO file")
        magic, version, lenkeys, startkey, startvalue, sizehash, offsethash = struct.unpack("%sLiiiiii" % endian, input[:(7*4)])
        if version > 1:
            raise ValueError("Unable to process MO files with versions > 1.  This is a %d version MO file" % version)
        encoding = 'UTF-8'
        for i in range(lenkeys):
            nextkey = startkey+(i*2*4)
            nextvalue = startvalue+(i*2*4)
            klength, koffset = struct.unpack("%sii" % endian, input[nextkey:nextkey+(2*4)])
            vlength, voffset = struct.unpack("%sii" % endian, input[nextvalue:nextvalue+(2*4)])
            source = input[koffset:koffset+klength]
            context = None
            if "\x04" in source:
                context, source = source.split("\x04")
            # Still need to handle KDE comments
            source = multistring(source.split("\0"), encoding=encoding)
            if source == "":
                charset = re.search("charset=([^\\s]+)", input[voffset:voffset+vlength])
                if charset:
                    encoding = po.encodingToUse(charset.group(1))
            target = multistring(input[voffset:voffset+vlength].split("\0"), encoding=encoding)
            newunit = mounit(source)
            newunit.settarget(target)
            if context is not None:
                newunit.msgctxt.append(context)
            self.addunit(newunit)
