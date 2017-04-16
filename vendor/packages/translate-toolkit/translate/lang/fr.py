#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007-2009 Zuza Software Foundation
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

"""This module represents French language.

For more information, see U{http://en.wikipedia.org/wiki/French_language}
"""

from translate.lang import common
import re

def guillemets(text):
    def convertquotation(match):
        prefix = match.group(1)
        # Let's see that we didn't perhaps match an XML tag property like
        # <a href="something">
        if prefix == u"=":
            return match.group(0)
        return u"%s«\u00a0%s\u00a0»" % (prefix, match.group(2)) #\u00a0 is NBSP

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

class fr(common.Common):
    """This class represents French."""

    validaccel = u"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890" + u"éÉ"

    # According to http://french.about.com/library/writing/bl-punctuation.htm, 
    # in French, a space is required both before and after all two- (or more) 
    # part punctuation marks and symbols, including : ; « » ! ? % $ # etc.
    puncdict = {}
    for c in u":;!?#":
        puncdict[c] = u"\u00a0%s" % c
    # TODO: consider adding % and $, but think about the consequences of how 
    # they could be part of variables

    def punctranslate(cls, text):
        """Implement some extra features for quotation marks.

        Known shortcomings:
            - % and $ are not touched yet for fear of variables
            - Double spaces might be introduced
        """
        text = super(cls, cls).punctranslate(text)
        # We might get problems where we got a space in URIs such as
        # http ://
        text = text.replace(u"\u00a0://", "://")
        return guillemets(text)
    punctranslate = classmethod(punctranslate)
