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
"""python < 2.5 compiler package compatibility module [1]


 [1] http://docs.python.org/lib/module-compiler.ast.html

"""

__docformat__ = "restructuredtext en"

from compiler.ast import Const, Node, Sliceobj

# nodes which are not part of astng
from compiler.ast import And as _And, Or as _Or,\
     UnaryAdd as _UnaryAdd, UnarySub as _UnarySub, Not as _Not,\
     Invert as _Invert, Add as _Add, Div as _Div, FloorDiv as _FloorDiv,\
     Mod as _Mod, Mul as _Mul, Power as _Power, Sub as _Sub, Bitand as _Bitand,\
     Bitor as _Bitor, Bitxor as _Bitxor, LeftShift as _LeftShift,\
     RightShift as _RightShift


from logilab.astng import nodes as new
from logilab.astng.rebuilder import RebuildVisitor


CONST_NAME_TRANSFORMS = {'None':  None,
                         'True':  True,
                         'False': False}


def native_repr_tree(node, indent='', _done=None):
    """enhanced compiler.ast tree representation"""
    if _done is None:
        _done = set()
    if node in _done:
        print ('loop in tree: %r (%s)' % (node, getattr(node, 'lineno', None)))
        return
    _done.add(node)
    print indent + "<%s>" % node.__class__
    indent += '    '
    if not hasattr(node, "__dict__"): # XXX
        return
    for field, attr in node.__dict__.items():
        if attr is None or field == "_proxied":
            continue
        if type(attr) is list:
            if not attr: continue
            print indent + field + ' ['
            for elt in attr:
                if type(elt) is tuple:
                    for val in elt:
                        native_repr_tree(val, indent, _done)
                else:
                    native_repr_tree(elt, indent, _done)
            print indent + ']'
            continue
        if isinstance(attr, Node):
            print indent + field
            native_repr_tree(attr, indent, _done)
        else:
            print indent + field,  repr(attr)


# some astng nodes unexistent in compiler #####################################

BinOp_OP_CLASSES = {_Add: '+',
              _Div: '/',
              _FloorDiv: '//',
              _Mod: '%',
              _Mul: '*',
              _Power: '**',
              _Sub: '-',
              _Bitand: '&',
              _Bitor: '|',
              _Bitxor: '^',
              _LeftShift: '<<',
              _RightShift: '>>'
              }
BinOp_BIT_CLASSES = {'&': _Bitand,
               '|': _Bitor,
               '^': _Bitxor
               }


BoolOp_OP_CLASSES = {_And: 'and',
              _Or: 'or'
              }

UnaryOp_OP_CLASSES = {_UnaryAdd: '+',
              _UnarySub: '-',
              _Not: 'not',
              _Invert: '~'
              }


# compiler rebuilder ##########################################################

def _filter_none(node):
    """transform Const(None) to None"""
    if isinstance(node, Const) and node.value is None:
        return None
    else:
        return node


