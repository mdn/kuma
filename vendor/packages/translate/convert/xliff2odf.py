#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2014 Zuza Software Foundation
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

"""Convert XLIFF translation files to OpenDocument (ODF) files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/odf2xliff.html
for examples and usage instructions.
"""

import zipfile
from cStringIO import StringIO

import lxml.etree as etree

from translate.convert import convert
from translate.storage import factory
from translate.storage.odf_io import copy_odf, open_odf
from translate.storage.odf_shared import (inline_elements,
                                          no_translate_content_elements)
from translate.storage.xml_extract.extract import ParseState
from translate.storage.xml_extract.generate import (apply_translations,
                                                    replace_dom_text)
from translate.storage.xml_extract.unit_tree import XPathTree, build_unit_tree


def translate_odf(template, input_file):

    def load_dom_trees(template):
        """Return a dict with translatable files in the template ODF package.

        The keys are the filenames inside the ODF package, and the values are
        the etrees for each of those translatable files.
        """
        odf_data = open_odf(template)
        return dict((filename, etree.parse(StringIO(data)))
                    for filename, data in odf_data.iteritems())

    def load_unit_tree(input_file):
        """Return a dict with the translations grouped by files ODF package.

        The keys are the filenames inside the template ODF package, and the
        values are XPathTree instances for each of those files.
        """
        store = factory.getobject(input_file)
        tree = build_unit_tree(store)

        def extract_unit_tree(filename, root_dom_element_name):
            """Find the subtree in 'tree' which corresponds to the data in XML
            file 'filename'.
            """
            try:
                file_tree = tree.children[root_dom_element_name, 0]
            except KeyError:
                file_tree = XPathTree()

            return (filename, file_tree)

        return dict([extract_unit_tree('content.xml', 'office:document-content'),
                     extract_unit_tree('meta.xml', 'office:document-meta'),
                     extract_unit_tree('styles.xml', 'office:document-styles')])

    def translate_dom_trees(unit_trees, dom_trees):
        """Return a dict with the translated files for the ODF package.

        The keys are the filenames for the translatable files inside the
        template ODF package, and the values are etree ElementTree instances
        for each of those files.
        """
        make_parse_state = lambda: ParseState(no_translate_content_elements,
                                              inline_elements)
        for filename, dom_tree in dom_trees.iteritems():
            file_unit_tree = unit_trees[filename]
            apply_translations(dom_tree.getroot(), file_unit_tree,
                               replace_dom_text(make_parse_state))
        return dom_trees

    dom_trees = load_dom_trees(template)
    unit_trees = load_unit_tree(input_file)
    return translate_dom_trees(unit_trees, dom_trees)


def write_odf(template, output_file, dom_trees):
    """Write the translated ODF package.

    The resulting ODF package is a copy of the template ODF package, with the
    translatable files replaced by their translated versions.
    """
    template_zip = zipfile.ZipFile(template, 'r')
    output_zip = zipfile.ZipFile(output_file, 'w',
                                 compression=zipfile.ZIP_DEFLATED)

    # Copy the ODF package.
    output_zip = copy_odf(template_zip, output_zip, dom_trees.keys())

    # Overwrite the translated files to the ODF package.
    for filename, dom_tree in dom_trees.iteritems():
        output_zip.writestr(filename, etree.tostring(dom_tree,
                                                     encoding='UTF-8',
                                                     xml_declaration=True))


def convertxliff(input_file, output_file, template):
    """Create a translated ODF using an ODF template and a XLIFF file."""
    # Since the convertoptionsparser will give us an open file, we risk that
    # it could have been opened in non-binary mode on Windows, and then we'll
    # have problems, so let's make sure we have what we want.
    template.close()
    template = file(template.name, mode='rb')
    output_file.close()
    output_file = file(output_file.name, mode='wb')

    xlf_data = input_file.read()
    dom_trees = translate_odf(template, StringIO(xlf_data))
    write_odf(template, output_file, dom_trees)
    output_file.close()
    return True


def main(argv=None):
    formats = {
        ('xlf', 'odt'): ("odt", convertxliff),  # Text
        ('xlf', 'ods'): ("ods", convertxliff),  # Spreadsheet
        ('xlf', 'odp'): ("odp", convertxliff),  # Presentation
        ('xlf', 'odg'): ("odg", convertxliff),  # Drawing
        ('xlf', 'odc'): ("odc", convertxliff),  # Chart
        ('xlf', 'odf'): ("odf", convertxliff),  # Formula
        ('xlf', 'odi'): ("odi", convertxliff),  # Image
        ('xlf', 'odm'): ("odm", convertxliff),  # Master Document
        ('xlf', 'ott'): ("ott", convertxliff),  # Text template
        ('xlf', 'ots'): ("ots", convertxliff),  # Spreadsheet template
        ('xlf', 'otp'): ("otp", convertxliff),  # Presentation template
        ('xlf', 'otg'): ("otg", convertxliff),  # Drawing template
        ('xlf', 'otc'): ("otc", convertxliff),  # Chart template
        ('xlf', 'otf'): ("otf", convertxliff),  # Formula template
        ('xlf', 'oti'): ("oti", convertxliff),  # Image template
        ('xlf', 'oth'): ("oth", convertxliff),  # Web page template
    }
    parser = convert.ConvertOptionParser(formats, usetemplates=True, description=__doc__)
    parser.run(argv)


if __name__ == '__main__':
    main()
