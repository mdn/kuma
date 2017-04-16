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
"""tests for specific behaviour of astng nodes
"""
import sys

from logilab.common import testlib
from logilab.astng import builder, nodes, NotFoundError
from logilab.astng.nodes_as_string import as_string

from data import module as test_module

abuilder = builder.ASTNGBuilder()

class _NodeTC(testlib.TestCase):
    """test transformation of If Node"""
    CODE = None
    @property
    def astng(self):
        try:
            return self.__class__.__dict__['CODE_ASTNG']
        except KeyError:
            astng = abuilder.string_build(self.CODE)
            self.__class__.CODE_ASTNG = astng
            return astng


class IfNodeTC(_NodeTC):
    """test transformation of If Node"""
    CODE = """
if 0:
    print

if True:
    print
else:
    pass

if "":
    print
elif []:
    raise

if 1:
    print
elif True:
    print
elif func():
    pass
else:
    raise
    """
        
    def test_if_elif_else_node(self):
        """test transformation for If node"""
        self.assertEquals(len(self.astng.body), 4)
        for stmt in self.astng.body:
            self.assertIsInstance( stmt, nodes.If)
        self.failIf(self.astng.body[0].orelse) # simple If
        self.assertIsInstance(self.astng.body[1].orelse[0], nodes.Pass) # If / else
        self.assertIsInstance(self.astng.body[2].orelse[0], nodes.If) # If / elif
        self.assertIsInstance(self.astng.body[3].orelse[0].orelse[0], nodes.If)

    def test_block_range(self):
        # XXX ensure expected values
        self.assertEquals(self.astng.block_range(1), (0, 22))
        self.assertEquals(self.astng.block_range(10), (0, 22)) # XXX (10, 22) ?
        self.assertEquals(self.astng.body[1].block_range(5), (5, 6))
        self.assertEquals(self.astng.body[1].block_range(6), (6, 6))
        self.assertEquals(self.astng.body[1].orelse[0].block_range(7), (7, 8))
        self.assertEquals(self.astng.body[1].orelse[0].block_range(8), (8, 8))


class TryExceptNodeTC(_NodeTC):
    CODE = """
try:
    print 'pouet'
except IOError:
    pass
except UnicodeError:
    print
else:
    print
    """
    def test_block_range(self):
        # XXX ensure expected values
        self.assertEquals(self.astng.body[0].block_range(1), (1, 8))
        self.assertEquals(self.astng.body[0].block_range(2), (2, 2))
        self.assertEquals(self.astng.body[0].block_range(3), (3, 8))
        self.assertEquals(self.astng.body[0].block_range(4), (4, 4))
        self.assertEquals(self.astng.body[0].block_range(5), (5, 5))
        self.assertEquals(self.astng.body[0].block_range(6), (6, 6))
        self.assertEquals(self.astng.body[0].block_range(7), (7, 7))
        self.assertEquals(self.astng.body[0].block_range(8), (8, 8))


class TryFinallyNodeTC(_NodeTC):
    CODE = """
try:
    print 'pouet'
finally:
    print 'pouet'
    """
    def test_block_range(self):
        # XXX ensure expected values
        self.assertEquals(self.astng.body[0].block_range(1), (1, 4))
        self.assertEquals(self.astng.body[0].block_range(2), (2, 2))
        self.assertEquals(self.astng.body[0].block_range(3), (3, 4))
        self.assertEquals(self.astng.body[0].block_range(4), (4, 4))


class TryFinally25NodeTC(_NodeTC):
    CODE = """
try:
    print 'pouet'
except Exception:
    print 'oops'
finally:
    print 'pouet'
    """
    def test_block_range(self):
        if sys.version_info < (2, 5):
            self.skip('require python >= 2.5')
        # XXX ensure expected values
        self.assertEquals(self.astng.body[0].block_range(1), (1, 6))
        self.assertEquals(self.astng.body[0].block_range(2), (2, 2))
        self.assertEquals(self.astng.body[0].block_range(3), (3, 4))
        self.assertEquals(self.astng.body[0].block_range(4), (4, 4))
        self.assertEquals(self.astng.body[0].block_range(5), (5, 5))
        self.assertEquals(self.astng.body[0].block_range(6), (6, 6))

        
MODULE = abuilder.module_build(test_module)
MODULE2 = abuilder.file_build('data/module2.py', 'data.module2')


