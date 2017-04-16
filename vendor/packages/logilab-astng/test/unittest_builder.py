# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
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

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""tests for the astng builder and rebuilder module"""

import unittest
import sys
from os.path import join, abspath, dirname

from logilab.common.testlib import TestCase, unittest_main
from pprint import pprint

from logilab.astng import builder, nodes, patchcomptransformer, MANAGER, \
                          InferenceError, NotFoundError
from logilab.astng.nodes import Module
from logilab.astng.bases import YES
from logilab.astng.nodes_as_string import as_string

from unittest_inference import get_name_node

import data
from data import module as test_module

class FromToLineNoTC(TestCase):

    def setUp(self):
        self.astng = builder.ASTNGBuilder().file_build('data/format.py')

    def test_callfunc_lineno(self):
        stmts = self.astng.body
        # on line 4:
        #    function('aeozrijz\
        #    earzer', hop)
        discard = stmts[0]
        self.assertIsInstance(discard, nodes.Discard)
        self.assertEquals(discard.fromlineno, 4)
        self.assertEquals(discard.tolineno, 5)
        callfunc = discard.value
        self.assertIsInstance(callfunc, nodes.CallFunc)
        self.assertEquals(callfunc.fromlineno, 4)
        self.assertEquals(callfunc.tolineno, 5)
        name = callfunc.func
        self.assertIsInstance(name, nodes.Name)
        self.assertEquals(name.fromlineno, 4)
        self.assertEquals(name.tolineno, 4)
        strarg = callfunc.args[0]
        self.assertIsInstance(strarg, nodes.Const)
        self.assertEquals(strarg.fromlineno, 5) # no way for this one (is 4 actually)
        self.assertEquals(strarg.tolineno, 5)
        namearg = callfunc.args[1]
        self.assertIsInstance(namearg, nodes.Name)
        self.assertEquals(namearg.fromlineno, 5)
        self.assertEquals(namearg.tolineno, 5)
        # on line 10:
        #    fonction(1,
        #             2,
        #             3,
        #             4)
        discard = stmts[2]
        self.assertIsInstance(discard, nodes.Discard)
        self.assertEquals(discard.fromlineno, 10)
        self.assertEquals(discard.tolineno, 13)
        callfunc = discard.value
        self.assertIsInstance(callfunc, nodes.CallFunc)
        self.assertEquals(callfunc.fromlineno, 10)
        self.assertEquals(callfunc.tolineno, 13)
        name = callfunc.func
        self.assertIsInstance(name, nodes.Name)
        self.assertEquals(name.fromlineno, 10)
        self.assertEquals(name.tolineno, 10)
        for i, arg in enumerate(callfunc.args):
            self.assertIsInstance(arg, nodes.Const)
            self.assertEquals(arg.fromlineno, 10+i)
            self.assertEquals(arg.tolineno, 10+i)

    def test_function_lineno(self):
        stmts = self.astng.body
        # on line 15:
        #    def definition(a,
        #                   b,
        #                   c):
        #        return a + b + c
        function = stmts[3]
        self.assertIsInstance(function, nodes.Function)
        self.assertEquals(function.fromlineno, 15)
        self.assertEquals(function.tolineno, 18)
        self.assertEquals(function.blockstart_tolineno, 17)
        return_ = function.body[0]
        self.assertIsInstance(return_, nodes.Return)
        self.assertEquals(return_.fromlineno, 18)
        self.assertEquals(return_.tolineno, 18)

    def test_decorated_function_lineno(self):
        if sys.version_info < (2, 4):
            self.skip('require python >=2.4')
        astng = builder.ASTNGBuilder().string_build('''
@decorator
def function(
    arg):
    print arg
''', __name__, __file__)
        function = astng['function']
        self.assertEquals(function.fromlineno, 3) # XXX discussable, but that's what is expected by pylint right now
        self.assertEquals(function.tolineno, 5)
        self.assertEquals(function.blockstart_tolineno, 4)
        self.assertEquals(function.decorators.fromlineno, 2)
        self.assertEquals(function.decorators.tolineno, 2)


    def test_class_lineno(self):
        stmts = self.astng.body
        # on line 20:
        #    class debile(dict,
        #                 object):
        #       pass
        class_ = stmts[4]
        self.assertIsInstance(class_, nodes.Class)
        self.assertEquals(class_.fromlineno, 20)
        self.assertEquals(class_.tolineno, 22)
        self.assertEquals(class_.blockstart_tolineno, 21)
        pass_ = class_.body[0]
        self.assertIsInstance(pass_, nodes.Pass)
        self.assertEquals(pass_.fromlineno, 22)
        self.assertEquals(pass_.tolineno, 22)

    def test_if_lineno(self):
        stmts = self.astng.body
        # on line 20:
        #    if aaaa: pass
        #    else:
        #        aaaa,bbbb = 1,2
        #        aaaa,bbbb = bbbb,aaaa
        if_ = stmts[5]
        self.assertIsInstance(if_, nodes.If)
        self.assertEquals(if_.fromlineno, 24)
        self.assertEquals(if_.tolineno, 27)
        self.assertEquals(if_.blockstart_tolineno, 24)
        self.assertEquals(if_.orelse[0].fromlineno, 26)
        self.assertEquals(if_.orelse[1].tolineno, 27)

    def test_for_while_lineno(self):
        for code in ('''
for a in range(4):
  print a
  break
else:
  print "bouh"
''', '''
while a:
  print a
  break
else:
  print "bouh"
''',
                     ):
            astng = builder.ASTNGBuilder().string_build(code, __name__, __file__)
            stmt = astng.body[0]
            self.assertEquals(stmt.fromlineno, 2)
            self.assertEquals(stmt.tolineno, 6)
            self.assertEquals(stmt.blockstart_tolineno, 2)
            self.assertEquals(stmt.orelse[0].fromlineno, 6) # XXX
            self.assertEquals(stmt.orelse[0].tolineno, 6)


    def test_try_except_lineno(self):
        astng = builder.ASTNGBuilder().string_build('''
try:
  print a
except:
  pass
else:
  print "bouh"
''', __name__, __file__)
        try_ = astng.body[0]
        self.assertEquals(try_.fromlineno, 2)
        self.assertEquals(try_.tolineno, 7)
        self.assertEquals(try_.blockstart_tolineno, 2)
        self.assertEquals(try_.orelse[0].fromlineno, 7) # XXX
        self.assertEquals(try_.orelse[0].tolineno, 7)
        hdlr = try_.handlers[0]
        self.assertEquals(hdlr.fromlineno, 4)
        self.assertEquals(hdlr.tolineno, 5)
        self.assertEquals(hdlr.blockstart_tolineno, 4)


    def test_try_finally_lineno(self):
        astng = builder.ASTNGBuilder().string_build('''
try:
  print a
finally:
  print "bouh"
''', __name__, __file__)
        try_ = astng.body[0]
        self.assertEquals(try_.fromlineno, 2)
        self.assertEquals(try_.tolineno, 5)
        self.assertEquals(try_.blockstart_tolineno, 2)
        self.assertEquals(try_.finalbody[0].fromlineno, 5) # XXX
        self.assertEquals(try_.finalbody[0].tolineno, 5)


    def test_try_finally_25_lineno(self):
        if sys.version_info < (2, 5):
            self.skip('require python >= 2.5')
        astng = builder.ASTNGBuilder().string_build('''
try:
  print a
except:
  pass
finally:
  print "bouh"
''', __name__, __file__)
        try_ = astng.body[0]
        self.assertEquals(try_.fromlineno, 2)
        self.assertEquals(try_.tolineno, 7)
        self.assertEquals(try_.blockstart_tolineno, 2)
        self.assertEquals(try_.finalbody[0].fromlineno, 7) # XXX
        self.assertEquals(try_.finalbody[0].tolineno, 7)


    def test_with_lineno(self):
        if sys.version_info < (2, 5):
            self.skip('require python >=2.5')
        astng = builder.ASTNGBuilder().string_build('''
from __future__ import with_statement
with file("/tmp/pouet") as f:
  print f
''', __name__, __file__)
        with_ = astng.body[1]
        self.assertEquals(with_.fromlineno, 3)
        self.assertEquals(with_.tolineno, 4)
        self.assertEquals(with_.blockstart_tolineno, 3)



class BuilderTC(TestCase):

    def setUp(self):
        self.builder = builder.ASTNGBuilder()

    def test_border_cases(self):
        """check that a file with no trailing new line is parseable"""
        self.builder.file_build('data/noendingnewline.py', 'data.noendingnewline')
        self.assertRaises(builder.ASTNGBuildingException,
                          self.builder.file_build, 'data/inexistant.py', 'whatever')

    def test_inspect_build0(self):
        """test astng tree build from a living object"""
        builtin_astng = MANAGER.astng_from_module_name('__builtin__')
        fclass = builtin_astng['file']
        self.assert_('name' in fclass)
        self.assert_('mode' in fclass)
        self.assert_('read' in fclass)
        self.assert_(fclass.newstyle)
        self.assert_(fclass.pytype(), '__builtin__.type')
        self.assertIsInstance(fclass['read'], nodes.Function)
        # check builtin function has args.args == None
        dclass = builtin_astng['dict']
        self.assertEquals(dclass['has_key'].args.args, None)
        # just check type and object are there
        builtin_astng.getattr('type')
        builtin_astng.getattr('object')
        # check open file alias
        builtin_astng.getattr('open')
        # check 'help' is there (defined dynamically by site.py)
        builtin_astng.getattr('help')
        # check property has __init__
        pclass = builtin_astng['property']
        self.assert_('__init__' in pclass)
        self.assertIsInstance(builtin_astng['None'], nodes.Const)
        self.assertIsInstance(builtin_astng['True'], nodes.Const)
        self.assertIsInstance(builtin_astng['False'], nodes.Const)
        self.assertIsInstance(builtin_astng['Exception'], nodes.From)
        self.assertIsInstance(builtin_astng['NotImplementedError'], nodes.From)

    def test_inspect_build1(self):
        time_astng = MANAGER.astng_from_module_name('time')
        self.assert_(time_astng)
        self.assertEquals(time_astng['time'].args.defaults, [])

    def test_inspect_build2(self):
        """test astng tree build from a living object"""
        try:
            from mx import DateTime
        except ImportError:
            self.skip('test skipped: mxDateTime is not available')
        else:
            dt_astng = self.builder.inspect_build(DateTime)
            dt_astng.getattr('DateTime')
            # this one is failing since DateTimeType.__module__ = 'builtins' !
            #dt_astng.getattr('DateTimeType')

    def test_inspect_build3(self):
        unittest_astng = self.builder.inspect_build(unittest)

    def test_inspect_build_instance(self):
        """test astng tree build from a living object"""
        import exceptions
        builtin_astng = self.builder.inspect_build(exceptions)
        fclass = builtin_astng['OSError']
        # things like OSError.strerror are now (2.5) data descriptors on the
        # class instead of entries in the __dict__ of an instance
        if sys.version_info < (2, 5):
            container = fclass.instance_attrs
        else:
            container = fclass
        self.assert_('errno' in container)
        self.assert_('strerror' in container)
        self.assert_('filename' in container)

    def test_inspect_build_type_object(self):
        builtin_astng = MANAGER.astng_from_module_name('__builtin__')

        infered = list(builtin_astng.igetattr('object'))
        self.assertEquals(len(infered), 1)
        infered = infered[0]
        self.assertEquals(infered.name, 'object')
        as_string(infered)

        infered = list(builtin_astng.igetattr('type'))
        self.assertEquals(len(infered), 1)
        infered = infered[0]
        self.assertEquals(infered.name, 'type')
        as_string(infered)

    def test_package_name(self):
        """test base properties and method of a astng module"""
        datap = self.builder.file_build('data/__init__.py', 'data')
        self.assertEquals(datap.name, 'data')
        self.assertEquals(datap.package, 1)
        datap = self.builder.file_build('data/__init__.py', 'data.__init__')
        self.assertEquals(datap.name, 'data')
        self.assertEquals(datap.package, 1)

    def test_yield_parent(self):
        """check if we added discard nodes as yield parent (w/ compiler)"""
        data = """
