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

"""This module represents Afrikaans language.

For more information, see U{http://en.wikipedia.org/wiki/Afrikaans_language}
"""

from translate.lang import common
import re

articlere = re.compile(r"'n\b")

class af(common.Common):
    """This class represents Afrikaans."""

    punctuation = u"".join([common.Common.commonpunc, common.Common.quotes, common.Common.miscpunc])
    sentenceend = u".!?…"
    sentencere = re.compile(r"""(?s)    #make . also match newlines
                            .*?         #anything, but match non-greedy
                            [%s]        #the puntuation for sentence ending
                            \s+         #the spacing after the puntuation
                            (?='n\s[A-Z]|[^'a-z\d]|'[^n])
                            #lookahead that next part starts with caps or 'n followed by caps
                            """ % sentenceend, re.VERBOSE)

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
    capsstart = classmethod(capsstart)
