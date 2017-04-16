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
"""This module contains the classes for "scoped" node, i.e. which are opening a
new local scope in the language definition : Module, Class, Function (and
Lambda and GenExpr to some extends).

"""
from __future__ import generators

__doctype__ = "restructuredtext en"

import __builtin__
import sys

from logilab.common.compat import chain, set
from logilab.common.decorators import cached

from logilab.astng import MANAGER, NotFoundError, NoDefault, \
     ASTNGBuildingException, InferenceError
from logilab.astng.node_classes import (Const, DelName, DelAttr,
     Dict, From, List, Name, Pass, Raise, Return, Tuple, Yield,
     are_exclusive, LookupMixIn, const_factory as cf, unpack_infer)
from logilab.astng.bases import (NodeNG, BaseClass, InferenceContext, Instance,
     YES, Generator, UnboundMethod, BoundMethod, _infer_stmts, copy_context)
from logilab.astng.mixins import (StmtMixIn, FilterStmtsMixin)

from logilab.astng.nodes_as_string import as_string


def remove_nodes(func, cls):
    def wrapper(*args, **kwargs):
        nodes = [n for n in func(*args, **kwargs) if not isinstance(n, cls)]
        if not nodes:
            raise NotFoundError()
        return nodes
    return wrapper


def function_to_method(n, klass):
    if isinstance(n, Function):
        if n.type == 'classmethod':
            return BoundMethod(n, klass)
        if n.type != 'staticmethod':
            return UnboundMethod(n)
    return n

def std_special_attributes(self, name, add_locals=True):
    if add_locals:
        locals = self.locals
    else:
        locals = {}
    if name == '__name__':
        return [cf(self.name)] + locals.get(name, [])
    if name == '__doc__':
        return [cf(self.doc)] + locals.get(name, [])
    if name == '__dict__':
        return [Dict()] + locals.get(name, [])
    raise NotFoundError(name)



def builtin_lookup(name):
    """lookup a name into the builtin module
    return the list of matching statements and the astng for the builtin
    module
    """
    # TODO : once there is no more monkey patching, make a BUILTINASTNG const
    builtinastng = MANAGER.astng_from_module(__builtin__)
    if name == '__dict__':
        return builtinastng, ()
    try:
        stmts = builtinastng.locals[name]
    except KeyError:
        stmts = ()
    return builtinastng, stmts


# TODO move this Mixin to mixins.py; problem: 'Function' in _scope_lookup
class LocalsDictNodeNG(LookupMixIn, NodeNG):
    """ this class provides locals handling common to Module, Function
    and Class nodes, including a dict like interface for direct access
    to locals information
    """

    # attributes below are set by the builder module or by raw factories

    # dictionary of locals with name as key and node defining the local as
    # value

    def qname(self):
        """return the 'qualified' name of the node, eg module.name,
        module.class.name ...
        """
        if self.parent is None:
            return self.name
        return '%s.%s' % (self.parent.frame().qname(), self.name)

    def frame(self):
        """return the first parent frame node (i.e. Module, Function or Class)
        """
        return self

    def scope(self):
        """return the first node defining a new scope (i.e. Module,
        Function, Class, Lambda but also GenExpr)
        """
        return self


    def _scope_lookup(self, node, name, offset=0):
        """XXX method for interfacing the scope lookup"""
        try:
            stmts = node._filter_stmts(self.locals[name], self, offset)
        except KeyError:
            stmts = ()
        if stmts:
            return self, stmts
        if self.parent: # i.e. not Module
            # nested scope: if parent scope is a function, that's fine
            # else jump to the module
            pscope = self.parent.scope()
            if not isinstance(pscope, Function):
                pscope = pscope.root()
            return pscope.scope_lookup(node, name)
        return builtin_lookup(name) # Module



    def set_local(self, name, stmt):
        """define <name> in locals (<stmt> is the node defining the name)
        if the node is a Module node (i.e. has globals), add the name to
        globals

        if the name is already defined, ignore it
        """
        #assert not stmt in self.locals.get(name, ()), (self, stmt)
        self.locals.setdefault(name, []).append(stmt)

    __setitem__ = set_local

    def _append_node(self, child):
        """append a child, linking it in the tree"""
        self.body.append(child)
        child.parent = self

    def add_local_node(self, child_node, name=None):
        """append a child which should alter locals to the given node"""
        if name != '__class__':
            # add __class__ node as a child will cause infinite recursion later!
            self._append_node(child_node)
        self.set_local(name or child_node.name, child_node)


    def __getitem__(self, item):
        """method from the `dict` interface returning the first node
        associated with the given name in the locals dictionary

        :type item: str
        :param item: the name of the locally defined object
        :raises KeyError: if the name is not defined
        """
        return self.locals[item][0]

    def __iter__(self):
        """method from the `dict` interface returning an iterator on
        `self.keys()`
        """
        return iter(self.keys())

    def keys(self):
        """method from the `dict` interface returning a tuple containing
        locally defined names
        """
        return self.locals.keys()

    def values(self):
        """method from the `dict` interface returning a tuple containing
        locally defined nodes which are instance of `Function` or `Class`
        """
        return [self[key] for key in self.keys()]

    def items(self):
        """method from the `dict` interface returning a list of tuple
        containing each locally defined name with its associated node,
        which is an instance of `Function` or `Class`
        """
        return zip(self.keys(), self.values())

    def has_key(self, name):
        """method from the `dict` interface returning True if the given
        name is defined in the locals dictionary
        """
        return self.locals.has_key(name)

    __contains__ = has_key


