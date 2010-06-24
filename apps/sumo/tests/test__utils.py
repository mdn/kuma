# -*- coding: utf-8 -*-

from nose.tools import eq_
from pyquery import PyQuery as pq

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
    fixtures = ['pages.json']

    def setUp(self):
        self.parser = WikiParser()

    def test_simple(self):
        """Simple internal link markup."""
        text = '[[Installing Firefox]]'
        link = pq(self.parser.parse(text))('a')
        eq_('/en-US/kb/Installing+Firefox', link.attr('href'))
        eq_('Installing Firefox', link.text())

    def test_link_hash(self):
        """Internal link with hash."""
        text = '[[Installing Firefox#section name]]'
        link = pq(self.parser.parse(text))('a')
        eq_('/en-US/kb/Installing+Firefox#section_name', link.attr('href'))
        eq_('Installing Firefox#section name', link.text())

    def test_hash_only(self):
        """Internal hash only."""
        text = '[[#section 3]]'
        link = pq(self.parser.parse(text))('a')
        eq_('#section_3', link.attr('href'))
        eq_('#section 3', link.text())

    def test_link_name(self):
        """Internal link with name."""
        text = '[[Installing Firefox|this name]]'
        link = pq(self.parser.parse(text))('a')
        eq_('/en-US/kb/Installing+Firefox', link.attr('href'))
        eq_('this name', link.text())

    def test_link_with_extra_pipe(self):
        text = '[[Installing Firefox|with|pipe]]'
        link = pq(self.parser.parse(text))('a')
        eq_('/en-US/kb/Installing+Firefox', link.attr('href'))
        eq_('with|pipe', link.text())

    def test_hash_name(self):
        """Internal hash with name."""
        text = '[[#section 3|this name]]'
        link = pq(self.parser.parse(text))('a')
        eq_('#section_3', link.attr('href'))
        eq_('this name', link.text())

    def test_link_hash_name(self):
        """Internal link with hash and name."""
        text = '[[Installing Firefox#section 3|this name]]'
        link = pq(self.parser.parse(text))('a')
        eq_('/en-US/kb/Installing+Firefox#section_3', link.attr('href'))
        eq_('this name', link.text())

    def test_simple_edit(self):
        """Simple link for inexistent page."""
        text = '[[A new page]]'
        link = pq(self.parser.parse(text))('a')
        eq_('/tiki-editpage.php?page=A+new+page', link.attr('href'))
        eq_('A new page', link.text())

    def test_link_edit_hash_name(self):
        """Internal link for inexistent page with hash and name."""
        text = '[[A new page#section 3|this name]]'
        link = pq(self.parser.parse(text))('a')
        eq_('/tiki-editpage.php?page=A+new+page#section_3', link.attr('href'))
        eq_('this name', link.text())
