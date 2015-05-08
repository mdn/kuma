#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007-2009,2011 Zuza Software Foundation
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

"""This module represents the Greek language.

.. seealso:: http://en.wikipedia.org/wiki/Greek_language
"""

import re

from translate.lang import common


class el(common.Common):
    """This class represents Greek."""

    # Greek uses ; as question mark and the middot instead
    sentenceend = u".!;…"

    sentencere = re.compile(ur"""
        (?s)        # make . also match newlines
        .*?         # anything, but match non-greedy
        [%s]        # the puntuation for sentence ending
        \s+         # the spacing after the puntuation
        (?=[^a-zά-ώ\d])  # lookahead that next part starts with caps
        """ % sentenceend, re.VERBOSE | re.UNICODE)

    puncdict = {
        u"?": u";",
        u";": u"·",
    }

    # Valid latin characters for use as accelerators
    valid_latin_accel = u"abcdefghijklmnopqrstuvwxyz" + \
                        u"ABCDEFGHIJKLMNOPQRSTUVWXYZ" + \
                        u"1234567890"

    # Valid greek characters for use as accelerators (accented characters
    # and "ς" omitted)
    valid_greek_accel = u"αβγδεζηθικλμνξοπρστυφχψω" + \
                        u"ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"

    # Valid accelerators
    validaccel = u"".join([valid_latin_accel, valid_greek_accel])
