#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

"""This module represents the Nepali language.

.. seealso:: http://en.wikipedia.org/wiki/Nepali_language
"""

import re

from translate.lang import common


class ne(common.Common):
    """This class represents Nepali."""

    sentenceend = u"।!?…"

    sentencere = re.compile(r"""(?s)    #make . also match newlines
                            .*?         #anything, but match non-greedy
                            \s?         #the single space before the punctuation
                            [%s]        #the puntuation for sentence ending
                            \s+         #the spacing after the puntuation
                            (?=[^a-z\d])#lookahead that next part starts with caps
                            """ % sentenceend, re.VERBOSE)

    puncdict = {
        u".": u" ।",
        u"?": u" ?",
    }

    ignoretests = ["startcaps", "simplecaps", "accelerators"]
