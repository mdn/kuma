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

"""Takes an IDML template file and a PO file containing translations of
strings in the IDML template. It creates a new IDML file using the translations
of the PO file.
"""

from cStringIO import StringIO
from zipfile import ZIP_DEFLATED, ZipFile

import lxml.etree as etree

from translate.convert import convert
from translate.storage import factory
from translate.storage.idml import (NO_TRANSLATE_ELEMENTS,
                                    INLINE_ELEMENTS, copy_idml, open_idml)
from translate.storage.xml_extract.extract import (ParseState,
                                                   process_idml_translatable)
from translate.storage.xml_extract.generate import (apply_translations,
                                                    replace_dom_text)
from translate.storage.xml_extract.unit_tree import XPathTree, build_unit_tree


def translate_idml(template, input_file, translatable_files):

    def load_dom_trees(template):
        """Return a dict with translatable files in the template IDML package.

        The keys are the filenames inside the IDML package, and the values are
        the etrees for each of those translatable files.
        """
        idml_data = open_idml(template)
        parser = etree.XMLParser(strip_cdata=False)
        return dict((filename, etree.fromstring(data, parser).getroottree())
                    for filename, data in idml_data.iteritems())

    def load_unit_tree(input_file):
        """Return a dict with the translations grouped by files IDML package.

        The keys are the filenames inside the template IDML package, and the
        values are XPathTree instances for each of those files.
        """
        store = factory.getobject(input_file)

        def extract_unit_tree(filename, root_dom_element_name):
            """Find the subtree in 'tree' which corresponds to the data in XML
            file 'filename'
            """
            tree = build_unit_tree(store, filename)

            try:
                file_tree = tree.children[root_dom_element_name, 0]
            except KeyError:
                file_tree = XPathTree()

            return (filename, file_tree)

        return dict(extract_unit_tree(filename, 'idPkg:Story')
                    for filename in translatable_files)

    def translate_dom_trees(unit_trees, dom_trees):
        """Return a dict with the translated files for the IDML package.

        The keys are the filenames for the translatable files inside the
        template IDML package, and the values are etree ElementTree instances
        for each of those files.
        """
        def get_po_doms(unit):
            """Return a tuple with unit source and target DOM objects.

            This method is method is meant to provide a way to retrieve the DOM
            objects for the unit source and target for PO stores.

            Since POunit doesn't have any source_dom nor target_dom attributes,
            it is necessary to craft those objects.
            """
            def add_node_content(string, node):
                """Append the translatable content to the node.

                The string is going to have XLIFF placeables, so we have to
                parse it as XML in order to get the right nodes to append to
                the node.
                """
                # Add a wrapper "whatever" tag to avoid problems when parsing
                # several sibling tags at the root level.
                fake_string = "<whatever>" + string + "</whatever>"

                # Copy the children to the XLIFF unit's source or target node.
                fake_node = etree.fromstring(fake_string)
                node.extend(fake_node.getchildren())

                return node

            source_dom = etree.Element("source")
            source_dom = add_node_content(unit.source, source_dom)
            target_dom = etree.Element("target")

            if unit.target:
                target_dom = add_node_content(unit.target, target_dom)
            else:
                target_dom = add_node_content(unit.source, target_dom)

            return (source_dom, target_dom)

        make_parse_state = lambda: ParseState(NO_TRANSLATE_ELEMENTS,
                                              INLINE_ELEMENTS)
        for filename, dom_tree in dom_trees.iteritems():
            file_unit_tree = unit_trees[filename]
            apply_translations(dom_tree.getroot(), file_unit_tree,
                               replace_dom_text(make_parse_state,
                                                dom_retriever=get_po_doms,
                                                process_translatable=process_idml_translatable))
        return dom_trees

    dom_trees = load_dom_trees(template)
    unit_trees = load_unit_tree(input_file)
    return translate_dom_trees(unit_trees, dom_trees)


def write_idml(template_zip, output_file, dom_trees):
    """Write the translated IDML package."""
    output_zip = ZipFile(output_file, 'w', compression=ZIP_DEFLATED)

    # Copy the IDML package.
    output_zip = copy_idml(template_zip, output_zip, dom_trees.keys())

    # Replace the translated files in the IDML package.
    for filename, dom_tree in dom_trees.iteritems():
        output_zip.writestr(filename, etree.tostring(dom_tree,
                                                     encoding='UTF-8',
                                                     xml_declaration=True,
                                                     standalone='yes'))


def convertpo(input_file, output_file, template):
    """Create a translated IDML using an IDML template and a PO file."""
    # Since the convertoptionsparser will give us a open files, we risk that
    # they could have been opened in non-binary mode on Windows, and then we'll
    # have problems, so let's make sure we have what we want.
    template.close()
    template = file(template.name, mode='rb')
    output_file.close()
    output_file = file(output_file.name, mode='wb')

    # Now proceed with the conversion.
    template_zip = ZipFile(template, 'r')

    translatable_files = [filename for filename in template_zip.namelist()
                          if filename.startswith('Stories/')]

    po_data = input_file.read()
    dom_trees = translate_idml(template, StringIO(po_data), translatable_files)

    write_idml(template_zip, output_file, dom_trees)
    output_file.close()
    return True


def main(argv=None):
    formats = {
        ('po', 'idml'): ("idml", convertpo),
    }
    parser = convert.ConvertOptionParser(formats, usetemplates=True,
                                         description=__doc__)
    parser.run(argv)


if __name__ == '__main__':
    main()
