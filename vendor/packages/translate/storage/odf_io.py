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
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#

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


def namespaced(nsmap, short_namespace, tag):
    return '{%s}%s' % (nsmap[short_namespace], tag)


def add_file(output_zip, manifest_data, new_filename, new_data):
    root = etree.fromstring(manifest_data)
    namer = XmlNamer(root)
    namespacer = namer.namespace('manifest')
    file_entry_tag = namespacer.name('file-entry')
    media_type_attr = namespacer.name('media-type')
    full_path_attr = namespacer.name('full-path')

    root.append(etree.Element(file_entry_tag, {media_type_attr: 'application/x-xliff+xml',
                                               full_path_attr: new_filename}))
    output_zip.writestr(new_filename, new_data)
    output_zip.writestr('META-INF/manifest.xml', etree.tostring(root, xml_declaration=True, encoding="UTF-8"))
    return output_zip
