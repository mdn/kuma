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
"""classes checker for Python code
"""
from __future__ import generators

from logilab import astng
from logilab.astng import YES, Instance, are_exclusive

from pylint.interfaces import IASTNGChecker
from pylint.checkers import BaseChecker
from pylint.checkers.utils import PYMETHODS, overrides_a_method

def class_is_abstract(node):
    """return true if the given class node should be considered as an abstract
    class
    """
    for method in node.methods():
        if method.parent.frame() is node:
            if method.is_abstract(pass_is_abstract=False):
                return True
    return False


MSGS = {
    'F0202': ('Unable to check methods signature (%s / %s)',
              'Used when PyLint has been unable to check methods signature \
              compatibility for an unexpected reason. Please report this kind \
              if you don\'t make sense of it.'),

    'E0202': ('An attribute inherited from %s hide this method',
              'Used when a class defines a method which is hidden by an \
              instance attribute from an ancestor class.'),
    'E0203': ('Access to member %r before its definition line %s',
              'Used when an instance member is accessed before it\'s actually\
              assigned.'),
    'W0201': ('Attribute %r defined outside __init__',
              'Used when an instance attribute is defined outside the __init__\
              method.'),

    'W0212': ('Access to a protected member %s of a client class', # E0214
              'Used when a protected member (i.e. class member with a name \
              beginning with an underscore) is access outside the class or a \
              descendant of the class where it\'s defined.'),

    'E0211': ('Method has no argument',
              'Used when a method which should have the bound instance as \
              first argument has no argument defined.'),
    'E0213': ('Method should have "self" as first argument',
              'Used when a method has an attribute different the "self" as\
              first argument. This is considered as an error since this is\
              a so common convention that you shouldn\'t break it!'),
    'C0202': ('Class method should have "cls" as first argument', # E0212
              'Used when a class method has an attribute different than "cls"\
              as first argument, to easily differentiate them from regular \
              instance methods.'),
    'C0203': ('Metaclass method should have "mcs" as first argument', # E0214
              'Used when a metaclass method has an attribute different the \
              "mcs" as first argument.'),

    'W0211': ('Static method with %r as first argument',
              'Used when a static method has "self" or "cls" as first argument.'
              ),
    'R0201': ('Method could be a function',
              'Used when a method doesn\'t use its bound instance, and so could\
              be written as a function.'
              ),

    'E0221': ('Interface resolved to %s is not a class',
              'Used when a class claims to implement an interface which is not \
              a class.'),
    'E0222': ('Missing method %r from %s interface' ,
              'Used when a method declared in an interface is missing from a \
              class implementing this interface'),
    'W0221': ('Arguments number differs from %s method',
              'Used when a method has a different number of arguments than in \
              the implemented interface or in an overridden method.'),
    'W0222': ('Signature differs from %s method',
              'Used when a method signature is different than in the \
              implemented interface or in an overridden method.'),
    'W0223': ('Method %r is abstract in class %r but is not overridden',
              'Used when an abstract method (i.e. raise NotImplementedError) is \
              not overridden in concrete class.'
              ),
    'F0220': ('failed to resolve interfaces implemented by %s (%s)', # W0224
              'Used when a PyLint as failed to find interfaces implemented by \
               a class'),


    'W0231': ('__init__ method from base class %r is not called',
              'Used when an ancestor class method has an __init__ method \
              which is not called by a derived class.'),
    'W0232': ('Class has no __init__ method',
              'Used when a class has no __init__ method, neither its parent \
              classes.'),
    'W0233': ('__init__ method from a non direct base class %r is called',
              'Used when an __init__ method is called on a class which is not \
              in the direct ancestors for the analysed class.'),

    }


