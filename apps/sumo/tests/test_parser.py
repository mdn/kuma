# -*- coding: utf-8 -*-

from nose.tools import eq_
from pyquery import PyQuery as pq

from django.test import TestCase

import settings
from sumo.parser import WikiParser

parser = WikiParser()


def pq_link(text):
    return pq(parser.parse(text))('a')


class TestWikiParser(TestCase):
    fixtures = ['pages.json']

    def test_image_path_sanity(self):
        """Image URLs are prefixed with the upload path."""
        eq_(settings.WIKI_UPLOAD_URL + 'file.png',
            parser._getImagePath('file.png'))

    def test_image_path_special_chars(self):
        """Image URLs with Unicode are prefixed with the upload path."""
        eq_(settings.WIKI_UPLOAD_URL + 'parl%C3%A9%20Fran%C3%A7ais.png',
            parser._getImagePath(u'parl\u00e9 Fran\u00e7ais.png'))

    def test_image_params_page(self):
        """_buildImageParams handles wiki pages."""
        items = ['page=Installing Firefox']
        params = parser._buildImageParams(items)
        eq_('/en-US/kb/Installing+Firefox', params['link'])

    def test_image_params_link(self):
        """_buildImageParams handles external links."""
        items = ['link=http://example.com']
        params = parser._buildImageParams(items)
        eq_('http://example.com', params['link'])

    def test_image_params_page_link(self):
        """_buildImageParams - wiki page overrides link."""
        items = ['page=Installing Firefox', 'link=http://example.com']
        params = parser._buildImageParams(items)
        eq_('/en-US/kb/Installing+Firefox', params['link'])

    def test_get_wiki_link(self):
        """Wiki links are properly built for existing pages."""
        eq_('/en-US/kb/Installing+Firefox',
            parser._getWikiLink('Installing Firefox'))

    def test_get_wiki_link_create(self):
        """Wiki links are properly built for inexisting pages."""
        eq_(settings.WIKI_CREATE_URL % 'Inexistent+Page',
            parser._getWikiLink('Inexistent Page'))


class TestWikiInternalLinks(TestCase):
    fixtures = ['pages.json']

    def test_simple(self):
        """Simple internal link markup."""
        link = pq_link('[[Installing Firefox]]')
        eq_('/en-US/kb/Installing+Firefox', link.attr('href'))
        eq_('Installing Firefox', link.text())

    def test_simple_markup(self):
        text = '[[Installing Firefox]]'
        eq_('<p><a href="/en-US/kb/Installing+Firefox">' +
            'Installing Firefox</a>\n</p>',
            parser.parse(text))

    def test_link_hash(self):
        """Internal link with hash."""
        link = pq_link('[[Installing Firefox#section name]]')
        eq_('/en-US/kb/Installing+Firefox#section_name', link.attr('href'))
        eq_('Installing Firefox#section name', link.text())

    def test_link_hash_markup(self):
        """Internal link with hash."""
        text = '[[Installing Firefox#section name]]'
        eq_('<p><a href="/en-US/kb/Installing+Firefox#section_name">' +
                'Installing Firefox#section name</a>\n</p>',
            parser.parse(text))

    def test_hash_only(self):
        """Internal hash only."""
        link = pq_link('[[#section 3]]')
        eq_('#section_3', link.attr('href'))
        eq_('#section 3', link.text())

    def test_link_name(self):
        """Internal link with name."""
        link = pq_link('[[Installing Firefox|this name]]')
        eq_('/en-US/kb/Installing+Firefox', link.attr('href'))
        eq_('this name', link.text())

    def test_link_with_extra_pipe(self):
        link = pq_link('[[Installing Firefox|with|pipe]]')
        eq_('/en-US/kb/Installing+Firefox', link.attr('href'))
        eq_('with|pipe', link.text())

    def test_hash_name(self):
        """Internal hash with name."""
        link = pq_link('[[#section 3|this name]]')
        eq_('#section_3', link.attr('href'))
        eq_('this name', link.text())

    def test_link_hash_name(self):
        """Internal link with hash and name."""
        link = pq_link('[[Installing Firefox#section 3|this name]]')
        eq_('/en-US/kb/Installing+Firefox#section_3', link.attr('href'))
        eq_('this name', link.text())

    def test_link_hash_name_markup(self):
        """Internal link with hash and name."""
        text = '[[Installing Firefox#section 3|this name]]'
        eq_('<p><a href="/en-US/kb/Installing+Firefox#section_3">' +
            'this name</a>\n</p>', parser.parse(text))

    def test_simple_edit(self):
        """Simple link for inexistent page."""
        link = pq_link('[[A new page]]')
        eq_('/tiki-editpage.php?page=A+new+page', link.attr('href'))
        eq_('A new page', link.text())

    def test_link_edit_hash_name(self):
        """Internal link for inexistent page with hash and name."""
        link = pq_link('[[A new page#section 3|this name]]')
        eq_('/tiki-editpage.php?page=A+new+page#section_3', link.attr('href'))
        eq_('this name', link.text())


