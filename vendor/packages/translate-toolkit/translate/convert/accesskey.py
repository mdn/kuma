#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2008 Zuza Software Foundation
#
# This file is part of The Translate Toolkit.
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
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""functions used to manipulate access keys in strings"""

from translate.storage.placeables.general import XMLEntityPlaceable

DEFAULT_ACCESSKEY_MARKER = u"&"

def extract(string, accesskey_marker=DEFAULT_ACCESSKEY_MARKER):
    """Extract the label and accesskey from a label+accesskey string

    The function will also try to ignore &entities; which would obviously not
    contain accesskeys.

    @type string: Unicode
    @param string: A string that might contain a label with accesskey marker
    @type accesskey_marker: Char
    @param accesskey_marker: The character that is used to prefix an access key
    """
    assert isinstance(string, unicode)
    assert isinstance(accesskey_marker, unicode)
    assert len(accesskey_marker) == 1
    if string == u"":
        return u"", u""
    accesskey = u""
    label = string
    marker_pos = 0
    while marker_pos >= 0:
        marker_pos = string.find(accesskey_marker, marker_pos)
        if marker_pos != -1:
            marker_pos += 1
            if accesskey_marker == '&' and XMLEntityPlaceable.regex.match(string[marker_pos-1:]):
                continue
            label = string[:marker_pos-1] + string[marker_pos:]
            accesskey = string[marker_pos]
            break
    return label, accesskey

def combine(label, accesskey, 
            accesskey_marker=DEFAULT_ACCESSKEY_MARKER):
    """Combine a label and and accesskey to form a label+accesskey string

    We place an accesskey marker before the accesskey in the label and this creates a 
    string with the two combined e.g. "File" + "F" = "&File"

    @type label: unicode
    @param label: a label
    @type accesskey: unicode char
    @param accesskey: The accesskey
    @rtype: unicode or None
    @return: label+accesskey string or None if uncombineable
    """
    assert isinstance(label, unicode)
    assert isinstance(accesskey, unicode)
    if len(accesskey) == 0:
        return None
    searchpos = 0
    accesskeypos = -1
    in_entity = False
    accesskeyaltcasepos = -1
    while (accesskeypos < 0) and searchpos < len(label):
        searchchar = label[searchpos]
        if searchchar == '&':
            in_entity = True
        elif searchchar == ';':
            in_entity = False
        else:
            if not in_entity:
                if searchchar == accesskey.upper():
                    # always prefer uppercase
                    accesskeypos = searchpos
                if searchchar == accesskey.lower():
                    # take lower case otherwise...
                    if accesskeyaltcasepos == -1:
                        # only want to remember first altcasepos
                        accesskeyaltcasepos = searchpos
                        # note: we keep on looping through in hope 
                        # of exact match
        searchpos += 1
    # if we didn't find an exact case match, use an alternate one if available
    if accesskeypos == -1:
        accesskeypos = accesskeyaltcasepos
    # now we want to handle whatever we found...
    if accesskeypos >= 0:
        string = label[:accesskeypos] + accesskey_marker + label[accesskeypos:]
        string = string.encode("UTF-8", "replace")
        return string
    else:
        # can't currently mix accesskey if it's not in label
        return None
