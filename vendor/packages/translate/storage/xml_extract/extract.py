#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2014 Zuza Software Foundation
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

from contextlib import contextmanager

from lxml import etree

from translate.storage import base
from translate.storage.placeables import StringElem, xliff
from translate.storage.xml_extract import misc, xpath_breadcrumb


class Translatable(object):
    """A node corresponds to a translatable element. A node may
       have children, which correspond to placeables."""

    def __init__(self, placeable_name, xpath, dom_node, source,
                 is_inline=False):
        self.placeable_name = placeable_name
        self.source = source
        self.xpath = xpath
        self.is_inline = is_inline
        self.dom_node = dom_node

    @property
    def placeables(self):
        return [placeable for placeable in self.source
                if isinstance(placeable, Translatable)]

    @property
    def has_translatable_text(self):
        """Check if it contains any chunk of text with more than whitespace.

        If not, then there's nothing to translate.
        """
        for chunk in self.source:
            if isinstance(chunk, unicode) and chunk.strip() != u"":
                return True
        return False


def reduce_unit_tree(f, unit_node, *state):
    return misc.reduce_tree(f, unit_node, unit_node,
                            lambda unit_node: unit_node.placeables, *state)


class ParseState(object):
    """Maintain constants and variables used during the walking of a
    DOM tree (via the function apply)."""

    def __init__(self, no_translate_content_elements, inline_elements={},
                 nsmap={}):
        self.no_translate_content_elements = no_translate_content_elements
        self.inline_elements = inline_elements
        self.is_inline = False
        self.xpath_breadcrumb = xpath_breadcrumb.XPathBreadcrumb()
        self.placeable_name = u"<top-level>"
        self.nsmap = nsmap


def _process_placeable(dom_node, state):
    """Process current placeable.

    This returns all nested translatable content for this placeable as a single
    Translatable object, or just returns an empty Translatable object for this
    placeable if there is no nested translatable content.
    """
    placeable = find_translatable_dom_nodes(dom_node, state,
                                            process_translatable)

    if len(placeable) == 0:
        # There are no recognized child tags and thus no Translatable object is
        # returned. So create a Translatable with the name "placeable".
        return Translatable(u"placeable", state.xpath_breadcrumb.xpath,
                            dom_node, [])
    elif len(placeable) == 1:
        # The ideal situation: we got exactly one Translatable back when
        # processing this tree.
        return placeable[0]
    else:
        raise Exception("BUG: find_translatable_dom_nodes should never return "
                        "more than a single Translatable object")


def process_translatable(dom_node, state):
    """Process a translatable DOM node.

    Any translatable content present in a child node is treated as a placeable.
    """
    source = [unicode(dom_node.text or u"")]

    # Append Translatable objects and unicode strings for the translatable
    # content for all the children.
    for child in dom_node:
        source.append(_process_placeable(child, state))
        source.append(unicode(child.tail or u""))

    translatable = Translatable(state.placeable_name,
                                state.xpath_breadcrumb.xpath, dom_node, source,
                                state.is_inline)
    return [translatable]


def _has_idml_translatable_content(dom_node):
    has_translatable_content = True
    if dom_node.tag == 'ParagraphStyleRange':
        has_translatable_content = False

        for content_node in dom_node.findall('.//Content'):
            # Iterate over all the Content tags in this ParagraphStyleRange tag.
            if content_node.text is not None and content_node.text.strip():
                return True

            for child in content_node.iterdescendants():
                # The Content node can just have a child before any nested
                # text, and therefore its text is None, so we have to check if
                # it has children, and if any of its children has text.
                if (not isinstance(child, etree._ProcessingInstruction) and
                    child.text is not None and child.text.strip()):
                    return True

                if child.tail is not None and child.tail.strip():
                    return True

    return has_translatable_content