# Module  #####################################################################

class Module(LocalsDictNodeNG):
    _astng_fields = ('body',)

    fromlineno = 0
    lineno = 0

    # attributes below are set by the builder module or by raw factories

    # the file from which as been extracted the astng representation. It may
    # be None if the representation has been built from a built-in module
    file = None
    # the module name
    name = None
    # boolean for astng built from source (i.e. ast)
    pure_python = None
    # boolean for package module
    package = None
    # dictionary of globals with name as key and node defining the global
    # as value
    globals = None

    # names of python special attributes (handled by getattr impl.)
    special_attributes = set(('__name__', '__doc__', '__file__', '__path__',
                              '__dict__'))
    # names of module attributes available through the global scope
    scope_attrs = set(('__name__', '__doc__', '__file__', '__path__'))

    def __init__(self, name, doc, pure_python=True):
        self.name = name
        self.doc = doc
        self.pure_python = pure_python
        self.locals = self.globals = {}
        self.body = []

    # Module is not a Statement node but needs the replace method (see StmtMixIn)
    def replace(self, child, newchild):
        sequence = self.child_sequence(child)
        newchild.parent = self
        child.parent = None
        sequence[sequence.index(child)] = newchild

    def block_range(self, lineno):
        """return block line numbers.

        start from the beginning whatever the given lineno
        """
        return self.fromlineno, self.tolineno

    def scope_lookup(self, node, name, offset=0):
        if name in self.scope_attrs and not name in self.locals:
            try:
                return self, self.getattr(name)
            except NotFoundError:
                return self, ()
        return self._scope_lookup(node, name, offset)

    def pytype(self):
        return '__builtin__.module'

    def display_type(self):
        return 'Module'

    def getattr(self, name, context=None):
        if not name in self.special_attributes:
            try:
                return self.locals[name]
            except KeyError:
                pass
        else:
            if name == '__file__':
                return [cf(self.file)] + self.locals.get(name, [])
            if name == '__path__':
                if self.package:
                    return [List()] + self.locals.get(name, [])
            return std_special_attributes(self, name)
        if self.package:
            try:
                return [self.import_module(name, relative_only=True)]
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                pass
        raise NotFoundError(name)
    getattr = remove_nodes(getattr, DelName)

    def igetattr(self, name, context=None):
        """inferred getattr"""
        # set lookup name since this is necessary to infer on import nodes for
        # instance
        context = copy_context(context)
        context.lookupname = name
        try:
            return _infer_stmts(self.getattr(name, context), context, frame=self)
        except NotFoundError:
            raise InferenceError(name)

    def fully_defined(self):
        """return True if this module has been built from a .py file
        and so contains a complete representation including the code
        """
        return self.file is not None and self.file.endswith('.py')

    def statement(self):
        """return the first parent node marked as statement node
        consider a module as a statement...
        """
        return self

    def previous_sibling(self):
        """module has no sibling"""
        return

    def next_sibling(self):
        """module has no sibling"""
        return

    def absolute_import_activated(self):
        for stmt in self.locals.get('absolute_import', ()):
            if isinstance(stmt, From) and stmt.modname == '__future__':
                return True
        return False

    def import_module(self, modname, relative_only=False, level=None):
        """import the given module considering self as context"""
        try:
            absmodname = self.absolute_modname(modname, level)
            return MANAGER.astng_from_module_name(absmodname)
        except ASTNGBuildingException:
            # we only want to import a sub module or package of this module,
            # skip here
            if relative_only:
                raise
        module = MANAGER.astng_from_module_name(modname)
        return module

    def absolute_modname(self, modname, level):
        if self.absolute_import_activated() and not level:
            return modname
        if level:
            parts = self.name.split('.')
            if self.package:
                parts.append('__init__')
            package_name = '.'.join(parts[:-level])
        elif self.package:
            package_name = self.name
        else:
            package_name = '.'.join(self.name.split('.')[:-1])
        if package_name:
            return '%s.%s' % (package_name, modname)
        return modname

    def wildcard_import_names(self):
        """return the list of imported names when this module is 'wildcard
        imported'

        It doesn't include the '__builtins__' name which is added by the
        current CPython implementation of wildcard imports.
        """
        # take advantage of a living module if it exists
        try:
            living = sys.modules[self.name]
        except KeyError:
            pass
        else:
            try:
                return living.__all__
            except AttributeError:
                return [name for name in living.__dict__.keys()
                        if not name.startswith('_')]
        # else lookup the astng
        #
        # We separate the different steps of lookup in try/excepts
        # to avoid catching too many Exceptions
        # However, we can not analyse dynamically constructed __all__
        try:
            all = self['__all__']
        except KeyError:
            return [name for name in self.keys() if not name.startswith('_')]
        try:
            explicit = all.assigned_stmts().next()
        except InferenceError:
            return [name for name in self.keys() if not name.startswith('_')]
        except AttributeError:
            # not an assignment node
            # XXX infer?
            return [name for name in self.keys() if not name.startswith('_')]
        try:
            # should be a Tuple/List of constant string / 1 string not allowed
            return [const.value for const in explicit.elts]
        except AttributeError:
            return [name for name in self.keys() if not name.startswith('_')]


