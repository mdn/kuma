#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2005, 2006, 2009 Zuza Software Foundation
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

"""A set of autocorrect functions that fix common punctuation and space problems automatically"""

from translate.filters import decoration

def correct(source, target):
    """Runs a set of easy and automatic corrections

    Current corrections include:
      - Ellipses - align target to use source form of ellipses (either three dots or the Unicode ellipses characters)
      - Missing whitespace and start or end of the target
      - Missing punction (.:?) at the end of the target
    """
    assert isinstance(source, unicode)
    assert isinstance(target, unicode)
    if target == "":
        return target
    if "..." in source and u"…" in target:
        return target.replace(u"…", "...")
    if u"…" in source and "..." in target:
        return target.replace("...", u"…")
    if decoration.spacestart(source) != decoration.spacestart(target) or decoration.spaceend(source) != decoration.spaceend(target):
        return decoration.spacestart(source) + target.strip() + decoration.spaceend(source)
    punctuation = (".", ":", ". ", ": ", "?")
    puncendid = decoration.puncend(source, punctuation)
    puncendstr = decoration.puncend(target, punctuation)
    if puncendid != puncendstr:
        if not puncendstr:
            return target + puncendid
    if source[:1].isalpha() and target[:1].isalpha():
        if source[:1].isupper() and target[:1].islower():
            return target[:1].upper() + target[1:]
        elif source[:1].islower() and target[:1].isupper():
            return target[:1].lower() + target[1:]
    return None
