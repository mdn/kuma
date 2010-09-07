from django.conf import settings

from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.parser import (WikiParser, _build_template_params as _btp,
                         _format_template_content as _ftc, _key_split,
                         PATTERNS)
from sumo.tests import TestCase
from wiki.tests import document, revision


def pq_link(p, text):
    return pq(p.parse(text))('a')


def doc_rev_parser(content, title='Installing Firefox'):
    p = WikiParser(wiki_hooks=True)
    d = document(title=title)
    d.save()
    r = revision(document=d, content=content, is_approved=True)
    r.save()
    return (d, r, p)


def markup_helper(content, markup, title='Template:test'):
    p = doc_rev_parser(content, title)[2]
    doc = pq(p.parse(markup))
    return (doc, p)


class SimpleSyntaxTestCase(TestCase):
    """Simple syntax regexing, like {note}...{/note}, {key Ctrl+K}"""
    fixtures = ['users.json']

    def test_note_simple(self):
        """Simple note syntax"""
        p = WikiParser()
        doc = pq(p.parse('{note}this is a note{/note}'))
        eq_('this is a note', doc('div.note').text())

    def test_warning_simple(self):
        """Simple warning syntax"""
        p = WikiParser()
        doc = pq(p.parse('{warning}this is a warning{/warning}'))
        eq_('this is a warning', doc('div.warning').text())

    def test_warning_multiline(self):
        """Multiline warning syntax"""
        p = WikiParser()
        doc = pq(p.parse('{warning}\nthis is a warning\n{/warning}'))
        eq_('this is a warning', doc('div.warning').text())

    def test_warning_multiline_breaks(self):
        """Multiline breaks warning syntax"""
        p = WikiParser()
        doc = pq(p.parse('\n\n{warning}\n\nthis is a warning\n\n'
                         '{/warning}\n\n'))
        eq_('this is a warning', doc('div.warning').text())

    def test_general_warning_note(self):
        """A bunch of wiki text with {warning} and {note}"""
        p = WikiParser()
        doc = pq(p.parse('\n\n{warning}\n\nthis is a warning\n\n{note}'
                         'this is a note{warning}!{/warning}{/note}'
                         "[[Installing Firefox]] '''internal''' ''link''"
                         '{/warning}\n\n'))
        eq_('!', doc('div.warning div.warning').text())
        eq_('this is a note !', doc('div.note').text())
        eq_('Installing Firefox', doc('a').text())
        eq_('internal', doc('strong').text())
        eq_('link', doc('em').text())

    def test_key_inline(self):
        """{key} stays inline"""
        p = WikiParser()
        doc = pq(p.parse('{key Cmd+Shift+Q}'))
        eq_(1, len(doc('p')))
        eq_(u'<span class="key">Cmd</span> + <span class="key">Shift</span>'
            u' + <span class="key">Q</span>', doc.html().replace('\n', ''))

    def test_template_inline(self):
        """Inline templates are not wrapped in <p>s"""
        doc, p = markup_helper('<span class="key">{{{1}}}</span>',
                               '[[T:test|Cmd]] + [[T:test|Shift]]')
        eq_(1, len(doc('p')))

    def test_template_multiline(self):
        """Multiline templates are wrapped in <p>s"""
        doc, p = markup_helper('<span class="key">\n{{{1}}}</span>',
                               '[[T:test|Cmd]]')
        eq_(3, len(doc('p')))

    def test_key_split_callback(self):
        """The _key_split regex callback does what it claims"""
        key_p = PATTERNS[2][0]
        # Multiple keys, with spaces
        eq_('<span class="key">ctrl</span> + <span class="key">alt</span> + '
            '<span class="key">del</span>',
            key_p.sub(_key_split, '{key ctrl + alt +   del}'))
        # Single key with spaces in it
        eq_('<span class="key">a key</span>',
            key_p.sub(_key_split, '{key a key}'))
        # Multiple keys with quotes and spaces
        eq_('<span class="key">"Param-One" and</span> + <span class="key">'
            'param</span> + <span class="key">two</span>',
            key_p.sub(_key_split, '{key  "Param-One" and + param+two}'))
        eq_('<span class="key">multi\nline</span> + '
            '<span class="key">me</span>',
            key_p.sub(_key_split, '{key multi\nline\n+me}'))

    def test_key_split_brace_callback(self):
        """Adding brace inside {key ...}"""
        key_p = PATTERNS[2][0]
        eq_('<span class="key">ctrl</span> + <span class="key">and</span> '
            'Here is }',
            key_p.sub(_key_split, '{key ctrl + and} Here is }'))
        eq_('<span class="key">ctrl</span> + <span class="key">and</span> + '
            '<span class="key">{</span>',
            key_p.sub(_key_split, '{key ctrl + and + {}'))

    def test_simple_inline_custom(self):
        """Simple custom inline syntax: menu, button, filepath"""
        p = WikiParser()
        tags = ['menu', 'button', 'filepath']
        for tag in tags:
            doc = pq(p.parse('{%s this is a %s}' % (tag, tag)))
            eq_('this is a ' + tag, doc('span.' + tag).text())

    def test_general_warning_note_inline_custom(self):
        """A mix of custom inline syntax with warnings and notes"""
        p = WikiParser()
        doc = pq(p.parse('\n\n{warning}\n\nthis is a {button warning}\n{note}'
                         'this is a {menu note}{warning}!{/warning}{/note}'
                         "'''{filepath internal}''' ''{menu hi!}''{/warning}"))
        eq_('warning', doc('div.warning span.button').text())
        eq_('this is a note !', doc('div.note').text())
        eq_('note', doc('div.warning div.note span.menu').text())
        eq_('internal', doc('strong span.filepath').text())
        eq_('hi!', doc('em span.menu').text())