class GenExpr(LocalsDictNodeNG):
    _astng_fields = ('elt', 'generators')

    def __init__(self):
        self.locals = {}
        self.elt = None
        self.generators = []

    def frame(self):
        return self.parent.frame()
GenExpr.scope_lookup = LocalsDictNodeNG._scope_lookup


# Function  ###################################################################


class Lambda(LocalsDictNodeNG, FilterStmtsMixin):
    _astng_fields = ('args', 'body',)

    # function's type, 'function' | 'method' | 'staticmethod' | 'classmethod'
    type = 'function'

    def __init__(self):
        self.locals = {}
        self.args = []
        self.body = []

    def pytype(self):
        if 'method' in self.type:
            return '__builtin__.instancemethod'
        return '__builtin__.function'

    def display_type(self):
        if 'method' in self.type:
            return 'Method'
        return 'Function'

    def callable(self):
        return True

    def argnames(self):
        """return a list of argument names"""
        if self.args.args: # maybe None with builtin functions
            names = _rec_get_names(self.args.args)
        else:
            names = []
        if self.args.vararg:
            names.append(self.args.vararg)
        if self.args.kwarg:
            names.append(self.args.kwarg)
        return names

    def infer_call_result(self, caller, context=None):
        """infer what a function is returning when called"""
        return self.body.infer(context)

    def scope_lookup(self, node, name, offset=0):
        if node in self.args.defaults:
            frame = self.parent.frame()
            # line offset to avoid that def func(f=func) resolve the default
            # value to the defined function
            offset = -1
        else:
            # check this is not used in function decorators
            frame = self
        return frame._scope_lookup(node, name, offset)

