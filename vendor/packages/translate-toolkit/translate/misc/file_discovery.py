#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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
#

__all__ = ['get_abs_data_filename']

import sys
import os

def get_abs_data_filename(path_parts, basedirs=None):
    """Get the absolute path to the given file- or directory name in the current
        running application's data directory.

        @type  path_parts: list
        @param path_parts: The path parts that can be joined by os.path.join().
        """
    if basedirs is None:
        basedirs = []

    if isinstance(path_parts, str):
        path_parts = [path_parts]

    BASE_DIRS = basedirs + [
        os.path.dirname(unicode(__file__, sys.getfilesystemencoding())),
        os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    ]

    # Freedesktop standard
    if 'XDG_DATA_HOME' in os.environ:
        BASE_DIRS += [os.environ['XDG_DATA_HOME']]
    if 'XDG_DATA_DIRS' in os.environ:
        BASE_DIRS += os.environ['XDG_DATA_DIRS'].split(os.path.pathsep)

    # Mac OSX app bundles
    if 'RESOURCEPATH' in os.environ:
        BASE_DIRS += os.environ['RESOURCEPATH'].split(os.path.pathsep)

    DATA_DIRS = [
        ["..", "share"],
        ["share"]
    ]

    for basepath, data_dir in ((x, y) for x in BASE_DIRS for y in DATA_DIRS):
        dir_and_filename = data_dir + path_parts
        datafile = os.path.join(basepath or os.path.dirname(__file__), *dir_and_filename)
        if os.path.exists(datafile):
            return datafile
    raise Exception('Could not find "%s"' % (os.path.join(*path_parts)))
