# -*- coding: utf-8 -*-
#
# Copyright 2002-2009,2011 Zuza Software Foundation
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
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""functions used to manipulate access keys in strings"""

from translate.storage.placeables.general import XMLEntityPlaceable


DEFAULT_ACCESSKEY_MARKER = u"&"


class UnitMixer(object):
    """Helper to mix separately defined labels and accesskeys into one unit."""

    def __init__(self, labelsuffixes, accesskeysuffixes):
        self.labelsuffixes = labelsuffixes
        self.accesskeysuffixes = accesskeysuffixes

    def match_entities(self, index):
        """Populates mixedentities from the index."""
        #: Entities which have a .label/.title and .accesskey combined
        mixedentities = {}
        for entity in index:
            for labelsuffix in self.labelsuffixes:
                if entity.endswith(labelsuffix):
                    entitybase = entity[:entity.rfind(labelsuffix)]
                    # see if there is a matching accesskey in this line,
                    # making this a mixed entity
                    for akeytype in self.accesskeysuffixes:
                        if (entitybase + akeytype) in index:
                            # add both versions to the list of mixed entities
                            mixedentities[entity] = {}
                            mixedentities[entitybase+akeytype] = {}
                    # check if this could be a mixed entity (labelsuffix and
                    # ".accesskey")
        return mixedentities

    def mix_units(self, label_unit, accesskey_unit, target_unit):
        """Mix the given units into the given target_unit if possible.

        Might return None if no match is possible.
        """
        target_unit.addlocations(label_unit.getlocations())
        target_unit.addlocations(accesskey_unit.getlocations())
        target_unit.msgidcomment = target_unit._extract_msgidcomments() + \
                             label_unit._extract_msgidcomments()
        target_unit.msgidcomment = target_unit._extract_msgidcomments() + \
                             accesskey_unit._extract_msgidcomments()
        target_unit.addnote(label_unit.getnotes("developer"), "developer")
        target_unit.addnote(accesskey_unit.getnotes("developer"), "developer")
        target_unit.addnote(label_unit.getnotes("translator"), "translator")
        target_unit.addnote(accesskey_unit.getnotes("translator"), "translator")
        label = label_unit.source
        accesskey = accesskey_unit.source
        label = combine(label, accesskey)
        if label is None:
            return None
        target_unit.source = label
        target_unit.target = ""
        return target_unit

    def find_mixed_pair(self, mixedentities, store, unit):
        entity = unit.getid()
        if entity not in mixedentities:
            return None, None

        # depending on what we come across first, work out the label
        # and the accesskey
        labelentity, accesskeyentity = None, None
        for labelsuffix in self.labelsuffixes:
            if entity.endswith(labelsuffix):
                entitybase = entity[:entity.rfind(labelsuffix)]
                for akeytype in self.accesskeysuffixes:
                    if (entitybase + akeytype) in store.id_index:
                        labelentity = entity
                        accesskeyentity = labelentity[:labelentity.rfind(labelsuffix)] + akeytype
                        break
        else:
            for akeytype in self.accesskeysuffixes:
                if entity.endswith(akeytype):
                    accesskeyentity = entity
                    for labelsuffix in self.labelsuffixes:
                        labelentity = accesskeyentity[:accesskeyentity.rfind(akeytype)] + labelsuffix
                        if labelentity in store.id_index:
                            break
                    else:
                        labelentity = None
                        accesskeyentity = None
        return (labelentity, accesskeyentity)


def extract(string, accesskey_marker=DEFAULT_ACCESSKEY_MARKER):
    """Extract the label and accesskey from a label+accesskey string

    The function will also try to ignore &entities; which would obviously not
    contain accesskeys.

    :type string: Unicode
    :param string: A string that might contain a label with accesskey marker
    :type accesskey_marker: Char
    :param accesskey_marker: The character that is used to prefix an access key
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
            if marker_pos == len(string):
                break
            if (accesskey_marker == '&' and
                XMLEntityPlaceable.regex.match(string[marker_pos-1:])):
                continue
            label = string[:marker_pos-1] + string[marker_pos:]
            if string[marker_pos] != " ":  # FIXME weak filtering
                accesskey = string[marker_pos]
    return label, accesskey


def combine(label, accesskey,
            accesskey_marker=DEFAULT_ACCESSKEY_MARKER):
    """Combine a label and and accesskey to form a label+accesskey string

    We place an accesskey marker before the accesskey in the label and this
    creates a string with the two combined e.g. "File" + "F" = "&File"

    The case of the accesskey is preferred unless no match is found, in which
    case the alternate case is used.

    :type label: unicode
    :param label: a label
    :type accesskey: unicode char
    :param accesskey: The accesskey
    :rtype: unicode or None
    :return: label+accesskey string or None if uncombineable
    """
    assert isinstance(label, unicode)
    assert isinstance(accesskey, unicode)

    if len(accesskey) == 0:
        return None

    searchpos = 0
    accesskeypos = -1
    in_entity = False
    accesskeyaltcasepos = -1

    if accesskey.isupper():
        accesskey_alt_case = accesskey.lower()
    else:
        accesskey_alt_case = accesskey.upper()

    while (accesskeypos < 0) and searchpos < len(label):
        searchchar = label[searchpos]
        if searchchar == '&':
            in_entity = True
        elif searchchar == ';' or searchchar == " ":
            in_entity = False
        if not in_entity:
            if searchchar == accesskey:  # Prefer supplied case
                accesskeypos = searchpos
            elif searchchar == accesskey_alt_case:  # Other case otherwise
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
        return label[:accesskeypos] + accesskey_marker + label[accesskeypos:]
    # can't currently mix accesskey if it's not in label
    return None