class Function(StmtMixIn, Lambda):
    _astng_fields = ('decorators', 'args', 'body')

    special_attributes = set(('__name__', '__doc__', '__dict__'))
    # attributes below are set by the builder module or by raw factories

    blockstart_tolineno = None

    def __init__(self, name, doc):
        self.locals = {}
        self.args = []
        self.body = []
        self.decorators = None
        self.name = name
        self.doc = doc

    def set_line_info(self, lastchild):
        self.fromlineno = self.lineno
        # lineno is the line number of the first decorator, we want the def statement lineno
        if self.decorators is not None:
            self.fromlineno += len(self.decorators.nodes)
        self.tolineno = lastchild.tolineno
        self.blockstart_tolineno = self.args.tolineno

    def block_range(self, lineno):
        """return block line numbers.

        start from the "def" position whatever the given lineno
        """
        return self.fromlineno, self.tolineno

    def getattr(self, name, context=None):
        """this method doesn't look in the instance_attrs dictionary since it's
        done by an Instance proxy at inference time.
        """
        if name == '__module__':
            return [cf(self.root().qname())]
        return std_special_attributes(self, name, False)

    def is_method(self):
        """return true if the function node should be considered as a method"""
        # check we are defined in a Class, because this is usually expected
        # (e.g. pylint...) when is_method() return True
        return self.type != 'function' and isinstance(self.parent.frame(), Class)

    @cached
    def decoratornames(self):
        """return a list of decorator qualified names"""
        result = set()
        decoratornodes = []
        if self.decorators is not None:
            decoratornodes += self.decorators.nodes
        decoratornodes += getattr(self, 'extra_decorators', [])
        for decnode in decoratornodes:
            for infnode in decnode.infer():
                result.add(infnode.qname())
        return result


    def is_bound(self):
        """return true if the function is bound to an Instance or a class"""
        return self.type == 'classmethod'

    def is_abstract(self, pass_is_abstract=True):
        """return true if the method is abstract
        It's considered as abstract if the only statement is a raise of
        NotImplementError, or, if pass_is_abstract, a pass statement
        """
        for child_node in self.body:
            if isinstance(child_node, Raise) and child_node.type:
                try:
                    name = child_node.type.nodes_of_class(Name).next()
                    if name.name == 'NotImplementedError':
                        return True
                except StopIteration:
                    pass
            if pass_is_abstract and isinstance(child_node, Pass):
                return True
            return False
        # empty function is the same as function with a single "pass" statement
        if pass_is_abstract:
            return True

    def is_generator(self):
        """return true if this is a generator function"""
        # XXX should be flagged, not computed
        try:
            return self.nodes_of_class(Yield, skip_klass=Function).next()
        except StopIteration:
            return False

    def infer_call_result(self, caller, context=None):
        """infer what a function is returning when called"""
        if self.is_generator():
            yield Generator(self)
            return
        returns = self.nodes_of_class(Return, skip_klass=Function)
        for returnnode in returns:
            if returnnode.value is None:
                yield None
            else:
                try:
                    for infered in returnnode.value.infer(context):
                        yield infered
                except InferenceError:
                    yield YES



def _rec_get_names(args, names=None):
    """return a list of all argument names"""
    if names is None:
        names = []
    for arg in args:
        if isinstance(arg, Tuple):
            _rec_get_names(arg.elts, names)
        else:
            names.append(arg.name)
    return names


def _format_args(args, defaults=None):
    values = []
    if args is None:
        return ''
    if defaults is not None:
        default_offset = len(args) - len(defaults)
    for i, arg in enumerate(args):
        if isinstance(arg, Tuple):
            values.append('(%s)' % _format_args(arg.elts))
        else:
            values.append(arg.name)
            if defaults is not None and i >= default_offset:
                values[-1] += '=' + defaults[i-default_offset].as_string()
    return ', '.join(values)


# Class ######################################################################

def _class_type(klass):
    """return a Class node type to differ metaclass, interface and exception
    from 'regular' classes
    """
    if klass._type is not None:
        return klass._type
    if klass.name == 'type':
        klass._type = 'metaclass'
    elif klass.name.endswith('Interface'):
        klass._type = 'interface'
    elif klass.name.endswith('Exception'):
        klass._type = 'exception'
    else:
        for base in klass.ancestors(recurs=False):
            if base.type != 'class':
                klass._type = base.type
                break
    if klass._type is None:
        klass._type = 'class'
    return klass._type

def _iface_hdlr(iface_node):
    """a handler function used by interfaces to handle suspicious
    interface nodes
    """
    return True


