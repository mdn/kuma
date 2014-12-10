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
"""tests for specific behaviour of astng scoped nodes (i.e. module, class and
function)
"""

import sys
from os.path import join, abspath

from logilab.common.testlib import TestCase, unittest_main
from logilab.common.compat import sorted

from logilab.astng import builder, nodes, scoped_nodes, \
     InferenceError, NotFoundError
from logilab.astng.bases import Instance, BoundMethod, UnboundMethod

abuilder = builder.ASTNGBuilder()
MODULE = abuilder.file_build('data/module.py', 'data.module')
MODULE2 = abuilder.file_build('data/module2.py', 'data.module2')
NONREGR = abuilder.file_build('data/nonregr.py', 'data.nonregr')
PACK = abuilder.file_build('data/__init__.py', 'data')

def _test_dict_interface(self, node, test_attr):
    self.assert_(node[test_attr] is node[test_attr])
    self.assert_(test_attr in node)
    node.keys()
    node.values()
    node.items()
    iter(node)


class ModuleNodeTC(TestCase):

    def test_special_attributes(self):
        self.assertEquals(len(MODULE.getattr('__name__')), 1)
        self.assertIsInstance(MODULE.getattr('__name__')[0], nodes.Const)
        self.assertEquals(MODULE.getattr('__name__')[0].value, 'data.module')
        self.assertEquals(len(MODULE.getattr('__doc__')), 1)
        self.assertIsInstance(MODULE.getattr('__doc__')[0], nodes.Const)
        self.assertEquals(MODULE.getattr('__doc__')[0].value, 'test module for astng\n')
        self.assertEquals(len(MODULE.getattr('__file__')), 1)
        self.assertIsInstance(MODULE.getattr('__file__')[0], nodes.Const)
        self.assertEquals(MODULE.getattr('__file__')[0].value, abspath(join('data', 'module.py')))
        self.assertEquals(len(MODULE.getattr('__dict__')), 1)
        self.assertIsInstance(MODULE.getattr('__dict__')[0], nodes.Dict)
        self.assertRaises(NotFoundError, MODULE.getattr, '__path__')
        self.assertEquals(len(PACK.getattr('__path__')), 1)
        self.assertIsInstance(PACK.getattr('__path__')[0], nodes.List)

    def test_dict_interface(self):
        _test_dict_interface(self, MODULE, 'YO')

    def test_getattr(self):
        yo = MODULE.getattr('YO')[0]
        self.assertIsInstance(yo, nodes.Class)
        self.assertEquals(yo.name, 'YO')
        red = MODULE.igetattr('redirect').next()
        self.assertIsInstance(red, nodes.Function)
        self.assertEquals(red.name, 'nested_args')
        spawn = MODULE.igetattr('spawn').next()
        self.assertIsInstance(spawn, nodes.Class)
        self.assertEquals(spawn.name, 'Execute')
        # resolve packageredirection
        sys.path.insert(1, 'data')
        try:
            m = abuilder.file_build('data/appl/myConnection.py', 'appl.myConnection')
            cnx = m.igetattr('SSL1').next().igetattr('Connection').next()
            self.assertEquals(cnx.__class__, nodes.Class)
            self.assertEquals(cnx.name, 'Connection')
            self.assertEquals(cnx.root().name, 'SSL1.Connection1')
        finally:
            del sys.path[1]
        self.assertEquals(len(NONREGR.getattr('enumerate')), 2)
        # raise ResolveError
        self.assertRaises(InferenceError, MODULE.igetattr, 'YOAA')

    def test_wildard_import_names(self):
        m = abuilder.file_build('data/all.py', 'all')
        self.assertEquals(m.wildcard_import_names(), ['Aaa', '_bla', 'name'])
        m = abuilder.file_build('data/notall.py', 'notall')
        res = m.wildcard_import_names()
        res.sort()
        self.assertEquals(res, ['Aaa', 'func', 'name', 'other'])

    def test_module_getattr(self):
        data = '''
appli = application
appli += 2
del appli
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        # test del statement not returned by getattr
        self.assertEquals(len(astng.getattr('appli')), 2,
                          astng.getattr('appli'))


class FunctionNodeTC(TestCase):

    def test_special_attributes(self):
        func = MODULE2['make_class']
        self.assertEquals(len(func.getattr('__name__')), 1)
        self.assertIsInstance(func.getattr('__name__')[0], nodes.Const)
        self.assertEquals(func.getattr('__name__')[0].value, 'make_class')
        self.assertEquals(len(func.getattr('__doc__')), 1)
        self.assertIsInstance(func.getattr('__doc__')[0], nodes.Const)
        self.assertEquals(func.getattr('__doc__')[0].value, 'check base is correctly resolved to Concrete0')
        self.assertEquals(len(MODULE.getattr('__dict__')), 1)
        self.assertIsInstance(MODULE.getattr('__dict__')[0], nodes.Dict)

    def test_dict_interface(self):
        _test_dict_interface(self, MODULE['global_access'], 'local')

    def test_default_value(self):
        func = MODULE2['make_class']
        self.assertIsInstance(func.args.default_value('base'), nodes.Getattr)
        self.assertRaises(scoped_nodes.NoDefault, func.args.default_value, 'args')
        self.assertRaises(scoped_nodes.NoDefault, func.args.default_value, 'kwargs')
        self.assertRaises(scoped_nodes.NoDefault, func.args.default_value, 'any')
        #self.assertIsInstance(func.mularg_class('args'), nodes.Tuple)
        #self.assertIsInstance(func.mularg_class('kwargs'), nodes.Dict)
        #self.assertEquals(func.mularg_class('base'), None)

    def test_navigation(self):
        function = MODULE['global_access']
        self.assertEquals(function.statement(), function)
        l_sibling = function.previous_sibling()
        # check taking parent if child is not a stmt
        self.assertIsInstance(l_sibling, nodes.Assign)
        child = function.args.args[0]
        self.assert_(l_sibling is child.previous_sibling())
        r_sibling = function.next_sibling()
        self.assertIsInstance(r_sibling, nodes.Class)
        self.assertEquals(r_sibling.name, 'YO')
        self.assert_(r_sibling is child.next_sibling())
        last = r_sibling.next_sibling().next_sibling().next_sibling()
        self.assertIsInstance(last, nodes.Assign)
        self.assertEquals(last.next_sibling(), None)
        first = l_sibling.previous_sibling().previous_sibling().previous_sibling().previous_sibling().previous_sibling()
        self.assertEquals(first.previous_sibling(), None)

    def test_nested_args(self):
        func = MODULE['nested_args']
        #self.assertEquals(func.args.args, ['a', ('b', 'c', 'd')])
        local = func.keys()
        local.sort()
        self.assertEquals(local, ['a', 'b', 'c', 'd'])
        self.assertEquals(func.type, 'function')

    def test_format_args(self):
        func = MODULE2['make_class']
        self.assertEquals(func.args.format_args(), 'any, base=data.module.YO, *args, **kwargs')
        func = MODULE['nested_args']
        self.assertEquals(func.args.format_args(), 'a, (b, c, d)')

    def test_is_abstract(self):
        method = MODULE2['AbstractClass']['to_override']
        self.assert_(method.is_abstract(pass_is_abstract=False))
        self.failUnlessEqual(method.qname(), 'data.module2.AbstractClass.to_override')
        self.failUnlessEqual(method.pytype(), '__builtin__.instancemethod')
        method = MODULE2['AbstractClass']['return_something']
        self.assert_(not method.is_abstract(pass_is_abstract=False))
        # non regression : test raise "string" doesn't cause an exception in is_abstract
        func = MODULE2['raise_string']
        self.assert_(not func.is_abstract(pass_is_abstract=False))

##     def test_raises(self):
##         method = MODULE2['AbstractClass']['to_override']
##         self.assertEquals([str(term) for term in method.raises()],
##                           ["CallFunc(Name('NotImplementedError'), [], None, None)"] )

##     def test_returns(self):
##         method = MODULE2['AbstractClass']['return_something']
##         # use string comp since Node doesn't handle __cmp__
##         self.assertEquals([str(term) for term in method.returns()],
##                           ["Const('toto')", "Const(None)"])

    def test_lambda_pytype(self):
        data = '''