class ClassChecker(BaseChecker):
    """checks for :
    * methods without self as first argument
    * overridden methods signature
    * access only to existent members via self
    * attributes not defined in the __init__ method
    * supported interfaces implementation
    * unreachable code
    """

    __implements__ = (IASTNGChecker,)

    # configuration section name
    name = 'classes'
    # messages
    msgs = MSGS
    priority = -2
    # configuration options
    options = (('ignore-iface-methods',
                {'default' : (#zope interface
        'isImplementedBy', 'deferred', 'extends', 'names',
        'namesAndDescriptions', 'queryDescriptionFor',  'getBases',
        'getDescriptionFor', 'getDoc', 'getName', 'getTaggedValue',
        'getTaggedValueTags', 'isEqualOrExtendedBy', 'setTaggedValue',
        'isImplementedByInstancesOf',
        # twisted
        'adaptWith',
        # logilab.common interface
        'is_implemented_by'),
                 'type' : 'csv',
                 'metavar' : '<method names>',
                 'help' : 'List of interface methods to ignore, \
separated by a comma. This is used for instance to not check methods defines \
in Zope\'s Interface base class.'}
                ),

               ('defining-attr-methods',
                {'default' : ('__init__', '__new__', 'setUp'),
                 'type' : 'csv',
                 'metavar' : '<method names>',
                 'help' : 'List of method names used to declare (i.e. assign) \
instance attributes.'}
                ),

               )

    def __init__(self, linter=None):
        BaseChecker.__init__(self, linter)
        self._accessed = []
        self._first_attrs = []
        self._meth_could_be_func = None

    def visit_class(self, node):
        """init visit variable _accessed and check interfaces
        """
        self._accessed.append({})
        self._check_bases_classes(node)
        self._check_interfaces(node)
        # if not an interface, exception, metaclass
        if node.type == 'class':
            try:
                node.local_attr('__init__')
            except astng.NotFoundError:
                self.add_message('W0232', args=node, node=node)

    def leave_class(self, cnode):
        """close a class node:
        check that instance attributes are defined in __init__ and check
        access to existent members
        """
        # checks attributes are defined in an allowed method such as __init__
        defining_methods = self.config.defining_attr_methods
        for attr, nodes in cnode.instance_attrs.items():
            nodes = [n for n in nodes if not
                    isinstance(n.statement(), (astng.Delete, astng.AugAssign))]
            if not nodes:
                continue # error detected by typechecking
            node = nodes[0] # XXX
            frame = node.frame()
            if frame.name not in defining_methods:
                # check attribute is defined in a parent's __init__
                for parent in cnode.instance_attr_ancestors(attr):
                    frame = parent.instance_attrs[attr][0].frame() # XXX
                    if frame.name in defining_methods:
                        # we're done :)
                        break
                else:
                    # check attribute is defined as a class attribute
                    try:
                        cnode.local_attr(attr)
                    except astng.NotFoundError:
                        self.add_message('W0201', args=attr, node=node)
        # check access to existent members on non metaclass classes
        accessed = self._accessed.pop()
        if cnode.type != 'metaclass':
            self._check_accessed_members(cnode, accessed)

    def visit_function(self, node):
        """check method arguments, overriding"""
        # ignore actual functions
        if not node.is_method():
            return
        klass = node.parent.frame()
        self._meth_could_be_func = True
        # check first argument is self if this is actually a method
        self._check_first_arg_for_type(node, klass.type == 'metaclass')
        if node.name == '__init__':
            self._check_init(node)
            return
        # check signature if the method overloads inherited method
        for overridden in klass.local_attr_ancestors(node.name):
            # get astng for the searched method
            try:
                meth_node = overridden[node.name]
            except KeyError:
                # we have found the method but it's not in the local
                # dictionary.
                # This may happen with astng build from living objects
                continue
            if not isinstance(meth_node, astng.Function):
                continue
            self._check_signature(node, meth_node, 'overridden')
            break
        # check if the method overload an attribute
        try:
            overridden = klass.instance_attr(node.name)[0] # XXX
            # we may be unable to get owner class if this is a monkey
            # patched method
            while overridden.parent and not isinstance(overridden, astng.Class):
                overridden = overridden.parent.frame()
            self.add_message('E0202', args=overridden.name, node=node)
        except astng.NotFoundError:
            pass

    def leave_function(self, node):
        """on method node, check if this method couldn't be a function

        ignore class, static and abstract methods, initializer,
        methods overridden from a parent class and any
        kind of method defined in an interface for this warning
        """
        if node.is_method():
            if node.args.args is not None:
                self._first_attrs.pop()
            class_node = node.parent.frame()
            if (self._meth_could_be_func and node.type == 'method'
                and not node.name in PYMETHODS
                and not (node.is_abstract() or
                         overrides_a_method(class_node, node.name))
                and class_node.type != 'interface'):
                self.add_message('R0201', node=node)

    def visit_getattr(self, node):
        """check if the getattr is an access to a class member
        if so, register it. Also check for access to protected
        class member from outside its class (but ignore __special__
        methods)
        """
        attrname = node.attrname
        if self._first_attrs and isinstance(node.expr, astng.Name) and \
               node.expr.name == self._first_attrs[-1]:
            self._accessed[-1].setdefault(attrname, []).append(node)
        elif attrname[0] == '_' and not attrname == '_' and not (
             attrname.startswith('__') and attrname.endswith('__')):
            # XXX move this in a reusable function
            klass = node.frame()
            while klass is not None and not isinstance(klass, astng.Class):
                if klass.parent is None:
                    klass = None
                else:
                    klass = klass.parent.frame()
            # XXX infer to be more safe and less dirty ??
            # in classes, check we are not getting a parent method
            # through the class object or through super
            callee = node.expr.as_string()
            if klass is None or not (callee == klass.name or
                callee in klass.basenames
                or (isinstance(node.expr, astng.CallFunc)
                    and isinstance(node.expr.func, astng.Name)
                    and node.expr.func.name == 'super')):
                self.add_message('W0212', node=node, args=attrname)


    def visit_name(self, node):
        """check if the name handle an access to a class member
        if so, register it
        """
        if self._first_attrs and (node.name == self._first_attrs[-1] or
                                  not self._first_attrs[-1]):
            self._meth_could_be_func = False

    def _check_accessed_members(self, node, accessed):
        """check that accessed members are defined"""
        # XXX refactor, probably much simpler now that E0201 is in type checker
        for attr, nodes in accessed.items():
            # deactivate "except doesn't do anything", that's expected
            # pylint: disable-msg=W0704
            # is it a class attribute ?
            try:
                node.local_attr(attr)
                # yes, stop here
                continue
            except astng.NotFoundError:
                pass
            # is it an instance attribute of a parent class ?
            try:
                node.instance_attr_ancestors(attr).next()
                # yes, stop here
                continue
            except StopIteration:
                pass
            # is it an instance attribute ?
            try:
                defstmts = node.instance_attr(attr)
            except astng.NotFoundError:
                pass
            else:
                if len(defstmts) == 1:
                    defstmt = defstmts[0]
                    # check that if the node is accessed in the same method as
                    # it's defined, it's accessed after the initial assignment
                    frame = defstmt.frame()
                    lno = defstmt.fromlineno
                    for _node in nodes:
                        if _node.frame() is frame and _node.fromlineno < lno \
                           and not are_exclusive(_node.statement(), defstmt, ('AttributeError', 'Exception', 'BaseException')):
                            self.add_message('E0203', node=_node,
                                             args=(attr, lno))

    def _check_first_arg_for_type(self, node, metaclass=0):
        """check the name of first argument, expect:

        * 'self' for a regular method
        * 'cls' for a class method
        * 'mcs' for a metaclass
        * not one of the above for a static method
        """
        # don't care about functions with unknown argument (builtins)
        if node.args.args is None:
            return
        first_arg = node.args.args and node.argnames()[0]
        self._first_attrs.append(first_arg)
        first = self._first_attrs[-1]
        # static method
        if node.type == 'staticmethod':
            if first_arg in ('self', 'cls', 'mcs'):
                self.add_message('W0211', args=first, node=node)
            self._first_attrs[-1] = None
        # class / regular method with no args
        elif not node.args.args:
            self.add_message('E0211', node=node)
        # metaclass method
        elif metaclass:
            if first != 'mcs':
                self.add_message('C0203', node=node)
        # class method
        elif node.type == 'classmethod':
            if first != 'cls':
                self.add_message('C0202', node=node)
        # regular method without self as argument
        elif first != 'self':
            self.add_message('E0213', node=node)

    def _check_bases_classes(self, node):
        """check that the given class node implements abstract methods from
        base classes
        """
        # check if this class abstract
        if class_is_abstract(node):
            return
        for method in node.methods():
            owner = method.parent.frame()
            if owner is node:
                continue
            # owner is not this class, it must be a parent class
            # check that the ancestor's method is not abstract
            if method.is_abstract(pass_is_abstract=False):
                self.add_message('W0223', node=node,
                                 args=(method.name, owner.name))

    def _check_interfaces(self, node):
        """check that the given class node really implements declared
        interfaces
        """
        e0221_hack = [False]
        def iface_handler(obj):
            """filter interface objects, it should be classes"""
            if not isinstance(obj, astng.Class):
                e0221_hack[0] = True
                self.add_message('E0221', node=node,
                                 args=(obj.as_string(),))
                return False
            return True
        ignore_iface_methods = self.config.ignore_iface_methods
        try:
            for iface in node.interfaces(handler_func=iface_handler):
                for imethod in iface.methods():
                    name = imethod.name
                    if name.startswith('_') or name in ignore_iface_methods:
                        # don't check method beginning with an underscore,
                        # usually belonging to the interface implementation
                        continue
                    # get class method astng
                    try:
                        method = node_method(node, name)
                    except astng.NotFoundError:
                        self.add_message('E0222', args=(name, iface.name),
                                         node=node)
                        continue
                    # ignore inherited methods
                    if method.parent.frame() is not node:
                        continue
                    # check signature
                    self._check_signature(method, imethod,
                                         '%s interface' % iface.name)
        except astng.InferenceError:
            if e0221_hack[0]:
                return
            implements = Instance(node).getattr('__implements__')[0]
            assignment = implements.parent
            assert isinstance(assignment, astng.Assign)
            # assignment.expr can be a Name or a Tuple or whatever.
            # Use as_string() for the message
            # FIXME: in case of multiple interfaces, find which one could not
            #        be resolved
            self.add_message('F0220', node=implements,
                             args=(node.name, assignment.value.as_string()))

    def _check_init(self, node):
        """check that the __init__ method call super or ancestors'__init__
        method
        """
        klass_node = node.parent.frame()
        to_call = _ancestors_to_call(klass_node)
        not_called_yet = dict(to_call)
        for stmt in node.nodes_of_class(astng.CallFunc):
            expr = stmt.func
            if not isinstance(expr, astng.Getattr) \
                   or expr.attrname != '__init__':
                continue
            # skip the test if using super
            if isinstance(expr.expr, astng.CallFunc) and \
               isinstance(expr.expr.func, astng.Name) and \
               expr.expr.func.name == 'super':
                return
            try:
                klass = expr.expr.infer().next()
                if klass is YES:
                    continue
                try:
                    del not_called_yet[klass]
                except KeyError:
                    if klass not in to_call:
                        self.add_message('W0233', node=expr, args=klass.name)
            except astng.InferenceError:
                continue
        for klass in not_called_yet.keys():
            if klass.name == 'object':
                continue
            self.add_message('W0231', args=klass.name, node=node)

    def _check_signature(self, method1, refmethod, class_type):
        """check that the signature of the two given methods match

        class_type is in 'class', 'interface'
        """
        if not (isinstance(method1, astng.Function)
                and isinstance(refmethod, astng.Function)):
            self.add_message('F0202', args=(method1, refmethod), node=method1)
            return
        # don't care about functions with unknown argument (builtins)
        if method1.args.args is None or refmethod.args.args is None:
            return
        if len(method1.args.args) != len(refmethod.args.args):
            self.add_message('W0221', args=class_type, node=method1)
        elif len(method1.args.defaults) < len(refmethod.args.defaults):
            self.add_message('W0222', args=class_type, node=method1)


def _ancestors_to_call(klass_node, method='__init__'):
    """return a dictionary where keys are the list of base classes providing
    the queried method, and so that should/may be called from the method node
    """
    to_call = {}
    for base_node in klass_node.ancestors(recurs=False):
        try:
            base_node.local_attr(method)
            to_call[base_node] = 1
        except astng.NotFoundError:
            continue
    return to_call


def node_method(node, method_name):
    """get astng for <method_name> on the given class node, ensuring it
    is a Function node
    """
    for n in node.local_attr(method_name):
        if isinstance(n, astng.Function):
            return n
    raise astng.NotFoundError(method_name)

def register(linter):
    """required method to auto register this checker """
    linter.register_checker(ClassChecker(linter))
