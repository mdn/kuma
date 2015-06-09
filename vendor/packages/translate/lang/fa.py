#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007, 2010 Zuza Software Foundation
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

"""This module represents the Persian language.

.. seealso:: http://en.wikipedia.org/wiki/Persian_language
"""

import re

from translate.lang import common


def guillemets(text):

    def convertquotation(match):
        prefix = match.group(1)
        # Let's see that we didn't perhaps match an XML tag property like
        # <a href="something">
        if prefix == u"=":
            return match.group(0)
        return u"%s«%s»" % (prefix, match.group(2))

    # Check that there is an even number of double quotes, otherwise it is
    # probably not safe to convert them.
    if text.count(u'"') % 2 == 0:
        text = re.sub('(.|^)"([^"]+)"', convertquotation, text)
    singlecount = text.count(u"'")
    if singlecount:
        if singlecount == text.count(u'`'):
            text = re.sub("(.|^)`([^']+)'", convertquotation, text)
        elif singlecount % 2 == 0:
            text = re.sub("(.|^)'([^']+)'", convertquotation, text)
    text = re.sub(u'(.|^)“([^”]+)”', convertquotation, text)
    return text


class fa(common.Common):
    """This class represents Persian."""

    listseperator = u"، "

    puncdict = {
        u",": u"،",
        u";": u"؛",
        u"?": u"؟",
        #This causes problems with variables, so commented out for now:
        #u"%": u"٪",
    }

    ignoretests = ["startcaps", "simplecaps"]
    #TODO: check persian numerics
    #TODO: zwj and zwnj?

    @classmethod
    def punctranslate(cls, text):
        """Implement "French" quotation marks."""
        text = super(cls, cls).punctranslate(text)
        return guillemets(text)
