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

"""This module provides functionality to work with zip files."""

# Perhaps all methods should work with a wildcard to limit searches in some
# way (examples: *.po, base.xlf, pootle-terminology.tbx)

#TODO: consider also providing directories as we currently provide files

#TODO: refactor with existing zip code (xpi.py, etc.)

from translate.storage import factory
from translate.storage import directory
from translate.misc import wStringIO
from os import path
from zipfile import ZipFile

class ZIPFile(directory.Directory):
    """This class represents a ZIP file like a directory."""
    def __init__(self, filename=None):
        self.filename = filename
        self.filedata = []

    def unit_iter(self):
        """Iterator over all the units in all the files in this zip file."""
        for dirname, filename in self.file_iter():
            strfile = wStringIO.StringIO(self.archive.read(path.join(dirname, filename)))
            strfile.filename = filename
            store = factory.getobject(strfile)
            #TODO: don't regenerate all the storage objects
            for unit in store.unit_iter():
                yield unit

    def scanfiles(self):
        """Populate the internal file data."""
        self.filedata = []
        self.archive = ZipFile(self.filename)
        for completename in self.archive.namelist():
            dir, name = path.split(completename)
            self.filedata.append((dir, name))

