#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

"""
This file contains abstract (semantic) interfaces for placeable implementations.
"""

from strelem import StringElem


class InvisiblePlaceable(StringElem):
    parse = None


class MaskingPlaceable(StringElem):
    parse = None


class ReplacementPlaceable(StringElem):
    parse = None


class SubflowPlaceable(StringElem):
    parse = None


class Delimiter(object):
    pass


class PairedDelimiter(object):
    pass
