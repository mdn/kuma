# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""provides unit tests for compat module"""

from logilab.common.testlib import TestCase, unittest_main
import sys
import types
import __builtin__
import pprint

class CompatTCMixIn:
    MODNAMES = {}
    BUILTINS = []
    ALTERED_BUILTINS = {}

    def setUp(self):
        self.builtins_backup = {}
        self.modules_backup = {}
        self.remove_builtins()
        self.alter_builtins()
        self.remove_modules()

    def tearDown(self):
        for modname in self.MODNAMES:
            del sys.modules[modname]
        for funcname, func in self.builtins_backup.items():
            setattr(__builtin__, funcname, func)
            # delattr(__builtin__, 'builtin_%s' % funcname)
        for modname, mod in self.modules_backup.items():
            sys.modules[modname] = mod
        try:
            del sys.modules['logilab.common.compat']
        except KeyError:
            pass

    def remove_builtins(self):
        for builtin in self.BUILTINS:
            func = getattr(__builtin__, builtin, None)
            if func is not None:
                self.builtins_backup[builtin] = func
                delattr(__builtin__, builtin)
                # setattr(__builtin__, 'builtin_%s' % builtin, func)
    def alter_builtins(self):
        for builtin, func in self.ALTERED_BUILTINS.iteritems():
            old_func = getattr(__builtin__, builtin, None)
            if func is not None:
                self.builtins_backup[builtin] = old_func
                setattr(__builtin__, builtin, func)
                # setattr(__builtin__, 'builtin_%s' % builtin, func)

    def remove_modules(self):
        for modname in self.MODNAMES:
            if modname in sys.modules:
                self.modules_backup[modname] = sys.modules[modname]
            sys.modules[modname] = types.ModuleType('faked%s' % modname)

    def test_removed_builtins(self):
        """tests that builtins are actually uncallable"""
        for builtin in self.BUILTINS:
            self.assertRaises(NameError, eval, builtin, {})

    def test_removed_modules(self):
        """tests that builtins are actually emtpy"""
        for modname, funcnames in self.MODNAMES.items():
            import_stmt = 'from %s import %s' % (modname, ', '.join(funcnames))
            # FIXME: use __import__ instead
            code = compile(import_stmt, 'foo.py', 'exec')
            self.assertRaises(ImportError, eval, code)


class Py23CompatTC(CompatTCMixIn, TestCase):
    BUILTINS = ('enumerate', 'sum')
    MODNAMES = {
        'sets' : ('Set', 'ImmutableSet'),
        'itertools' : ('izip', 'chain'),
        }

    def test_sum(self):
        from logilab.common.compat import sum
        self.assertEquals(sum(range(5)), 10)
        self.assertRaises(TypeError, sum, 'abc')

    def test_enumerate(self):
        from logilab.common.compat import enumerate
        self.assertEquals(list(enumerate([])), [])
        self.assertEquals(list(enumerate('abc')),
                          [(0, 'a'), (1, 'b'), (2, 'c')])

    def test_basic_set(self):
        from logilab.common.compat import set
        s = set('abc')
        self.assertEquals(len(s), 3)
        s.remove('a')
        self.assertEquals(len(s), 2)
        s.add('a')
        self.assertEquals(len(s), 3)
        s.add('a')
        self.assertEquals(len(s), 3)
        self.assertRaises(KeyError, s.remove, 'd')

    def test_basic_set(self):
        from logilab.common.compat import set
        s = set('abc')
        self.assertEquals(len(s), 3)
        s.remove('a')
        self.assertEquals(len(s), 2)
        s.add('a')
        self.assertEquals(len(s), 3)
        s.add('a')
        self.assertEquals(len(s), 3)
        self.assertRaises(KeyError, s.remove, 'd')
        self.assertRaises(TypeError, dict, [(s, 'foo')])


    def test_frozenset(self):
        from logilab.common.compat import frozenset
        s = frozenset('abc')
        self.assertEquals(len(s), 3)
        self.assertRaises(AttributeError, getattr, s, 'remove')
        self.assertRaises(AttributeError, getattr, s, 'add')
        d = {s : 'foo'} # frozenset should be hashable
        d[s] = 'bar'
        self.assertEquals(len(d), 1)
        self.assertEquals(d[s], 'bar')


