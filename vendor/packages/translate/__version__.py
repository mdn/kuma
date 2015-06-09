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

"""This file contains the version of the Translate Toolkit."""

build = 12021
"""The build number is used by external users of the Translate Toolkit to
trigger refreshes.  Thus increase the build number whenever changes are made to
code touching stats or quality checks.  An increased build number will force a
toolkit user, like Pootle, to regenerate it's stored stats and check
results."""

sver = "1.12.0"
"""Human readable version number. Used for version number display."""

ver = (1, 12, 0)
"""Machine readable version number. Used by tools that need to adjust code
paths based on a Translate Toolkit release number."""
