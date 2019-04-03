from __future__ import unicode_literals

import pytest
from django.test import TestCase
from django.urls import get_urlconf, set_urlconf

from kuma.core.utils import order_params, override_urlconf, smart_int


class SmartIntTestCase(TestCase):
    def test_sanity(self):
        assert 10 == smart_int('10')
        assert 10 == smart_int('10.5')

    def test_int(self):
        assert 10 == smart_int(10)

    def test_invalid_string(self):
        assert 0 == smart_int('invalid')

    def test_empty_string(self):
        assert 0 == smart_int('')

    def test_wrong_type(self):
        assert 0 == smart_int(None)
        assert 10 == smart_int([], 10)


@pytest.mark.parametrize(
    'original,expected',
    (('https://example.com', 'https://example.com'),
     ('http://example.com?foo=bar&foo=', 'http://example.com?foo=&foo=bar'),
     ('http://example.com?foo=bar&bar=baz', 'http://example.com?bar=baz&foo=bar'),
     ))
def test_order_params(original, expected):
    assert order_params(original) == expected


@pytest.mark.parametrize(
    'current,override',
    ((None, None),
     (None, 'kuma.urls'),
     ('kuma.urls', None),
     ('kuma.urls', 'kuma.urls_beta'))
)
def test_override_urlconf(current, override):
    set_urlconf(current)
    assert get_urlconf() == current
    with override_urlconf(override):
        assert get_urlconf() == override
    assert get_urlconf() == current


@pytest.mark.parametrize(
    'current,override',
    ((None, None),
     (None, 'kuma.urls'),
     ('kuma.urls', None),
     ('kuma.urls', 'kuma.urls_beta'))
)
def test_override_urlconf_when_exception(current, override):
    set_urlconf(current)
    assert get_urlconf() == current
    try:
        with override_urlconf(override):
            assert get_urlconf() == override
            raise Exception('something went wrong')
    except Exception as err:
        assert str(err) == 'something went wrong'
    assert get_urlconf() == current
