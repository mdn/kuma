# pylint: disable-msg=W0611
#
# Copyright (c) 2003-2010 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""some functions that may be useful for various checkers
"""

from logilab import astng

try:
    # python >= 2.4
    COMP_NODE_TYPES = (astng.ListComp, astng.GenExpr)
    FOR_NODE_TYPES = (astng.For, astng.Comprehension, astng.Comprehension)
except AttributeError:
    COMP_NODE_TYPES = astng.ListComp
    FOR_NODE_TYPES = (astng.For, astng.Comprehension)

def safe_infer(node):
    """return the inferred value for the given node.
    Return None if inference failed or if there is some ambiguity (more than
    one node has been inferred)
    """
    try:
        inferit = node.infer()
        value = inferit.next()
    except astng.InferenceError:
        return
    try:
        inferit.next()
        return # None if there is ambiguity on the inferred node
    except StopIteration:
        return value

def is_super(node):
    """return True if the node is referencing the "super" builtin function
    """
    if getattr(node, 'name', None) == 'super' and \
           node.root().name == '__builtin__':
        return True
    return False

def is_error(node):
    """return true if the function does nothing but raising an exception"""
    for child_node in node.get_children():
        if isinstance(child_node, astng.Raise):
            return True
        return False

def is_raising(body):
    """return true if the given statement node raise an exception"""
    for node in body:
        if isinstance(node, astng.Raise):
            return True
    return False

def is_empty(body):
    """return true if the given node does nothing but 'pass'"""
    return len(body) == 1 and isinstance(body[0], astng.Pass)

builtins = __builtins__.copy()
SPECIAL_BUILTINS = ('__builtins__',) # '__path__', '__file__')

def is_builtin(name): # was is_native_builtin
    """return true if <name> could be considered as a builtin defined by python
    """
    if builtins.has_key(name):
        return True
    if name in SPECIAL_BUILTINS:
        return True
    return False

def is_defined_before(var_node, comp_node_types=COMP_NODE_TYPES):
    """return True if the variable node is defined by a parent node (list
    or generator comprehension, lambda) or in a previous sibling node
    one the same line (statement_defining ; statement_using)
    """
    varname = var_node.name
    _node = var_node.parent
    while _node:
        if isinstance(_node, comp_node_types):
            for ass_node in _node.nodes_of_class(astng.AssName):
                if ass_node.name == varname:
                    return True
        elif isinstance(_node, astng.For):
            for ass_node in _node.target.nodes_of_class(astng.AssName):
                if ass_node.name == varname:
                    return True
        elif isinstance(_node, astng.With):
            if _node.vars.name == varname:
                return True
        elif isinstance(_node, (astng.Lambda, astng.Function)):
            if _node.args.is_argument(varname):
                return True
            if getattr(_node, 'name', None) == varname:
                return True
            break
        _node = _node.parent
    # possibly multiple statements on the same line using semi colon separator
    stmt = var_node.statement()
    _node = stmt.previous_sibling()
    lineno = stmt.fromlineno
    while _node and _node.fromlineno == lineno:
        for ass_node in _node.nodes_of_class(astng.AssName):
            if ass_node.name == varname:
                return True
        for imp_node in _node.nodes_of_class( (astng.From, astng.Import)):
            if varname in [name[1] or name[0] for name in imp_node.names]:
                return True
        _node = _node.previous_sibling()
    return False

def is_func_default(node):
    """return true if the given Name node is used in function default argument's
    value
    """
    parent = node.scope()
    if isinstance(parent, astng.Function):
        for default_node in parent.args.defaults:
            for default_name_node in default_node.nodes_of_class(astng.Name):
                if default_name_node is node:
                    return True
    return False

def is_func_decorator(node):
    """return true if the name is used in function decorator"""
    parent = node.parent
    while parent is not None:
        if isinstance(parent, astng.Decorators):
            return True
        if parent.is_statement or isinstance(parent, astng.Lambda):
            break
        parent = parent.parent
    return False

def is_ancestor_name(frame, node):
    """return True if `frame` is a astng.Class node with `node` in the
    subtree of its bases attribute
    """
    try:
        bases = frame.bases
    except AttributeError:
        return False
    for base in bases:
        if node in base.nodes_of_class(astng.Name):
            return True
    return False

def assign_parent(node):
    """return the higher parent which is not an AssName, Tuple or List node
    """
    while node and isinstance(node, (astng.AssName,
                                     astng.Tuple,
                                     astng.List)):
        node = node.parent
    return node

def overrides_an_abstract_method(class_node, name):
    """return True if pnode is a parent of node"""
    for ancestor in class_node.ancestors():
        if name in ancestor and isinstance(ancestor[name], astng.Function) and \
               ancestor[name].is_abstract(pass_is_abstract=False):
            return True
    return False

def overrides_a_method(class_node, name):
    """return True if <name> is a method overridden from an ancestor"""
    for ancestor in class_node.ancestors():
        if name in ancestor and isinstance(ancestor[name], astng.Function):
            return True
    return False

PYMETHODS = set(('__new__', '__init__', '__del__', '__hash__',
                 '__str__', '__repr__',
                 '__len__', '__iter__',
                 '__delete__', '__get__', '__set__',
                 '__getitem__', '__setitem__', '__delitem__', '__contains__',
                 '__getattribute__', '__getattr__', '__setattr__', '__delattr__',
                 '__call__',
                 '__enter__', '__exit__',
                 '__cmp__', '__ge__', '__gt__', '__le__', '__lt__', '__eq__',
                 '__nonzero__', '__neg__', '__invert__',
                 '__mul__', '__imul__', '__rmul__',
                 '__div__', '__idiv__', '__rdiv__',
                 '__add__', '__iadd__', '__radd__',
                 '__sub__', '__isub__', '__rsub__',
                 '__pow__', '__ipow__', '__rpow__',
                 '__mod__', '__imod__', '__rmod__',
                 '__and__', '__iand__', '__rand__',
                 '__or__', '__ior__', '__ror__',
                 '__xor__', '__ixor__', '__rxor__',
                 # XXX To be continued
                 ))
