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
import unittest
import os
import sys
from os.path import join, dirname
from logilab.astng.manager import ASTNGManager


class ASTNGManagerTC(unittest.TestCase):
    def setUp(self):
        self.manager = ASTNGManager(borg=False)
        
    def test_astng_from_module(self):
        astng = self.manager.astng_from_module(unittest)
        self.assertEquals(astng.pure_python, True)
        import time
        astng = self.manager.astng_from_module(time)
        self.assertEquals(astng.pure_python, False)
        
    def test_astng_from_class(self):
        astng = self.manager.astng_from_class(file)
        self.assertEquals(astng.name, 'file')
        self.assertEquals(astng.parent.frame().name, '__builtin__')

        astng = self.manager.astng_from_class(object)
        self.assertEquals(astng.name, 'object')
        self.assertEquals(astng.parent.frame().name, '__builtin__')
        self.failUnless('__setattr__' in astng)
        
    def _test_astng_from_zip(self, archive):
        origpath = sys.path[:]
        sys.modules.pop('mypypa', None)
        sys.path.insert(0, join(dirname(__file__), 'data', archive))
        try:
            module = self.manager.astng_from_module_name('mypypa')
            self.assertEquals(module.name, 'mypypa')
            self.failUnless(module.file.endswith('%s/mypypa' % archive),
                            module.file)
        finally:
            sys.path = origpath

    def test_astng_from_module_name_egg(self):
        self._test_astng_from_zip('MyPyPa-0.1.0-py2.5.egg')

    def test_astng_from_module_name_zip(self):
        self._test_astng_from_zip('MyPyPa-0.1.0-py2.5.zip')            
        
    def test_from_directory(self):
        obj = self.manager.from_directory('data')
        self.assertEquals(obj.name, 'data')
        self.assertEquals(obj.path, join(os.getcwd(), 'data'))
        
    def test_package_node(self):
        obj = self.manager.from_directory('data')
        expected_short = ['SSL1', '__init__', 'all', 'appl', 'format', 'module', 'module2',
                          'noendingnewline', 'nonregr', 'notall']
        expected_long = ['SSL1', 'data', 'data.all', 'appl', 'data.format', 'data.module',
                         'data.module2', 'data.noendingnewline', 'data.nonregr',
                         'data.notall']
        self.assertEquals(obj.keys(), expected_short)
        self.assertEquals([m.name for m in obj.values()], expected_long)
        self.assertEquals([m for m in list(obj)], expected_short)
        self.assertEquals([(name, m.name) for name, m in obj.items()],
                          zip(expected_short, expected_long))
        self.assertEquals([(name, m.name) for name, m in obj.items()],
                          zip(expected_short, expected_long))
        
        self.assertEquals('module' in obj, True)
        self.assertEquals(obj.has_key('module'), True)
        self.assertEquals(obj.get('module').name, 'data.module')
        self.assertEquals(obj['module'].name, 'data.module')
        self.assertEquals(obj.get('whatever'), None)
        self.assertEquals(obj.fullname(), 'data')
        # FIXME: test fullname on a subpackage

        
if __name__ == '__main__':
    unittest.main()

    