class TreeRebuilder(RebuildVisitor):
    """Rebuilds the compiler tree to become an ASTNG tree"""

    def _init_else_node(self, node, newnode):
        """visit else block; replace None by empty list"""
        if not node.else_:
            return []
        return [self.visit(child, newnode) for child in node.else_.nodes]

    def _set_infos(self, oldnode, newnode, newparent):
        newnode.parent = newparent
        if hasattr(oldnode, 'lineno'):
            newnode.lineno = oldnode.lineno
        if hasattr(oldnode, 'fromlineno'):
            newnode.fromlineno = oldnode.fromlineno
        if hasattr(oldnode, 'tolineno'):
            newnode.tolineno = oldnode.tolineno
        if hasattr(oldnode, 'blockstart_tolineno'):
            newnode.blockstart_tolineno = oldnode.blockstart_tolineno

    def _check_del_node(self, node, parent, targets):
        """insert a Delete node if necessary.

        As for assignments we have a Assign (or For or ...) node, this method
        is only called in delete contexts. Hence we return a Delete node"""
        if self.asscontext is None:
            self.asscontext = "Del"
            newnode = new.Delete()
            self._set_infos(node, newnode, parent)
            newnode.targets = [self.visit(elt, newnode) for elt in targets]
            self.asscontext = None
            return newnode
        else:
            # this will trigger the visit_ass* methods to create the right nodes
            return False

    def _nodify_args(self, parent, values):
        """transform arguments and tuples or lists of arguments into astng nodes"""
        res = []
        for arg in values:
            if isinstance(arg, (tuple, list)):
                n = new.Tuple()
                self._set_infos(parent, n, parent)
                n.elts = self._nodify_args(n, arg)
            else:
                assert isinstance(arg, basestring)
                n = new.AssName()
                self._set_infos(parent, n, parent)
                n.name = arg
                self._save_assignment(n, n.name)
            res.append(n)
        return res

    def visit_arguments(self, node, parent):
        """visit an Arguments node by returning a fresh instance of it"""
        # /!\ incoming node is Function or Lambda, coming directly from visit_*
        if node.flags & 8:
            kwarg = node.argnames.pop()
        else:
            kwarg = None
        if node.flags & 4:
            vararg = node.argnames.pop()
        else:
            vararg = None
        newnode = new.Arguments(vararg, kwarg)
        newnode.parent = parent
        newnode.fromlineno = parent.fromlineno
        try:
            newnode.tolineno = parent.blockstart_tolineno
        except AttributeError: # lambda
            newnode.tolineno = parent.tolineno
        newnode.args = self._nodify_args(newnode, node.argnames)
        self._save_argument_name(newnode)
        newnode.defaults = [self.visit(n, newnode) for n in node.defaults]
        return newnode

    def visit_assattr(self, node, parent):
        """visit an AssAttr node by returning a fresh instance of it"""
        delnode = self._check_del_node(node, parent, [node])
        if delnode:
            return delnode
        elif self.asscontext == "Del":
            return self.visit_delattr(node, parent)
        elif self.asscontext in ("Ass", "Aug"):
            newnode = new.AssAttr()
            self._set_infos(node, newnode, parent)
            asscontext, self.asscontext = self.asscontext, None
            newnode.expr = self.visit(node.expr, newnode)
            self.asscontext = asscontext
            newnode.attrname = node.attrname
            self._delayed_assattr.append(newnode)
            return newnode

    def visit_assname(self, node, parent):
        """visit an AssName node by returning a fresh instance of it"""
        delnode = self._check_del_node(node, parent, [node])
        if delnode:
            return delnode
        elif self.asscontext == "Del":
            return self.visit_delname(node, parent)
        assert self.asscontext in ("Ass", "Aug")
        newnode = new.AssName()
        self._set_infos(node, newnode, parent)
        newnode.name = node.name
        self._save_assignment(newnode)
        return newnode

    def visit_assert(self, node, parent):
        """visit an Assert node by returning a fresh instance of it"""
        newnode = new.Assert()
        self._set_infos(node, newnode, parent)
        newnode.test = self.visit(node.test, newnode)
        newnode.fail = self.visit(node.fail, newnode)
        return newnode

    def visit_assign(self, node, parent):
        """visit an Assign node by returning a fresh instance of it"""
        newnode = new.Assign()
        self._set_infos(node, newnode, parent)
        self.asscontext = 'Ass'
        newnode.targets = [self.visit(child, newnode) for child in node.nodes]
        # /!\ Subscript can appear on both sides,
        # so we need 'Ass' in rhs to avoid inserting a Delete node
        newnode.value = self.visit(node.expr, newnode)
        self.asscontext = None
        self._set_assign_infos(newnode)
        return newnode

    def visit_asslist(self, node, parent):
        # FIXME : use self._check_del_node(node, [node]) more precise ?
        delnode = self._check_del_node(node, parent, node.nodes)
        if delnode:
            return delnode
        return self.visit_list(node, parent)

    def visit_asstuple(self, node, parent):
        delnode = self._check_del_node(node, parent, node.nodes)
        if delnode:
            return delnode
        return self.visit_tuple(node, parent)

    def visit_augassign(self, node, parent):
        """visit an AugAssign node by returning a fresh instance of it"""
        newnode = new.AugAssign()
        self._set_infos(node, newnode, parent)
        self.asscontext = "Aug"
        newnode.target = self.visit(node.node, newnode)
        self.asscontext = None
        newnode.op = node.op
        newnode.value = self.visit(node.expr, newnode)
        return newnode

    def visit_backquote(self, node, parent):
        """visit a Backquote node by returning a fresh instance of it"""
        newnode = new.Backquote()
        self._set_infos(node, newnode, parent)
        newnode.value = self.visit(node.expr, newnode)
        return newnode

    def visit_binop(self, node, parent):
        """visit a BinOp node by returning a fresh instance of it"""
        newnode = new.BinOp()
        self._set_infos(node, newnode, parent)
        newnode.op = BinOp_OP_CLASSES[node.__class__]
        if newnode.op in ('&', '|', '^'):
            newnode.right = self.visit(node.nodes[-1], newnode)
            bitop = BinOp_BIT_CLASSES[newnode.op]
            if len(node.nodes) > 2:
                # create a bitop node on the fly and visit it:
                # XXX can't we create directly the right node ?
                newnode.left = self.visit(bitop(node.nodes[:-1]), newnode)
            else:
                newnode.left = self.visit(node.nodes[0], newnode)
        else:
            newnode.left = self.visit(node.left, newnode)
            newnode.right = self.visit(node.right, newnode)
        return newnode

    def visit_boolop(self, node, parent):
        """visit a BoolOp node by returning a fresh instance of it"""
        newnode = new.BoolOp()
        self._set_infos(node, newnode, parent)
        newnode.values = [self.visit(child, newnode) for child in node.nodes]
        newnode.op = BoolOp_OP_CLASSES[node.__class__]
        return newnode

    def visit_callfunc(self, node, parent):
        """visit a CallFunc node by returning a fresh instance of it"""
        newnode = new.CallFunc()
        self._set_infos(node, newnode, parent)
        newnode.func = self.visit(node.node, newnode)
        newnode.args = [self.visit(child, newnode) for child in node.args]
        if node.star_args:
            newnode.starargs = self.visit(node.star_args, newnode)
        if node.dstar_args:
            newnode.kwargs = self.visit(node.dstar_args, newnode)
        return newnode

    def _visit_class(self, node, parent):
        """visit a Class node by returning a fresh instance of it"""
        newnode = new.Class(node.name, node.doc)
        self._set_infos(node, newnode, parent)
        newnode.bases = [self.visit(child, newnode) for child in node.bases]
        newnode.body = [self.visit(child, newnode) for child in node.code.nodes]
        return newnode

    def visit_compare(self, node, parent):
        """visit a Compare node by returning a fresh instance of it"""
        newnode = new.Compare()
        self._set_infos(node, newnode, parent)
        newnode.left = self.visit(node.expr, newnode)
        newnode.ops = [(op, self.visit(child, newnode)) for op, child in node.ops]
        return newnode

    def visit_comprehension(self, node, parent):
        """visit a Comprehension node by returning a fresh instance of it"""
        newnode = new.Comprehension()
        self._set_infos(node, newnode, parent)
        self.asscontext = "Ass"
        newnode.target = self.visit(node.assign, newnode)
        self.asscontext = None
        if hasattr(node, 'list'):# ListCompFor
            iters = node.list
        else:# GenExprFor
            iters = node.iter
        newnode.iter = self.visit(iters, newnode)
        if node.ifs:
            newnode.ifs = [self.visit(iff.test, newnode) for iff in node.ifs]
        else:
            newnode.ifs = []
        return newnode

    def visit_decorators(self, node, parent):
        """visit a Decorators node by returning a fresh instance of it"""
        newnode = new.Decorators()
        self._set_infos(node, newnode, parent)
        newnode.nodes = [self.visit(child, newnode) for child in node.nodes]
        return newnode

    def visit_delattr(self, node, parent):
        """visit a DelAttr node by returning a fresh instance of it"""
        newnode = new.DelAttr()
        self._set_infos(node, newnode, parent)
        newnode.expr = self.visit(node.expr, newnode)
        newnode.attrname = node.attrname
        return newnode

    def visit_delname(self, node, parent):
        """visit a DelName node by returning a fresh instance of it"""
        newnode = new.DelName()
        self._set_infos(node, newnode, parent)
        newnode.name = node.name
        self._save_assignment(newnode) # ???
        return newnode

    def visit_dict(self, node, parent):
        """visit a Dict node by returning a fresh instance of it"""
        newnode = new.Dict()
        self._set_infos(node, newnode, parent)
        newnode.items = [(self.visit(key, newnode), self.visit(value, newnode))
                         for (key, value) in node.items]
        return newnode

    def visit_discard(self, node, parent):
        """visit a Discard node by returning a fresh instance of it"""
        newnode = new.Discard()
        if node.lineno is None:
            # ignore dummy Discard introduced when a statement
            # is ended by a semi-colon: remove it at the end of rebuilding
            self._remove_nodes.append((newnode, parent))
        self._set_infos(node, newnode, parent)
        self.asscontext = "Dis"
        newnode.value = self.visit(node.expr, newnode)
        self.asscontext = None
        return newnode

    def visit_excepthandler(self, node, parent):
        """visit an ExceptHandler node by returning a fresh instance of it"""
        newnode = new.ExceptHandler()
        self._set_infos(node, newnode, parent)
        newnode.type = self.visit(node.type, newnode)
        newnode.name = self.visit(node.name, newnode)
        newnode.body = [self.visit(child, newnode) for child in node.body]
        return newnode

    def visit_exec(self, node, parent):
        """visit an Exec node by returning a fresh instance of it"""
        newnode = new.Exec()
        self._set_infos(node, newnode, parent)
        newnode.expr = self.visit(node.expr, newnode)
        newnode.globals = self.visit(node.locals, newnode)
        newnode.locals = self.visit(node.globals, newnode)
        return newnode

    def visit_extslice(self, node, parent):
        """visit an ExtSlice node by returning a fresh instance of it"""
        newnode = new.ExtSlice()
        self._set_infos(node, newnode, parent)
        newnode.dims = [self.visit(dim, newnode) for dim in node.subs]
        return newnode

    def visit_for(self, node, parent):
        """visit a For node by returning a fresh instance of it"""
        newnode = new.For()
        self._set_infos(node, newnode, parent)
        self.asscontext = "Ass"
        newnode.target = self.visit(node.assign, newnode)
        self.asscontext = None
        newnode.iter = self.visit(node.list, newnode)
        newnode.body = [self.visit(child, newnode) for child in node.body.nodes]
        newnode.orelse = self._init_else_node(node, newnode)
        return newnode

    def visit_from(self, node, parent):
        """visit a From node by returning a fresh instance of it"""
        newnode = new.From(node.modname, node.names)
        self._set_infos(node, newnode, parent)
        self._store_from_node(newnode)
        return newnode

    def _visit_function(self, node, parent):
        """visit a Function node by returning a fresh instance of it"""
        newnode = new.Function(node.name, node.doc)
        self._set_infos(node, newnode, parent)
        newnode.decorators = self.visit(node.decorators, newnode)
        newnode.args = self.visit_arguments(node, newnode)
        newnode.body = [self.visit(child, newnode) for child in node.code.nodes]
        return newnode

    def visit_genexpr(self, node, parent):
        """visit a GenExpr node by returning a fresh instance of it"""
        newnode = new.GenExpr()
        self._set_infos(node, newnode, parent)
        # remove GenExprInner node
        newnode.elt = self.visit(node.code.expr, newnode)
        newnode.generators = [self.visit(n, newnode) for n in node.code.quals]
        return newnode

    def visit_getattr(self, node, parent):
        """visit a Getattr node by returning a fresh instance of it"""
        newnode = new.Getattr()
        self._set_infos(node, newnode, parent)
        if self.asscontext == "Aug":
            return self.visit_assattr(node, parent)
        newnode.expr = self.visit(node.expr, newnode)
        newnode.attrname = node.attrname
        return newnode
        
    def visit_if(self, node, parent):
        """visit an If node by returning a fresh instance of it"""
        newnode = subnode = new.If()
        self._set_infos(node, newnode, parent)
        test, body = node.tests[0]
        newnode.test = self.visit(test, newnode)
        newnode.body = [self.visit(child, newnode) for child in body.nodes]
        for test, body in node.tests[1:]:# this represents 'elif'
            # create successively If nodes and put it in orelse of the previous
            subparent, subnode = subnode, new.If()
            subnode.parent = subparent
            subnode.fromlineno = test.fromlineno
            subnode.tolineno = body.nodes[-1].tolineno
            subnode.blockstart_tolineno = test.tolineno
            subnode.test = self.visit(test, subnode)
            subnode.body = [self.visit(child, subnode) for child in body.nodes]
            subparent.orelse = [subnode]
        # the last subnode gets the else block:
        subnode.orelse = self._init_else_node(node, subnode)
        return newnode

    def visit_ifexp(self, node, parent):
        """visit an IfExp node by returning a fresh instance of it"""
        newnode = new.IfExp()
        self._set_infos(node, newnode, parent)
        newnode.test = self.visit(node.test, newnode)
        newnode.body = [self.visit(child, newnode) for child in node.body]
        newnode.orelse = self.visit(node.orelse, newnode)
        return newnode

    def visit_import(self, node, parent):
        """visit an Import node by returning a fresh instance of it"""
        newnode = new.Import()
        self._set_infos(node, newnode, parent)
        newnode.names = node.names
        self._save_import_locals(newnode)
        return newnode

    def visit_index(self, node, parent):
        """visit an Index node by returning a fresh instance of it"""
        newnode = new.Index()
        self._set_infos(node, newnode, parent)
        newnode.value = self.visit(node.subs[0], newnode)
        return newnode

    def visit_keyword(self, node, parent):
        """visit a Keyword node by returning a fresh instance of it"""
        newnode = new.Keyword()
        self._set_infos(node, newnode, parent)
        newnode.value = self.visit(node.expr, newnode)
        newnode.arg = node.name
        return newnode

    def visit_lambda(self, node, parent):
        """visit a Lambda node by returning a fresh instance of it"""
        newnode = new.Lambda()
        self._set_infos(node, newnode, parent)
        newnode.body = self.visit(node.code, newnode)
        newnode.args = self.visit_arguments(node, newnode)
        return newnode

    def visit_list(self, node, parent):
        """visit a List node by returning a fresh instance of it"""
        newnode = new.List()
        self._set_infos(node, newnode, parent)
        newnode.elts = [self.visit(child, newnode) for child in node.nodes]
        return newnode

    def visit_listcomp(self, node, parent):
        """visit a ListComp node by returning a fresh instance of it"""
        newnode = new.ListComp()
        self._set_infos(node, newnode, parent)
        newnode.elt = self.visit(node.expr, newnode)
        newnode.generators = [self.visit(child, newnode) for child in node.quals]
        return newnode

    def visit_module(self, node, modname):
        """visit a Module node by returning a fresh instance of it"""
        newnode = new.Module(modname, node.doc)
        self._set_infos(node, newnode, None)
        self._remove_nodes = [] # list of ';' Discard nodes to be removed
        newnode.body = [self.visit(child, newnode) for child in node.node.nodes]
        for discard, d_parent in self._remove_nodes:
            d_parent.child_sequence(discard).remove(discard)
        return newnode

    def visit_name(self, node, parent):
        """visit a Name node by returning a fresh instance of it"""
        if node.name in CONST_NAME_TRANSFORMS:
            newnode = new.Const(CONST_NAME_TRANSFORMS[node.name])
            self._set_infos(node, newnode, parent)
            return newnode
        if self.asscontext == "Aug":
            return self.visit_assname(node, parent)
        newnode = new.Name()
        self._set_infos(node, newnode, parent)
        newnode.name = node.name
        return newnode

    def visit_print(self, node, parent):
        """visit a Print node by returning a fresh instance of it"""
        newnode = new.Print()
        self._set_infos(node, newnode, parent)
        newnode.dest = self.visit(node.dest, newnode)
        newnode.values = [self.visit(child, newnode) for child in node.nodes]
        newnode.nl = False
        return newnode

    def visit_printnl(self, node, parent):
        newnode = self.visit_print(node, parent)
        self._set_infos(node, newnode, parent)
        newnode.nl = True
        return newnode

    def visit_raise(self, node, parent):
        """visit a Raise node by returning a fresh instance of it"""
        newnode = new.Raise()
        self._set_infos(node, newnode, parent)
        newnode.type = self.visit(node.expr1, newnode)
        newnode.inst = self.visit(node.expr2, newnode)
        newnode.tback = self.visit(node.expr3, newnode)
        return newnode

    def visit_return(self, node, parent):
        """visit a Return node by returning a fresh instance of it"""
        newnode = new.Return()
        self._set_infos(node, newnode, parent)
        newnode.value = self.visit(_filter_none(node.value), newnode)
        return newnode

    def visit_slice(self, node, parent):
        """visit a compiler.Slice by returning a astng.Subscript"""
        # compiler.Slice nodes represent astng.Subscript nodes
        # the astng.Subscript node has a astng.Slice node as child
        if node.flags == 'OP_DELETE':
            delnode = self._check_del_node(node, parent, [node])
            if delnode:
                return delnode
        newnode = new.Subscript()
        self._set_infos(node, newnode, parent)
        newnode.value = self.visit(node.expr, newnode)
        newnode.slice = self.visit_sliceobj(node, newnode, slice=True)
        return newnode

    def visit_sliceobj(self, node, parent, slice=False):
        """visit a Slice or Sliceobj; transform Sliceobj into a astng.Slice"""
        newnode = new.Slice()
        self._set_infos(node, newnode, parent)
        if slice:
            subs = [node.lower, node.upper, None]
        else:
            subs = node.nodes
            if len(subs) == 2:
                subs.append(None)
        newnode.lower = self.visit(_filter_none(subs[0]), newnode)
        newnode.upper = self.visit(_filter_none(subs[1]), newnode)
        newnode.step = self.visit(_filter_none(subs[2]), newnode)
        return newnode

    def visit_subscript(self, node, parent):
        """visit a Subscript node by returning a fresh instance of it"""
        if node.flags == 'OP_DELETE':
            delnode = self._check_del_node(node, parent, [node])
            if delnode:
                return delnode
        newnode = new.Subscript()
        self._set_infos(node, newnode, parent)
        self.asscontext, asscontext = None, self.asscontext
        newnode.value = self.visit(node.expr, newnode)
        if [n for n in node.subs if isinstance(n, Sliceobj)]:
            if len(node.subs) == 1: # Sliceobj -> new.Slice
                newnode.slice = self.visit_sliceobj(node.subs[0], newnode)
            else: # ExtSlice
                newnode.slice = self.visit_extslice(node, newnode)
        else: # Index
            newnode.slice = self.visit_index(node, newnode)
        self.asscontext = asscontext
        return newnode

    def visit_tryexcept(self, node, parent):
        """visit a TryExcept node by returning a fresh instance of it"""
        newnode = new.TryExcept()
        self._set_infos(node, newnode, parent)
        newnode.body = [self.visit(child, newnode) for child in node.body.nodes]
        newnode.handlers = [self._visit_excepthandler(newnode, values)
                            for values in node.handlers]
        newnode.orelse = self._init_else_node(node, newnode)
        return newnode

    def _visit_excepthandler(self, parent, values):
        """build an ExceptHandler node from given values and visit children"""
        newnode = new.ExceptHandler()
        newnode.parent = parent
        exctype, excobj, body = values
        if exctype and exctype.lineno:
            newnode.fromlineno =  exctype.lineno
        else:
            newnode.fromlineno =  body.nodes[0].fromlineno - 1
        newnode.tolineno = body.nodes[-1].tolineno
        if excobj:
            newnode.blockstart_tolineno = excobj.tolineno
        elif exctype:
            newnode.blockstart_tolineno = exctype.tolineno
        else:
            newnode.blockstart_tolineno = newnode.fromlineno
        newnode.type = self.visit(exctype, newnode)
        self.asscontext = "Ass"
        newnode.name = self.visit(excobj, newnode)
        self.asscontext = None
        newnode.body = [self.visit(child, newnode) for child in body.nodes]
        return newnode

    def visit_tryfinally(self, node, parent):
        """visit a TryFinally node by returning a fresh instance of it"""
        newnode = new.TryFinally()
        self._set_infos(node, newnode, parent)
        newnode.body = [self.visit(child, newnode) for child in node.body.nodes]
        newnode.finalbody = [self.visit(n, newnode) for n in node.final.nodes]
        return newnode

    def visit_tuple(self, node, parent):
        """visit a Tuple node by returning a fresh instance of it"""
        newnode = new.Tuple()
        self._set_infos(node, newnode, parent)
        newnode.elts = [self.visit(child, newnode) for child in node.nodes]
        return newnode

    def visit_unaryop(self, node, parent):
        """visit an UnaryOp node by returning a fresh instance of it"""
        newnode = new.UnaryOp()
        self._set_infos(node, newnode, parent)
        newnode.operand = self.visit(node.expr, newnode)
        newnode.op = UnaryOp_OP_CLASSES[node.__class__]
        return newnode

    def visit_while(self, node, parent):
        """visit a While node by returning a fresh instance of it"""
        newnode = new.While()
        self._set_infos(node, newnode, parent)
        newnode.test = self.visit(node.test, newnode)
        newnode.body = [self.visit(child, newnode) for child in node.body.nodes]
        newnode.orelse = self._init_else_node(node, newnode)
        return newnode

    def visit_with(self, node, parent):
        """visit a With node by returning a fresh instance of it"""
        newnode = new.With()
        self._set_infos(node, newnode, parent)
        newnode.expr = self.visit(node.expr, newnode)
        newnode.vars = self.visit(node.vars, newnode)
        newnode.body = [self.visit(child, newnode) for child in node.body]
        return newnode

    def visit_yield(self, node, parent):
        """visit a Yield node by returning a fresh instance of it"""
        discard = self._check_discard(node, parent)
        if discard:
            return discard
        newnode = new.Yield()
        self._set_infos(node, newnode, parent)
        newnode.value = self.visit(node.value, newnode)
        return newnode

    def _check_discard(self, node, parent):
        """check if we introduced already a discard node."""
        # XXX we should maybe use something else then 'asscontext' here
        if self.asscontext is None:
            self.asscontext = 'Dis'
            newnode = new.Discard()
            self._set_infos(node, newnode, parent)
            newnode.value = self.visit(node, newnode)
            self.asscontext = None
            return newnode
        return False

