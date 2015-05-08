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
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""A class loader that will load C or Python implementations of the PO class
depending on the USECPO variable.

Use the environment variable USECPO=2 (or 1) to choose the C implementation which
uses Gettext's libgettextpo for high parsing speed.  Otherise the local
Python based parser is used (slower but very well tested)."""

import logging
import os
import platform


usecpo = os.getenv('USECPO')

if platform.python_implementation() == "CPython":
    if usecpo == "1":
        logging.info("Using cPO")
        from translate.storage.cpo import *  # pylint: disable=W0401,W0614
    elif usecpo == "2":
        logging.info("Using new fPO")
        from translate.storage.fpo import *  # pylint: disable=W0401,W0614
    else:
        logging.info("Using Python PO")
        from translate.storage.pypo import *  # pylint: disable=W0401,W0614
else:
    if usecpo:
        logging.error("cPO and fPO do not work on %s defaulting to PyPO" %
                      platform.python_implementation())
    from translate.storage.pypo import *  # pylint: disable=W0401
