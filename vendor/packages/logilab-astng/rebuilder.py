# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
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
"""this module contains utilities for rebuilding a compiler.ast or _ast tree in
order to get a single ASTNG representation

"""

from logilab.astng import ASTNGBuildingException, InferenceError
from logilab.astng import nodes
from logilab.astng.bases import YES, Instance

REDIRECT = {'arguments': 'Arguments',
            'Attribute': 'Getattr',
            'comprehension': 'Comprehension',
            'Call': 'CallFunc',
            'ClassDef': 'Class',
            "ListCompFor": 'Comprehension',
            "GenExprFor": 'Comprehension',
            'excepthandler': 'ExceptHandler',
            'Expr': 'Discard',
            'FunctionDef': 'Function',
            'GeneratorExp': 'GenExpr',
            'ImportFrom': 'From',
            'keyword': 'Keyword',
            'Repr': 'Backquote',
            
            'Add': 'BinOp',
            'Bitand': 'BinOp',
            'Bitor': 'BinOp',
            'Bitxor': 'BinOp',
            'Div': 'BinOp',
            'FloorDiv': 'BinOp',
            'LeftShift': 'BinOp',
            'Mod': 'BinOp',
            'Mul': 'BinOp',
            'Power': 'BinOp',
            'RightShift': 'BinOp',
            'Sub': 'BinOp',

            'And': 'BoolOp',
            'Or': 'BoolOp',

            'UnaryAdd': 'UnaryOp',
            'UnarySub': 'UnaryOp',
            'Not': 'UnaryOp',
            'Invert': 'UnaryOp'
            }


