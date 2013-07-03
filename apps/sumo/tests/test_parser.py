# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial

from django.conf import settings

from nose.tools import eq_
from pyquery import PyQuery as pq

from gallery.tests import image
from sumo.parser import (WikiParser, build_hook_params, _get_wiki_link,
                         get_object_fallback, IMAGE_PARAMS, IMAGE_PARAM_VALUES)
from sumo.tests import TestCase
from wiki.models import Document
from wiki.tests import document, revision


def pq_link(p, text):
    return pq(p.parse(text))('a')


def pq_img(p, text, selector='img', locale=settings.WIKI_DEFAULT_LANGUAGE):
    doc = pq(p.parse(text, locale=locale))
    return doc(selector)


def doc_rev_parser(content, title='Installing Firefox', parser_cls=WikiParser):
    p = parser_cls()
    d = document(title=title)
    d.save()
    r = revision(document=d, content=content, is_approved=True)
    r.save()
    return (d, r, p)


build_hook_params_default = partial(build_hook_params,
                                    locale=settings.WIKI_DEFAULT_LANGUAGE,
                                    allowed_params=IMAGE_PARAMS,
                                    allowed_param_values=IMAGE_PARAM_VALUES)


class GetObjectFallbackTests(TestCase):
    fixtures = ['users.json']

    def test_empty(self):
        """get_object_fallback returns message when no objects."""
        # English does not exist
        obj = get_object_fallback(Document, 'A doc', 'en-US', '!')
        eq_('!', obj)

    def test_english(self):
        # Create the English document
        d = document(title='A doc')
        d.save()
        # Now it exists
        obj = get_object_fallback(Document, 'A doc', 'en-US', '!')
        eq_(d, obj)

    def test_from_french(self):
        # Create the English document
        d = document(title='A doc')
        d.save()
        # Returns English document for French
        obj = get_object_fallback(Document, 'A doc', 'fr', '!')
        eq_(d, obj)

    def test_french(self):
        # Create English parent document
        en_d = document()
        en_d.save()
        en_r = revision(document=en_d, is_approved=True)
        en_r.save()

        # Create the French document
        fr_d = document(parent=en_d, title='A doc', locale='fr')
        fr_d.save()
        obj = get_object_fallback(Document, 'A doc', 'fr', '!')
        eq_(fr_d, obj)

        # Also works when English exists
        d = document(title='A doc')
        d.save()
        obj = get_object_fallback(Document, 'A doc', 'fr', '!')
        eq_(fr_d, obj)

    def test_translated(self):
        """If a localization of the English fallback exists, use it."""

        en_d = document(title='A doc')
        en_d.save()
        en_r = revision(document=en_d, is_approved=True)
        en_r.save()

        fr_d = document(parent=en_d, title='Une doc', locale='fr')
        fr_d.save()

        # Without an approved revision, the en-US doc should be returned.
        obj = get_object_fallback(Document, 'A doc', 'fr')
        eq_(en_d, obj)

        # Approve a revision, then fr doc should be returned.
        fr_r = revision(document=fr_d, is_approved=True)
        fr_r.save()
        obj = get_object_fallback(Document, 'A doc', 'fr')
        eq_(fr_d, obj)

    def test_redirect(self):
        """Assert get_object_fallback follows wiki redirects."""
        target_rev = revision(
            document=document(title='target', save=True),
            is_approved=True,
            save=True)
        translated_target_rev = revision(
            document=document(parent=target_rev.document, locale='de',
                              save=True),
            is_approved=True,
            save=True)
        revision(
            document=document(title='redirect', save=True),
            content='REDIRECT [[target]]',
            is_approved=True).save()

        eq_(translated_target_rev.document,
            get_object_fallback(Document, 'redirect', 'de'))

    def test_redirect_translations_only(self):
        """Make sure get_object_fallback doesn't follow redirects when working
        purely in the default language.

        That would make it hard to navigate to redirects (to edit them, for
        example).

        """
        revision(document=document(title='target', save=True),
                              content='O hai.',
                              is_approved=True).save()
        redirect_rev = revision(document=document(title='redirect', save=True),
                                content='REDIRECT [[target]]',
                                is_approved=True,
                                save=True)
        eq_(redirect_rev.document,
            get_object_fallback(Document, 'redirect',
                                redirect_rev.document.locale))


