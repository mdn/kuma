import pytest
from django.test import TestCase

from kuma.core.utils import order_params, smart_int

from . import eq_


class SmartIntTestCase(TestCase):
    def test_sanity(self):
        eq_(10, smart_int('10'))
        eq_(10, smart_int('10.5'))

    def test_int(self):
        eq_(10, smart_int(10))

    def test_invalid_string(self):
        eq_(0, smart_int('invalid'))

    def test_empty_string(self):
        eq_(0, smart_int(''))

    def test_wrong_type(self):
        eq_(0, smart_int(None))
        eq_(10, smart_int([], 10))


@pytest.mark.parametrize(
    'original,expected',
    (('https://example.com', 'https://example.com'),
     ('http://example.com?foo=bar&foo=', 'http://example.com?foo=&foo=bar'),
     ('http://example.com?foo=bar&bar=baz', 'http://example.com?bar=baz&foo=bar'),
     ))
def test_order_params(original, expected):
    assert order_params(original) == expected
