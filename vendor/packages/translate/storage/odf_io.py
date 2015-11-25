#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008, 2014 Zuza Software Foundation
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

import zipfile

from lxml import etree

from translate.storage.xml_name import XmlNamer


def open_odf(filename):
    z = zipfile.ZipFile(filename, 'r')
    return {'content.xml': z.read("content.xml"),
            'meta.xml': z.read("meta.xml"),
            'styles.xml': z.read("styles.xml")}


def copy_odf(input_zip, output_zip, exclusion_list):
    for name in [name for name in input_zip.namelist() if name not in exclusion_list]:
        output_zip.writestr(name, input_zip.read(name))
    return output_zip
