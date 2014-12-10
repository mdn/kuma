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

"""This module represents Amharic language.

For more information, see U{http://en.wikipedia.org/wiki/Amharic_language}
"""

import re

from translate.lang import common

class am(common.Common):
    """This class represents Amharic."""

    listseperator = u"፣ "

    sentenceend = u"።!?…"

    sentencere = re.compile(r"""(?s)    #make . also match newlines
                            .*?         #anything, but match non-greedy
                            [%s]        #the puntuation for sentence ending
                            \s*         #optional spacing after the puntuation
                            """ % sentenceend, re.VERBOSE)
    
    puncdict = {
        u".": u"።",
        u";": u"፤",
        u",": u"፣",
    }

    ignoretests = ["startcaps", "simplecaps"]
