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

"""This module provides functionality to work with directories."""

# Perhaps all methods should work with a wildcard to limit searches in some
# way (examples: *.po, base.xlf, pootle-terminology.tbx)

#TODO: consider also providing directories as we currently provide files

import os

from translate.storage import factory


class Directory:
    """This class represents a directory."""

    def __init__(self, dir=None):
        self.dir = dir
        self.filedata = []

    def file_iter(self):
        """Iterator over (dir, filename) for all files in this directory."""
        if not self.filedata:
            self.scanfiles()
        for filetuple in self.filedata:
            yield filetuple

    def getfiles(self):
        """Returns a list of (dir, filename) tuples for all the file names in
        this directory."""
        return [filetuple for filetuple in self.file_iter()]

    def unit_iter(self):
        """Iterator over all the units in all the files in this directory."""
        for dirname, filename in self.file_iter():
            store = factory.getobject(os.path.join(dirname, filename))
            #TODO: don't regenerate all the storage objects
            for unit in store.unit_iter():
                yield unit

    def getunits(self):
        """List of all the units in all the files in this directory."""
        return [unit for unit in self.unit_iter()]

    def scanfiles(self):
        """Populate the internal file data."""
        self.filedata = []

        for dirpath, dirnames, filenames in os.walk(self.dir):
            fnames = dirnames + filenames
            for fname in fnames:
                if os.path.isfile(os.path.join(dirpath, fname)):
                    self.filedata.append((dirpath, fname))