class ImportNodeTC(testlib.TestCase):
    
    def test_import_self_resolve(self):
        myos = MODULE2.igetattr('myos').next()
        self.failUnless(isinstance(myos, nodes.Module), myos)
        self.failUnlessEqual(myos.name, 'os')
        self.failUnlessEqual(myos.qname(), 'os')
        self.failUnlessEqual(myos.pytype(), '__builtin__.module')

    def test_from_self_resolve(self):
        spawn = MODULE.igetattr('spawn').next()
        self.failUnless(isinstance(spawn, nodes.Class), spawn)
        self.failUnlessEqual(spawn.root().name, 'logilab.common.shellutils')
        self.failUnlessEqual(spawn.qname(), 'logilab.common.shellutils.Execute')
        self.failUnlessEqual(spawn.pytype(), '__builtin__.classobj')
        abspath = MODULE2.igetattr('abspath').next()
        self.failUnless(isinstance(abspath, nodes.Function), abspath)
        self.failUnlessEqual(abspath.root().name, 'os.path')
        self.failUnlessEqual(abspath.qname(), 'os.path.abspath')
        self.failUnlessEqual(abspath.pytype(), '__builtin__.function')

    def test_real_name(self):
        from_ = MODULE['spawn']
        self.assertEquals(from_.real_name('spawn'), 'Execute')
        imp_ = MODULE['os']
        self.assertEquals(imp_.real_name('os'), 'os')
        self.assertRaises(NotFoundError, imp_.real_name, 'os.path')
        imp_ = MODULE['spawn']
        self.assertEquals(imp_.real_name('spawn'), 'Execute')
        self.assertRaises(NotFoundError, imp_.real_name, 'Execute')
        imp_ = MODULE2['YO']
        self.assertEquals(imp_.real_name('YO'), 'YO')
        self.assertRaises(NotFoundError, imp_.real_name, 'data')

    def test_as_string(self):
        
        ast = MODULE['modutils']
        self.assertEquals(as_string(ast), "from logilab.common import modutils")
        ast = MODULE['spawn']
        self.assertEquals(as_string(ast), "from logilab.common.shellutils import Execute as spawn")
        ast = MODULE['os']
        self.assertEquals(as_string(ast), "import os.path")
    
    def test_module_as_string(self):
        """just check as_string on a whole module doesn't raise an exception
        """
        self.assert_(as_string(MODULE))
        self.assert_(as_string(MODULE2))
        

class CmpNodeTC(testlib.TestCase):
    def test_as_string(self):
        ast = abuilder.string_build("a == 2")
        self.assertEquals(as_string(ast), "a == 2")


class ConstNodeTC(testlib.TestCase):
    
    def _test(self, value):
        node = nodes.const_factory(value)
        self.assertIsInstance(node._proxied, nodes.Class)
        self.assertEquals(node._proxied.name, value.__class__.__name__)
        self.assertIs(node.value, value)
        self.failUnless(node._proxied.parent)
        self.assertEquals(node._proxied.root().name, value.__class__.__module__)
        
    def test_none(self):
        self._test(None)
        
    def test_bool(self):
        self._test(True)
        
    def test_int(self):
        self._test(1)
        
    def test_float(self):
        self._test(1.0)
        
    def test_complex(self):
        self._test(1.0j)
        
    def test_str(self):
        self._test('a')
        
    def test_unicode(self):
        self._test(u'a')


class ArgumentsNodeTC(testlib.TestCase):
    def test_linenumbering(self):
        ast = abuilder.string_build('''
def func(a,
    b): pass
x = lambda x: None
        ''')
        self.assertEquals(ast['func'].args.fromlineno, 2)
        self.assertEquals(ast['func'].args.tolineno, 3)
        self.failIf(ast['func'].args.is_statement)
        xlambda = ast['x'].infer().next()
        self.assertEquals(xlambda.args.fromlineno, 4)
        self.assertEquals(xlambda.args.tolineno, 4)
        self.failIf(xlambda.args.is_statement)


class SliceNodeTC(testlib.TestCase):
    def test(self):
        for code in ('a[0]', 'a[1:3]', 'a[:-1:step]', 'a[:,newaxis]',
                     'a[newaxis,:]', 'del L[::2]', 'del A[1]', 'del Br[:]'):
            ast = abuilder.string_build(code)
            self.assertEquals(ast.as_string(), code)

    def test_slice_and_subscripts(self):
        code = """a[:1] = bord[2:]
a[:1] = bord[2:]
del bree[3:d]
bord[2:]
del av[d::f], a[df:]
a[:1] = bord[2:]
del SRC[::1,newaxis,1:]
tous[vals] = 1010
del thousand[key]
del a[::2], a[:-1:step]
del Fee.form[left:]
aout.vals = miles.of_stuff
del (ccok, (name.thing, foo.attrib.value)), Fee.form[left:]
if all[1] == bord[0:]:
    pass"""
        ast = abuilder.string_build(code)
        self.assertEquals(ast.as_string(), code)

class EllipsisNodeTC(testlib.TestCase):
    def test(self):
        ast = abuilder.string_build('a[...]')
        self.assertEquals(ast.as_string(), 'a[...]')
        
if __name__ == '__main__':
    testlib.unittest_main()
