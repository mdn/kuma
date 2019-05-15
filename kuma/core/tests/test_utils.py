# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from django.urls import get_urlconf, set_urlconf
from django.utils.encoding import force_bytes

from kuma.core.utils import (
    order_params,
    override_urlconf,
    safer_pyquery,
    smart_int
)


def test_smart_int():
    # Sanity check
    assert 10 == smart_int('10')
    assert 10 == smart_int('10.5')

    # Test int
    assert 10 == smart_int(10)

    # Invalid string
    assert 0 == smart_int('invalid')

    # Empty string
    assert 0 == smart_int('')

    # Wrong type
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


def test_safer_pyquery(mock_requests):
    # Note! the `mock_requests` fixture is just there to make absolutely
    # sure the whole test doesn't ever use requests.get().
    # My not setting up expectations, and if it got used,
    # these tests would raise a `NoMockAddress` exception.

    parsed = safer_pyquery('https://www.peterbe.com')
    assert parsed.outer_html() == '<p>https://www.peterbe.com</p>'

    # Note! Since this file uses `__future__.unicode_literals` the only
    # way to produce a byte string is to use force_bytes.
    # Byte strings in should continue to work.
    parsed = safer_pyquery(force_bytes('https://www.peterbe.com'))
    assert parsed.outer_html() == '<p>https://www.peterbe.com</p>'

    # Non-ascii as Unicode
    parsed = safer_pyquery('https://www.peterbe.com/ë')

    parsed = safer_pyquery("""<!doctype html>
    <html>
        <body>
            <b>Bold!</b>
        </body>
    </html>
    """)
    assert parsed('b').text() == 'Bold!'
    parsed = safer_pyquery("""
    <html>
        <body>
            <a href="https://www.peterbe.com">URL</a>
        </body>
    </html>
    """)
    assert parsed('a[href]').text() == 'URL'
