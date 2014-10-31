#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

"""
Contains the base L{StringElem} class that represents a node in a parsed rich-
string tree. It is the base class of all placeables.
"""

import logging
import sys


class ElementNotFoundError(ValueError):
    pass


class StringElem(object):
    """
    This class represents a sub-tree of a string parsed into a rich structure.
    It is also the base class of all placeables.
    """

    renderer = None
    """An optional function that returns the Unicode representation of the string."""
    sub = []
    """The sub-elements that make up this this string."""
    has_content = True
    """Whether this string can have sub-elements."""
    iseditable = True
    """Whether this string should be changable by the user. Not used at the moment."""
    isfragile = False
    """Whether this element should be deleted in its entirety when partially
        deleted. Only checked when C{iseditable = False}"""
    istranslatable = True
    """Whether this string is translatable into other languages."""
    isvisible = True
    """Whether this string should be visible to the user. Not used at the moment."""

    # INITIALIZERS #
    def __init__(self, sub=None, id=None, rid=None, xid=None, **kwargs):
        if sub is None:
            sub = []
        if isinstance(sub, (unicode, StringElem)):
            sub = [sub]

        for elem in sub:
            if not isinstance(elem, (unicode, StringElem)):
                raise ValueError(elem)

        self.sub   = sub
        self.id    = id
        self.rid   = rid
        self.xid   = xid

        for key, value in kwargs.items():
            if hasattr(self, key):
                raise ValueError('attribute already exists: %s' % (key))
            setattr(self, key, value)

        self.prune()

    # SPECIAL METHODS #
    def __add__(self, rhs):
        """Emulate the C{unicode} class."""
        return unicode(self) + rhs

    def __contains__(self, item):
        """Emulate the C{unicode} class."""
        return item in unicode(self)

    def __eq__(self, rhs):
        """@returns: C{True} if (and only if) all members as well as sub-trees
            are equal. False otherwise."""
        if not isinstance(rhs, StringElem):
            return False

        return  self.id             == rhs.id             and \
                self.iseditable     == rhs.iseditable     and \
                self.istranslatable == rhs.istranslatable and \
                self.isvisible      == rhs.isvisible      and \
                self.rid            == rhs.rid            and \
                self.xid            == rhs.xid            and \
                len(self.sub) == len(rhs.sub) and \
                not [i for i in range(len(self.sub)) if self.sub[i] != rhs.sub[i]]

    def __ge__(self, rhs):
        """Emulate the C{unicode} class."""
        return unicode(self) >= rhs

    def __getitem__(self, i):
        """Emulate the C{unicode} class."""
        return unicode(self)[i]

    def __getslice__(self, i, j):
        """Emulate the C{unicode} class."""
        return unicode(self)[i:j]

    def __gt__(self, rhs):
        """Emulate the C{unicode} class."""
        return unicode(self) > rhs

    def __iter__(self):
        """Create an iterator of this element's sub-elements."""
        for elem in self.sub:
            yield elem

    def __le__(self, rhs):
        """Emulate the C{unicode} class."""
        return unicode(self) <= rhs

    def __len__(self):
        """Emulate the C{unicode} class."""
        return len(unicode(self))

    def __lt__(self, rhs):
        """Emulate the C{unicode} class."""
        return unicode(self) < rhs

    def __mul__(self, rhs):
        """Emulate the C{unicode} class."""
        return unicode(self) * rhs

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def __radd__(self, lhs):
        """Emulate the C{unicode} class."""
        return self + lhs

    def __rmul__(self, lhs):
        """Emulate the C{unicode} class."""
        return self * lhs

    def __repr__(self):
        elemstr = ', '.join([repr(elem) for elem in self.sub])
        return '<%(class)s(%(id)s%(rid)s%(xid)s[%(subs)s])>' % {
            'class': self.__class__.__name__,
            'id':  self.id  is not None and 'id="%s" '  % (self.id) or '',
            'rid': self.rid is not None and 'rid="%s" ' % (self.rid) or '',
            'xid': self.xid is not None and 'xid="%s" ' % (self.xid) or '',
            'subs': elemstr
        }

    def __str__(self):
        if not self.isvisible:
            return ''
        return ''.join([unicode(elem).encode('utf-8') for elem in self.sub])

    def __unicode__(self):
        if callable(self.renderer):
            return self.renderer(self)
        if not self.isvisible:
            return u''
        return u''.join([unicode(elem) for elem in self.sub])

    # METHODS #
    def apply_to_strings(self, f):
        """Apply C{f} to all actual strings in the tree.
            @param f: Must take one (str or unicode) argument and return a
                string or unicode."""
        for elem in self.flatten():
            for i in range(len(elem.sub)):
                if isinstance(elem.sub[i], basestring):
                    elem.sub[i] = f(elem.sub[i])

    def copy(self):
        """Returns a copy of the sub-tree.
            This should be overridden in sub-classes with more data.

            NOTE: C{self.renderer} is B{not} copied."""
        #logging.debug('Copying instance of class %s' % (self.__class__.__name__))
        cp = self.__class__(id=self.id, xid=self.xid, rid=self.rid)
        for sub in self.sub:
            if isinstance(sub, StringElem):
                cp.sub.append(sub.copy())
            else:
                cp.sub.append(sub.__class__(sub))
        return cp

    def delete_elem(self, elem):
        if elem is self:
            self.sub = []
            return
        parent = self.get_parent_elem(elem)
        if parent is None:
            raise ElementNotFoundError(repr(elem))
        subidx = -1
        for i in range(len(parent.sub)):
            if parent.sub[i] is elem:
                subidx = i
                break
        if subidx < 0:
            raise ElementNotFoundError(repr(elem))
        del parent.sub[subidx]

    def delete_range(self, start_index, end_index):
        """Delete the text in the range given by the string-indexes
            C{start_index} and C{end_index}.
            Partial nodes will only be removed if they are editable.
            @returns: A C{StringElem} representing the removed sub-string, the
                parent node from which it was deleted as well as the offset at
                which it was deleted from. C{None} is returned for the parent
                value if the root was deleted. If the parent and offset values
                are not C{None}, C{parent.insert(offset, deleted)} effectively
                undoes the delete."""
        if start_index == end_index:
            return StringElem(), self, 0
        if start_index > end_index:
            raise IndexError('start_index > end_index: %d > %d' % (start_index, end_index))
        if start_index < 0 or start_index > len(self):
            raise IndexError('start_index: %d' % (start_index))
        if end_index < 1 or end_index > len(self) + 1:
            raise IndexError('end_index: %d' % (end_index))

        start = self.get_index_data(start_index)
        if isinstance(start['elem'], tuple):
            # If {start} is "between" elements, we use the one on the "right"
            start['elem']   = start['elem'][-1]
            start['offset'] = start['offset'][-1]
        end = self.get_index_data(end_index)
        if isinstance(end['elem'], tuple):
            # If {end} is "between" elements, we use the one on the "left"
            end['elem']   = end['elem'][0]
            end['offset'] = end['offset'][0]
        assert start['elem'].isleaf() and end['elem'].isleaf()

        #logging.debug('FROM %s TO %s' % (start, end))

        # Ranges can be one of 3 types:
        # 1) The entire string.
        # 2) An entire element.
        # 3) Restricted to a single element.
        # 4) Spans multiple elements (start- and ending elements are not the same).

        # Case 1: Entire string #
        if start_index == 0 and end_index == len(self):
            #logging.debug('Case 1: [%s]' % (unicode(self)))
            removed = self.copy()
            self.sub = []
            return removed, None, None

        # Case 2: An entire element #
        if start['elem'] is end['elem'] and start['offset'] == 0 and end['offset'] == len(start['elem']) or \
                (not start['elem'].iseditable and start['elem'].isfragile):
            ##### FOR DEBUGGING #####
            #s = ''
            #for e in self.flatten():
            #    if e is start['elem']:
            #        s += '[' + unicode(e) + ']'
            #    else:
            #        s += unicode(e)
            #logging.debug('Case 2: %s' % (s))
            #########################

            if start['elem'] is self and self.__class__ is StringElem:
                removed = self.copy()
                self.sub = []
                return removed, None, None
            removed = start['elem'].copy()
            parent = self.get_parent_elem(start['elem'])
            offset = parent.elem_offset(start['elem'])
            parent.sub.remove(start['elem'])
            return removed, parent, offset

        # Case 3: Within a single element #
        if start['elem'] is end['elem'] and start['elem'].iseditable:
            ##### FOR DEBUGGING #####
            #s = ''
            #for e in self.flatten():
            #    if e is start['elem']:
            #        s += '%s[%s]%s' % (
            #            e[:start['offset']],
            #            e[start['offset']:end['offset']],
            #            e[end['offset']:]
            #        )
            #    else:
            #        s += unicode(e)
            #logging.debug('Case 3: %s' % (s))
            #########################

            # XXX: This might not have the expected result if start['elem'] is a StringElem sub-class instance.
            newstr = u''.join(start['elem'].sub)
            removed = StringElem(newstr[start['offset']:end['offset']])
            newstr = newstr[:start['offset']] + newstr[end['offset']:]
            parent = self.get_parent_elem(start['elem'])
            if parent is None and start['elem'] is self:
                parent = self
            start['elem'].sub = [newstr]
            self.prune()
            return removed, start['elem'], start['offset']

        # Case 4: Across multiple elements #
        range_nodes = self.depth_first()
        startidx = 0
        endidx = -1
        for i in range(len(range_nodes)):
            if range_nodes[i] is start['elem']:
                startidx = i
            elif range_nodes[i] is end['elem']:
                endidx = i
                break
        range_nodes = range_nodes[startidx:endidx+1]
        #assert range_nodes[0] is start['elem'] and range_nodes[-1] is end['elem']
        #logging.debug("Nodes in delete range: %s" % (str(range_nodes)))

        marked_nodes = [] # Contains nodes that have been marked for deletion (directly or inderectly (via parent)).
        for node in range_nodes[1:-1]:
            if [n for n in marked_nodes if n is node]:
                continue
            subtree = node.depth_first()
            if not [e for e in subtree if e is end['elem']]:
                #logging.debug("Marking node: %s" % (subtree))
                marked_nodes.extend(subtree) # "subtree" does not include "node"

        ##### FOR DEBUGGING #####
        #s = ''
        #for e in self.flatten():
        #    if e is start['elem']:
        #        s += '%s[%s' % (e[:start['offset']], e[start['offset']:])
        #    elif e is end['elem']:
        #        s += '%s]%s' % (e[:end['offset']], e[end['offset']:])
        #    else:
        #        s += unicode(e)
        #logging.debug('Case 4: %s' % (s))
        #########################

        removed = self.copy()

        # Save offsets before we start changing the tree
        start_offset = self.elem_offset(start['elem'])
        end_offset = self.elem_offset(end['elem'])

        for node in marked_nodes:
            try:
                self.delete_elem(node)
            except ElementNotFoundError, e:
                pass

        if start['elem'] is not end['elem']:
            if start_offset == start['index'] or (not start['elem'].iseditable and start['elem'].isfragile):
                self.delete_elem(start['elem'])
            elif start['elem'].iseditable:
                start['elem'].sub = [ u''.join(start['elem'].sub)[:start['offset']] ]

            if end_offset + len(end['elem']) == end['index'] or (not end['elem'].iseditable and end['elem'].isfragile):
                self.delete_elem(end['elem'])
            elif end['elem'].iseditable:
                end['elem'].sub = [ u''.join(end['elem'].sub)[end['offset']:] ]

        self.prune()
        return removed, None, None

    def depth_first(self, filter=None):
        """Returns a list of the nodes in the tree in depth-first order."""
        if filter is None or not callable(filter):
            filter = lambda e: True
        elems = []
        if filter(self):
            elems.append(self)

        for sub in self.sub:
            if not isinstance(sub, StringElem):
                continue
            if sub.isleaf() and filter(sub):
                elems.append(sub)
            else:
                elems.extend(sub.depth_first())
        return elems

    def encode(self, encoding=sys.getdefaultencoding()):
        """More C{unicode} class emulation."""
        return unicode(self).encode(encoding)

    def elem_offset(self, elem):
        """Find the offset of C{elem} in the current tree.
            This cannot be reliably used if C{self.renderer} is used and even
            less so if the rendering function renders the string differently
            upon different calls. In Virtaal the C{StringElemGUI.index()} method
            is used as replacement for this one.
            @returns: The string index where element C{e} starts, or -1 if C{e}
                was not found."""
        offset = 0
        for e in self.iter_depth_first():
            if e is elem:
                return offset
            if e.isleaf():
                offset += len(e)

        # If we can't find the same instance element, settle for one that looks like it
        offset = 0
        for e in self.iter_depth_first():
            if e.isleaf():
                leafoffset = 0
                for s in e.sub:
                    if unicode(s) == unicode(elem):
                        return offset + leafoffset
                    else:
                        leafoffset += len(unicode(s))
                offset += len(e)
        return -1

    def elem_at_offset(self, offset):
        """Get the C{StringElem} in the tree that contains the string rendered
            at the given offset."""
        if offset < 0 or offset > len(self):
            return None

        length = 0
        elem = None
        for elem in self.flatten():
            elem_len = len(elem)
            if length <= offset < length+elem_len:
                return elem
            length += elem_len
        return elem

    def find(self, x):
        """Find sub-string C{x} in this string tree and return the position
            at which it starts."""
        if isinstance(x, basestring):
            return unicode(self).find(x)
        if isinstance(x, StringElem):
            return unicode(self).find(unicode(x))
        return None

    def find_elems_with(self, x):
        """Find all elements in the current sub-tree containing C{x}."""
        return [elem for elem in self.flatten() if x in unicode(elem)]

    def flatten(self, filter=None):
        """Flatten the tree by returning a depth-first search over the tree's leaves."""
        if filter is None or not callable(filter):
            filter = lambda e: True
        return [elem for elem in self.iter_depth_first(lambda e: e.isleaf() and filter(e))]

    def get_ancestor_where(self, child, criteria):
        parent = self.get_parent_elem(child)
        if parent is None or criteria(parent):
            return parent
        return self.get_ancestor_where(parent, criteria)

    def get_index_data(self, index):
        """Get info about the specified range in the tree.
            @returns: A dictionary with the following items:
                * I{elem}: The element in which C{index} resides.
                * I{index}: Copy of the C{index} parameter
                * I{offset}: The offset of C{index} into C{'elem'}."""
        info = {
            'elem':  self.elem_at_offset(index),
            'index': index,
        }
        info['offset'] = info['index'] - self.elem_offset(info['elem'])

        # Check if there "index" is actually between elements
        leftelem = self.elem_at_offset(index - 1)
        if leftelem is not None and leftelem is not info['elem']:
            info['elem'] = (leftelem, info['elem'])
            info['offset'] = (len(leftelem), 0)

        return info

    def get_parent_elem(self, child):
        """Searches the current sub-tree for and returns the parent of the
            C{child} element."""
        for elem in self.iter_depth_first():
            if not isinstance(elem, StringElem):
                continue
            for sub in elem.sub:
                if sub is child:
                    return elem
        return None

    def insert(self, offset, text):
        """Insert the given text at the specified offset of this string-tree's
            string (Unicode) representation."""
        if offset < 0 or offset > len(self) + 1:
            raise IndexError('Index out of range: %d' % (offset))
        if isinstance(text, (str, unicode)):
            text = StringElem(text)
        if not isinstance(text, StringElem):
            raise ValueError('text must be of type StringElem')

        def checkleaf(elem, text):
            if elem.isleaf() and type(text) is StringElem and text.isleaf():
                return unicode(text)
            return text

        # There are 4 general cases (including specific cases) where text can be inserted:
        # 1) At the beginning of the string (self)
        # 1.1) self.sub[0] is editable
        # 1.2) self.sub[0] is not editable
        # 2) At the end of the string (self)
        # 3) In the middle of a node
        # 4) Between two nodes
        # 4.1) Neither of the nodes are editable
        # 4.2) Both nodes are editable
        # 4.3) Node at offset-1 is editable, node at offset is not
        # 4.4) Node at offset is editable, node at offset-1 is not

        oelem = self.elem_at_offset(offset)

        # Case 1 #
        if offset == 0:
            # 1.1 #
            if oelem.iseditable:
                #logging.debug('Case 1.1')
                oelem.sub.insert(0, checkleaf(oelem, text))
                oelem.prune()
                return True
            # 1.2 #
            else:
                #logging.debug('Case 1.2')
                oparent = self.get_ancestor_where(oelem, lambda x: x.iseditable)
                if oparent is not None:
                    oparent.sub.insert(0, checkleaf(oparent, text))
                    return True
                else:
                    self.sub.insert(0, checkleaf(self, text))
                    return True
            return False

        # Case 2 #
        if offset >= len(self):
            #logging.debug('Case 2')
            last = self.flatten()[-1]
            parent = self.get_ancestor_where(last, lambda x: x.iseditable)
            if parent is None:
                parent = self
            parent.sub.append(checkleaf(parent, text))
            return True

        before = self.elem_at_offset(offset-1)

        # Case 3 #
        if oelem is before:
            if oelem.iseditable:
                #logging.debug('Case 3')
                eoffset = offset - self.elem_offset(oelem)
                if oelem.isleaf():
                    s = unicode(oelem) # Collapse all sibling strings into one
                    head = s[:eoffset]
                    tail = s[eoffset:]
                    if type(text) is StringElem and text.isleaf():
                        oelem.sub = [head + unicode(text) + tail]
                    else:
                        oelem.sub = [StringElem(head), text, StringElem(tail)]
                    return True
                else:
                    return oelem.insert(eoffset, text)
            return False

        # And the only case left: Case 4 #
        # 4.1 #
        if not before.iseditable and not oelem.iseditable:
            #logging.debug('Case 4.1')
            # Neither are editable, so we add it as a sibling (to the right) of before
            bparent = self.get_parent_elem(before)
            # bparent cannot be a leaf (because it has before as a child), so we
            # insert the text as StringElem(text)
            bindex = bparent.sub.index(before)
            bparent.sub.insert(bindex + 1, text)
            return True

        # 4.2 #
        elif before.iseditable and oelem.iseditable:
            #logging.debug('Case 4.2')
            return before.insert(len(before)+1, text) # Reinterpret as a case 2

        # 4.3 #
        elif before.iseditable and not oelem.iseditable:
            #logging.debug('Case 4.3')
            return before.insert(len(before)+1, text) # Reinterpret as a case 2

        # 4.4 #
        elif not before.iseditable and oelem.iseditable:
            #logging.debug('Case 4.4')
            return oelem.insert(0, text) # Reinterpret as a case 1

        return False

    def insert_between(self, left, right, text):
        """Insert the given text between the two parameter C{StringElem}s."""
        if not isinstance(left, StringElem) and left is not None:
            raise ValueError('"left" is not a StringElem or None')
        if not isinstance(right, StringElem) and right is not None:
            raise ValueError('"right" is not a StringElem or None')
        if left is right:
            if left.sub:
                # This is an error because the cursor cannot be inside an element ("left is right"),
                # if it has any other content. If an element has content, it will be at least directly
                # left or directly right of the current cursor position.
                raise ValueError('"left" and "right" refer to the same element and is not empty.')
            if not left.iseditable:
                return False
        if isinstance(text, unicode):
            text = StringElem(text)

        if left is right:
            #logging.debug('left%s.sub.append(%s)' % (repr(left), repr(text)))
            left.sub.append(text)
            return True
        # XXX: The "in" keyword is *not* used below, because the "in" tests
        # with __eq__ and not "is", as we do below. Testing for identity is
        # intentional and required.

        if left is None:
            if self is right:
                #logging.debug('self%s.sub.insert(0, %s)' % (repr(self), repr(text)))
                self.sub.insert(0, text)
                return True
            parent = self.get_parent_elem(right)
            if parent is not None:
                #logging.debug('parent%s.sub.insert(0, %s)' % (repr(parent), repr(text)))
                parent.sub.insert(0, text)
                return True
            return False

        if right is None:
            if self is left:
                #logging.debug('self%s.sub.append(%s)' % (repr(self), repr(text)))
                self.sub.append(text)
                return True
            parent = self.get_parent_elem(left)
            if parent is not None:
                #logging.debug('parent%s.sub.append(%s)' % (repr(parent), repr(text)))
                parent.sub.append(text)
                return True
            return False

        # The following two blocks handle the cases where one element
        # "surrounds" another as its parent. In that way the parent would be
        # "left" of its first child, like in the first case.
        ischild = False
        for sub in left.sub:
            if right is sub:
                ischild = True
                break
        if ischild:
            #logging.debug('left%s.sub.insert(0, %s)' % (repr(left), repr(text)))
            left.sub.insert(0, text)
            return True

        ischild = False
        for sub in right.sub:
            if left is sub:
                ischild = True
                break
        if ischild:
            #logging.debug('right%s.sub.append(%s)' % (repr(right), repr(text)))
            right.sub.append(text)
            return True

        parent = self.get_parent_elem(left)
        if parent.iseditable:
            idx = 1
            for child in parent.sub:
                if child is left:
                    break
                idx += 1
            #logging.debug('parent%s.sub.insert(%d, %s)' % (repr(parent), idx, repr(text)))
            parent.sub.insert(idx, text)
            return True

        parent = self.get_parent_elem(right)
        if parent.iseditable:
            idx = 0
            for child in parent.sub:
                if child is right:
                    break
                idx += 1
            #logging.debug('parent%s.sub.insert(%d, %s)' % (repr(parent), idx, repr(text)))
            parent.sub.insert(0, text)
            return True

        logging.debug('Could not insert between %s and %s... odd.' % (repr(left), repr(right)))
        return False

    def isleaf(self):
        """
        Whether or not this instance is a leaf node in the C{StringElem} tree.

        A node is a leaf node if it is a C{StringElem} (not a sub-class) and
        contains only sub-elements of type C{str} or C{unicode}.

        @rtype: bool
        """
        for e in self.sub:
            if not isinstance(e, (str, unicode)):
                return False
        return True

    def iter_depth_first(self, filter=None):
        """Iterate through the nodes in the tree in dept-first order."""
        if filter is None or not callable(filter):
            filter = lambda e: True
        if filter(self):
            yield self
        for sub in self.sub:
            if not isinstance(sub, StringElem):
                continue
            if sub.isleaf() and filter(sub):
                yield sub
            else:
                for node in sub.iter_depth_first():
                    if filter(node):
                        yield node

    def map(self, f, filter=None):
        """Apply C{f} to all nodes for which C{filter} returned C{True} (optional)."""
        if filter is not None and not callable(filter):
            raise ValueError('filter is not callable or None')
        if filter is None:
            filter = lambda e: True

        for elem in self.depth_first():
            if filter(elem):
                f(elem)

    @classmethod
    def parse(cls, pstr):
        """Parse an instance of this class from the start of the given string.
            This method should be implemented by any sub-class that wants to
            parseable by L{translate.storage.placeables.parse}.

            @type  pstr: unicode
            @param pstr: The string to parse into an instance of this class.
            @returns: An instance of the current class, or C{None} if the
                string not parseable by this class."""
        return cls(pstr)

    def print_tree(self, indent=0, verbose=False):
        """Print the tree from the current instance's point in an indented
            manner."""
        indent_prefix = " " * indent * 2
        out = (u"%s%s [%s]" % (indent_prefix, self.__class__.__name__, unicode(self))).encode('utf-8')
        if verbose:
            out += u' ' + repr(self)

        print out

        for elem in self.sub:
            if isinstance(elem, StringElem):
                elem.print_tree(indent+1, verbose=verbose)
            else:
                print (u'%s%s[%s]' % (indent_prefix, indent_prefix, elem)).encode('utf-8')

    def prune(self):
        """Remove unnecessary nodes to make the tree optimal."""
        for elem in self.iter_depth_first():
            if len(elem.sub) == 1:
                child = elem.sub[0]
                # Symbolically: X->StringElem(leaf) => X(leaf)
                #   (where X is any sub-class of StringElem, but not StringElem)
                if type(child) is StringElem and child.isleaf():
                    elem.sub = child.sub

                # Symbolically: StringElem->StringElem2->(leaves) => StringElem->(leaves)
                if type(elem) is StringElem and type(child) is StringElem:
                    elem.sub = child.sub

                # Symbolically: StringElem->X(leaf) => X(leaf)
                #   (where X is any sub-class of StringElem, but not StringElem)
                if type(elem) is StringElem and isinstance(child, StringElem) and type(child) is not StringElem:
                    parent = self.get_parent_elem(elem)
                    if parent is not None:
                        parent.sub[parent.sub.index(elem)] = child

            if type(elem) is StringElem and elem.isleaf():
                # Collapse all strings in this leaf into one string.
                elem.sub = [u''.join(elem.sub)]

            for i in reversed(range(len(elem.sub))):
                # Remove empty strings or StringElem nodes
                # (but not StringElem sub-class instances, because they might contain important (non-rendered) data.
                if type(elem.sub[i]) in (StringElem, str, unicode) and len(elem.sub[i]) == 0:
                    del elem.sub[i]
                    continue

                if type(elem.sub[i]) in (str, unicode) and not elem.isleaf():
                    elem.sub[i] = StringElem(elem.sub[i])

            # Merge sibling StringElem leaves
            if not elem.isleaf():
                changed = True
                while changed:
                    changed = False

                    for i in range(len(elem.sub)-1):
                        lsub = elem.sub[i]
                        rsub = elem.sub[i+1]

                        if type(lsub) is StringElem and type(rsub) is StringElem:
                            lsub.sub.extend(rsub.sub)
                            del elem.sub[i+1]
                            changed = True
                            break

    # TODO: Write unit test for this method
    def remove_type(self, ptype):
        """Replace nodes with type C{ptype} with base C{StringElem}s, containing
            the same sub-elements. This is only applicable to elements below the
            element tree root node."""
        for elem in self.iter_depth_first():
            if type(elem) is ptype:
                parent = self.get_parent_elem(elem)
                pindex = parent.sub.index(elem)
                parent.sub[pindex] = StringElem(
                    sub=elem.sub,
                    id=elem.id,
                    xid=elem.xid,
                    rid=elem.rid
                )

    def translate(self):
        """Transform the sub-tree according to some class-specific needs.
            This method should be either overridden in implementing sub-classes
            or dynamically replaced by specific applications.

            @returns: The transformed Unicode string representing the sub-tree.
            """
        return self.copy()
