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

    def test_image_params_align(self):
        """Align valid options."""
        align_vals = ('none', 'left', 'center', 'right')
        for align in align_vals:
            items = ['align=' + align]
            params = parser._buildImageParams(items)
            eq_(align, params['align'])

    def test_image_params_align_invalid(self):
        """Align invalid options."""
        items = ['align=zzz']
        params = parser._buildImageParams(items)
        assert not 'align' in params, 'Align is present in params'

    def test_image_params_valign(self):
        """Vertical align valid options."""
        valign_vals = ('baseline', 'sub', 'super', 'top', 'text-top',
                       'middle', 'bottom', 'text-bottom')
        for valign in valign_vals:
            items = ['valign=' + valign]
            params = parser._buildImageParams(items)
            eq_(valign, params['valign'])

    def test_image_params_valign_invalid(self):
        """Vertical align invalid options."""
        items = ['valign=zzz']
        params = parser._buildImageParams(items)
        assert not 'valign' in params, 'Vertical align is present in params'

    def test_image_params_alt(self):
        """Image alt override."""
        items = ['alt=some alternative text']
        params = parser._buildImageParams(items)
        eq_('some alternative text', params['alt'])

    def test_image_params_frameless(self):
        """Frameless image."""
        items = ['frameless']
        params = parser._buildImageParams(items)
        eq_(True, params['frameless'])

    def test_image_params_width_height(self):
        """Image width."""
        items = ['width=10', 'height=20']
        params = parser._buildImageParams(items)
        eq_('10', params['width'])
        eq_('20', params['height'])

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
        eq_('<p><a href="/en-US/kb/Installing+Firefox" rel="nofollow">' +
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
        eq_('<p><a href="/en-US/kb/Installing+Firefox#section_name"' +
                ' rel="nofollow">Installing Firefox#section name</a>\n</p>',
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
        eq_('<p><a href="/en-US/kb/Installing+Firefox#section_3"' +
            ' rel="nofollow">this name</a>\n</p>', parser.parse(text))

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
        img_div = pq_img('[[Image:file.png|page=Installing Firefox]]')
        img_a = img_div('a')
        img = img_a('img')
        caption = img_div.text()

        eq_('file.png', img.attr('alt'))
        eq_('file.png', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('/en-US/kb/Installing+Firefox', img_a.attr('href'))

    def test_page_link_edit(self):
        """Link to an inexistent wiki page."""
        img_div = pq_img('[[Image:file.png|page=Article List]]')
        img_a = img_div('a')
        img = img_a('img')
        caption = img_div.text()

        eq_('file.png', img.attr('alt'))
        eq_('file.png', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('/tiki-editpage.php?page=Article+List', img_a.attr('href'))

    def test_page_link_caption(self):
        """Link to a wiki page with caption."""
        img_div = pq_img('[[Image:file.png|page=Article List|my caption]]')
        img_a = img_div('a')
        img = img_a('img')
        caption = img_div.text()

        eq_('my caption', img.attr('alt'))
        eq_('my caption', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('/tiki-editpage.php?page=Article+List', img_a.attr('href'))

    def test_link(self):
        """Link to an external page."""
        img_div = pq_img('[[Image:file.png|link=http://example.com]]')
        img_a = img_div('a')
        img = img_a('img')
        caption = img_div.text()

        eq_('file.png', img.attr('alt'))
        eq_('file.png', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('http://example.com', img_a.attr('href'))

    def test_link_caption(self):
        """Link to an external page with caption."""
        img_div = pq_img('[[Image:file.png|link=http://example.com|caption]]')
        img_a = img_div('a')
        img = img_div('img')
        caption = img_div.text()

        eq_('caption', img.attr('alt'))
        eq_('caption', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('http://example.com', img_a.attr('href'))

    def test_link_align(self):
        """Link with align."""
        img_div = pq_img('[[Image:file.png|link=http://site.com|align=left]]')
        eq_('img align-left', img_div.attr('class'))

    def test_link_align_invalid(self):
        """Link with invalid align."""
        img_div = pq_img('[[Image:file.png|link=http://example.ro|align=inv]]')
        eq_('img', img_div.attr('class'))

    def test_link_valign(self):
        """Link with valign."""
        img = pq_img(
            '[[Image:file.png|link=http://example.com|valign=top]]', 'img')
        eq_('vertical-align: top;', img.attr('style'))

    def test_link_valign_invalid(self):
        """Link with invalid valign."""
        img = pq_img(
            '[[Image:file.png|link=http://example.com|valign=off]]', 'img')
        eq_(None, img.attr('style'))

    def test_alt(self):
        """Image alt attribute is overriden but caption is not."""
        img_div = pq_img('[[Image:img.png|alt=my alt|my caption]]')
        img = img_div('img')
        caption = img_div.text()

        eq_('my alt', img.attr('alt'))
        eq_('my caption', caption)

    def test_alt_empty(self):
        """Image alt attribute can be empty."""
        img = pq_img('[[Image:img.png|alt=|my caption]]', 'img')

        eq_('', img.attr('alt'))

    def test_alt_unsafe(self):
        """Potentially unsafe alt content is escaped."""
        unsafe_vals = (
            ('an"<script>alert()</script>',
             'an&quot;&amp;lt;script&amp;gt;alert()&amp;lt;/script&amp;gt;'),
            ("an'<script>alert()</script>",
             "an'&amp;lt;script&amp;gt;alert()&amp;lt;/script&amp;gt;"),
            ('single\'"double',
             "single'&quot;double"),
        )
        for alt_sent, alt_expected in unsafe_vals:
            img_div = pq_img('[[Image:img.png|alt=' + alt_sent + ']]')
            img = img_div('img')

            is_true = str(img).startswith('<img alt="' + alt_expected + '"')
            assert is_true, ('Expected "%s", sent "%s"' %
                             (alt_expected, alt_sent))

    def test_width(self):
        """Image width attribute set."""
        img_div = pq_img('[[Image:img.png|width=10]]')
        img = img_div('img')

        eq_('10', img.attr('width'))

    def test_width_invalid(self):
        """Invalid image width attribute set to auto."""
        img_div = pq_img('[[Image:img.png|width=invalid]]')
        img = img_div('img')

        eq_(None, img.attr('width'))

    def test_height(self):
        """Image height attribute set."""
        img_div = pq_img('[[Image:img.png|height=10]]')
        img = img_div('img')

        eq_('10', img.attr('height'))

    def test_height_invalid(self):
        """Invalid image height attribute set to auto."""
        img_div = pq_img('[[Image:img.png|height=invalid]]')
        img = img_div('img')

        eq_(None, img.attr('height'))

    def test_frameless(self):
        """Image container has frameless class if specified."""
        img = pq_img('[[Image:img.png|frameless|caption]]', 'img')
        eq_('frameless', img.attr('class'))
        eq_('caption', img.attr('alt'))
        eq_('/img/wiki_up/img.png', img.attr('src'))

    def test_frameless_link(self):
        """Image container has frameless class and link if specified."""
        img_a = pq_img('[[Image:img.png|frameless|page=Installing Firefox]]',
                       'a')
        img = img_a('img')
        eq_('frameless', img.attr('class'))
        eq_('/en-US/kb/Installing+Firefox', img_a.attr('href'))