def f():
        g = lambda: None
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        g = list(astng['f'].ilookup('g'))[0]
        self.failUnlessEqual(g.pytype(), '__builtin__.function')

    def test_is_method(self):
        if sys.version_info < (2, 4):
            self.skip('this test require python >= 2.4')
        data = '''
class A:
    def meth1(self):
        return 1
    @classmethod
    def meth2(cls):
        return 2
    @staticmethod
    def meth3():
        return 3

def function():
    return 0

@staticmethod
def sfunction():
    return -1
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        self.failUnless(astng['A']['meth1'].is_method())
        self.failUnless(astng['A']['meth2'].is_method())
        self.failUnless(astng['A']['meth3'].is_method())
        self.failIf(astng['function'].is_method())
        self.failIf(astng['sfunction'].is_method())

    def test_argnames(self):
        code = 'def f(a, (b, c), *args, **kwargs): pass'
        astng = abuilder.string_build(code, __name__, __file__)
        self.assertEquals(astng['f'].argnames(), ['a', 'b', 'c', 'args', 'kwargs'])


class ClassNodeTC(TestCase):

    def test_dict_interface(self):
        _test_dict_interface(self, MODULE['YOUPI'], 'method')

    def test_cls_special_attributes_1(self):
        cls = MODULE['YO']
        self.assertEquals(len(cls.getattr('__bases__')), 1)
        self.assertEquals(len(cls.getattr('__name__')), 1)
        self.assertIsInstance(cls.getattr('__name__')[0], nodes.Const)
        self.assertEquals(cls.getattr('__name__')[0].value, 'YO')
        self.assertEquals(len(cls.getattr('__doc__')), 1)
        self.assertIsInstance(cls.getattr('__doc__')[0], nodes.Const)
        self.assertEquals(cls.getattr('__doc__')[0].value, 'hehe')
        self.assertEquals(len(cls.getattr('__module__')), 1)
        self.assertIsInstance(cls.getattr('__module__')[0], nodes.Const)
        self.assertEquals(cls.getattr('__module__')[0].value, 'data.module')
        self.assertEquals(len(cls.getattr('__dict__')), 1)
        self.assertRaises(NotFoundError, cls.getattr, '__mro__')
        for cls in (nodes.List._proxied, nodes.Const(1)._proxied):
            self.assertEquals(len(cls.getattr('__bases__')), 1)
            self.assertEquals(len(cls.getattr('__name__')), 1)
            self.assertEquals(len(cls.getattr('__doc__')), 1, (cls, cls.getattr('__doc__')))
            self.assertEquals(cls.getattr('__doc__')[0].value, cls.doc)
            self.assertEquals(len(cls.getattr('__module__')), 1)
            self.assertEquals(len(cls.getattr('__dict__')), 1)
            self.assertEquals(len(cls.getattr('__mro__')), 1)

    def test_cls_special_attributes_2(self):
        astng = abuilder.string_build('''