def _retrieve_idml_placeables(dom_node, state):
    source = []
    for child in dom_node:
        if not isinstance(child, etree._Element):
            continue

        if isinstance(child, etree._ProcessingInstruction):
            #TODO this probably won't be using the right xpath.
            source.append(Translatable(u"placeable",
                                       state.xpath_breadcrumb.xpath, child, [],
                                       False))

            if child.tail is not None and child.tail.strip():
                source.append(unicode(child.tail))

            continue

        namespace, tag = misc.parse_tag(child.tag)

        with parse_status_set(namespace, tag, state):
            # Ensure we extract all the tags below ParagraphStyleRange as
            # placeables, independently of them being translatable or not.
            #state.is_inline = True

            nested_stuff = []

            if child.text is not None and child.text.strip():
                nested_stuff = [unicode(child.text)]

            nested_stuff.extend(_retrieve_idml_placeables(child, state))

            source.append(Translatable(u"placeable",
                                       state.xpath_breadcrumb.xpath, child,
                                       nested_stuff, state.is_inline))

            if child.tail is not None and child.tail.strip():
                source.append(unicode(child.tail))

    return source


def process_idml_translatable(dom_node, state):
    if _has_idml_translatable_content(dom_node):
        source = _retrieve_idml_placeables(dom_node, state)

        translatable = Translatable(state.placeable_name,
                                    state.xpath_breadcrumb.xpath, dom_node,
                                    source, state.is_inline)
        return [translatable]

    return []


def _process_children(dom_node, state, process_func):
    """Process an untranslatable DOM node.

    Since the node is untranslatable it just returns any translatable content
    present in its child nodes.
    """
    children = [find_translatable_dom_nodes(child, state, process_func)
                for child in dom_node]

    # Flatten a list of lists into a list of elements
    children = [child for child_list in children for child in child_list]

    if len(children) > 1:
        _namespace, tag = misc.parse_tag(dom_node.tag)
        intermediate_translatable = Translatable(tag,
                                                 state.xpath_breadcrumb.xpath,
                                                 dom_node, children)
        return [intermediate_translatable]
    else:
        return children


def compact_tag(nsmap, namespace, tag):
    if namespace in nsmap:
        return u'%s:%s' % (nsmap[namespace], tag)
    else:
        return u'{%s}%s' % (namespace, tag)


@contextmanager
def parse_status_set(namespace, tag, state):
    # Set XPath breadcrumb item for the current node.
    xpath_item = compact_tag(state.nsmap, namespace, tag)
    state.xpath_breadcrumb.start_tag(xpath_item)

    # Set the placeable name for the current node.
    old_placeable_name = state.placeable_name
    state.placeable_name = tag

    # Set the inline status for the current node.
    old_inline = state.is_inline
    state.is_inline = (namespace, tag) in state.inline_elements

    yield state

    # Reset inline status, placeable name and XPath breadcrumb to the
    # previous values.
    state.is_inline = old_inline
    state.placeable_name = old_placeable_name
    state.xpath_breadcrumb.end_tag()


def find_translatable_dom_nodes(dom_node, state,
                                process_func=process_translatable):
    # For now, we only want to deal with XML elements.
    # And we want to avoid processing instructions, which
    # are XML elements (in the inheritance hierarchy).
    if (not isinstance(dom_node, etree._Element) or
        isinstance(dom_node, etree._ProcessingInstruction)):
        return []

    namespace, tag = misc.parse_tag(dom_node.tag)

    with parse_status_set(namespace, tag, state):
        if (namespace, tag) not in state.no_translate_content_elements:
            return process_func(dom_node, state)
        else:
            return _process_children(dom_node, state, process_func)


class IdMaker(object):

    def __init__(self):
        self._max_id = 0
        self._obj_id_map = {}

    def get_id(self, obj):
        if not self.has_id(obj):
            self._obj_id_map[obj] = self._max_id
            self._max_id += 1
        return self._obj_id_map[obj]

    def has_id(self, obj):
        return obj in self._obj_id_map