class TestWikiTemplate(TestCase):
    fixtures = ['users.json']

    def test_template(self):
        """Simple template markup."""
        doc = markup_helper('Test content', '[[Template:test]]')[0]
        eq_('Test content', doc.text())

    def test_template_does_not_exist(self):
        """Return a message if template does not exist"""
        p = WikiParser(wiki_hooks=True)
        doc = pq(p.parse('[[Template:test]]'))
        eq_('The template "test" does not exist.', doc.text())

    def test_template_anonymous_params(self):
        """Template markup with anonymous parameters."""
        doc, p = markup_helper('{{{1}}}:{{{2}}}', '[[Template:test|one|two]]')
        eq_('one:two', doc.text())
        doc = pq(p.parse('[[T:test|two|one]]'))
        eq_('two:one', doc.text())

    def test_template_named_params(self):
        """Template markup with named parameters."""
        doc, p = markup_helper('{{{a}}}:{{{b}}}',
                             '[[Template:test|a=one|b=two]]')
        eq_('one:two', doc.text())
        doc = pq(p.parse('[[T:test|a=two|b=one]]'))
        eq_('two:one', doc.text())

    def test_template_numbered_params(self):
        """Template markup with numbered parameters."""
        doc, p = markup_helper('{{{1}}}:{{{2}}}',
                               '[[Template:test|2=one|1=two]]')
        eq_('two:one', doc.text())
        doc = pq(p.parse('[[T:test|2=two|1=one]]'))
        eq_('one:two', doc.text())

    def test_template_wiki_markup(self):
        """A template with wiki markup"""
        doc = markup_helper("{{{1}}}:{{{2}}}\n''wiki''\n'''markup'''",
                            '[[Template:test|2=one|1=two]]')[0]

        eq_('two:one', doc('p')[1].text.replace('\n', ''))
        eq_('wiki', doc('em')[0].text)
        eq_('markup', doc('strong')[0].text)

    def test_template_args_inline_wiki_markup(self):
        """Args that contain inline wiki markup are parsed"""
        doc = markup_helper('{{{1}}}\n\n{{{2}}}',
                            "[[Template:test|'''one'''|''two'']]")[0]

        eq_("<p/><p><strong>one</strong></p><p><em>two</em></p><p/>",
            doc.html().replace('\n', ''))

    def test_template_args_block_wiki_markup(self):
        """Args that contain block level wiki markup aren't parsed"""
        doc = markup_helper('{{{1}}}\n\n{{{2}}}',
                            "[[Template:test|* ordered|# list]]")[0]

        eq_("<p/><p>* ordered</p><p># list</p><p/>",
            doc.html().replace('\n', ''))

    def test_format_template_content_named(self):
        """_ftc handles named arguments"""
        eq_('ab', _ftc('{{{some}}}{{{content}}}',
                       {'some': 'a', 'content': 'b'}))

    def test_format_template_content_numbered(self):
        """_ftc handles numbered arguments"""
        eq_('a:b', _ftc('{{{1}}}:{{{2}}}', {'1': 'a', '2': 'b'}))

    def test_build_template_params_anonymous(self):
        """_btp handles anonymous arguments"""
        eq_({'1': '<span>a</span>', '2': 'test'},
            _btp(['<span>a</span>', 'test']))

    def test_build_template_params_numbered(self):
        """_btp handles numbered arguments"""
        eq_({'20': 'a', '10': 'test'}, _btp(['20=a', '10=test']))

    def test_build_template_params_named(self):
        """_btp handles only named-arguments"""
        eq_({'a': 'b', 'hi': 'test'}, _btp(['hi=test', 'a=b']))

    def test_build_template_params_named_anonymous(self):
        """_btp handles mixed named and anonymous arguments"""
        eq_({'1': 'a', 'hi': 'test'}, _btp(['hi=test', 'a']))

    def test_build_template_params_named_numbered(self):
        """_btp handles mixed named and numbered arguments"""
        eq_({'10': 'a', 'hi': 'test'}, _btp(['hi=test', '10=a']))

    def test_build_template_params_named_anonymous_numbered(self):
        """_btp handles mixed named, anonymous and numbered arguments"""
        eq_({'1': 'a', 'hi': 'test', '3': 'z'}, _btp(['hi=test', 'a', '3=z']))


