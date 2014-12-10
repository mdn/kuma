#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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
This module implements basic functionality to support placeables.

A placeable is used to represent things like:
  1. Substitutions

     For example, in ODF, footnotes appear in the ODF XML
     where they are defined; so if we extract a paragraph with some
     footnotes, the translator will have a lot of additional XML to with;
     so we separate the footnotes out into separate translation units and
     mark their positions in the original text with placeables.

  2. Hiding of inline formatting data

     The translator doesn't want to have to deal with all the weird
     formatting conventions of wherever the text came from.

  3. Marking variables

     This is an old issue - translators translate variable names which
     should remain untranslated. We can wrap placeables around variable
     names to avoid this.

The placeables model follows the XLIFF standard's list of placeables.
Please refer to the XLIFF specification to get a better understanding.
"""

import base
import interfaces
import general
import xliff
from base import *
from base import __all__ as all_your_base
from strelem import StringElem
from parse import parse

__all__ = ['base', 'interfaces', 'general', 'parse', 'StringElem', 'xliff'] + all_your_base