class A: pass
class B: pass

A.__bases__ += (B,)
''', __name__, __file__)
        self.assertEquals(len(astng['A'].getattr('__bases__')), 2)
        self.assertIsInstance(astng['A'].getattr('__bases__')[0], nodes.Tuple)
        self.assertIsInstance(astng['A'].getattr('__bases__')[1], nodes.AssAttr)

    def test_instance_special_attributes(self):
        for inst in (Instance(MODULE['YO']), nodes.List(), nodes.Const(1)):
            self.assertRaises(NotFoundError, inst.getattr, '__mro__')
            self.assertRaises(NotFoundError, inst.getattr, '__bases__')
            self.assertRaises(NotFoundError, inst.getattr, '__name__')
            self.assertEquals(len(inst.getattr('__dict__')), 1)
            self.assertEquals(len(inst.getattr('__doc__')), 1)

    def test_navigation(self):
        klass = MODULE['YO']
        self.assertEquals(klass.statement(), klass)
        l_sibling = klass.previous_sibling()
        self.assert_(isinstance(l_sibling, nodes.Function), l_sibling)
        self.assertEquals(l_sibling.name, 'global_access')
        r_sibling = klass.next_sibling()
        self.assertIsInstance(r_sibling, nodes.Class)
        self.assertEquals(r_sibling.name, 'YOUPI')

    def test_local_attr_ancestors(self):
        klass2 = MODULE['YOUPI']
        it = klass2.local_attr_ancestors('__init__')
        anc_klass = it.next()
        self.assertIsInstance(anc_klass, nodes.Class)
        self.assertEquals(anc_klass.name, 'YO')
        self.assertRaises(StopIteration, it.next)
        it = klass2.local_attr_ancestors('method')
        self.assertRaises(StopIteration, it.next)

    def test_instance_attr_ancestors(self):
        klass2 = MODULE['YOUPI']
        it = klass2.instance_attr_ancestors('yo')
        anc_klass = it.next()
        self.assertIsInstance(anc_klass, nodes.Class)
        self.assertEquals(anc_klass.name, 'YO')
        self.assertRaises(StopIteration, it.next)
        klass2 = MODULE['YOUPI']
        it = klass2.instance_attr_ancestors('member')
        self.assertRaises(StopIteration, it.next)

    def test_methods(self):
        klass2 = MODULE['YOUPI']
        methods = [m.name for m in klass2.methods()]
        methods.sort()
        self.assertEquals(methods, ['__init__', 'class_method',
                                   'method', 'static_method'])
        methods = [m.name for m in klass2.mymethods()]
        methods.sort()
        self.assertEquals(methods, ['__init__', 'class_method',
                                   'method', 'static_method'])
        klass2 = MODULE2['Specialization']
        methods = [m.name for m in klass2.mymethods()]
        methods.sort()
        self.assertEquals(methods, [])
        method_locals = klass2.local_attr('method')
        self.assertEquals(len(method_locals), 1)
        self.assertEquals(method_locals[0].name, 'method')
        self.assertRaises(NotFoundError, klass2.local_attr, 'nonexistant')
        methods = [m.name for m in klass2.methods()]
        methods.sort()
        self.assertEquals(methods, ['__init__', 'class_method',
                                   'method', 'static_method'])

    #def test_rhs(self):
    #    my_dict = MODULE['MY_DICT']
    #    self.assertIsInstance(my_dict.rhs(), nodes.Dict)
    #    a = MODULE['YO']['a']
    #    value = a.rhs()
    #    self.assertIsInstance(value, nodes.Const)
    #    self.assertEquals(value.value, 1)

    def test_ancestors(self):
        klass = MODULE['YOUPI']
        ancs = [a.name for a in klass.ancestors()]
        self.assertEquals(ancs, ['YO'])
        klass = MODULE2['Specialization']
        ancs = [a.name for a in klass.ancestors()]
        self.assertEquals(ancs, ['YOUPI', 'YO', 'YO'])

    def test_type(self):
        klass = MODULE['YOUPI']
        self.assertEquals(klass.type, 'class')
        klass = MODULE2['Metaclass']
        self.assertEquals(klass.type, 'metaclass')
        klass = MODULE2['MyException']
        self.assertEquals(klass.type, 'exception')
        klass = MODULE2['MyIFace']
        self.assertEquals(klass.type, 'interface')
        klass = MODULE2['MyError']
        self.assertEquals(klass.type, 'exception')

    def test_interfaces(self):
        for klass, interfaces in (('Concrete0', ['MyIFace']),
                                  ('Concrete1', ['MyIFace', 'AnotherIFace']),
                                  ('Concrete2', ['MyIFace', 'AnotherIFace']),
                                  ('Concrete23', ['MyIFace', 'AnotherIFace'])):
            klass = MODULE2[klass]
            self.assertEquals([i.name for i in klass.interfaces()],
                              interfaces)

    def test_concat_interfaces(self):
        astng = abuilder.string_build('''
