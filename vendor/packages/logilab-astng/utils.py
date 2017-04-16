# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
# copyright 2003-2010 Sylvain Thenault, all rights reserved.
# contact mailto:thenault@gmail.com
#
# This file is part of logilab-astng.
#
# logilab-astng is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 2.1 of the License, or (at your
# option) any later version.
#
# logilab-astng is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-astng. If not, see <http://www.gnu.org/licenses/>.
"""this module contains some utilities to navigate in the tree or to
extract information from it

"""

__docformat__ = "restructuredtext en"

from logilab.astng._exceptions import IgnoreChild, ASTNGBuildingException


class ASTVisitor(object):
    """Abstract Base Class for Python AST Visitors.

    Visitors inheriting from ASTVisitors could visit
    compiler.ast, _ast or astng trees.

    Not all methods will have to be implemented;
    so some methods are just empty interfaces for catching
    cases where we don't want to do anything on the
    concerned node.
    """

    def visit_arguments(self, node):
        """dummy method for visiting an Arguments node"""

    def visit_assattr(self, node):
        """dummy method for visiting an AssAttr node"""

    def visit_assert(self, node):
        """dummy method for visiting an Assert node"""

    def visit_assign(self, node):
        """dummy method for visiting an Assign node"""

    def visit_assname(self, node):
        """dummy method for visiting an AssName node"""

    def visit_augassign(self, node):
        """dummy method for visiting an AugAssign node"""

    def visit_backquote(self, node):
        """dummy method for visiting an Backquote node"""

    def visit_binop(self, node):
        """dummy method for visiting an BinOp node"""

    def visit_boolop(self, node):
        """dummy method for visiting an BoolOp node"""

    def visit_break(self, node):
        """dummy method for visiting an Break node"""

    def visit_callfunc(self, node):
        """dummy method for visiting an CallFunc node"""

    def visit_class(self, node):
        """dummy method for visiting an Class node"""

    def visit_compare(self, node):
        """dummy method for visiting an Compare node"""

    def visit_comprehension(self, node):
        """dummy method for visiting an Comprehension node"""

    def visit_const(self, node):
        """dummy method for visiting an Const node"""

    def visit_continue(self, node):
        """dummy method for visiting an Continue node"""

    def visit_decorators(self, node):
        """dummy method for visiting an Decorators node"""

    def visit_delattr(self, node):
        """dummy method for visiting an DelAttr node"""

    def visit_delete(self, node):
        """dummy method for visiting an Delete node"""

    def visit_delname(self, node):
        """dummy method for visiting an DelName node"""

    def visit_dict(self, node):
        """dummy method for visiting an Dict node"""

    def visit_discard(self, node):
        """dummy method for visiting an Discard node"""

    def visit_emptynode(self, node):
        """dummy method for visiting an EmptyNode node"""

    def visit_excepthandler(self, node):
        """dummy method for visiting an ExceptHandler node"""

    def visit_ellipsis(self, node):
        """dummy method for visiting an Ellipsis node"""

    def visit_empty(self, node):
        """dummy method for visiting an Empty node"""

    def visit_exec(self, node):
        """dummy method for visiting an Exec node"""

    def visit_extslice(self, node):
        """dummy method for visiting an ExtSlice node"""

    def visit_for(self, node):
        """dummy method for visiting an For node"""

    def visit_from(self, node):
        """dummy method for visiting an From node"""

    def visit_function(self, node):
        """dummy method for visiting an Function node"""

    def visit_genexpr(self, node):
        """dummy method for visiting an ListComp node"""

    def visit_getattr(self, node):
        """dummy method for visiting an Getattr node"""

    def visit_global(self, node):
        """dummy method for visiting an Global node"""

    def visit_if(self, node):
        """dummy method for visiting an If node"""

    def visit_ifexp(self, node):
        """dummy method for visiting an IfExp node"""

    def visit_import(self, node):
        """dummy method for visiting an Import node"""

    def visit_index(self, node):
        """dummy method for visiting an Index node"""

    def visit_keyword(self, node):
        """dummy method for visiting an Keyword node"""

    def visit_lambda(self, node):
        """dummy method for visiting an Lambda node"""

    def visit_list(self, node):
        """dummy method for visiting an List node"""

    def visit_listcomp(self, node):
        """dummy method for visiting an ListComp node"""

    def visit_module(self, node):
        """dummy method for visiting an Module node"""

    def visit_name(self, node):
        """dummy method for visiting an Name node"""

    def visit_pass(self, node):
        """dummy method for visiting an Pass node"""

    def visit_print(self, node):
        """dummy method for visiting an Print node"""

    def visit_raise(self, node):
        """dummy method for visiting an Raise node"""

    def visit_return(self, node):
        """dummy method for visiting an Return node"""

    def visit_slice(self, node):
        """dummy method for visiting an Slice node"""

    def visit_subscript(self, node):
        """dummy method for visiting an Subscript node"""

    def visit_tryexcept(self, node):
        """dummy method for visiting an TryExcept node"""

    def visit_tryfinally(self, node):
        """dummy method for visiting an TryFinally node"""

    def visit_tuple(self, node):
        """dummy method for visiting an Tuple node"""

    def visit_unaryop(self, node):
        """dummy method for visiting an UnaryOp node"""

    def visit_while(self, node):
        """dummy method for visiting an While node"""

    def visit_with(self, node):
        """dummy method for visiting an With node"""

    def visit_yield(self, node):
        """dummy method for visiting an Yield node"""