def _to_placeables(parent_translatable, translatable, id_maker):
    """Convert the translatable object to a list of strings and XLIFF
    placeables.
    """
    result = []
    for chunk in translatable.source:
        if isinstance(chunk, unicode):
            result.append(chunk)
        else:
            id = unicode(id_maker.get_id(chunk))
            if chunk.is_inline:
                sub = _to_placeables(parent_translatable, chunk, id_maker)
                result.append(xliff.G(id=id, sub=sub))
            else:
                result.append(xliff.X(id=id, xid=chunk.xpath))
    return result


def _make_store_adder(store):
    """Return a function which, when called with a Translatable will add
    a unit to 'store'. The placeables will be represented as strings according
    to 'placeable_quoter'.
    """
    id_maker = IdMaker()

    def add_translatable_to_store(parent_translatable, translatable):
        """Construct a new translation unit, set its source and location
        information and add it to 'store'.
        """
        unit = store.UnitClass(u'')
        unit.rich_source = [StringElem(_to_placeables(parent_translatable,
                                                      translatable, id_maker))]
        unit.addlocation(translatable.xpath)
        store.addunit(unit)

    return add_translatable_to_store


def make_postore_adder(store, id_maker, filename):
    """Return a function which, when called with a Translatable will add
    a unit to 'store'. The placeables will be represented as strings according
    to 'placeable_quoter'.
    """
    from translate.storage.xliff import xliffunit

    def add_translatable_to_store(parent_translatable, translatable):
        """Construct a new translation unit, set its source and location
        information and add it to 'store'.
        """
        xliff_unit = xliffunit(u'')
        placeables = _to_placeables(parent_translatable, translatable, id_maker)
        xliff_unit.rich_source = [StringElem(placeables)]

        # Get the plain text for the unit source. The output is enclosed within
        # XLIFF source tags we don't want, so strip them.
        unit_source = etree.tostring(xliff_unit.source_dom)
        unit_source = unit_source[unit_source.find(">", 1) + 1:]
        unit_source = unit_source[:unit_source.rfind("<", 1)]

        # Create the PO unit and add it to the PO store.
        po_unit = store.UnitClass(unit_source)
        po_unit.addlocation(translatable.xpath)
        po_unit.addlocation(filename)
        store.addunit(po_unit)

    return add_translatable_to_store


def _walk_idml_translatable_tree(translatables, store_adder,
                                 parent_translatable):
    """Traverse all the found IDML translatables and add them to the Store.

    Inline translatables are not added to the Store.
    """
    for translatable in translatables:
        if translatable.dom_node.tag == "ParagraphStyleRange":
            store_adder(parent_translatable, translatable)
            continue

        new_parent_translatable = parent_translatable
        _walk_idml_translatable_tree(translatable.placeables, store_adder,
                                     new_parent_translatable)


def _walk_translatable_tree(translatables, store_adder, parent_translatable):
    """Traverse all the found translatables and add them to the Store.

    Inline translatables are not added to the Store.
    """
    for translatable in translatables:
        if translatable.has_translatable_text and not translatable.is_inline:
            store_adder(parent_translatable, translatable)
            new_parent_translatable = parent_translatable
        else:
            new_parent_translatable = parent_translatable

        _walk_translatable_tree(translatable.placeables, store_adder,
                                new_parent_translatable)


def reverse_map(a_map):
    return dict((value, key) for key, value in a_map.iteritems())


def build_idml_store(odf_file, store, parse_state, store_adder=None):
    """Build a store for the given IDML file."""
    store_adder = store_adder or _make_store_adder(store)
    tree = etree.parse(odf_file)
    root = tree.getroot()
    parse_state.nsmap = reverse_map(root.nsmap)
    translatables = find_translatable_dom_nodes(root, parse_state,
                                                process_idml_translatable)
    _walk_idml_translatable_tree(translatables, store_adder, None)
    return tree


def build_store(odf_file, store, parse_state, store_adder=None):
    """Build a store for the given XML file."""
    store_adder = store_adder or _make_store_adder(store)
    tree = etree.parse(odf_file)
    root = tree.getroot()
    parse_state.nsmap = reverse_map(root.nsmap)
    translatables = find_translatable_dom_nodes(root, parse_state)
    _walk_translatable_tree(translatables, store_adder, None)
    return tree
