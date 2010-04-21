# -*- coding: utf-8 -*-

from nose.tools import eq_

from sumo.utils import urlencode


def test_urlencode():
    """Our urlencode is Unicode-safe."""
    items = [('q', u'Fran\xe7ais')]
    eq_('q=Fran%C3%A7ais', urlencode(items))

    items = [('q', u'は「着')]
    eq_('q=%E3%81%AF%E3%80%8C%E7%9D%80', urlencode(items))


def test_urlencode_int():
    """urlencode() should not choke on integers."""
    items = [('q', 't'), ('a', 1)]
    eq_('q=t&a=1', urlencode(items))