class TestWikiInclude(TestCase):
    fixtures = ['users.json']

    def test_revision_include(self):
        """Simple include markup."""
        p = doc_rev_parser('Test content', 'Test title')[2]

        # Existing title returns document's content
        doc = pq(p.parse('[[Include:Test title]]'))
        eq_('Test content', doc.text())

        # Nonexisting title returns 'Document not found'
        doc = pq(p.parse('[[Include:Another title]]'))
        eq_('The document "Another title" does not exist.', doc.text())


class TestWikiParser(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.d, self.r, self.p = doc_rev_parser(
            'Test content', 'Installing Firefox')

    def test_image_path_sanity(self):
        """Image URLs are prefixed with the upload path."""
        eq_(settings.WIKI_UPLOAD_URL + 'file.png',
            self.p._getImagePath('file.png'))

    def test_image_path_special_chars(self):
        """Image URLs with Unicode are prefixed with the upload path."""
        eq_(settings.WIKI_UPLOAD_URL + 'parl%C3%A9%20Fran%C3%A7ais.png',
            self.p._getImagePath(u'parl\u00e9 Fran\u00e7ais.png'))

    def test_image_params_page(self):
        """_buildImageParams handles wiki pages."""
        items = ['page=Installing Firefox']
        params = self.p._buildImageParams(items)
        eq_('/en-US/kb/installing-firefox', params['link'])

    def test_image_params_link(self):
        """_buildImageParams handles external links."""
        items = ['link=http://example.com']
        params = self.p._buildImageParams(items)
        eq_('http://example.com', params['link'])

    def test_image_params_page_link(self):
        """_buildImageParams - wiki page overrides link."""
        items = ['page=Installing Firefox', 'link=http://example.com']
        params = self.p._buildImageParams(items)
        eq_('/en-US/kb/installing-firefox', params['link'])

    def test_image_params_align(self):
        """Align valid options."""
        align_vals = ('none', 'left', 'center', 'right')
        for align in align_vals:
            items = ['align=' + align]
            params = self.p._buildImageParams(items)
            eq_(align, params['align'])

    def test_image_params_align_invalid(self):
        """Align invalid options."""
        items = ['align=zzz']
        params = self.p._buildImageParams(items)
        assert not 'align' in params, 'Align is present in params'

    def test_image_params_valign(self):
        """Vertical align valid options."""
        valign_vals = ('baseline', 'sub', 'super', 'top', 'text-top',
                       'middle', 'bottom', 'text-bottom')
        for valign in valign_vals:
            items = ['valign=' + valign]
            params = self.p._buildImageParams(items)
            eq_(valign, params['valign'])

    def test_image_params_valign_invalid(self):
        """Vertical align invalid options."""
        items = ['valign=zzz']
        params = self.p._buildImageParams(items)
        assert not 'valign' in params, 'Vertical align is present in params'

    def test_image_params_alt(self):
        """Image alt override."""
        items = ['alt=some alternative text']
        params = self.p._buildImageParams(items)
        eq_('some alternative text', params['alt'])

    def test_image_params_frameless(self):
        """Frameless image."""
        items = ['frameless']
        params = self.p._buildImageParams(items)
        eq_(True, params['frameless'])

    def test_image_params_width_height(self):
        """Image width."""
        items = ['width=10', 'height=20']
        params = self.p._buildImageParams(items)
        eq_('10', params['width'])
        eq_('20', params['height'])

    def test_get_wiki_link(self):
        """Wiki links are properly built for existing pages."""
        eq_('/en-US/kb/installing-firefox',
            self.p._getWikiLink('Installing Firefox'))


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

    def test_simple_markup(self):
        text = '[[Installing Firefox]]'
        eq_('<p><a href="/en-US/kb/installing-firefox" rel="nofollow">' +
            'Installing Firefox</a></p>',
            self.p.parse(text).replace('\n', ''))

    def test_link_hash(self):
        """Internal link with hash."""
        link = pq_link(self.p, '[[Installing Firefox#section name]]')
        eq_('/en-US/kb/installing-firefox#section_name', link.attr('href'))
        eq_('Installing Firefox#section name', link.text())

    def test_link_hash_markup(self):
        """Internal link with hash."""
        text = '[[Installing Firefox#section name]]'
        eq_('<p><a href="/en-US/kb/installing-firefox#section_name"' +
                ' rel="nofollow">Installing Firefox#section name</a></p>',
            self.p.parse(text).replace('\n', ''))

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

    def test_link_hash_name(self):
        """Internal link with hash and name."""
        link = pq_link(self.p, '[[Installing Firefox#section 3|this name]]')
        eq_('/en-US/kb/installing-firefox#section_3', link.attr('href'))
        eq_('this name', link.text())

    def test_link_hash_name_markup(self):
        """Internal link with hash and name."""
        text = '[[Installing Firefox#section 3|this name]]'
        eq_('<p><a href="/en-US/kb/installing-firefox#section_3"' +
            ' rel="nofollow">this name</a>\n</p>', self.p.parse(text))

    def test_simple_create(self):
        """Simple link for inexistent page."""
        link = pq_link(self.p, '[[A new page]]')
        eq_('/kb/new?title=A+new+page', link.attr('href'))
        eq_('A new page', link.text())

    def test_link_edit_hash_name(self):
        """Internal link for inexistent page with hash and name."""
        link = pq_link(self.p, '[[A new page#section 3|this name]]')
        eq_('/kb/new?title=A+new+page#section_3', link.attr('href'))
        eq_('this name', link.text())


def pq_img(p, text, selector='div.img'):
    doc = pq(p.parse(text))
    return doc(selector)


class TestWikiImageTags(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.d, self.r, self.p = doc_rev_parser(
            'Test content', 'Installing Firefox')

    def test_empty(self):
        """Empty image tag markup does not change."""
        img = pq_img(self.p, '[[Image:]]', 'img')
        eq_('', img.attr('alt'))
        eq_('/img/wiki_up/', img.attr('src'))

    def test_simple(self):
        """Simple image tag markup."""
        img = pq_img(self.p, '[[Image:file.png]]', 'img')
        eq_('file.png', img.attr('alt'))
        eq_('/img/wiki_up/file.png', img.attr('src'))

    def test_caption(self):
        """Give the image a caption."""
        img_div = pq_img(self.p, '[[Image:img file.png|my caption]]')
        img = img_div('img')
        caption = img_div.text()

        eq_('/img/wiki_up/img%20file.png', img.attr('src'))
        eq_('my caption', img.attr('alt'))
        eq_('my caption', caption)

    def test_page_link(self):
        """Link to a wiki page."""
        img_div = pq_img(self.p, '[[Image:file.png|page=Installing Firefox]]')
        img_a = img_div('a')
        img = img_a('img')
        caption = img_div.text()

        eq_('file.png', img.attr('alt'))
        eq_('file.png', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('/en-US/kb/installing-firefox', img_a.attr('href'))

    def test_page_link_edit(self):
        """Link to a nonexistent wiki page."""
        img_div = pq_img(self.p, '[[Image:file.png|page=Article List]]')
        img_a = img_div('a')
        img = img_a('img')
        caption = img_div.text()

        eq_('file.png', img.attr('alt'))
        eq_('file.png', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('/kb/new?title=Article+List', img_a.attr('href'))

    def test_page_link_caption(self):
        """Link to a wiki page with caption."""
        img_div = pq_img(self.p,
                         '[[Image:file.png|page=Article List|my caption]]')
        img_a = img_div('a')
        img = img_a('img')
        caption = img_div.text()

        eq_('my caption', img.attr('alt'))
        eq_('my caption', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('/kb/new?title=Article+List', img_a.attr('href'))

    def test_link(self):
        """Link to an external page."""
        img_div = pq_img(self.p, '[[Image:file.png|link=http://example.com]]')
        img_a = img_div('a')
        img = img_a('img')
        caption = img_div.text()

        eq_('file.png', img.attr('alt'))
        eq_('file.png', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('http://example.com', img_a.attr('href'))

    def test_link_caption(self):
        """Link to an external page with caption."""
        img_div = pq_img(self.p,
                         '[[Image:file.png|link=http://example.com|caption]]')
        img_a = img_div('a')
        img = img_div('img')
        caption = img_div.text()

        eq_('caption', img.attr('alt'))
        eq_('caption', caption)
        eq_('/img/wiki_up/file.png', img.attr('src'))
        eq_('http://example.com', img_a.attr('href'))

    def test_link_align(self):
        """Link with align."""
        img_div = pq_img(self.p,
                  '[[Image:file.png|link=http://site.com|align=left]]')
        eq_('img align-left', img_div.attr('class'))

    def test_link_align_invalid(self):
        """Link with invalid align."""
        img_div = pq_img(self.p,
                         '[[Image:file.png|link=http://example.ro|align=inv]]')
        eq_('img', img_div.attr('class'))

    def test_link_valign(self):
        """Link with valign."""
        img = pq_img(
            self.p,
            '[[Image:file.png|link=http://example.com|valign=top]]', 'img')
        eq_('vertical-align: top;', img.attr('style'))

    def test_link_valign_invalid(self):
        """Link with invalid valign."""
        img = pq_img(
            self.p,
            '[[Image:file.png|link=http://example.com|valign=off]]', 'img')
        eq_(None, img.attr('style'))

    def test_alt(self):
        """Image alt attribute is overriden but caption is not."""
        img_div = pq_img(self.p, '[[Image:img.png|alt=my alt|my caption]]')
        img = img_div('img')
        caption = img_div.text()

        eq_('my alt', img.attr('alt'))
        eq_('my caption', caption)

    def test_alt_empty(self):
        """Image alt attribute can be empty."""
        img = pq_img(self.p, '[[Image:img.png|alt=|my caption]]', 'img')

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
            img_div = pq_img(self.p, '[[Image:img.png|alt=' + alt_sent + ']]')
            img = img_div('img')

            is_true = str(img).startswith('<img alt="' + alt_expected + '"')
            assert is_true, ('Expected "%s", sent "%s"' %
                             (alt_expected, alt_sent))

    def test_width(self):
        """Image width attribute set."""
        img_div = pq_img(self.p, '[[Image:img.png|width=10]]')
        img = img_div('img')

        eq_('10', img.attr('width'))

    def test_width_invalid(self):
        """Invalid image width attribute set to auto."""
        img_div = pq_img(self.p, '[[Image:img.png|width=invalid]]')
        img = img_div('img')

        eq_(None, img.attr('width'))

    def test_height(self):
        """Image height attribute set."""
        img_div = pq_img(self.p, '[[Image:img.png|height=10]]')
        img = img_div('img')

        eq_('10', img.attr('height'))

    def test_height_invalid(self):
        """Invalid image height attribute set to auto."""
        img_div = pq_img(self.p, '[[Image:img.png|height=invalid]]')
        img = img_div('img')

        eq_(None, img.attr('height'))

    def test_frameless(self):
        """Image container has frameless class if specified."""
        img = pq_img(self.p, '[[Image:img.png|frameless|caption]]', 'img')
        eq_('frameless', img.attr('class'))
        eq_('caption', img.attr('alt'))
        eq_('/img/wiki_up/img.png', img.attr('src'))

    def test_frameless_link(self):
        """Image container has frameless class and link if specified."""
        img_a = pq_img(
            self.p, '[[Image:img.png|frameless|page=Installing Firefox]]', 'a')
        img = img_a('img')
        eq_('frameless', img.attr('class'))
        eq_('/en-US/kb/installing-firefox', img_a.attr('href'))