class Py24CompatTC(CompatTCMixIn, TestCase):
    BUILTINS = ('reversed', 'sorted', 'set', 'frozenset',)

    def test_sorted(self):
        from logilab.common.compat import sorted
        l = [3, 1, 2, 5, 4]
        s = sorted(l)
        self.assertEquals(s, [1, 2, 3, 4, 5])
        self.assertEquals(l, [3, 1, 2, 5, 4])
        self.assertEquals(sorted('FeCBaD'), list('BCDFae'))
        self.assertEquals(sorted('FeCBaD', key=str.lower), list('aBCDeF'))
        self.assertEquals(sorted('FeCBaD', key=str.lower, reverse=True), list('FeDCBa'))
        def strcmp(s1, s2):
            return cmp(s1.lower(), s2.lower())
        self.assertEquals(sorted('FeCBaD', cmp=strcmp), list('aBCDeF'))


    def test_reversed(self):
        from logilab.common.compat import reversed
        l = range(5)
        r = reversed(l)
        self.assertEquals(r, [4, 3, 2, 1, 0])
        self.assertEquals(l, range(5))

    def test_set(self):
        from logilab.common.compat import set
        s1 = set(range(5))
        s2 = set(range(2, 6))
        self.assertEquals(len(s1), 5)
        self.assertEquals(s1 & s2, set([2, 3, 4]))
        self.assertEquals(s1 | s2, set(range(6)))



class _MaxFaker(object):
    def __init__(self, func):
        self.func = func
    def fake(self,*args,**kargs):
        if kargs:
            raise TypeError("max() takes no keyword argument")
        return self.func(*args)


class Py25CompatTC(CompatTCMixIn, TestCase):
    BUILTINS = ('any', 'all',)
    ALTERED_BUILTINS = {'max': _MaxFaker(max).fake}

    def test_any(self):
        from logilab.common.compat import any
        testdata = ([], (), '', 'abc', xrange(0, 10), xrange(0, -10, -1))
        self.assertEquals(any([]), False)
        self.assertEquals(any(()), False)
        self.assertEquals(any(''), False)
        self.assertEquals(any('abc'), True)
        self.assertEquals(any(xrange(10)), True)
        self.assertEquals(any(xrange(0, -10, -1)), True)
        # python2.5's any consumes iterables
        irange = iter(range(10))
        self.assertEquals(any(irange), True)
        self.assertEquals(irange.next(), 2)


    def test_all(self):
        from logilab.common.compat import all
        testdata = ([], (), '', 'abc', xrange(0, 10), xrange(0, -10, -1))
        self.assertEquals(all([]), True)
        self.assertEquals(all(()), True)
        self.assertEquals(all(''), True)
        self.assertEquals(all('abc'), True)
        self.assertEquals(all(xrange(10)), False)
        self.assertEquals(all(xrange(0, -10, -1)), False)
        # python2.5's all consumes iterables
        irange = iter(range(10))
        self.assertEquals(all(irange), False)
        self.assertEquals(irange.next(), 1)

    def test_max(self):
        from logilab.common.compat import max

        # old apy
        self.assertEquals(max("fdjkmhsgmdfhsg"),'s')
        self.assertEquals(max(1,43,12,45,1337,34,2), 1337)
        self.assertRaises(TypeError,max)
        self.assertRaises(TypeError,max,1)
        self.assertRaises(ValueError,max,[])
        self.assertRaises(TypeError,max,bob=None)

        # new apy
        self.assertEquals(max("shorter","longer",key=len),"shorter")
        self.assertEquals(max(((1,1),(2,3,5),(8,13,21)),key=len),(2,3,5))
        self.assertEquals(max(((1,1),(42,),(2,3,5),(8,13,21)),key=max),(42,))
        self.assertRaises(TypeError,max,key=None)
        self.assertRaises(TypeError,max,1,key=len)
        self.assertRaises(ValueError,max,[],key=max)
        self.assertRaises(TypeError,max,"shorter","longer",key=len,kathy=None)

if __name__ == '__main__':
    unittest_main()