class RebuildVisitor(object):
    """Visitor to transform an AST to an ASTNG
    """
    def __init__(self, manager):
        self._manager = manager
        self.asscontext = None
        self._metaclass = None
        self._global_names = None
        self._delayed_assattr = []

    def visit(self, node, parent):
        if node is None: # some attributes of some nodes are just None
            return None
        cls_name = node.__class__.__name__
        visit_name = 'visit_' + REDIRECT.get(cls_name, cls_name).lower()
        visit_method = getattr(self, visit_name)
        return visit_method(node, parent)

    def build(self, node, modname, module_file):
        """rebuild the tree starting with an Module node;
        return an astng.Module node
        """
        self._metaclass = ['']
        self._global_names = []
        self._from_nodes = []
        module = self.visit_module(node, modname)
        module.file = module.path = module_file
        # init module cache here else we may get some infinite recursion
        # errors while infering delayed assignments
        if self._manager is not None:
            self._manager._cache[module.name] = module
        # handle delayed assattr nodes
        for from_node in self._from_nodes:
            self._add_from_names_to_locals(from_node, delayed=True)
        delay_assattr = self.delayed_assattr
        for delayed in self._delayed_assattr:
            delay_assattr(delayed)
        return module

    def _save_argument_name(self, node):
        """save argument names in locals"""
        if node.vararg:
            node.parent.set_local(node.vararg, node)
        if node.kwarg:
            node.parent.set_local(node.kwarg, node)


    # visit_<node> and delayed_<node> methods #################################

    def _set_assign_infos(self, newnode):
        """set some function or metaclass infos""" # XXX right ?
        klass = newnode.parent.frame()
        if (isinstance(klass, nodes.Class)
            and isinstance(newnode.value, nodes.CallFunc)
            and isinstance(newnode.value.func, nodes.Name)):
            func_name = newnode.value.func.name
            for ass_node in newnode.targets:
                try:
                    meth = klass[ass_node.name]
                    if isinstance(meth, nodes.Function):
                        if func_name in ('classmethod', 'staticmethod'):
                            meth.type = func_name
                        try: # XXX use setdefault ?
                            meth.extra_decorators.append(newnode.value)
                        except AttributeError:
                            meth.extra_decorators = [newnode.value]
                except (AttributeError, KeyError):
                    continue
        elif getattr(newnode.targets[0], 'name', None) == '__metaclass__':
            # XXX check more...
            self._metaclass[-1] = 'type' # XXX get the actual metaclass

    def visit_class(self, node, parent):
        """visit a Class node to become astng"""
        self._metaclass.append(self._metaclass[-1])
        newnode = self._visit_class(node, parent)
        metaclass = self._metaclass.pop()
        if not newnode.bases:
            # no base classes, detect new / style old style according to
            # current scope
            newnode._newstyle = metaclass == 'type'
        newnode.parent.frame().set_local(newnode.name, newnode)
        return newnode

    def visit_break(self, node, parent):
        """visit a Break node by returning a fresh instance of it"""
        newnode = nodes.Break()
        self._set_infos(node, newnode, parent)
        return newnode

    def visit_const(self, node, parent):
        """visit a Const node by returning a fresh instance of it"""
        newnode = nodes.Const(node.value)
        self._set_infos(node, newnode, parent)
        return newnode

    def visit_continue(self, node, parent):
        """visit a Continue node by returning a fresh instance of it"""
        newnode = nodes.Continue()
        self._set_infos(node, newnode, parent)
        return newnode

    def visit_ellipsis(self, node, parent):
        """visit an Ellipsis node by returning a fresh instance of it"""
        newnode = nodes.Ellipsis()
        self._set_infos(node, newnode, parent)
        return newnode

    def visit_emptynode(self, node, parent):
        """visit an EmptyNode node by returning a fresh instance of it"""
        newnode = nodes.EmptyNode()
        self._set_infos(node, newnode, parent)
        return newnode

    def _store_from_node(self, node):
        """handle From names by adding them to locals now or after"""
        # we can not handle wildcard imports if the source module is not
        # in the cache since 'import_module' calls the MANAGER and we will
        # end up with infinite recursions working with unfinished trees
        if node.modname in self._manager._cache:
             self._add_from_names_to_locals(node)
        else:
             self._from_nodes.append(node)

    def _add_from_names_to_locals(self, node, delayed=False):
        """store imported names to the locals;
        resort the locals if coming from a delayed node
        """
        cmp_nodes = lambda x, y: cmp(x.fromlineno, y.fromlineno)
        for (name, asname) in node.names:
            if name == '*':
                try:
                    imported = node.root().import_module(node.modname)
                except ASTNGBuildingException:
                    continue
                for name in imported.wildcard_import_names():
                    node.parent.set_local(name, node)
                    if delayed:
                        node.parent.scope().locals[name].sort(cmp=cmp_nodes)
            else:
                node.parent.set_local(asname or name, node)
                if delayed:
                    node.parent.scope().locals[asname or name].sort(cmp=cmp_nodes)


    def visit_function(self, node, parent):
        """visit an Function node to become astng"""
        self._global_names.append({})
        newnode = self._visit_function(node, parent)
        self._global_names.pop()
        frame = newnode.parent.frame()
        if isinstance(frame, nodes.Class):
            if newnode.name == '__new__':
                newnode.type = 'classmethod'
            else:
                newnode.type = 'method'
        if newnode.decorators is not None:
            for decorator_expr in newnode.decorators.nodes:
                if isinstance(decorator_expr, nodes.Name) and \
                       decorator_expr.name in ('classmethod', 'staticmethod'):
                    newnode.type = decorator_expr.name
        frame.set_local(newnode.name, newnode)
        return newnode

    def visit_global(self, node, parent):
        """visit an Global node to become astng"""
        newnode = nodes.Global(node.names)
        self._set_infos(node, newnode, parent)
        if self._global_names: # global at the module level, no effect
            for name in node.names:
                self._global_names[-1].setdefault(name, []).append(newnode)
        return newnode

    def _save_import_locals(self, newnode):
        """save import names in parent's locals"""
        for (name, asname) in newnode.names:
            name = asname or name
            newnode.parent.set_local(name.split('.')[0], newnode)

    def visit_pass(self, node, parent):
        """visit a Pass node by returning a fresh instance of it"""
        newnode = nodes.Pass()
        self._set_infos(node, newnode, parent)
        return newnode

    def _save_assignment(self, node, name=None):
        """save assignement situation since node.parent is not available yet"""
        if self._global_names and node.name in self._global_names[-1]:
            node.root().set_local(node.name, node)
        else:
            node.parent.set_local(node.name, node)

    def delayed_assattr(self, node):
        """visit a AssAttr node -> add name to locals, handle members
        definition
        """
        try:
            frame = node.frame()
            for infered in node.expr.infer():
                if infered is YES:
                    continue
                try:
                    if infered.__class__ is Instance:
                        infered = infered._proxied
                        iattrs = infered.instance_attrs
                    elif isinstance(infered, Instance):
                        # Const, Tuple, ... we may be wrong, may be not, but
                        # anyway we don't want to pollute builtin's namespace
                        continue
                    else:
                        iattrs = infered.locals
                except AttributeError:
                    # XXX log error
                    #import traceback
                    #traceback.print_exc()
                    continue
                values = iattrs.setdefault(node.attrname, [])
                if node in values:
                    continue
                # get assign in __init__ first XXX useful ?
                if frame.name == '__init__' and values and not \
                       values[0].frame().name == '__init__':
                    values.insert(0, node)
                else:
                    values.append(node)
        except InferenceError:
            pass


