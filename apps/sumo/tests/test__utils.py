# -*- coding: utf-8 -*-

from nose.tools import eq_

from django.test import TestCase

from sumo.utils import urlencode, WikiParser


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


class TestWikiInternalLinks(TestCase):

    def setUp(self):
        self.parser = WikiParser()

    def test_simple(self):
        """Simple internal link markup."""
        text = '[[Internal link]]'
        eq_('<p><a href="/kb/Internal+link">Internal link</a>\n</p>',
            self.parser.parse(text))

    def test_link_hash(self):
        """Internal link with hash."""
        text = '[[Internal link#section name]]'
        eq_('<p><a href="/kb/Internal+link#section_name">' +
                'Internal link#section name</a>\n</p>',
            self.parser.parse(text))

    def test_hash_only(self):
        """Internal hash only."""
        text = '[[#section 3]]'
        eq_('<p><a href="#section_3">#section 3</a>\n</p>',
            self.parser.parse(text))

    def test_link_name(self):
        """Internal link with name."""
        text = '[[Internal link|this name]]'
        eq_('<p><a href="/kb/Internal+link">this name</a>\n</p>',
            self.parser.parse(text))

    def test_link_with_extra_pipe(self):
        text = '[[Link|with|pipe]]'
        eq_('<p><a href="/kb/Link">with|pipe</a>\n</p>',
            self.parser.parse(text))

    def test_hash_name(self):
        """Internal hash with name."""
        text = '[[#section 3|this name]]'
        eq_('<p><a href="#section_3">this name</a>\n</p>',
            self.parser.parse(text))

    def test_link_hash_name(self):
        """Internal link with hash and name."""
        text = '[[Internal link#section 3|this name]]'
        eq_('<p><a href="/kb/Internal+link#section_3">this name</a>\n</p>',
            self.parser.parse(text))