def pq_img(text, selector='div.img'):
    doc = pq(parser.parse(text))
    return doc(selector)


class TestWikiImageTags(TestCase):
    fixtures = ['pages.json']

    def test_empty(self):
        """Empty image tag markup does not change."""
        img = pq_img('[[Image:]]', 'img')
        eq_('', img.attr('alt'))
        eq_('/img/wiki_up/', img.attr('src'))

    def test_simple(self):
        """Simple image tag markup."""
        img = pq_img('[[Image:file.png]]', 'img')
        eq_('file.png', img.attr('alt'))
        eq_('/img/wiki_up/file.png', img.attr('src'))

    def test_caption(self):
        """Give the image a caption."""
        img_div = pq_img('[[Image:img file.png|my caption]]')
        img = img_div('img')
        caption = img_div.text()

        eq_('/img/wiki_up/img%20file.png', img.attr('src'))
        eq_('my caption', img.attr('alt'))
        eq_('my caption', caption)

    def test_page_link(self):
        """Link to a wiki page."""
        img_a = pq_img('[[Image:file.png|page=Installing Firefox]]', 'a.img')
        img = img_a('img')
        caption = img_a.text()

        eq_('file.png', img.attr('alt'))
        eq_('file.png', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('/en-US/kb/Installing+Firefox', img_a.attr('href'))

    def test_page_link_edit(self):
        """Link to an inexistent wiki page."""
        img_a = pq_img('[[Image:file.png|page=Article List]]', 'a.img')
        img = img_a('img')
        caption = img_a.text()

        eq_('file.png', img.attr('alt'))
        eq_('file.png', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('/tiki-editpage.php?page=Article+List', img_a.attr('href'))

    def test_page_link_caption(self):
        """Link to a wiki page with caption."""
        img_a = pq_img('[[Image:file.png|page=Article List|my caption]]',
                       'a.img')
        img = img_a('img')
        caption = img_a.text()

        eq_('my caption', img.attr('alt'))
        eq_('my caption', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('/tiki-editpage.php?page=Article+List', img_a.attr('href'))

    def test_link(self):
        """Link to an external page."""
        img_a = pq_img('[[Image:file.png|link=http://example.com]]', 'a.img')
        img = img_a('img')
        caption = img_a.text()

        eq_('file.png', img.attr('alt'))
        eq_('file.png', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('http://example.com', img_a.attr('href'))

    def test_link_caption(self):
        """Link to an external page with caption."""
        img_a = pq_img('[[Image:file.png|link=http://example.com|my caption]]',
                       'a.img')
        img = img_a('img')
        caption = img_a.text()

        eq_('my caption', img.attr('alt'))
        eq_('my caption', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('http://example.com', img_a.attr('href'))