class ASTWalker:
    """a walker visiting a tree in preorder, calling on the handler:

    * visit_<class name> on entering a node, where class name is the class of
    the node in lower case

    * leave_<class name> on leaving a node, where class name is the class of
    the node in lower case
    """

    def __init__(self, handler):
        self.handler = handler
        self._cache = {}

    def walk(self, node, _done=None):
        """walk on the tree from <node>, getting callbacks from handler"""
        if _done is None:
            _done = set()
        if node in _done:
            raise AssertionError((id(node), node, node.parent))
        _done.add(node)
        try:
            self.visit(node)
        except IgnoreChild:
            pass
        else:
            try:
                for child_node in node.get_children():
                    self.handler.set_context(node, child_node)
                    assert child_node is not node
                    self.walk(child_node, _done)
            except AttributeError:
                print node.__class__, id(node.__class__)
                raise
        self.leave(node)
        assert node.parent is not node

    def get_callbacks(self, node):
        """get callbacks from handler for the visited node"""
        klass = node.__class__
        methods = self._cache.get(klass)
        if methods is None:
            handler = self.handler
            kid = klass.__name__.lower()
            e_method = getattr(handler, 'visit_%s' % kid,
                               getattr(handler, 'visit_default', None))
            l_method = getattr(handler, 'leave_%s' % kid,
                               getattr(handler, 'leave_default', None))
            self._cache[klass] = (e_method, l_method)
        else:
            e_method, l_method = methods
        return e_method, l_method

    def visit(self, node):
        """walk on the tree from <node>, getting callbacks from handler"""
        method = self.get_callbacks(node)[0]
        if method is not None:
            method(node)

    def leave(self, node):
        """walk on the tree from <node>, getting callbacks from handler"""
        method = self.get_callbacks(node)[1]
        if method is not None:
            method(node)


class LocalsVisitor(ASTWalker):
    """visit a project by traversing the locals dictionary"""
    def __init__(self):
        ASTWalker.__init__(self, self)
        self._visited = {}

    def visit(self, node):
        """launch the visit starting from the given node"""
        if self._visited.has_key(node):
            return
        self._visited[node] = 1 # FIXME: use set ?
        methods = self.get_callbacks(node)
        recurse = 1
        if methods[0] is not None:
            try:
                methods[0](node)
            except IgnoreChild:
                recurse = 0
        if recurse:
            if 'locals' in node.__dict__: # skip Instance and other proxy
                for name, local_node in node.items():
                    self.visit(local_node)
        if methods[1] is not None:
            return methods[1](node)


def _check_children(node):
    """a helper function to check children - parent relations"""
    for child in node.get_children():
        ok = False
        if child is None:
            print "Hm, child of %s is None" % node
            continue
        if not hasattr(child, 'parent'):
            print " ERROR: %s has child %s %x with no parent" % (node, child, id(child))
        elif not child.parent:
            print " ERROR: %s has child %s %x with parent %r" % (node, child, id(child), child.parent)
        elif child.parent is not node:
            print " ERROR: %s %x has child %s %x with wrong parent %s" % (node,
                                      id(node), child, id(child), child.parent)
        else:
            ok = True
        if not ok:
            print "lines;", node.lineno, child.lineno
            print "of module", node.root(), node.root().name
            raise ASTNGBuildingException
        _check_children(child)


__all__ = ('LocalsVisitor', 'ASTWalker', 'ASTVisitor',)

