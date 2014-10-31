from nose.plugins.attrib import attr
import unittest

def test_one():
    pass
test_one.a = 1
test_one.d = [1, 2]


def test_two():
    pass
test_two.a = 1
test_two.c = 20
test_two.d = [2, 3]

def test_three():
    pass
test_three.b = 1
test_three.d = [1, 3]

class TestClass:
    a = 1
    def test_class_one(self):
        pass

    def test_class_two(self):
        pass
    test_class_two.b = 2

    def test_class_three(self):
        pass

    
class Something(unittest.TestCase):
    b = 2
    def test_case_one(self):
        pass
    
    def test_case_two(self):
        pass
    test_case_two.c = 50
    
    def test_case_three(self):
        pass


class Superclass:
    def test_method(self):
        pass
    test_method.from_super = True

class TestSubclass(Superclass):
    pass


class Static:
    def test_with_static(self):
        pass
    test_with_static.with_static = True

    def static(self):
        pass
    static = staticmethod(static)


class TestClassAndMethodAttrs(unittest.TestCase):
    def test_method(self):
        pass
    test_method.meth_attr = 'method'
TestClassAndMethodAttrs.cls_attr = 'class'


class TestAttrClass:
    from_super = True

    def ends_with_test(self):
        pass

    def test_one(self):
        pass

    def test_two(self):
        pass
    test_two.from_super = False

TestAttrClass = attr('a')(TestAttrClass)


class TestAttrSubClass(TestAttrClass):
    def test_sub_three(self):
        pass

def added_later_test(self):
    pass

TestAttrSubClass.added_later_test = added_later_test
