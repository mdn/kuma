#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007 Zuza Software Foundation
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

"""This module represents the Afrikaans language.

.. seealso:: http://en.wikipedia.org/wiki/Afrikaans_language
"""

import re

from translate.lang import common


articlere = re.compile(r"'n\b")


class af(common.Common):
    """This class represents Afrikaans."""
    validdoublewords = [u"u"]

    punctuation = u"".join([common.Common.commonpunc, common.Common.quotes,
                            common.Common.miscpunc])
    sentenceend = u".!?…"
    sentencere = re.compile(r"""
        (?s)        # make . also match newlines
        .*?         # anything, but match non-greedy
        [%s]        # the puntuation for sentence ending
        \s+         # the spacing after the puntuation
        (?='n\s[A-Z]|[^'a-z\d]|'[^n])
        # lookahead that next part starts with caps or 'n followed by caps
        """ % sentenceend, re.VERBOSE)

    specialchars = u"ëïêôûáéíóúý"

    @classmethod
    def capsstart(cls, text):
        """Modify this for the indefinite article ('n)."""
        match = articlere.search(text, 0, 20)
        if match:
            #construct a list of non-apostrophe punctuation:
            nonapos = u"".join(cls.punctuation.split(u"'"))
            stripped = text.lstrip().lstrip(nonapos)
            match = articlere.match(stripped)
            if match:
                return common.Common.capsstart(stripped[match.end():])
        return common.Common.capsstart(text)

cyr2lat = {
   u"А": "A", u"а": "a",
   u"Б": "B", u"б": "b",
   u"В": "W", u"в": "w",  # Different if at the end of a syllable see rule 2.
   u"Г": "G", u"г": "g",  # see rule 3 and 4
   u"Д": "D", u"д": "d",
   u"ДЖ": "Dj", u"дж": "dj",
   u"Е": "Je", u"е": "je",  # Sometimes e need to check when/why see rule 5.
   u"Ё": "Jo", u"ё": "jo",  # see rule 6
   u"ЕЙ": "Ei", u"ей": "ei",
   u"Ж": "Zj", u"ж": "zj",
   u"З": "Z", u"з": "z",
   u"И": "I", u"и": "i",
   u"Й": "J", u"й": "j",  # see rule 9 and 10
   u"К": "K", u"к": "k",  # see note 11
   u"Л": "L", u"л": "l",
   u"М": "M", u"м": "m",
   u"Н": "N", u"н": "n",
   u"О": "O", u"о": "o",
   u"П": "P", u"п": "p",
   u"Р": "R", u"р": "r",
   u"С": "S", u"с": "s",  # see note 12
   u"Т": "T", u"т": "t",
   u"У": "Oe", u"у": "oe",
   u"Ф": "F", u"ф": "f",
   u"Х": "Ch", u"х": "ch",  # see rule 12
   u"Ц": "Ts", u"ц": "ts",
   u"Ч": "Tj", u"ч": "tj",
   u"Ш": "Sj", u"ш": "sj",
   u"Щ": "Sjtsj", u"щ": "sjtsj",
   u"Ы": "I", u"ы": "i",  # see note 13
   u"Ъ": "", u"ъ": "",  # See note 14
   u"Ь": "", u"ь": "",  # this letter is not in the AWS we assume it is left out as in the previous letter
   u"Э": "E", u"э": "e",
   u"Ю": "Joe", u"ю": "joe",
   u"Я": "Ja", u"я": "ja",
}
"""Mapping of Cyrillic to Latin letters for transliteration in Afrikaans"""

cyr_vowels = u"аеёиоуыэюя"


def tranliterate_cyrillic(text):
    """Convert Cyrillic text to Latin according to the AWS transliteration rules."""
    trans = u""
    for i in text:
        trans += cyr2lat.get(i, i)
    return trans
