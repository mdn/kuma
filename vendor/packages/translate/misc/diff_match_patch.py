#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Zuza Software Foundation
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

"""Module for providing backwards compatible diff-match-patch.

Some old third-party apps, like Virtaal, rely on diff-match-patch being
provided by Translate Toolkit.
"""

from __future__ import absolute_import  # Needed because of cyclic self-import.

from diff_match_patch import diff_match_patch
