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

"""This module provides a factory to instantiate language classes."""

from translate.lang import common
from translate.lang import data

prefix = "code_"

def getlanguage(code):
    """This returns a language class.

    @param code: The ISO 639 language code
    """
    if code:
        code = code.replace("-", "_").replace("@", "_")
    try:
        try:
            if code is None:
                raise ImportError ("Can't determine language code")
            exec("from translate.lang import %s" % code)
            exec("langclass = %s.%s" % (code, code))
            return langclass(code)
        except SyntaxError, e:
            # Someone is probably trying to import a language of which the code
            # is a reserved word in python (like Icelandic (is) / Oriya (or))
            # The convention to handle these is to have it in a file like  
            # code_is, for example.
            exec("from translate.lang import %s%s" % (prefix, code))
            exec("langclass = %s%s.%s%s" % (prefix, code, prefix, code))
            return langclass(code)
    except ImportError, e:
        if code and code.startswith(prefix):
            code = code[:len(prefix)]
        simplercode = data.simplercode(code)
        if simplercode:
            relatedlanguage = getlanguage(simplercode)
            if isinstance(relatedlanguage, common.Common):
                relatedlanguage = relatedlanguage.__class__(code)
            return relatedlanguage
        else:
            return common.Common(code)