class Class(StmtMixIn, LocalsDictNodeNG, FilterStmtsMixin):

    # some of the attributes below are set by the builder module or
    # by a raw factories

    # a dictionary of class instances attributes
    _astng_fields = ('bases', 'body',) # name

    instance_attrs = None
    special_attributes = set(('__name__', '__doc__', '__dict__', '__module__',
                              '__bases__', '__mro__'))

    blockstart_tolineno = None

    _type = None
    type = property(_class_type,
                    doc="class'type, possible values are 'class' | "
                    "'metaclass' | 'interface' | 'exception'")

    def __init__(self, name, doc):
        self.instance_attrs = {}
        self.locals = {}
        self.bases = []
        self.body = []
        self.name = name
        self.doc = doc

    def _newstyle_impl(self, context=None):
        if context is None:
            context = InferenceContext()
        if self._newstyle is not None:
            return self._newstyle
        for base in self.ancestors(recurs=False, context=context):
            if base._newstyle_impl(context):
                self._newstyle = True
                break
        if self._newstyle is None:
            self._newstyle = False
        return self._newstyle

    _newstyle = None
    newstyle = property(_newstyle_impl,
                        doc="boolean indicating if it's a new style class"
                        "or not")

    def set_line_info(self, lastchild):
        self.fromlineno = self.lineno
        self.blockstart_tolineno = self.bases and self.bases[-1].tolineno or self.fromlineno
        if lastchild is not None:
            self.tolineno = lastchild.tolineno
        # else this is a class with only a docstring, then tolineno is (should be) already ok

    def block_range(self, lineno):
        """return block line numbers.

        start from the "class" position whatever the given lineno
        """
        return self.fromlineno, self.tolineno

    def pytype(self):
        if self.newstyle:
            return '__builtin__.type'
        return '__builtin__.classobj'

    def display_type(self):
        return 'Class'

    def callable(self):
        return True

    def infer_call_result(self, caller, context=None):
        """infer what a class is returning when called"""
        yield Instance(self)

    def scope_lookup(self, node, name, offset=0):
        if node in self.bases:
            frame = self.parent.frame()
            # line offset to avoid that class A(A) resolve the ancestor to
            # the defined class
            offset = -1
        else:
            frame = self
        return frame._scope_lookup(node, name, offset)

    # list of parent class as a list of string (i.e. names as they appear
    # in the class definition) XXX bw compat
    def basenames(self):
        return [as_string(bnode) for bnode in self.bases]
    basenames = property(basenames)

    def ancestors(self, recurs=True, context=None):
        """return an iterator on the node base classes in a prefixed
        depth first order

        :param recurs:
          boolean indicating if it should recurse or return direct
          ancestors only
        """
        # FIXME: should be possible to choose the resolution order
        # XXX inference make infinite loops possible here (see BaseTransformer
        # manipulation in the builder module for instance !)
        if context is None:
            context = InferenceContext()
        for stmt in self.bases:
            try:
                for baseobj in stmt.infer(context):
                    if not isinstance(baseobj, Class):
                        # duh ?
                        continue
                    if baseobj is self:
                        continue # cf xxx above
                    yield baseobj
                    if recurs:
                        for grandpa in baseobj.ancestors(True, context):
                            if grandpa is self:
                                continue # cf xxx above
                            yield grandpa
            except InferenceError:
                # XXX log error ?
                continue

    def local_attr_ancestors(self, name, context=None):
        """return an iterator on astng representation of parent classes
        which have <name> defined in their locals
        """
        for astng in self.ancestors(context=context):
            if astng.locals.has_key(name):
                yield astng

    def instance_attr_ancestors(self, name, context=None):
        """return an iterator on astng representation of parent classes
        which have <name> defined in their instance attribute dictionary
        """
        for astng in self.ancestors(context=context):
            if astng.instance_attrs.has_key(name):
                yield astng

    def has_base(self, node):
        return node in self.bases

    def local_attr(self, name, context=None):
        """return the list of assign node associated to name in this class
        locals or in its parents

        :raises `NotFoundError`:
          if no attribute with this name has been find in this class or
          its parent classes
        """
        try:
            return self.locals[name]
        except KeyError:
            # get if from the first parent implementing it if any
            for class_node in self.local_attr_ancestors(name, context):
                return class_node.locals[name]
        raise NotFoundError(name)
    local_attr = remove_nodes(local_attr, DelAttr)

    def instance_attr(self, name, context=None):
        """return the astng nodes associated to name in this class instance
        attributes dictionary and in its parents

        :raises `NotFoundError`:
          if no attribute with this name has been find in this class or
          its parent classes
        """
        values = self.instance_attrs.get(name, [])
        # get if from the first parent implementing it if any
        for class_node in self.instance_attr_ancestors(name, context):
            values += class_node.instance_attrs[name]
        if not values:
            raise NotFoundError(name)
        return values
    instance_attr = remove_nodes(instance_attr, DelAttr)

    def instanciate_class(self):
        """return Instance of Class node, else return self"""
        return Instance(self)

    def getattr(self, name, context=None):
        """this method doesn't look in the instance_attrs dictionary since it's
        done by an Instance proxy at inference time.

        It may return a YES object if the attribute has not been actually
        found but a __getattr__ or __getattribute__ method is defined
        """
        values = self.locals.get(name, [])
        if name in self.special_attributes:
            if name == '__module__':
                return [cf(self.root().qname())] + values
            if name == '__bases__':
                return [cf(tuple(self.ancestors(recurs=False, context=context)))] + values
            # XXX need proper meta class handling + MRO implementation
            if name == '__mro__' and self.newstyle:
                # XXX mro is read-only but that's not our job to detect that
                return [cf(tuple(self.ancestors(recurs=True, context=context)))] + values
            return std_special_attributes(self, name)
        # don't modify the list in self.locals!
        values = list(values)
        for classnode in self.ancestors(recurs=False, context=context):
            try:
                values += classnode.getattr(name, context)
            except NotFoundError:
                continue
        if not values:
            raise NotFoundError(name)
        return values

    def igetattr(self, name, context=None):
        """inferred getattr, need special treatment in class to handle
        descriptors
        """
        # set lookup name since this is necessary to infer on import nodes for
        # instance
        context = copy_context(context)
        context.lookupname = name
        try:
            for infered in _infer_stmts(self.getattr(name, context), context,
                                        frame=self):
                # yield YES object instead of descriptors when necessary
                if not isinstance(infered, Const) and isinstance(infered, Instance):
                    try:
                        infered._proxied.getattr('__get__', context)
                    except NotFoundError:
                        yield infered
                    else:
                        yield YES
                else:
                    yield function_to_method(infered, self)
        except NotFoundError:
            if not name.startswith('__') and self.has_dynamic_getattr(context):
                # class handle some dynamic attributes, return a YES object
                yield YES
            else:
                raise InferenceError(name)

    def has_dynamic_getattr(self, context=None):
        """return True if the class has a custom __getattr__ or
        __getattribute__ method
        """
        # need to explicitly handle optparse.Values (setattr is not detected)
        if self.name == 'Values' and self.root().name == 'optparse':
            return True
        try:
            self.getattr('__getattr__', context)
            return True
        except NotFoundError:
            #if self.newstyle: XXX cause an infinite recursion error
            try:
                getattribute = self.getattr('__getattribute__', context)[0]
                if getattribute.root().name != '__builtin__':
                    # class has a custom __getattribute__ defined
                    return True
            except NotFoundError:
                pass
        return False

    def methods(self):
        """return an iterator on all methods defined in the class and
        its ancestors
        """
        done = {}
        for astng in chain(iter((self,)), self.ancestors()):
            for meth in astng.mymethods():
                if done.has_key(meth.name):
                    continue
                done[meth.name] = None
                yield meth

    def mymethods(self):
        """return an iterator on all methods defined in the class"""
        for member in self.values():
            if isinstance(member, Function):
                yield member

    def interfaces(self, herited=True, handler_func=_iface_hdlr):
        """return an iterator on interfaces implemented by the given
        class node
        """
        # FIXME: what if __implements__ = (MyIFace, MyParent.__implements__)...
        try:
            implements = Instance(self).getattr('__implements__')[0]
        except NotFoundError:
            return
        if not herited and not implements.frame() is self:
            return
        found = set()
        for iface in unpack_infer(implements):
            if iface is YES:
                continue
            if not iface in found and handler_func(iface):
                found.add(iface)
                yield iface
        if not found:
            raise InferenceError()