class IMachin: pass

class Correct2:
    """docstring"""
    __implements__ = (IMachin,)

class BadArgument:
    """docstring"""
    __implements__ = (IMachin,)

class InterfaceCanNowBeFound:
    """docstring"""
    __implements__ = BadArgument.__implements__ + Correct2.__implements__

        ''')
        self.assertEquals([i.name for i in astng['InterfaceCanNowBeFound'].interfaces()],
                          ['IMachin'])

    def test_inner_classes(self):
        eee = NONREGR['Ccc']['Eee']
        self.assertEquals([n.name for n in eee.ancestors()], ['Ddd', 'Aaa', 'object'])


    def test_classmethod_attributes(self):
        data = '''
class WebAppObject(object):
    def registered(cls, application):
        cls.appli = application
        cls.schema = application.schema
        cls.config = application.config
        return cls
    registered = classmethod(registered)
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        cls = astng['WebAppObject']
        self.assertEquals(sorted(cls.locals.keys()),
                          ['appli', 'config', 'registered', 'schema'])


    def test_class_getattr(self):
        data =         '''
class WebAppObject(object):
    appli = application
    appli += 2
    del self.appli
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        cls = astng['WebAppObject']
        # test del statement not returned by getattr
        self.assertEquals(len(cls.getattr('appli')), 2)


    def test_instance_getattr(self):
        data =         '''
