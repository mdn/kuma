import os
import sys
import unittest
from nose.plugins.attrib import AttributeSelector
from nose.plugins import PluginTester

support = os.path.join(os.path.dirname(__file__), 'support')

compat_24 = sys.version_info >= (2, 4)

class AttributePluginTester(PluginTester, unittest.TestCase):
    plugins = [AttributeSelector()]
    suitepath = os.path.join(support, 'att')
    # Some cases need -a to activate and others need -A, so
    # let's treat -v as the activate argument and let individual
    # cases specify their -a arguments as part of args
    activate = '-v'

    def runTest(self):
        print '*' * 70
        print str(self.output)
        print '*' * 70
        self.verify()

    def verify(self):
        raise NotImplementedError()


class TestSimpleAttribute(AttributePluginTester):
    args = ["-a", "a"]

    def verify(self):
        assert 'test_attr.test_one ... ok' in self.output
        assert 'test_attr.test_two ... ok' in self.output
        assert 'TestClass.test_class_one ... ok' in self.output
        assert 'TestClass.test_class_two ... ok' in self.output
        assert 'TestClass.test_class_three ... ok' in self.output
        assert 'test_three' not in self.output
        assert 'test_case_two' not in self.output
        assert 'test_case_one' not in self.output
        assert 'test_case_three' not in self.output
        assert 'TestAttrClass.test_one ... ok' in self.output
        assert 'TestAttrClass.test_two ... ok' in self.output
        assert 'TestAttrClass.ends_with_test ... ok' in self.output


class TestNotSimpleAttribute(AttributePluginTester):
    args = ["-a", "!a"]

    def verify(self):
        assert 'test_attr.test_one ... ok' not in self.output
        assert 'test_attr.test_two ... ok' not in self.output
        assert 'TestClass.test_class_one ... ok' not in self.output
        assert 'TestClass.test_class_two ... ok' not in self.output
        assert 'TestClass.test_class_three ... ok' not in self.output
        assert 'test_three' in self.output
        assert 'test_case_two' in self.output
        assert 'test_case_one' in self.output
        assert 'test_case_three' in self.output


class TestAttributeValue(AttributePluginTester):
    args = ["-a", "b=2"]

    def verify(self):
        assert 'test_attr.test_one ... ok' not in self.output
        assert 'test_attr.test_two ... ok' not in self.output
        assert 'test_attr.test_three ... ok' not in self.output
        assert 'TestClass.test_class_one ... ok' not in self.output
        assert 'TestClass.test_class_two ... ok' in self.output
        assert 'TestClass.test_class_three ... ok' not in self.output
        assert 'test_case_two' in self.output
        assert 'test_case_one' in self.output
        assert 'test_case_three' in self.output


class TestAttributeArray(AttributePluginTester):
    args = ["-a", "d=2"]

    def verify(self):
        assert 'test_attr.test_one ... ok' in self.output
        assert 'test_attr.test_two ... ok' in self.output
        assert 'test_attr.test_three ... ok' not in self.output
        assert 'TestClass.test_class_one ... ok' not in self.output
        assert 'TestClass.test_class_two ... ok' not in self.output
        assert 'TestClass.test_class_three ... ok' not in self.output
        assert 'test_case_two' not in self.output
        assert 'test_case_one' not in self.output
        assert 'test_case_three' not in self.output


class TestAttributeArrayAnd(AttributePluginTester):
    args = ["-a", "d=1,d=2"]

    def verify(self):
        assert 'test_attr.test_one ... ok' in self.output
        assert 'test_attr.test_two ... ok' not in self.output
        assert 'test_attr.test_three ... ok' not in self.output
        assert 'TestClass.test_class_one ... ok' not in self.output
        assert 'TestClass.test_class_two ... ok' not in self.output
        assert 'TestClass.test_class_three ... ok' not in self.output
        assert 'test_case_two' not in self.output
        assert 'test_case_one' not in self.output
        assert 'test_case_three' not in self.output


class TestAttributeArrayOr(AttributePluginTester):
    args = ["-a", "d=1", "-a", "d=2"]

    def verify(self):
        assert 'test_attr.test_one ... ok' in self.output
        assert 'test_attr.test_two ... ok' in self.output
        assert 'test_attr.test_three ... ok' in self.output
        assert 'TestClass.test_class_one ... ok' not in self.output
        assert 'TestClass.test_class_two ... ok' not in self.output
        assert 'TestClass.test_class_three ... ok' not in self.output
        assert 'test_case_two' not in self.output
        assert 'test_case_one' not in self.output
        assert 'test_case_three' not in self.output
        

class TestInheritance(AttributePluginTester):
    # Issue #412
    args = ["-a", "from_super"]

    def verify(self):
        assert 'TestSubclass.test_method ... ok' in self.output
        assert 'TestAttrSubClass.test_sub_three ... ok' in self.output
        assert 'TestAttrSubClass.test_one ... ok' in self.output
        assert 'TestAttrSubClass.added_later_test ... ok' in self.output
        assert 'test_two' not in self.output
        assert 'test_case_one' not in self.output
        assert 'test_case_three' not in self.output


class TestStatic(AttributePluginTester):
    # Issue #411
    args = ["-a", "with_static"]
    suitepath = os.path.join(support, 'att', 'test_attr.py:Static')

    def verify(self):
        assert 'Static.test_with_static ... ok' in self.output
        assert 'test_case_two' not in self.output
        assert 'test_case_one' not in self.output
        assert 'test_case_three' not in self.output


class TestClassAndMethodAttrs(AttributePluginTester):
    # Issue #324
    args = ["-a", "meth_attr=method,cls_attr=class"]

    def verify(self):
        assert '(test_attr.TestClassAndMethodAttrs) ... ok' in self.output
        assert 'test_case_two' not in self.output
        assert 'test_case_one' not in self.output
        assert 'test_case_three' not in self.output


if compat_24:
    class TestAttributeEval(AttributePluginTester):
        args = ["-A", "c>20"]

        def verify(self):
            assert 'test_attr.test_one ... ok' not in self.output
            assert 'test_attr.test_two ... ok' not in self.output
            assert 'test_attr.test_three ... ok' not in self.output
            assert 'TestClass.test_class_one ... ok' not in self.output
            assert 'TestClass.test_class_two ... ok' not in self.output
            assert 'TestClass.test_class_three ... ok' not in self.output
            assert 'test_case_two' in self.output
            assert 'test_case_one' not in self.output
            assert 'test_case_three' not in self.output


# Avoid trying to run base class as tests
del AttributePluginTester

if __name__ == '__main__':
    #import logging
    #logging.basicConfig(level=logging.DEBUG)
    unittest.main()
