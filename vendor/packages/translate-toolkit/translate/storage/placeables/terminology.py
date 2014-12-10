#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

"""
Contains the placeable that represents a terminology term.
"""

__all__ = ['TerminologyPlaceable', 'parsers']

from translate.storage.placeables import base, StringElem


class TerminologyPlaceable(base.Ph):
    """Terminology distinguished from the rest of a string by being a placeable."""

    matchers = []
    """A list of matcher objects to use to identify terminology."""
    translations = []
    """The available translations for this placeable."""

    def __init__(self, *args, **kwargs):
        self.translations = []
        super(TerminologyPlaceable, self).__init__(*args, **kwargs)

    @classmethod
    def parse(cls, pstr):
        parts = []
        matches = []
        match_info = {}

        for matcher in cls.matchers:
            matches.extend(matcher.matches(pstr))
            match_info.update(matcher.match_info)

        lastend = 0
        def sort_matches(x, y):
            # This function will sort a list of matches according to the match's starting
            # position, putting the one with the longer source text first, if two are the same.
            c = cmp(match_info[x.source]['pos'], match_info[y.source]['pos'])
            return c and c or cmp(len(y.source), len(x.source))
        matches.sort(sort_matches)

        for match in matches:
            info = match_info[match.source]
            if info['pos'] < lastend:
                continue
            end = info['pos'] + len(match.source)
            if 'newtermlen' in info:
                end = info['pos'] + info['newtermlen']

            if lastend < info['pos']:
                parts.append(StringElem(pstr[lastend:info['pos']]))

            term_string = pstr[info['pos']:end]
            term_placeable = cls([term_string])
            parts.append(term_placeable)

            # Get translations for the placeable
            for m in matches:
                m_info = match_info[m.source]
                m_end = m_info['pos']
                if 'newtermlen' in m_info:
                    m_end += m_info['newtermlen']
                else:
                    m_end += len(m.source)
                if info['pos'] == m_info['pos'] and end == m_end:
                    term_placeable.translations.append(m.target)

            # remove duplicates:
            term_placeable.translations = list(set(term_placeable.translations))

            lastend = end
        if lastend != len(pstr):
            parts.append(StringElem(pstr[lastend:]))

        return parts or None

    def translate(self):
        return self.translations and self.translations[0] or super(TerminologyPlaceable, self).translate()


parsers = [TerminologyPlaceable.parse]
