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
from __future__ import generators

from data.module import YO, YOUPI
import data

class Specialization(YOUPI, YO): pass

class Metaclass(type): pass

class Interface: pass

class MyIFace(Interface): pass

class AnotherIFace(Interface): pass

class MyException(Exception): pass
class MyError(MyException): pass

class AbstractClass(object):

    def to_override(self, whatever):
        raise NotImplementedError()

    def return_something(self, param):
        if param:
            return 'toto'
        return
    
class Concrete0:
    __implements__ = MyIFace
class Concrete1:
    __implements__ = MyIFace, AnotherIFace
class Concrete2:
    __implements__ = (MyIFace,
                      AnotherIFace)
class Concrete23(Concrete1): pass

del YO.member

del YO
[SYN1, SYN2] = Concrete0, Concrete1
assert `1`
b = 1 | 2 & 3 ^ 8
bb = 1 | two | 6
ccc = one & two & three
dddd = x ^ o ^ r
exec 'c = 3'
exec 'c = 3' in {}, {}

def raise_string(a=2, *args, **kwargs):
    raise 'pas glop'
    raise Exception, 'yo'
    yield 'coucou'
    
a = b + 2
c = b * 2
c = b / 2
c = b // 2
c = b - 2
c = b % 2
c = b ** 2
c = b << 2
c = b >> 2
c = ~b

c = not b

d = [c]
e = d[:]
e = d[a:b:c]

raise_string(*args, **kwargs)

print >> stream, 'bonjour'
print >> stream, 'salut',


def make_class(any, base=data.module.YO, *args, **kwargs):
    """check base is correctly resolved to Concrete0"""
    class Aaaa(base):
        """dynamic class"""
    return Aaaa

from os.path import abspath

import os as myos


class A:
    pass

class A(A):
    pass