class TestWikiParser(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.d, self.r, self.p = doc_rev_parser(
            'Test content', 'Installing Firefox')

    def test_image_params_page(self):
        """build_hook_params handles wiki pages."""
        _, params = build_hook_params_default('t|page=Installing Firefox')
        eq_('/en-US/kb/installing-firefox', params['link'])
        assert params['found']

    def test_image_params_link(self):
        """_build_image_params handles external links."""
        _, params = build_hook_params_default('t|link=http://example.com')
        eq_('http://example.com', params['link'])

    def test_image_params_page_link(self):
        """_build_image_params - wiki page overrides link."""
        text = 't|page=Installing Firefox|link=http://example.com'
        _, params = build_hook_params_default(text)
        eq_('/en-US/kb/installing-firefox', params['link'])

    def test_image_params_align(self):
        """Align valid options."""
        align_vals = ('none', 'left', 'center', 'right')
        for align in align_vals:
            _, params = build_hook_params_default('test.jpg|align=' + align)
            eq_(align, params['align'])

    def test_image_params_align_invalid(self):
        """Align invalid options."""
        _, params = build_hook_params_default('align=zzz')
        assert not 'align' in params, 'Align is present in params'

    def test_image_params_valign(self):
        """Vertical align valid options."""
        valign_vals = ('baseline', 'sub', 'super', 'top', 'text-top',
                       'middle', 'bottom', 'text-bottom')
        for valign in valign_vals:
            _, params = build_hook_params_default('title|valign=' + valign)
            eq_(valign, params['valign'])

    def test_image_params_valign_invalid(self):
        """Vertical align invalid options."""
        _, params = build_hook_params_default('valign=zzz')
        assert not 'valign' in params, 'Vertical align is present in params'

    def test_image_params_alt(self):
        """Image alt override."""
        _, params = build_hook_params_default('t|alt=some alternative text')
        eq_('some alternative text', params['alt'])

    def test_image_params_frame(self):
        """Framed image."""
        _, params = build_hook_params_default('title|frame')
        assert params['frame']

    def test_image_params_width_height(self):
        """Image width."""
        _, params = build_hook_params_default('t|width=10|height=20')
        eq_('10', params['width'])
        eq_('20', params['height'])

    def test_get_wiki_link(self):
        """Wiki links are properly built for existing pages."""
        eq_({'found': True, 'url': '/en-US/kb/installing-firefox',
             'text': 'Installing Firefox'},
            _get_wiki_link('Installing Firefox',
                         locale=settings.WIKI_DEFAULT_LANGUAGE))

    def test_showfor(self):
        """<showfor> tags should be escaped, not obeyed."""
        eq_('<p>&lt;showfor&gt;smoo&lt;/showfor&gt;</p>',
            self.p.parse('<showfor>smoo</showfor>').replace('\n', ''))


class TestWikiInternalLinks(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.d, self.r, self.p = doc_rev_parser(
            'Test content', 'Installing Firefox')

    def test_simple(self):
        """Simple internal link markup."""
        link = pq_link(self.p, '[[Installing Firefox]]')
        eq_('/en-US/kb/installing-firefox', link.attr('href'))
        eq_('Installing Firefox', link.text())
        assert not link.hasClass('new')

    def test_simple_markup(self):
        text = '[[Installing Firefox]]'
        eq_('<p><a href="/en-US/kb/installing-firefox">' +
            'Installing Firefox</a></p>',
            self.p.parse(text).replace('\n', ''))

    def test_link_hash(self):
        """Internal link with hash."""
        link = pq_link(self.p, '[[Installing Firefox#section name]]')
        eq_('/en-US/kb/installing-firefox#section_name', link.attr('href'))
        eq_('Installing Firefox', link.text())

    def test_link_hash_text(self):
        """Internal link with hash and text."""
        link = pq_link(self.p, '[[Installing Firefox#section name|section]]')
        eq_('/en-US/kb/installing-firefox#section_name', link.attr('href'))
        eq_('section', link.text())

    def test_hash_only(self):
        """Internal hash only."""
        link = pq_link(self.p, '[[#section 3]]')
        eq_('#section_3', link.attr('href'))
        eq_('#section 3', link.text())

    def test_link_name(self):
        """Internal link with name."""
        link = pq_link(self.p, '[[Installing Firefox|this name]]')
        eq_('/en-US/kb/installing-firefox', link.attr('href'))
        eq_('this name', link.text())

    def test_link_with_extra_pipe(self):
        link = pq_link(self.p, '[[Installing Firefox|with|pipe]]')
        eq_('/en-US/kb/installing-firefox', link.attr('href'))
        eq_('with|pipe', link.text())

    def test_hash_name(self):
        """Internal hash with name."""
        link = pq_link(self.p, '[[#section 3|this name]]')
        eq_('#section_3', link.attr('href'))
        eq_('this name', link.text())
        assert not link.hasClass('new')

    def test_link_hash_name(self):
        """Internal link with hash and name."""
        link = pq_link(self.p, '[[Installing Firefox#section 3|this name]]')
        eq_('/en-US/kb/installing-firefox#section_3', link.attr('href'))
        eq_('this name', link.text())

    def test_link_hash_name_markup(self):
        """Internal link with hash and name."""
        text = '[[Installing Firefox#section 3|this name]]'
        eq_('<p><a href="/en-US/kb/installing-firefox#section_3"' +
            '>this name</a>\n</p>', self.p.parse(text))

    def test_simple_create(self):
        """Simple link for inexistent page."""
        link = pq_link(self.p, '[[A new page]]')
        assert link.hasClass('new')
        eq_('/en-US/kb/new?title=A+new+page', link.attr('href'))
        eq_('A new page', link.text())

    def test_link_edit_hash_name(self):
        """Internal link for inexistent page with hash and name."""
        link = pq_link(self.p, '[[A new page#section 3|this name]]')
        eq_('/en-US/kb/new?title=A+new+page#section_3', link.attr('href'))
        eq_('this name', link.text())

    def test_link_with_localization(self):
        """A link to an English doc with a local translation."""
        en_d = document(title='A doc')
        en_d.save()
        en_r = revision(document=en_d, is_approved=True)
        en_r.save()

        fr_d = document(parent=en_d, title='Une doc', locale='fr')
        fr_d.save()

        # Without an approved revision, link should go to en-US doc.
        link = pq(self.p.parse('[[A doc]]', locale='fr'))
        eq_('/en-US/kb/a-doc', link.find('a').attr('href'))
        eq_('A doc', link.find('a').text())

         # Approve a revision. Now link should go to fr doc.
        fr_r = revision(document=fr_d, is_approved=True)
        fr_r.save()
        link = pq(self.p.parse('[[A doc]]', locale='fr'))
        eq_('/fr/kb/une-doc', link.find('a').attr('href'))
        eq_('Une doc', link.find('a').text())


class TestWikiImageTags(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.d, self.r, self.p = doc_rev_parser(
            'Test content', 'Installing Firefox')
        self.img = image(title='test.jpg')

    def tearDown(self):
        self.img.delete()

    def test_empty(self):
        """Empty image tag markup does not change."""
        img = pq_img(self.p, '[[Image:]]', 'p')
        eq_('The image "" does not exist.', img.text())

    def test_simple(self):
        """Simple image tag markup."""
        img = pq_img(self.p, '[[Image:test.jpg]]', 'img')
        eq_('test.jpg', img.attr('alt'))
        eq_(self.img.file.url, img.attr('src'))

    def test_simple_fallback(self):
        """Fallback to English if current locale doesn't have the image."""
        img = pq_img(self.p, '[[Image:test.jpg]]', selector='img', locale='ja')
        eq_('test.jpg', img.attr('alt'))
        eq_(self.img.file.url, img.attr('src'))

    def test_full_fallback(self):
        """Find current locale's image, not the English one."""
        # first, pretend there is no English version
        self.img.locale = 'ja'
        self.img.save()
        img = pq_img(self.p, '[[Image:test.jpg]]', selector='img', locale='ja')
        eq_('test.jpg', img.attr('alt'))
        eq_(self.img.file.url, img.attr('src'))

        # then, create an English version
        en_img = image(title='test.jpg')
        # Ensure they're not equal
        self.assertNotEquals(en_img.file.url, self.img.file.url)

        # make sure there is no fallback
        img = pq_img(self.p, '[[Image:test.jpg]]', selector='img', locale='ja')
        eq_('test.jpg', img.attr('alt'))
        eq_(self.img.file.url, img.attr('src'))

        # now delete the English version
        self.img.delete()
        self.img = en_img  # don't break tearDown
        img = pq_img(self.p, '[[Image:test.jpg]]', selector='img', locale='ja')
        eq_('test.jpg', img.attr('alt'))
        eq_(self.img.file.url, img.attr('src'))

    def test_caption(self):
        """Give the image a caption."""
        self.img.title = 'img test.jpg'
        self.img.save()
        img_div = pq_img(self.p, '[[Image:img test.jpg|frame|my caption]]',
                         'div.img')
        img = img_div('img')
        caption = img_div.text()

        eq_(self.img.file.url, img.attr('src'))
        eq_('my caption', img.attr('alt'))
        eq_('my caption', caption)

    def test_page_link(self):
        """Link to a wiki page."""
        img_a = pq_img(self.p, '[[Image:test.jpg|page=Installing Firefox]]',
                       'a')
        img = img_a('img')

        eq_('test.jpg', img.attr('alt'))
        eq_(self.img.file.url, img.attr('src'))
        eq_('/en-US/kb/installing-firefox', img_a.attr('href'))

    def test_page_link_edit(self):
        """Link to a nonexistent wiki page."""
        img_a = pq_img(self.p, '[[Image:test.jpg|page=Article List]]', 'a')
        img = img_a('img')

        eq_('test.jpg', img.attr('alt'))
        eq_(self.img.file.url, img.attr('src'))
        assert img_a.hasClass('new')
        eq_('/en-US/kb/new?title=Article+List', img_a.attr('href'))

    def test_page_link_caption(self):
        """Link to a wiki page with caption and frame."""
        img_div = pq_img(self.p,
                         '[[Image:test.jpg|frame|page=A page|my caption]]',
                         'div.img')
        img_a = img_div('a')
        img = img_a('img')
        caption = img_div.text()

        eq_('my caption', img.attr('alt'))
        eq_('my caption', caption)
        eq_(self.img.file.url, img.attr('src'))
        assert img_a.hasClass('new')
        eq_('/en-US/kb/new?title=A+page', img_a.attr('href'))

    def test_link(self):
        """Link to an external page."""
        img_a = pq_img(self.p, '[[Image:test.jpg|link=http://test.com]]', 'a')
        img = img_a('img')

        eq_('test.jpg', img.attr('alt'))
        eq_(self.img.file.url, img.attr('src'))
        eq_('http://test.com', img_a.attr('href'))

    def test_link_caption(self):
        """Link to an external page with caption."""
        img_div = pq_img(self.p,
                         '[[Image:test.jpg|link=http://ab.us|frame|caption]]',
                         'div.img')
        img = img_div('img')
        img_a = img_div('a')

        eq_(self.img.file.url, img.attr('src'))
        eq_('http://ab.us', img_a.attr('href'))

    def test_link_align(self):
        """Link with align."""
        img_div = pq_img(self.p,
                         '[[Image:test.jpg|link=http://site.com|align=left]]',
                         'div.img')
        eq_('img align-left', img_div.attr('class'))

    def test_link_align_invalid(self):
        """Link with invalid align."""
        img = pq_img(self.p,
                     '[[Image:test.jpg|link=http://example.ro|align=inv]]')
        eq_('frameless', img.attr('class'))

    def test_link_valign(self):
        """Link with valign."""
        img = pq_img(self.p,
                     '[[Image:test.jpg|link=http://example.com|valign=top]]')
        eq_('vertical-align: top;', img.attr('style'))

    def test_link_valign_invalid(self):
        """Link with invalid valign."""
        img = pq_img(self.p,
                     '[[Image:test.jpg|link=http://example.com|valign=off]]')
        eq_(None, img.attr('style'))

    def test_alt(self):
        """Image alt attribute is overriden but caption is not."""
        img_div = pq_img(self.p,
                         '[[Image:test.jpg|alt=my alt|frame|my caption]]',
                         'div.img')
        img = img_div('img')
        caption = img_div.text()

        eq_('my alt', img.attr('alt'))
        eq_('my caption', caption)

    def test_alt_empty(self):
        """Image alt attribute can be empty."""
        img = pq_img(self.p, '[[Image:test.jpg|alt=|my caption]]')

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
            img = pq_img(self.p, '[[Image:test.jpg|alt=' + alt_sent + ']]')

            is_true = str(img).startswith('<img alt="' + alt_expected + '"')
            assert is_true, ('Expected "%s", sent "%s"' %
                             (alt_expected, alt_sent))

    def test_width(self):
        """Image width attribute set."""
        img = pq_img(self.p, '[[Image:test.jpg|width=10]]')

        eq_('10', img.attr('width'))

    def test_width_invalid(self):
        """Invalid image width attribute set to auto."""
        img = pq_img(self.p, '[[Image:test.jpg|width=invalid]]')

        eq_(None, img.attr('width'))

    def test_height(self):
        """Image height attribute set."""
        img = pq_img(self.p, '[[Image:test.jpg|height=10]]')

        eq_('10', img.attr('height'))

    def test_height_invalid(self):
        """Invalid image height attribute set to auto."""
        img = pq_img(self.p, '[[Image:test.jpg|height=invalid]]')

        eq_(None, img.attr('height'))

    def test_frame(self):
        """Image has frame if specified."""
        img_div = pq_img(self.p, '[[Image:test.jpg|frame|caption]]', 'div.img')
        assert not img_div('img').hasClass('frameless')
        eq_('caption', img_div('img').attr('alt'))
        eq_('caption', img_div.text())
        eq_(self.img.file.url, img_div('img').attr('src'))

    def test_frameless_link(self):
        """Image has frameless class and link if specified."""
        img_a = pq_img(self.p,
                       '[[Image:test.jpg|page=Installing Firefox]]', 'a')
        img = img_a('img')
        eq_('frameless', img.attr('class'))
        eq_('/en-US/kb/installing-firefox', img_a.attr('href'))
