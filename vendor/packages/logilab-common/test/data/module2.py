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
