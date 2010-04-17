# -*- coding: utf-8 -*-

from nose.tools import eq_

from sumo.utils import urlencode


def test_urlencode():
    """Our urlencode is UTF-8-safe."""
    items = [('q', u'Fran\xc3\xa7ais')]
    eq_('q=Fran%C3%A7ais', urlencode(items))


def test_urlencode_int():
    """urlencode() should not try to encode integers."""
    items = [('q', 't'), ('a', 1)]
    eq_('q=t&a=1', urlencode(items))
