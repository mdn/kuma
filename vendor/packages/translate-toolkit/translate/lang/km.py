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

"""This module represents Khmer language.

For more information, see U{http://en.wikipedia.org/wiki/Khmer_language}
"""

import re

from translate.lang import common

class km(common.Common):
    """This class represents Khmer."""

    khmerpunc = u"។៕៖៘"
    """These marks are only used for Khmer."""

    punctuation = u"".join([common.Common.commonpunc, common.Common.quotes, common.Common.miscpunc, khmerpunc])

    sentenceend = u"!?…។៕៘"

    sentencere = re.compile(r"""(?s)    #make . also match newlines
                            .*?         #anything, but match non-greedy
                            [%s]        #the puntuation for sentence ending
                            \s+         #the spacing after the puntuation
                            (?=[^a-z\d])#lookahead that next part starts with caps
                            """ % sentenceend, re.VERBOSE)
    #\u00a0 is non-breaking space
    puncdict = {
        u".": u"\u00a0។",
        u":": u"\u00a0៖",
        u"!": u"\u00a0!",
        u"?": u"\u00a0?",
    }

    ignoretests = ["startcaps", "simplecaps"]
