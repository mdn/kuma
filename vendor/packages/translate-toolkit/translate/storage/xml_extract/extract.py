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

from lxml import etree

from translate.storage import base
from translate.misc.typecheck import accepts, Self, IsCallable, IsOneOf, Any, Class
from translate.misc.typecheck.typeclasses import Number
from translate.misc.contextlib import contextmanager, nested
from translate.misc.context import with_
from translate.storage.xml_extract import xpath_breadcrumb
from translate.storage.xml_extract import misc
from translate.storage.placeables import xliff, StringElem

def Nullable(t):
    return IsOneOf(t, type(None))

TranslatableClass = Class('Translatable')

class Translatable(object):
    """A node corresponds to a translatable element. A node may
       have children, which correspond to placeables."""
    @accepts(Self(), unicode, unicode, etree._Element, [IsOneOf(TranslatableClass, unicode)])
    def __init__(self, placeable_name, xpath, dom_node, source):
        self.placeable_name = placeable_name
        self.source = source
        self.xpath = xpath
        self.is_inline = False
        self.dom_node = dom_node

    def _get_placeables(self):
        return [placeable for placeable in self.source if isinstance(placeable, Translatable)]

    placeables = property(_get_placeables)

@accepts(IsCallable(), Translatable, state=[Any()])
def reduce_unit_tree(f, unit_node, *state):
    return misc.reduce_tree(f, unit_node, unit_node, lambda unit_node: unit_node.placeables, *state)

class ParseState(object):
    """Maintain constants and variables used during the walking of a
    DOM tree (via the function apply)."""
    def __init__(self, no_translate_content_elements, inline_elements = {}, nsmap = {}):
        self.no_translate_content_elements = no_translate_content_elements
        self.inline_elements = inline_elements
        self.is_inline = False
        self.xpath_breadcrumb = xpath_breadcrumb.XPathBreadcrumb()
        self.placeable_name = u"<top-level>"
        self.nsmap = nsmap

@accepts(etree._Element, ParseState)
def _process_placeable(dom_node, state):
    """Run find_translatable_dom_nodes on the current dom_node"""
    placeable = find_translatable_dom_nodes(dom_node, state)
    # This happens if there were no recognized child tags and thus
    # no translatable is returned. Make a placeable with the name
    # "placeable"
    if len(placeable) == 0:
        return Translatable(u"placeable", state.xpath_breadcrumb.xpath, dom_node, [])
    # The ideal situation: we got exactly one translateable back
    # when processing this tree.
    elif len(placeable) == 1:
        return placeable[0]
    else:
        raise Exception("BUG: find_translatable_dom_nodes should never return more than a single translatable")

@accepts(etree._Element, ParseState)
def _process_placeables(dom_node, state):
    """Return a list of placeables and list with
    alternating string-placeable objects. The former is
    useful for directly working with placeables and the latter
    is what will be used to build the final translatable string."""

    source = []
    for child in dom_node:
        source.extend([_process_placeable(child, state), unicode(child.tail or u"")])
    return source

@accepts(etree._Element, ParseState)
def _process_translatable(dom_node, state):
    source = [unicode(dom_node.text or u"")] + _process_placeables(dom_node, state)
    translatable = Translatable(state.placeable_name, state.xpath_breadcrumb.xpath, dom_node, source)
    translatable.is_inline = state.is_inline
    return [translatable]

@accepts(etree._Element, ParseState)
def _process_children(dom_node, state):
    _namespace, tag = misc.parse_tag(dom_node.tag)
    children = [find_translatable_dom_nodes(child, state) for child in dom_node]
    # Flatten a list of lists into a list of elements
    children = [child for child_list in children for child in child_list]
    if len(children) > 1:
        intermediate_translatable = Translatable(tag, state.xpath_breadcrumb.xpath, dom_node, children)
        return [intermediate_translatable]
    else:
        return children

def compact_tag(nsmap, namespace, tag):
    if namespace in nsmap:
        return u'%s:%s' % (nsmap[namespace], tag)
    else:
        return u'{%s}%s' % (namespace, tag)

