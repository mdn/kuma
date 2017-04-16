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
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""This module represents Spanish language.
However, as it only has special case code for initial inverted punctuation,
it could also be used for Asturian, Galician, or Catalan.
"""

from translate.lang import common
import re

class es(common.Common):
    """This class represents Spanish."""

    def punctranslate(cls, text):
        """Implement some extra features for inverted punctuation.
        """
        text = super(cls, cls).punctranslate(text)
        # If the first sentence ends with ? or !, prepend inverted ¿ or ¡
        firstmatch = cls.sentencere.match(text)
        if firstmatch == None:
            # only one sentence (if any) - use entire string
            first = text
        else:
            first = firstmatch.group()
        # remove trailing whitespace
        first = first.strip()
        # protect against incorrectly handling an empty string
        if not first:
            return text
        if first[-1] == '?':
            text = u"¿" + text
        elif first[-1] == '!':
            text = u"¡" + text
        return text
    punctranslate = classmethod(punctranslate)