class WebAppObject(object):
    def __init__(self, application):
        self.appli = application
        self.appli += 2
        del self.appli
         '''
        astng = abuilder.string_build(data, __name__, __file__)
        inst = Instance(astng['WebAppObject'])
        # test del statement not returned by getattr
        self.assertEquals(len(inst.getattr('appli')), 2)


    def test_instance_getattr_with_class_attr(self):
        data = '''
class Parent:
    aa = 1
    cc = 1

class Klass(Parent):
    aa = 0
    bb = 0

    def incr(self, val):
        self.cc = self.aa
        if val > self.aa:
            val = self.aa
        if val < self.bb:
            val = self.bb
        self.aa += val
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        inst = Instance(astng['Klass'])
        self.assertEquals(len(inst.getattr('aa')), 3, inst.getattr('aa'))
        self.assertEquals(len(inst.getattr('bb')), 1, inst.getattr('bb'))
        self.assertEquals(len(inst.getattr('cc')), 2, inst.getattr('cc'))


    def test_getattr_method_transform(self):
        data = '''
class Clazz(object):

    def m1(self, value):
        self.value = value
    m2 = m1

def func(arg1, arg2):
    "function that will be used as a method"
    return arg1.value + arg2

Clazz.m3 = func
inst = Clazz()
inst.m4 = func
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        cls = astng['Clazz']
        # test del statement not returned by getattr
        for method in ('m1', 'm2', 'm3'):
            inferred = list(cls.igetattr(method))
            self.assertEquals(len(inferred), 1)
            self.assertIsInstance(inferred[0], UnboundMethod)
            inferred = list(Instance(cls).igetattr(method))
            self.assertEquals(len(inferred), 1)
            self.assertIsInstance(inferred[0], BoundMethod)
        inferred = list(Instance(cls).igetattr('m4'))
        self.assertEquals(len(inferred), 1)
        self.assertIsInstance(inferred[0], nodes.Function)

__all__ = ('ModuleNodeTC', 'ImportNodeTC', 'FunctionNodeTC', 'ClassNodeTC')

if __name__ == '__main__':
    unittest_main()