@accepts(etree._Element, ParseState)
def find_translatable_dom_nodes(dom_node, state):
    # For now, we only want to deal with XML elements.
    # And we want to avoid processing instructions, which
    # are XML elements (in the inheritance hierarchy).
    if not isinstance(dom_node, etree._Element) or \
           isinstance(dom_node, etree._ProcessingInstruction):
        return []

    namespace, tag = misc.parse_tag(dom_node.tag)

    @contextmanager
    def xpath_set():
        state.xpath_breadcrumb.start_tag(compact_tag(state.nsmap, namespace, tag))
        yield state.xpath_breadcrumb
        state.xpath_breadcrumb.end_tag()

    @contextmanager
    def placeable_set():
        old_placeable_name = state.placeable_name
        state.placeable_name = tag
        yield state.placeable_name
        state.placeable_name = old_placeable_name

    @contextmanager
    def inline_set():
        old_inline = state.is_inline
        if (namespace, tag) in state.inline_elements:
            state.is_inline = True
        else:
            state.is_inline = False
        yield state.is_inline
        state.is_inline = old_inline

    def with_block(xpath_breadcrumb, placeable_name, is_inline):
        if (namespace, tag) not in state.no_translate_content_elements:
            return _process_translatable(dom_node, state)
        else:
            return _process_children(dom_node, state)
    return with_(nested(xpath_set(), placeable_set(), inline_set()), with_block)

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

@accepts(Nullable(Translatable), Translatable, IdMaker)
def _to_placeables(parent_translatable, translatable, id_maker):
    result = []
    for chunk in translatable.source:
        if isinstance(chunk, unicode):
            result.append(chunk)
        else:
            id = unicode(id_maker.get_id(chunk))
            if chunk.is_inline:
                result.append(xliff.G(sub=_to_placeables(parent_translatable, chunk, id_maker), id=id))
            else:
                result.append(xliff.X(id=id, xid=chunk.xpath))
    return result

@accepts(base.TranslationStore, Nullable(Translatable), Translatable, IdMaker)
def _add_translatable_to_store(store, parent_translatable, translatable, id_maker):
    """Construct a new translation unit, set its source and location
    information and add it to 'store'.
    """
    unit = store.UnitClass(u'')
    unit.rich_source = [StringElem(_to_placeables(parent_translatable, translatable, id_maker))]
    unit.addlocation(translatable.xpath)
    store.addunit(unit)

@accepts(Translatable)
def _contains_translatable_text(translatable):
    """Checks whether translatable contains any chunks of text which contain
    more than whitespace.

    If not, then there's nothing to translate."""
    for chunk in translatable.source:
        if isinstance(chunk, unicode):
            if chunk.strip() != u"":
                return True
    return False

@accepts(base.TranslationStore)
def _make_store_adder(store):
    """Return a function which, when called with a Translatable will add
    a unit to 'store'. The placeables will represented as strings according
    to 'placeable_quoter'."""
    id_maker = IdMaker()

    def add_to_store(parent_translatable, translatable, rid):
        _add_translatable_to_store(store, parent_translatable, translatable, id_maker)

    return add_to_store

@accepts([Translatable], IsCallable(), Nullable(Translatable), Number)
def _walk_translatable_tree(translatables, f, parent_translatable, rid):
    for translatable in translatables:
        if _contains_translatable_text(translatable) and not translatable.is_inline:
            rid = rid + 1
            new_parent_translatable = translatable
            f(parent_translatable, translatable, rid)
        else:
            new_parent_translatable = parent_translatable

        _walk_translatable_tree(translatable.placeables, f, new_parent_translatable, rid)

def reverse_map(a_map):
    return dict((value, key) for key, value in a_map.iteritems())

@accepts(lambda obj: hasattr(obj, "read"), base.TranslationStore, ParseState, Nullable(IsCallable()))
def build_store(odf_file, store, parse_state, store_adder = None):
    """Utility function for loading xml_filename"""
    store_adder = store_adder or _make_store_adder(store)
    tree = etree.parse(odf_file)
    root = tree.getroot()
    parse_state.nsmap = reverse_map(root.nsmap)
    translatables = find_translatable_dom_nodes(root, parse_state)
    _walk_translatable_tree(translatables, store_adder, None, 0)
    return tree