def yiell():
    yield 0
    if noe:
        yield more
"""
        func = self.builder.string_build(data).body[0]
        self.assertIsInstance(func, nodes.Function)
        stmt = func.body[0]
        self.assertIsInstance(stmt, nodes.Discard)
        self.assertIsInstance(stmt.value, nodes.Yield)
        self.assertIsInstance(func.body[1].body[0], nodes.Discard)
        self.assertIsInstance(func.body[1].body[0].value, nodes.Yield)

    def test_object(self):
        obj_astng = self.builder.inspect_build(object)
        self.failUnless('__setattr__' in obj_astng)

    def test_newstyle_detection(self):
        data = '''
class A:
    "old style"

class B(A):
    "old style"

class C(object):
    "new style"

class D(C):
    "new style"

__metaclass__ = type

class E(A):
    "old style"

class F:
    "new style"
'''
        mod_astng = self.builder.string_build(data, __name__, __file__)
        self.failIf(mod_astng['A'].newstyle)
        self.failIf(mod_astng['B'].newstyle)
        self.failUnless(mod_astng['C'].newstyle)
        self.failUnless(mod_astng['D'].newstyle)
        self.failIf(mod_astng['E'].newstyle)
        self.failUnless(mod_astng['F'].newstyle)

    def test_globals(self):
        data = '''
CSTE = 1

def update_global():
    global CSTE
    CSTE += 1

def global_no_effect():
    global CSTE2
    print CSTE
'''
        astng = self.builder.string_build(data, __name__, __file__)
        self.failUnlessEqual(len(astng.getattr('CSTE')), 2)
        self.assertIsInstance(astng.getattr('CSTE')[0], nodes.AssName)
        self.failUnlessEqual(astng.getattr('CSTE')[0].fromlineno, 2)
        self.failUnlessEqual(astng.getattr('CSTE')[1].fromlineno, 6)
        self.assertRaises(NotFoundError,
                          astng.getattr, 'CSTE2')
        self.assertRaises(InferenceError,
                          astng['global_no_effect'].ilookup('CSTE2').next)

    def test_socket_build(self):
        import socket
        astng = self.builder.module_build(socket)
        # XXX just check the first one. Actually 3 objects are inferred (look at
        # the socket module) but the last one as those attributes dynamically
        # set and astng is missing this.
        for fclass in astng.igetattr('socket'):
            #print fclass.root().name, fclass.name, fclass.lineno
            self.assert_('connect' in fclass)
            self.assert_('send' in fclass)
            self.assert_('close' in fclass)
            break

    if sys.version_info >= (2, 4):
        def test_gen_expr_var_scope(self):
            data = 'l = list(n for n in range(10))\n'
            astng = self.builder.string_build(data, __name__, __file__)
            # n unavailable outside gen expr scope
            self.failIf('n' in astng)
            # test n is inferable anyway
            n = get_name_node(astng, 'n')
            self.failIf(n.scope() is astng)
            self.failUnlessEqual([i.__class__ for i in n.infer()],
                                 [YES.__class__])

class FileBuildTC(TestCase):

    def setUp(self):
        abuilder = builder.ASTNGBuilder()
        self.module = abuilder.file_build('data/module.py', 'data.module')

    def test_module_base_props(self):
        """test base properties and method of a astng module"""
        module = self.module
        self.assertEquals(module.name, 'data.module')
        self.assertEquals(module.doc, "test module for astng\n")
        self.assertEquals(module.fromlineno, 0)
        self.assertEquals(module.parent, None)
        self.assertEquals(module.frame(), module)
        self.assertEquals(module.root(), module)
        self.assertEquals(module.file, join(abspath(data.__path__[0]), 'module.py'))
        self.assertEquals(module.pure_python, 1)
        self.assertEquals(module.package, 0)
        self.assert_(not module.is_statement)
        self.assertEquals(module.statement(), module)
        self.assertEquals(module.statement(), module)

    def test_module_locals(self):
        """test the 'locals' dictionary of a astng module"""
        module = self.module
        _locals = module.locals
        self.assert_(_locals is module.globals)
        keys = _locals.keys()
        keys.sort()
        should = ['MY_DICT', 'YO', 'YOUPI',
                '__revision__',  'global_access','modutils', 'nested_args',
                 'os', 'redirect', 'spawn', 'LocalsVisitor',
                'ASTWalker', 'ASTVisitor']
        should.sort()
        self.assertEquals(keys, should)

    def test_function_base_props(self):
        """test base properties and method of a astng function"""
        module = self.module
        function = module['global_access']
        self.assertEquals(function.name, 'global_access')
        self.assertEquals(function.doc, 'function test')
        self.assertEquals(function.fromlineno, 15)
        self.assert_(function.parent)
        self.assertEquals(function.frame(), function)
        self.assertEquals(function.parent.frame(), module)
        self.assertEquals(function.root(), module)
        self.assertEquals([n.name for n in function.args.args], ['key', 'val'])
        self.assertEquals(function.type, 'function')

    def test_function_locals(self):
        """test the 'locals' dictionary of a astng function"""
        _locals = self.module['global_access'].locals
        self.assertEquals(len(_locals), 4)
        keys = _locals.keys()
        keys.sort()
        self.assertEquals(keys, ['i', 'key', 'local', 'val'])

    def test_class_base_props(self):
        """test base properties and method of a astng class"""
        module = self.module
        klass = module['YO']
        self.assertEquals(klass.name, 'YO')
        self.assertEquals(klass.doc, 'hehe')
        self.assertEquals(klass.fromlineno, 28)
        self.assert_(klass.parent)
        self.assertEquals(klass.frame(), klass)
        self.assertEquals(klass.parent.frame(), module)
        self.assertEquals(klass.root(), module)
        self.assertEquals(klass.basenames, [])
        self.assertEquals(klass.newstyle, False)

    def test_class_locals(self):
        """test the 'locals' dictionary of a astng class"""
        module = self.module
        klass1 = module['YO']
        locals1 = klass1.locals
        keys = locals1.keys()
        keys.sort()
        self.assertEquals(keys, ['__init__', 'a'])
        klass2 = module['YOUPI']
        locals2 = klass2.locals
        keys = locals2.keys()
        keys.sort()
        self.assertEquals(keys, ['__init__', 'class_attr', 'class_method',
                                 'method', 'static_method'])

    def test_class_instance_attrs(self):
        module = self.module
        klass1 = module['YO']
        klass2 = module['YOUPI']
        self.assertEquals(klass1.instance_attrs.keys(), ['yo'])
        self.assertEquals(klass2.instance_attrs.keys(), ['member'])

    def test_class_basenames(self):
        module = self.module
        klass1 = module['YO']
        klass2 = module['YOUPI']
        self.assertEquals(klass1.basenames, [])
        self.assertEquals(klass2.basenames, ['YO'])

    def test_method_base_props(self):
        """test base properties and method of a astng method"""
        klass2 = self.module['YOUPI']
        # "normal" method
        method = klass2['method']
        self.assertEquals(method.name, 'method')
        self.assertEquals([n.name for n in method.args.args], ['self'])
        self.assertEquals(method.doc, 'method test')
        self.assertEquals(method.fromlineno, 48)
        self.assertEquals(method.type, 'method')
        # class method
        method = klass2['class_method']
        self.assertEquals([n.name for n in method.args.args], ['cls'])
        self.assertEquals(method.type, 'classmethod')
        # static method
        method = klass2['static_method']
        self.assertEquals(method.args.args, [])
        self.assertEquals(method.type, 'staticmethod')

    def test_method_locals(self):
        """test the 'locals' dictionary of a astng method"""
        klass2 = self.module['YOUPI']
        method = klass2['method']
        _locals = method.locals
        self.assertEquals(len(_locals), 5)
        keys = _locals.keys()
        keys.sort()
        self.assertEquals(keys, ['a', 'autre', 'b', 'local', 'self'])


class ModuleBuildTC(FileBuildTC):

    def setUp(self):
        abuilder = builder.ASTNGBuilder()
        self.module = abuilder.module_build(test_module)


class MoreTC(TestCase):

    def setUp(self):
        self.builder = builder.ASTNGBuilder()

    def test_infered_build(self):
        code = '''class A: pass
A.type = "class"

def A_ass_type(self):
    print self
A.ass_type = A_ass_type
    '''
        astng = self.builder.string_build(code)
        lclass = list(astng.igetattr('A'))
        self.assertEquals(len(lclass), 1)
        lclass = lclass[0]
        self.assert_('ass_type' in lclass.locals, lclass.locals.keys())
        self.assert_('type' in lclass.locals.keys())

#     def test_1(self):
#         from logilab import astng
#         import compiler
#         sn = astng.MANAGER.astng_from_file(join(astng.__path__[0], 'inference.py'))
#         astastng = astng.MANAGER.astng_from_file(join(compiler.__path__[0], 'ast.py'))
#         # check monkey patching of the compiler module has been inferred
#         lclass = list(astastng.igetattr('Function'))
#         self.assertEquals(len(lclass), 1)
#         lclass = lclass[0]
#         self.assert_('ass_type' in lclass.locals, lclass.locals.keys())

    def test_augassign_attr(self):
        astng = self.builder.string_build("""class Counter:
    v = 0
    def inc(self):
        self.v += 1
        """, __name__, __file__)
        # Check self.v += 1 generate AugAssign(AssAttr(...)), not AugAssign(GetAttr(AssName...))

    def test_dumb_module(self):
        astng = self.builder.string_build("pouet")

    def test_infered_dont_pollute(self):
        code = '''
def func(a=None):
    a.custom_attr = 0
def func2(a={}):
    a.custom_attr = 0
    '''
        astng = self.builder.string_build(code)
        nonetype = nodes.const_factory(None)
        self.failIf('custom_attr' in nonetype.locals)
        self.failIf('custom_attr' in nonetype.instance_attrs)
        nonetype = nodes.const_factory({})
        self.failIf('custom_attr' in nonetype.locals)
        self.failIf('custom_attr' in nonetype.instance_attrs)


    def test_asstuple(self):
        code = 'a, b = range(2)'
        astng = self.builder.string_build(code)
        self.failUnless('b' in astng.locals)
        code = '''
def visit_if(self, node):
    node.test, body = node.tests[0]
'''
        astng = self.builder.string_build(code)
        self.failUnless('body' in astng['visit_if'].locals)

    def test_build_constants(self):
        '''test expected values of constants after rebuilding'''
        code = '''
def func():
    return None
    return
    return 'None'
'''
        astng = self.builder.string_build(code)
        none, nothing, chain = [ret.value for ret in astng.body[0].body]
        self.assertIsInstance(none, nodes.Const)
        self.assertEquals(none.value, None)
        self.assertEquals(nothing, None)
        self.assertIsInstance(chain, nodes.Const)
        self.assertEquals(chain.value, 'None')


if __name__ == '__main__':
    unittest_main()
